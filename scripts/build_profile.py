#!/usr/bin/env python3
"""Build the pixel-art SVGs for the GitHub profile README.

Reads data/profile.json and writes:
  assets/banner.svg        bouldering-wall header with an animated climber
  assets/routes.svg        skill "problems" (tape colour = focus, holds = skills)
  assets/sends/<repo>.svg  one card per project ("send log")

and refreshes the skills and send-log blocks in README.md (between the
<!-- skills:start/end --> and <!-- sends:start/end --> markers).

All text is drawn with a built-in 5x7 pixel font, because SVGs embedded in a
README cannot load web fonts. Standard library only:

    python3 scripts/build_profile.py
"""
from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "profile.json"
ASSETS = ROOT / "assets"

# ---------------------------------------------------------------- palette
TAPE = {
    "red": ("#e05a47", "#a63a2c"),
    "yellow": ("#f2c14e", "#b98a24"),
    "green": ("#5fb36b", "#3b7f47"),
    "blue": ("#4f93e6", "#2f63a8"),
    "purple": ("#a374dc", "#6f48a3"),
    "orange": ("#ee8a3a", "#b05e1e"),
    "pink": ("#e57bb0", "#a9507e"),
}
WALL = "#23253f"
SEAM = "#1a1c33"
BOLT = "#191a2e"
INK = "#12131f"  # panels / HUD
CHALK = "#ece8dc"
MUTED = "#8d93b0"
CARD = "#141a24"
CARD_EDGE = "#263042"
TEXT = "#c9d1d9"

# ------------------------------------------------------------- pixel font
# 5x7 glyphs, '#' = on. Variable width: a glyph is as wide as its rows.
_F = {
    "A": ".###.|#...#|#...#|#####|#...#|#...#|#...#",
    "B": "####.|#...#|#...#|####.|#...#|#...#|####.",
    "C": ".###.|#...#|#....|#....|#....|#...#|.###.",
    "D": "####.|#...#|#...#|#...#|#...#|#...#|####.",
    "E": "#####|#....|#....|####.|#....|#....|#####",
    "F": "#####|#....|#....|####.|#....|#....|#....",
    "G": ".###.|#...#|#....|#.###|#...#|#...#|.####",
    "H": "#...#|#...#|#...#|#####|#...#|#...#|#...#",
    "I": "###|.#.|.#.|.#.|.#.|.#.|###",
    "J": "..###|...#.|...#.|...#.|...#.|#..#.|.##..",
    "K": "#...#|#..#.|#.#..|##...|#.#..|#..#.|#...#",
    "L": "#....|#....|#....|#....|#....|#....|#####",
    "M": "#...#|##.##|#.#.#|#.#.#|#...#|#...#|#...#",
    "N": "#...#|#...#|##..#|#.#.#|#..##|#...#|#...#",
    "O": ".###.|#...#|#...#|#...#|#...#|#...#|.###.",
    "P": "####.|#...#|#...#|####.|#....|#....|#....",
    "Q": ".###.|#...#|#...#|#...#|#.#.#|#..#.|.##.#",
    "R": "####.|#...#|#...#|####.|#.#..|#..#.|#...#",
    "S": ".####|#....|#....|.###.|....#|....#|####.",
    "T": "#####|..#..|..#..|..#..|..#..|..#..|..#..",
    "U": "#...#|#...#|#...#|#...#|#...#|#...#|.###.",
    "V": "#...#|#...#|#...#|#...#|#...#|.#.#.|..#..",
    "W": "#...#|#...#|#...#|#.#.#|#.#.#|#.#.#|.#.#.",
    "X": "#...#|#...#|.#.#.|..#..|.#.#.|#...#|#...#",
    "Y": "#...#|#...#|.#.#.|..#..|..#..|..#..|..#..",
    "Z": "#####|....#|...#.|..#..|.#...|#....|#####",
    "0": ".###.|#...#|#..##|#.#.#|##..#|#...#|.###.",
    "1": ".#.|##.|.#.|.#.|.#.|.#.|###",
    "2": ".###.|#...#|....#|...#.|..#..|.#...|#####",
    "3": "####.|....#|....#|.###.|....#|....#|####.",
    "4": "...#.|..##.|.#.#.|#..#.|#####|...#.|...#.",
    "5": "#####|#....|####.|....#|....#|#...#|.###.",
    "6": ".###.|#....|#....|####.|#...#|#...#|.###.",
    "7": "#####|....#|...#.|..#..|.#...|.#...|.#...",
    "8": ".###.|#...#|#...#|.###.|#...#|#...#|.###.",
    "9": ".###.|#...#|#...#|.####|....#|....#|.###.",
    " ": "...|...|...|...|...|...|...",
    "&": ".##..|#..#.|#.#..|.#...|#.#.#|#..#.|.##.#",
    "-": "...|...|...|###|...|...|...",
    "+": ".....|..#..|..#..|#####|..#..|..#..|.....",
    ".": ".|.|.|.|.|.|#",
    ",": "..|..|..|..|..|.#|#.",
    ":": ".|.|#|.|.|#|.",
    "'": "#|#|.|.|.|.|.",
    "!": "#|#|#|#|#|.|#",
    "?": ".###.|#...#|....#|...#.|..#..|.....|..#..",
    "/": "....#|...#.|...#.|..#..|.#...|.#...|#....",
    "(": ".#|#.|#.|#.|#.|#.|.#",
    ")": "#.|.#|.#|.#|.#|.#|#.",
    "|": "#|#|#|#|#|#|#",
    "·": ".|.|.|#|.|.|.",  # middle dot
    "▶": "#...|##..|###.|####|###.|##..|#...",  # play triangle
    "■": ".....|#####|#####|#####|#####|#####|.....",  # filled block
    "□": ".....|#####|#...#|#...#|#...#|#####|.....",  # empty block
    "✓": ".....|....#|...##|#.##.|###..|.#...|.....",  # check
    "★": "..#..|..#..|#####|.###.|.#.#.|#...#|.....",  # star
}
FONT = {k: v.split("|") for k, v in _F.items()}


