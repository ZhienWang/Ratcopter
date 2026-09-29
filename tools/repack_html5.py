"""Rebuild the HTML5 build in build_output/ from mainGame/ without Solar2D.

Solar2D is no longer installed, so CoronaBuilder cannot produce a build. This
does the part of its job that changes when the game does, on top of the last
build it made:

  * main.lua and config.lua are compiled with Lua 5.1 (via the `lupa`
    package) and the bytecode is rewritten from the host's 64-bit layout to
    the 32-bit one the wasm runtime reads (only size_t differs: 8 -> 4
    bytes), then packed into resource.car, Corona's archive of compiled Lua.
  * Every other file in mainGame/ -- art, sounds, gameSetting.csv -- is
    swapped into ratcopter.data, the Emscripten file package, adding any the
    old build did not have.
  * The package index inside ratcopter.bin (a zip of ratcopter.js and
    ratcopter.wasm) is rewritten to match.

The wasm runtime, index.html and everything the old build carried that is not
in mainGame/ (widget themes, icons, the vk plugin shim) are kept as they are.
build.settings is deliberately NOT updated: CoronaBuilder read it at build
time, so the copy in the package is whatever that last real build used, and
the current file has only ever been checked against a build that never ran.

Run from the repo root:

    python tools/repack_html5.py            # rebuild build_output/ in place
    python tools/repack_html5.py --check    # self-tests only, write nothing
"""

import io
import json
import os
import re
import struct
import sys
import uuid
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "mainGame")
OUT = os.path.join(ROOT, "build_output", "ratcopter.html5")
BIN = os.path.join(OUT, "ratcopter.bin")
DATA = os.path.join(OUT, "ratcopter.data")

LUA_FILES = ["main.lua", "config.lua"]      # compiled into resource.car as .lu
SKIP = {"build.settings"}                   # see the docstring
MIRRORED = ("/Assets/", "/Sounds/")         # package dirs kept identical to mainGame/


# ---------------------------------------------------------------- bytecode

HEADER_64 = b"\x1bLuaQ\x00\x01\x04\x08\x04\x08\x00"   # host: size_t 8
HEADER_32 = b"\x1bLuaQ\x00\x01\x04\x04\x04\x08\x00"   # wasm: size_t 4


class Reader:
    def __init__(self, b, size_t):
        self.b, self.i, self.st = b, 0, size_t

    def take(self, n):
        v = self.b[self.i:self.i + n]
        assert len(v) == n, "truncated bytecode"
        self.i += n
        return v

    def int(self):
        return struct.unpack("<i", self.take(4))[0]

    def byte(self):
        return self.take(1)[0]

    def string(self):
        n = struct.unpack("<Q" if self.st == 8 else "<I", self.take(self.st))[0]
        return None if n == 0 else self.take(n)


class Writer:
    def __init__(self, size_t):
        self.o, self.st = io.BytesIO(), size_t

    def raw(self, b):
        self.o.write(b)

    def int(self, v):
        self.o.write(struct.pack("<i", v))

    def byte(self, v):
        self.o.write(bytes([v]))

    def string(self, s):
        n = 0 if s is None else len(s)
        self.o.write(struct.pack("<Q" if self.st == 8 else "<I", n))
        if s:
            self.o.write(s)


def copy_function(r, w):
    """Lua 5.1 lundump.c LoadFunction, re-emitted field by field."""
    w.string(r.string())                        # source
    w.int(r.int()); w.int(r.int())              # linedefined, lastlinedefined
    for _ in range(4):                          # nups, numparams, is_vararg, maxstack
        w.byte(r.byte())
    n = r.int(); w.int(n); w.raw(r.take(4 * n)) # code
    n = r.int(); w.int(n)                       # constants
    for _ in range(n):
        t = r.byte(); w.byte(t)
        if t == 1:
            w.byte(r.byte())
        elif t == 3:
            w.raw(r.take(8))
        elif t == 4:
            w.string(r.string())
        else:
            assert t == 0, f"bad constant type {t}"
    n = r.int(); w.int(n)                       # nested functions
    for _ in range(n):
        copy_function(r, w)
    n = r.int(); w.int(n); w.raw(r.take(4 * n)) # lineinfo
    n = r.int(); w.int(n)                       # locvars
    for _ in range(n):
        w.string(r.string()); w.int(r.int()); w.int(r.int())
    n = r.int(); w.int(n)                       # upvalue names
    for _ in range(n):
        w.string(r.string())


def convert(b, from_st, to_st):
    src_h = HEADER_64 if from_st == 8 else HEADER_32
    dst_h = HEADER_64 if to_st == 8 else HEADER_32
    assert b[:12] == src_h, f"unexpected bytecode header {b[:12]!r}"
    r, w = Reader(b, from_st), Writer(to_st)
    r.i = 12
    w.raw(dst_h)
    copy_function(r, w)
    assert r.i == len(b), "trailing bytes after main function"
    return w.o.getvalue()


