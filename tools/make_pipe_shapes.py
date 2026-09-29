"""Generate the pipe-jaw artwork main.lua draws.

A pipe is two jaws (a top one and the same image flipped for the bottom), so
the gap between them can be moved at runtime -- that is what lets a clamp
pipe close slowly. Each jaw's inner end carries a shape: flat, a triangular
point, a pentagon's chamfered flat, a half-moon bulge, or a row of teeth.

Run from the repo root:

    python tools/make_pipe_shapes.py

Source art is the four existing full-pipe images in mainGame/Assets. Each is
a vertical column of texture -- every row of the pipe body is essentially the
same horizontal gradient, with speckles on top -- so a jaw of any height can
be rebuilt from one representative row, and the mouth rim redrawn to follow
whatever outline the shape asks for. Output is
mainGame/Assets/jaw_<skin>_<shape>.png.

NOTCH_PX and ART_HALF_FRAC below are mirrored by constants of the same name
in main.lua; they have to agree or the hitbox stops matching the art.
"""

import math
import os
import random

from PIL import Image

ASSETS = os.path.join("mainGame", "Assets")

# Skins, by the stem of the source file they are cut from.
SKINS = ["pipe", "pipe_rusty", "pipe_concrete", "pipe_mossy"]

JAW_W = 100      # matches the source art's width, so the body gradient maps 1:1
JAW_H = 560      # tall enough to run off the lane at any gap height, plus clamp travel
NOTCH_PX = 20    # deepest a shaped tip reaches past the flat gap edge
RIM_PX = 26      # thickness of the darker band at the pipe mouth

# How far into the gap each shape actually bites, as a fraction of NOTCH_PX.
# The broader the tight region a shape creates, the shallower it is made --
# a triangle is only tight at the exact centre and can afford full depth,
# while the pentagon holds its tight band across half the opening.
SHAPE_DEPTH = {
    "straight": 0.0,
    "triangle": 1.0,
    "halfmoon": 0.8,
    "pentagon": 0.65,
    # Kept last: seeds are handed out by position in this dict, so adding a
    # shape anywhere else would reshuffle the speckles on every existing jaw.
    # Three teeth, each a small triangle. Every tooth reaches the same depth,
    # so it is no crueller than a triangle at the tip -- just three times as
    # many tips to line up with -- and is trimmed a little for that.
    "teeth": 0.85,
}

TEETH = 3        # teeth across the visible body

# Triangle and half-moon are no longer drawn: in the game they became ground
# obstacles (tools/make_ground_obstacles.py). Their depths stay in
# SHAPE_DEPTH because each shape's speckle seed is its position in that dict,
# and dropping two entries would repaint every jaw after them.
RETIRED = {"triangle", "halfmoon"}

# The source art's opaque body spans x 18..81 of 100, so the drawn pipe is
# 63% of the image width. Shape profiles are defined across that visible
# body -- not the wider hitbox -- so a triangle comes to a point at the edge
# of the art you can actually see.
ART_HALF_FRAC = 0.63


def notch_at(shape, u):
    """Depth in px that a jaw's tip reaches past the flat edge, at -1<=u<=1
    across the visible body. Mirrored by shapeNotchPx() in main.lua."""
    depth = SHAPE_DEPTH[shape] * NOTCH_PX
    if depth <= 0:
        return 0.0
    a = abs(u)
    if a >= 1.0:
        return 0.0
    if shape == "triangle":
        return depth * (1.0 - a)
    if shape == "halfmoon":
        return depth * math.sqrt(max(0.0, 1.0 - a * a))
    if shape == "pentagon":
        flat = 0.45                      # tip is flat across the middle 45%
        if a <= flat:
            return depth
        return depth * (1.0 - (a - flat) / (1.0 - flat))
    if shape == "teeth":
        # A sawtooth of TEETH triangles tip-to-tip across -1..1. Written on
        # u rather than a so the middle tooth's point lands on u = 0 for an
        # odd count, which is where main.lua's pipeAim takes the tightest
        # point from.
        t = (u + 1.0) * TEETH / 2.0
        f = t - math.floor(t)
        return depth * (1.0 - abs(2.0 * f - 1.0))
    return 0.0