def glyph(ch: str) -> list[str]:
    return FONT.get(ch.upper(), FONT["?"])


def text_width(s: str, scale: int) -> int:
    if not s:
        return 0
    return (sum(len(glyph(c)[0]) for c in s) + len(s) - 1) * scale


def wrap(s: str, scale: int, max_w: int) -> list[str]:
    lines, cur = [], ""
    for word in s.split():
        trial = f"{cur} {word}".strip()
        if text_width(trial, scale) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ----------------------------------------------------------------- canvas
class Layer:
    """Collects axis-aligned rectangles in paint order and emits compact paths."""

    def __init__(self, attrs: str = ""):
        self.attrs = attrs
        self.rects: list[tuple[str, int, int, int, int]] = []

    def rect(self, x, y, w, h, color):
        if w > 0 and h > 0:
            self.rects.append((color, int(x), int(y), int(w), int(h)))

    def sprite(self, rows, palette, s, x0, y0):
        for y, row in enumerate(rows):
            x = 0
            while x < len(row):
                c = row[x]
                if c not in palette:
                    x += 1
                    continue
                w = 1
                while x + w < len(row) and row[x + w] == c:
                    w += 1
                self.rect(x0 + x * s, y0 + y * s, w * s, s, palette[c])
                x += w

    def text(self, x, y, s, scale, color):
        cx = x
        for ch in s:
            g = glyph(ch)
            self.sprite(g, {"#": color}, scale, cx, y)
            cx += (len(g[0]) + 1) * scale
        return cx

    def frame(self, x, y, w, h, t, color):
        self.rect(x, y, w, t, color)
        self.rect(x, y + h - t, w, t, color)
        self.rect(x, y, t, h, color)
        self.rect(x + w - t, y, t, h, color)

    def svg(self) -> str:
        # Merge consecutive same-colour rects into one path; keeps paint order intact.
        out, color, d = [], None, ""
        for c, x, y, w, h in self.rects:
            if c != color and d:
                out.append(f'<path fill="{color}" d="{d}"/>')
                d = ""
            color = c
            d += f"M{x} {y}h{w}v{h}h-{w}z"
        if d:
            out.append(f'<path fill="{color}" d="{d}"/>')
        body = "".join(out)
        return f"<g {self.attrs}>{body}</g>" if self.attrs else body


def document(w, h, layers, title, desc, style=""):
    style_block = f"<style>{style}</style>" if style else ""
    inner = "".join(layer if isinstance(layer, str) else layer.svg() for layer in layers)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'shape-rendering="crispEdges" role="img" aria-labelledby="t d">'
        f'<title id="t">{esc(title)}</title><desc id="d">{esc(desc)}</desc>{style_block}{inner}</svg>\n'
    )


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------- sprites
CLIMBER = [
    ".........ss.",
    ".........st.",
    "....hhh..t..",
    "...hhhhh.t..",
    "...hhhhhtt..",
    "...stttttt..",
    "..sttttttt..",
    ".s.tttttt...",
    "s..ttcttt...",
    "...pppppp...",
    "...pp..pp...",
    "..pp...pp...",
    "..pp....pp..",
    ".kk.....pp..",
    ".........kk.",
]
CLIMBER_PAL = {"h": "#1e1a2a", "s": "#f0c7a0", "t": "#3fb8a6", "p": "#3b4a7a", "k": "#e05a47", "c": CHALK}