def compile_lua(path, chunkname):
    from lupa.lua51 import LuaRuntime
    lua = LuaRuntime(encoding=None)
    src = open(path, "rb").read()
    dump = lua.eval("""function(s, name)
        local f, e = loadstring(s, name)
        if not f then error(e) end
        return string.dump(f)
    end""")
    b = dump(src, chunkname.encode())
    return convert(b, 8, 4)


# ---------------------------------------------------------------- resource.car
# Layout, as written by CoronaBuilder and read back here:
#   "rac" 0x01 | u32 1 | u32 index_bytes | u32 count
#   count x ( u32 1 | u32 data_offset | u32 name_len | name\0 padded to 4 )
#   per entry at data_offset: u32 2 | u32 4 + padded_len | u32 len | data padded to 4
#   end marker: u32 0xffffffff | u32 0

CAR_END = struct.pack("<II", 0xFFFFFFFF, 0)


def pad4(n):
    return (n + 3) & ~3


def read_car(b):
    assert b[:4] == b"rac\x01", "not a resource.car"
    one, index_bytes, count = struct.unpack_from("<III", b, 4)
    assert one == 1
    i, entries = 16, []
    for _ in range(count):
        kind, off, nlen = struct.unpack_from("<III", b, i)
        assert kind == 1
        name = b[i + 12:i + 12 + nlen].decode()
        i += 12 + pad4(nlen + 1)
        tag, _, size = struct.unpack_from("<III", b, off)
        assert tag == 2
        entries.append((name, b[off + 12:off + 12 + size]))
    assert i == 12 + index_bytes
    assert b.endswith(CAR_END)
    return entries


def write_car(entries):
    index = io.BytesIO()
    body = io.BytesIO()
    index_bytes = 4 + sum(12 + pad4(len(n) + 1) for n, _ in entries)
    base = 12 + index_bytes
    for name, data in entries:
        nb = name.encode()
        index.write(struct.pack("<III", 1, base + body.tell(), len(nb)))
        index.write(nb + b"\x00" * (pad4(len(nb) + 1) - len(nb)))
        body.write(struct.pack("<III", 2, 4 + pad4(len(data)), len(data)))
        body.write(data + b"\x00" * (pad4(len(data)) - len(data)))
    return (b"rac\x01" + struct.pack("<III", 1, index_bytes, len(entries))
            + index.getvalue() + body.getvalue() + CAR_END)


# ---------------------------------------------------------------- package

META_RE = re.compile(r"loadPackage\((\{\"files\".*?\})\)")


def read_bin():
    z = zipfile.ZipFile(BIN)
    members = [(i, z.read(i.filename)) for i in z.infolist()]
    js = dict((i.filename, b) for i, b in members)["ratcopter.js"].decode("latin-1")
    m = META_RE.search(js)
    assert m, "package metadata not found in ratcopter.js"
    return members, js, m, json.loads(m.group(1))


def write_bin(members, js):
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        for info, b in members:
            if info.filename == "ratcopter.js":
                b = js.encode("latin-1")
            zi = zipfile.ZipInfo(info.filename, info.date_time)
            zi.compress_type = info.compress_type
            zi.external_attr = info.external_attr
            z.writestr(zi, b)
    return out.getvalue()


def source_files():
    """Package path -> bytes for everything mainGame/ ships besides Lua."""
    files = {}
    for dirpath, _, names in os.walk(SRC):
        for n in names:
            full = os.path.join(dirpath, n)
            rel = os.path.relpath(full, SRC).replace(os.sep, "/")
            if rel in SKIP or rel.endswith(".lua"):
                continue
            files["/" + rel] = open(full, "rb").read()
    return files


# ---------------------------------------------------------------- self-tests

def self_test():
    members, js, m, meta = read_bin()
    data = open(DATA, "rb").read()
    assert meta["remote_package_size"] == len(data)
    car_meta = next(f for f in meta["files"] if f["filename"] == "/resource.car")
    car = data[car_meta["start"]:car_meta["end"]]

    # The car reader/writer reproduce CoronaBuilder's own archive exactly.
    entries = read_car(car)
    assert write_car(entries) == car, "resource.car does not round-trip"

    # The bytecode rewriter reproduces CoronaBuilder's own 32-bit bytecode
    # exactly (32 -> 32), and 32 -> 64 -> 32 loses nothing.
    for name, b in entries:
        assert convert(b, 4, 4) == b, f"{name}: 32->32 not identical"
        assert convert(convert(b, 4, 8), 8, 4) == b, f"{name}: 32->64->32 not identical"

    # A freshly compiled main.lua survives 64 -> 32 -> 64 byte for byte, and
    # the result still loads in a real Lua 5.1.
    from lupa.lua51 import LuaRuntime
    lua = LuaRuntime(encoding=None)
    src = open(os.path.join(SRC, "main.lua"), "rb").read()
    dump64 = lua.eval("function(s) return string.dump(assert(loadstring(s, 'main.lua'))) end")(src)
    b32 = convert(dump64, 8, 4)
    assert convert(b32, 4, 8) == dump64, "main.lua: 64->32->64 not identical"
    ok = lua.eval("function(b) return loadstring(b) ~= nil end")(convert(b32, 4, 8))
    assert ok, "converted main.lua no longer loads"

    # Re-zipping the untouched .bin gives back the same members byte for byte.
    z = zipfile.ZipFile(io.BytesIO(write_bin(members, js)))
    assert [(i.filename, z.read(i.filename)) for i in z.infolist()] == \
        [(i.filename, b) for i, b in members], ".bin does not round-trip"
    print("self-tests passed: car round-trip, bytecode 32<->64, package index")
    return members, js, m, meta, data, entries


