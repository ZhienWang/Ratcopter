"""Generate the ground-obstacle artwork main.lua draws.

Two obstacles stand on the ground in place of a column's bottom pipe:

  pyramid  a stepped pyramid of bricks, `rows` courses high, each course one
           brick narrower than the one below (half a brick in from each side)
  hump     half an ellipse, w wide and h tall

each in a skin per theme -- clay sewer bricks and a sludge mound for the
sewer, sandstone blocks and a grassy hill for the surface. Output is
mainGame/Assets/<kind>_<theme>_<size>.png, size counting from 1.

Run from the repo root:

    python tools/make_ground_obstacles.py

Drawn at half size and doubled with nearest-neighbour, so the pixels come out
as chunky as the background art's. BRICK_W, BRICK_H, PYRAMID_ROWS and HUMPS
are mirrored in main.lua's GROUND table, whose surfaceAt() is the hitbox;
the outline drawn here is that same outline, so the two have to agree.
"""

import math
import os
import random

from PIL import Image

ASSETS = os.path.join("mainGame", "Assets")

BRICK_W = 28           # lane pixels
BRICK_H = 18
PYRAMID_ROWS = [3, 4, 5, 6]
HUMPS = [(150, 56), (190, 74), (230, 92)]   # (w, h) in lane pixels

SCALE = 2              # drawn at 1/SCALE, then blown up

PALETTES = {
    "sewer": {
        # old clay bricks: warmer than the green-grey wall behind them so a
        # pyramid reads as something in the way, not part of the scenery
        "brick": [(128, 70, 50), (138, 78, 54), (118, 64, 48), (146, 84, 58)],
        "brick_hi": (170, 104, 72),
        "mortar": (60, 46, 40),
        "outline": (26, 20, 18),
        "moss": [(84, 110, 56), (98, 126, 62)],
        "grime": (40, 34, 28),
        # sludge mound: dark silt with a slimy green crust
        "mound": [(84, 72, 46), (88, 76, 48), (80, 69, 44)],
        "mound_hi": (108, 94, 60),
        "crust": [(112, 156, 70), (124, 168, 76)],
        "speckle": (62, 54, 36),
        "stone": [(96, 98, 92), (80, 82, 78)],
        "bubble": (120, 156, 80),
    },
    "surface": {
        # sandstone blocks in the sand's own family, a shade brighter
        "brick": [(222, 186, 108), (230, 196, 118), (214, 178, 102), (236, 204, 128)],
        "brick_hi": (248, 224, 160),
        "mortar": (160, 120, 66),
        "outline": (84, 56, 30),
        "moss": None,
        "grime": (190, 150, 86),
        # grassy hill in the greens of the bushes along the horizon
        "mound": [(94, 200, 84), (86, 190, 78), (100, 208, 90)],
        "mound_hi": (140, 226, 120),
        "crust": [(116, 218, 100), (128, 226, 108)],
        "stone": None,
        "bubble": None,
        "shade": (66, 156, 64),
    },
}


def shade(c, d):
    return tuple(max(0, min(255, v + d)) for v in c[:3]) + (255,)


def outline(px, w, h, col):
    """Darken every filled pixel that touches an empty one (or the edge,
    except along the bottom, which stands on the ground)."""
    edge = []
    for y in range(h):
        for x in range(w):
            if px[x, y][3] == 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, -1), (0, 1)):
                nx, ny = x + dx, y + dy
                if ny >= h:
                    continue
                if nx < 0 or nx >= w or ny < 0 or px[nx, ny][3] == 0:
                    edge.append((x, y))
                    break
    for x, y in edge:
        px[x, y] = col + (255,)