def mirror(rows):
    return [r[::-1] for r in rows]


HOLDS = [
    [".xxx.", "xxxxx", "xxxxy", ".xyy."],  # jug
    ["xxxxxx", "yyyyyy"],  # crimp
    [".xxxx.", "xxxxxx", "yyyyyy"],  # sloper
    [".xx.", "xxxx", "xxxy", "xxxy", ".yy."],  # pinch
]


def hold(layer, shape, tape, s, x, y):
    main, dark = TAPE[tape]
    layer.sprite(HOLDS[shape], {"x": main, "y": dark}, s, x, y)


# ----------------------------------------------------------------- banner
def build_banner(p) -> str:
    W, H = 832, 272
    bg = Layer()
    bg.rect(0, 0, W, H, WALL)
    for x in range(208, W, 208):
        bg.rect(x, 0, 4, H, SEAM)
    bg.rect(0, 136, W, 4, SEAM)
    for y in range(44, H - 24, 24):
        for x in range(12, W, 24):
            bg.rect(x, y, 4, 4, BOLT)

    # pixel volumes (staircase triangles)
    def volume(x0, x1, apex_x, apex_y, base_y):
        for y in range(apex_y, base_y, 4):
            t = (y - apex_y) / (base_y - apex_y)
            l = round((apex_x - (apex_x - x0) * t) / 4) * 4
            r = round((apex_x + (x1 - apex_x) * t) / 4) * 4
            bg.rect(l, y, apex_x - l, 4, "#2f3358")
            bg.rect(apex_x, y, r - apex_x, 4, "#272a4a")

    volume(452, 640, 548, 188, 252)
    volume(712, 812, 776, 40, 112)

    # scattered holds, avoiding the title panel, the climber's line and the HUD
    rnd = random.Random(7)
    tapes = list(TAPE)
    placed = 0
    while placed < 44:
        x, y = rnd.randrange(0, 205) * 4, rnd.randrange(9, 60) * 4
        if 8 <= x <= 428 and 44 <= y <= 236:
            continue
        if 584 <= x <= 708 and y <= 240:
            continue
        hold(bg, rnd.randrange(4), tapes[rnd.randrange(len(tapes))], 4, x, y)
        placed += 1

    # the climber's yellow problem
    cx, cy = 600, 150
    for hx, hy in [(642, 146), (642, 110), (642, 74), (642, 40), (602, 152), (602, 116), (602, 80)]:
        hold(bg, 0, "yellow", 4, hx, hy)
    hold(bg, 1, "yellow", 4, 598, 220)
    hold(bg, 1, "yellow", 4, 640, 226)

    # crash pad
    bg.rect(500, 252, 280, 20, "#3b4a7a")
    bg.rect(500, 252, 280, 4, "#5566a0")
    for x in range(570, 780, 70):
        bg.rect(x, 256, 2, 16, "#33416c")

    climber_a = Layer('class="fa"')
    climber_a.sprite(CLIMBER, CLIMBER_PAL, 5, cx, cy)
    climber_b = Layer('class="fb"')
    climber_b.sprite(mirror(CLIMBER), CLIMBER_PAL, 5, cx - 4, cy + 4)
    climber = f'<g class="climb">{climber_a.svg()}{climber_b.svg()}</g>'

    ui = Layer()
    ui.rect(0, 0, W, 28, INK)
    max_grade = max((r["grade"] for r in p["routes"]), key=lambda g: int("".join(c for c in g if c.isdigit()) or 0))
    ui.text(16, 10, "1P", 2, TAPE["red"][0])
    ui.text(48, 10, p["handle"], 2, CHALK)
    hud = f"HI-GRADE {max_grade}"
    ui.text((W - text_width(hud, 2)) // 2, 10, hud, 2, CHALK)
    chalk = "CHALK ■■■□"
    ui.text(W - 16 - text_width(chalk, 2), 10, chalk, 2, TAPE["yellow"][0])

    ui.rect(24, 56, 392, 172, INK)
    ui.rect(24, 56, 392, 4, TAPE["yellow"][0])
    ui.rect(24, 224, 392, 4, TAPE["yellow"][0])
    first, last = p["name"]
    ui.text(48, 80, first, 5, CHALK)
    ui.text(48, 124, last, 5, CHALK)
    ui.text(48, 176, p["role"], 2, TAPE["yellow"][0])

    blink = Layer('class="blink"')
    blink.text(48, 200, "▶ PRESS START", 2, TAPE["red"][0])

    style = (
        "@keyframes fa{0%,49.9%{opacity:1}50%,100%{opacity:0}}"
        "@keyframes fb{0%,49.9%{opacity:0}50%,100%{opacity:1}}"
        "@keyframes climb{0%,32.9%{transform:translateY(0)}33%,65.9%{transform:translateY(-36px)}"
        "66%,95.9%{transform:translateY(-72px)}96%,100%{transform:translateY(0)}}"
        "@keyframes blink{0%,49.9%{opacity:1}50%,100%{opacity:0}}"
        ".fa{animation:fa .9s infinite}.fb{animation:fb .9s infinite}"
        ".climb{animation:climb 5.4s infinite}.blink{animation:blink 1.2s infinite}"
        "@media (prefers-reduced-motion:reduce){.fa,.fb,.climb,.blink{animation:none}.fb{opacity:0}}"
    )
    first_name = " ".join(p["name"]).title()
    return document(
        W, H, [bg, climber, ui, blink],
        f"{first_name} - {p['role'].title()}",
        "Pixel-art bouldering wall at night. A small climber moves up a yellow problem next to a title panel.",
        style,
    )


# ----------------------------------------------------------------- routes
def build_routes(p) -> str:
    W, COL_W, GAP, PAD = 832, 404, 24, 16
    S = 2
    inner_w = COL_W - 2 * PAD
    row_h, item_gap = 26, 20

    def layout(route):
        """Return (height, draw_fn) for one route card."""
        y = PAD + 4
        head_h = 30
        y += head_h + 14
        items, x, rows = [], 0, 1
        for skill in route["skills"]:
            w = 18 + 8 + text_width(skill, S)
            if x and x + w > inner_w:
                x, rows = 0, rows + 1
            items.append((x, rows - 1, skill))
            x += w + item_gap
        skills_y = y
        y += rows * row_h + 6
        beta_lines = wrap(route["beta"].upper(), S, inner_w)
        beta_y = y
        y += len(beta_lines) * 20 + PAD - 6

        def draw(layer, ox, oy, h):
            main, dark = TAPE[route["tape"]]
            layer.rect(ox, oy, COL_W, h, CARD)
            layer.frame(ox, oy, COL_W, h, 2, CARD_EDGE)
            layer.rect(ox - 2, oy - 2, 32, 10, main)
            gx, gy = ox + PAD, oy + PAD + 4
            gw = text_width(route["grade"], S) + 16
            layer.rect(gx, gy, gw, head_h, main)
            layer.text(gx + 8, gy + 8, route["grade"], S, "#10131a")
            layer.text(gx + gw + 12, gy + 8, route["name"].upper(), S, CHALK)
            for i, (ix, r, skill) in enumerate(items):
                sx, sy = ox + PAD + ix, oy + skills_y + r * row_h
                hold(layer, i % 4, route["tape"], 3, sx, sy + (2 if i % 4 != 1 else 5))
                layer.text(sx + 26, sy + 1, skill, S, TEXT)
            for j, line in enumerate(beta_lines):
                layer.text(ox + PAD, oy + beta_y + j * 20, line, S, MUTED)

        return y, draw

    cards = [layout(r) for r in p["routes"]]
    layer = Layer()
    y = 2
    for i in range(0, len(cards), 2):
        pair = cards[i:i + 2]
        h = max(c[0] for c in pair)
        for j, (_, draw) in enumerate(pair):
            draw(layer, 2 + j * (COL_W + GAP - 4), y, h)
        y += h + 20
    H = y - 18
    skills = "; ".join(f"{r['name']} ({r['grade']}): {', '.join(r['skills'])}" for r in p["routes"])
    return document(W, H, [layer], "Skills as bouldering problems", skills)


# ------------------------------------------------------------------ sends
def build_sends(p) -> dict[str, str]:
    W, PAD, S = 404, 16, 2
    inner = W - 2 * PAD

    def layout(send):
        y = PAD + 6
        badge_y = y
        y += 30 + 14
        title_lines = wrap(send["title"].upper(), 3, inner)
        title_y = y
        y += len(title_lines) * 28 + 4
        crag_y = y
        y += 20
        beta_lines = wrap(send["beta"].upper(), S, inner)
        beta_y = y + 6
        y = beta_y + len(beta_lines) * 20 + 10
        chips, x, rows = [], 0, 1
        for tool in send["rack"]:
            w = text_width(tool, S) + 16
            if x and x + w > inner:
                x, rows = 0, rows + 1
            chips.append((x, rows - 1, tool, w))
            x += w + 8
        rack_y = y
        y += rows * 30 + PAD - 6
        return y, dict(badge_y=badge_y, title=title_lines, title_y=title_y, crag_y=crag_y,
                       beta=beta_lines, beta_y=beta_y, chips=chips, rack_y=rack_y)

    laid = [(s, *layout(s)) for s in p["sends"]]
    H = max(h for _, h, _ in laid)  # equal heights so cards line up side by side
    out = {}
    for send, _, L in laid:
        main, _dark = TAPE[send["tape"]]
        layer = Layer()
        layer.rect(0, 0, W, H, CARD)
        layer.frame(0, 0, W, H, 2, CARD_EDGE)
        layer.rect(0, 0, 32, 10, main)
        tick = f"✓ {send['tick']}"
        bw = text_width(tick, S) + 16
        layer.rect(PAD, L["badge_y"], bw, 30, main)
        layer.text(PAD + 8, L["badge_y"] + 8, tick, S, "#10131a")
        arrow = "REPO ▶"
        layer.text(W - PAD - text_width(arrow, S), L["badge_y"] + 8, arrow, S, MUTED)
        for i, line in enumerate(L["title"]):
            layer.text(PAD, L["title_y"] + i * 28, line, 3, CHALK)
        layer.text(PAD, L["crag_y"], "CRAG: " + send["crag"].upper(), S, main)
        for i, line in enumerate(L["beta"]):
            layer.text(PAD, L["beta_y"] + i * 20, line, S, TEXT)
        for x, r, tool, w in L["chips"]:
            cx, cy = PAD + x, L["rack_y"] + r * 30
            layer.frame(cx, cy, w, 24, 2, "#3a4660")
            layer.text(cx + 8, cy + 5, tool, S, MUTED)
        desc = f"{send['title']} - {send['crag']}. {send['beta']} Built with {', '.join(send['rack'])}."
        out[send["repo"]] = document(W, H, [layer], f"{send['title']} ({send['tick'].lower()})", desc)
    return out


def readme_blocks(p) -> dict[str, str]:
    alt = "Skills grouped as bouldering problems. " + " ".join(
        f"{r['name']}: {', '.join(r['skills'])}." for r in p["routes"]
    )
    plain = "\n".join(f"- **{r['name']}** ({r['grade']}): {', '.join(r['skills'])}" for r in p["routes"])
    skills = (
        f'<img src="assets/routes.svg" alt="{alt}" width="100%" />\n\n'
        "<sub>Tape colour = focus area \u00b7 V-grade = depth \u00b7 each hold = one skill</sub>\n\n"
        "<details>\n<summary>Plain-text skill list</summary>\n\n"
        f"{plain}\n\n</details>"
    )
    user = p.get("github_user", p["handle"].lower())
    cards = []
    for s in p["sends"]:
        alt = f"{s['title']}: {s['beta']}".replace('"', "'")
        cards.append(
            f'<a href="https://github.com/{user}/{s["repo"]}">'
            f'<img src="assets/sends/{s["repo"]}.svg" alt="{alt}" width="49%" /></a>'
        )
    sends = "<p>\n" + "\n".join(cards) + "\n</p>\n\n<sub>Every send links to its repo.</sub>"
    return {"skills": skills, "sends": sends}


def update_readme(p):
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    for key, block in readme_blocks(p).items():
        start, end = f"<!-- {key}:start -->", f"<!-- {key}:end -->"
        if start not in text or end not in text:
            print(f"README.md has no {start} / {end} markers; skipped")
            continue
        head, rest = text.split(start, 1)
        _, tail = rest.split(end, 1)
        text = f"{head}{start}\n{block}\n{end}{tail}"
    path.write_text(text, encoding="utf-8")


def main():
    p = json.loads(DATA.read_text(encoding="utf-8"))
    (ASSETS / "sends").mkdir(parents=True, exist_ok=True)
    (ASSETS / "banner.svg").write_text(build_banner(p), encoding="utf-8")
    (ASSETS / "routes.svg").write_text(build_routes(p), encoding="utf-8")
    sends = build_sends(p)
    for old in (ASSETS / "sends").glob("*.svg"):
        if old.stem not in sends:
            old.unlink()
    for repo, svg in sends.items():
        (ASSETS / "sends" / f"{repo}.svg").write_text(svg, encoding="utf-8")
    update_readme(p)
    print(f"wrote banner.svg, routes.svg, {len(sends)} send cards and updated README.md")


if __name__ == "__main__":
    main()