def main():
    members, js, m, meta, data, entries = self_test()
    if "--check" in sys.argv:
        return

    # resource.car: replace the compiled game code, keep the rest (the plugin
    # shims) exactly as CoronaBuilder wrote them.
    new_lu = {os.path.splitext(n)[0] + ".lu": compile_lua(os.path.join(SRC, n), n) for n in LUA_FILES}
    car_entries = [(n, new_lu.pop(n, b)) for n, b in entries] + sorted(new_lu.items())
    car = write_car(car_entries)

    # ratcopter.data: old files in their old order, with anything mainGame/
    # now ships swapped in, then files the old build never had.
    fresh = source_files()
    fresh["/resource.car"] = car
    blob, files, changed, added, removed = io.BytesIO(), [], [], [], []
    for f in meta["files"]:
        name = f["filename"]
        old = data[f["start"]:f["end"]]
        # Game art and sound mirror mainGame/ exactly, so art deleted there
        # (or replaced under a new name) leaves the build too. Everything
        # else the old build carried -- widget themes, icons, the plugin
        # shim -- came from Solar2D itself and is kept.
        if name.startswith(MIRRORED) and name not in fresh:
            removed.append(name)
            continue
        b = fresh.pop(name, old)
        if b != old:
            changed.append(name)
        files.append(dict(f, start=blob.tell(), end=blob.tell() + len(b)))
        blob.write(b)
    for name in sorted(fresh):
        b = fresh[name]
        files.append({"audio": 1 if name.lower().endswith((".mp3", ".ogg", ".wav")) else 0,
                      "start": blob.tell(), "crunched": 0,
                      "end": blob.tell() + len(b), "filename": name})
        blob.write(b)
        added.append(name)
    new_data = blob.getvalue()

    build_id = str(uuid.uuid4())
    meta = dict(meta, files=files, remote_package_size=len(new_data), package_uuid=build_id)
    js = js[:m.start(1)] + json.dumps(meta, separators=(",", ":")) + js[m.end(1):]

    # Stamp both download URLs with this build's id. The .bin holds the byte
    # offsets into the .data, so the two only work as a matched pair -- and a
    # browser holding either one from an earlier build in its HTTP cache will
    # happily reuse it (it did: fresh .bin, cached .data, black screen, no
    # error). A URL no earlier build used cannot be answered from cache.
    stamp = build_id[:8]
    js, n = re.subn(r'REMOTE_PACKAGE_BASE="ratcopter\.data(\?v=[0-9a-f]+)?"',
                    f'REMOTE_PACKAGE_BASE="ratcopter.data?v={stamp}"', js)
    assert n == 1, "ratcopter.data URL not found in ratcopter.js"
    pages = {}
    for page in ("index.html", "index-nosplash.html", "index-debug.html"):
        path = os.path.join(OUT, page)
        if os.path.exists(path):
            html, n = re.subn(r'xml\.open\(\'GET\', "ratcopter\.bin(\?v=[0-9a-f]+)?"',
                              f'xml.open(\'GET\', "ratcopter.bin?v={stamp}"',
                              open(path, encoding="utf-8", newline="").read())
            assert n == 1, f"ratcopter.bin URL not found in {page}"
            pages[path] = html

    open(DATA, "wb").write(new_data)
    open(BIN, "wb").write(write_bin(members, js))
    for path, html in pages.items():
        open(path, "w", encoding="utf-8", newline="").write(html)
    print(f"build {stamp}: ratcopter.bin?v={stamp}, ratcopter.data?v={stamp}")
    print(f"changed {len(changed)}: {', '.join(changed)}")
    print(f"added   {len(added)}: {', '.join(added)}")
    print(f"removed {len(removed)}: {', '.join(removed)}")
    print(f"ratcopter.data {len(data)} -> {len(new_data)} bytes")


if __name__ == "__main__":
    main()