def pyramid(rows, pal, rnd):
    bw, bh = BRICK_W // SCALE, BRICK_H // SCALE
    w, h = rows * bw, rows * bh
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    for k in range(rows):                     # course k, 0 at the bottom
        n = rows - k
        x0 = k * bw // 2
        y0 = h - (k + 1) * bh
        for b in range(n):
            base = rnd.choice(pal["brick"])
            # lower courses carry more grime
            grime = (rows - 1 - k) / max(1, rows - 1)
            for yy in range(bh):
                for xx in range(bw):
                    x, y = x0 + b * bw + xx, y0 + yy
                    if yy == bh - 1 or xx == bw - 1:
                        c = pal["mortar"]
                    elif yy == 0:
                        c = pal["brick_hi"]
                    else:
                        c = base
                        if rnd.random() < 0.06:
                            c = shade(c, rnd.choice((-14, 10)))
                    if pal["grime"] and yy > bh // 2 and rnd.random() < 0.25 * grime:
                        c = pal["grime"]
                    px[x, y] = c[:3] + (255,)
            # moss on the upper edge of some sewer bricks
            if pal["moss"] and rnd.random() < 0.35:
                start = rnd.randint(0, bw - 5)
                for xx in range(start, start + rnd.randint(3, 6)):
                    if xx < bw - 1:
                        px[x0 + b * bw + xx, y0] = rnd.choice(pal["moss"]) + (255,)
                        if rnd.random() < 0.5:
                            px[x0 + b * bw + xx, y0 + 1] = rnd.choice(pal["moss"]) + (255,)
    outline(px, w, h, pal["outline"])
    return img


def hump_top(i, w, h):
    """Top edge, in half-size pixels, of the column of pixels i."""
    cx = w / 2
    r = abs(i + 0.5 - cx) / (w / 2)
    if r >= 1:
        return None
    return h - h * math.sqrt(1 - r * r)


def hump(wl, hl, pal, rnd):
    w, h = wl // SCALE, hl // SCALE
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    for x in range(w):
        top = hump_top(x, w, h)
        if top is None:
            continue
        t0 = int(round(top))
        for y in range(t0, h):
            depth = y - t0
            c = rnd.choice(pal["mound"])
            if depth < (3 if pal["stone"] else 2):
                c = rnd.choice(pal["crust"])
            elif pal.get("speckle") and rnd.random() < 0.08:
                c = pal["speckle"]
            elif depth < 3 and x < w * 0.45:
                c = pal["mound_hi"]
            if pal.get("shade") and y > h * 0.6 + 0.15 * h * math.sin(x * 0.4):
                c = pal["shade"]
            px[x, y] = c[:3] + (255,)
    # stones and slime bubbles in the sewer mound
    if pal["stone"]:
        for _ in range(w // 10):
            x = rnd.randint(3, w - 4)
            top = hump_top(x, w, h)
            if top is None or h - top < 6:
                continue
            y = rnd.randint(int(top) + 3, h - 2)
            col = rnd.choice(pal["stone"])
            for dx in (-1, 0, 1):
                for dy in (0, 1):
                    if px[x + dx, min(h - 1, y + dy)][3]:
                        px[x + dx, min(h - 1, y + dy)] = col + (255,)
    if pal["bubble"]:
        for _ in range(w // 16):
            x = rnd.randint(2, w - 3)
            top = hump_top(x, w, h)
            if top is not None:
                px[x, int(round(top)) + 1] = pal["bubble"] + (255,)
    outline(px, w, h, pal["outline"])
    return img


def main():
    made = []
    for ti, (theme, pal) in enumerate(PALETTES.items()):
        for si, rows in enumerate(PYRAMID_ROWS, start=1):
            img = pyramid(rows, pal, random.Random(1000 + ti * 10 + si))
            made.append((img, f"pyramid_{theme}_{si}.png", (rows * BRICK_W, rows * BRICK_H)))
        for si, (wl, hl) in enumerate(HUMPS, start=1):
            img = hump(wl, hl, pal, random.Random(2000 + ti * 10 + si))
            made.append((img, f"hump_{theme}_{si}.png", (wl, hl)))
    total = 0
    for img, name, size in made:
        big = img.resize((img.width * SCALE, img.height * SCALE), Image.NEAREST)
        assert big.size == size, (name, big.size, size)
        out = os.path.join(ASSETS, name)
        big.save(out, optimize=True)
        total += os.path.getsize(out)
        print(f"  {out}  {big.size[0]}x{big.size[1]}  {os.path.getsize(out)/1024:.1f} KB")
    print(f"{len(made)} files, {total/1024:.0f} KB total")


if __name__ == "__main__":
    main()