def sample_source(stem):
    """Pull the body gradient, a rim colour and a few speckles off a source pipe."""
    im = Image.open(os.path.join(ASSETS, stem + ".png")).convert("RGBA")
    w, h = im.size
    assert w == JAW_W, f"{stem}: expected {JAW_W}px wide source, got {w}"

    body = [im.getpixel((x, 200)) for x in range(w)]

    # The mouth rim is the darkest band just above the gap; average a few of
    # its rows so speckles do not skew the colour.
    rim_rows = range(415, 440)
    rim = []
    for x in range(w):
        px = [im.getpixel((x, y)) for y in rim_rows]
        opaque = [p for p in px if p[3] > 200]
        if opaque:
            rim.append(tuple(sum(c[i] for c in opaque) // len(opaque) for i in range(4)))
        else:
            rim.append(body[x])
    return body, rim


def build_jaw(shape, body, rim, seed):
    """Draw one top jaw: solid from the top, tip shaped at the bottom."""
    img = Image.new("RGBA", (JAW_W, JAW_H), (0, 0, 0, 0))
    px = img.load()

    flat_edge = JAW_H - NOTCH_PX  # where a straight jaw's gap edge sits
    half = ART_HALF_FRAC * JAW_W / 2.0
    centre = (JAW_W - 1) / 2.0

    tip = []
    for x in range(JAW_W):
        u = (x - centre) / half
        tip.append(flat_edge + notch_at(shape, u))

    for x in range(JAW_W):
        br, bg, bb, ba = body[x]
        rr, rg, rb, ra = rim[x]
        end = tip[x]
        if ba == 0:
            continue
        for y in range(JAW_H):
            if y >= end:
                # Antialias the one row the outline falls inside.
                frac = end - y
                if frac <= 0:
                    break
                a = int(ba * frac)
                px[x, y] = (rr, rg, rb, a)
                break
            if y > end - RIM_PX:
                px[x, y] = (rr, rg, rb, ra)
            else:
                px[x, y] = (br, bg, bb, ba)

    # Speckles, so a rebuilt jaw does not read as a flat extrusion next to
    # the source art. Seeded per (skin, shape) so regenerating is stable.
    rnd = random.Random(seed)
    # Kept well clear of x 18..27 and the mirror on the right: the source art
    # outlines the pipe with a dark edge there, and a speckle centred on it
    # smears that dark colour across the disc as a black blob.
    inset = 10
    lo = int(centre - half) + inset
    hi = int(centre + half) - inset
    for _ in range(26):
        x = rnd.randint(lo, hi)
        y = rnd.randint(6, JAW_H - RIM_PX - 8)
        r = rnd.randint(1, 3)
        base = px[x, y]
        if base[3] < 255:
            continue
        shade = rnd.choice((-20, -13, 12))
        col = tuple(max(0, min(255, c + shade)) for c in base[:3]) + (base[3],)
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if dx * dx + dy * dy <= r * r:
                    sx, sy = x + dx, y + dy
                    if 0 <= sx < JAW_W and 0 <= sy < JAW_H and px[sx, sy][3] > 0:
                        px[sx, sy] = col
    return img


def main():
    made = []
    for si, stem in enumerate(SKINS):
        body, rim = sample_source(stem)
        for shi, shape in enumerate(SHAPE_DEPTH):
            if shape in RETIRED:
                continue
            img = build_jaw(shape, body, rim, seed=si * 17 + shi)
            out = os.path.join(ASSETS, f"jaw_{stem}_{shape}.png")
            img.save(out, optimize=True)
            made.append((out, os.path.getsize(out)))
    total = sum(s for _, s in made)
    for path, size in made:
        print(f"  {path}  {size/1024:.1f} KB")
    print(f"{len(made)} files, {total/1024:.0f} KB total")


if __name__ == "__main__":
    main()
