"""
Builds dist/SakshamCard.ttf

Every glyph is drawn from a pixel grid: horizontal runs of "on" cells become
rectangles, so a letter is a handful of contours rather than one per pixel.

The point of the font is the ligatures. Typing a project name substitutes a
single wide glyph that draws that project's card, so the text does not spell
the project, it *becomes* it.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
import grid as G

UPEM = 1000
CELL = 80
CARD_CELL = 30      # cards draw at a finer scale, else a card is 16em wide
GRID_H = 12
BASELINE_ROW = 10          # bottom of this row sits on the baseline
CW, CH = 8, 12

FAMILY = "Saksham Card"
VERSION = "1.000"

CARDS = {
    "saksham":   ("SAKSHAM ARORA", "data science + quant research"),
    "gitrade":   ("GITRADE", "an exchange in a readme"),
    "lmex":      ("LMEX", "llm apis as tickers"),
    "qrscholes": ("QRSCHOLES", "black-scholes in 731 bytes"),
    "latch":     ("LATCH", "pins a lecture full screen"),
}


def runs(grid):
    """Merge each row's consecutive ink cells into (row, x0, x1) rectangles."""
    out = []
    for y, row in enumerate(grid):
        x = 0
        while x < len(row):
            if row[x]:
                x0 = x
                while x < len(row) and row[x]:
                    x += 1
                out.append((y, x0, x))
            else:
                x += 1
    return out


def pen_for(grid, rows_above_baseline=BASELINE_ROW, cell=CELL):
    pen = TTGlyphPen(None)
    for (y, x0, x1) in runs(grid):
        top = (rows_above_baseline - y) * cell
        bot = top - cell
        left, right = x0 * cell, x1 * cell
        pen.moveTo((left, bot))
        pen.lineTo((left, top))
        pen.lineTo((right, top))
        pen.lineTo((right, bot))
        pen.closePath()
    return pen.glyph()


def card_grid(title, subtitle):
    """A bordered card: title in the big grid, subtitle in a smaller one."""
    t = G.text_grid(title.upper(), CW, CH, tracking=1)
    s = G.text_grid(subtitle.upper(), 7, 10, tracking=1)
    inner_w = max(len(t[0]), len(s[0]))
    pad = 3
    width = inner_w + pad * 2 + 2
    gap = 2
    height = 2 + pad + len(t) + gap + len(s) + pad

    g = [[False] * width for _ in range(height)]
    for x in range(width):                       # top and bottom rules
        g[0][x] = g[height - 1][x] = True
    for y in range(height):                      # sides
        g[y][0] = g[y][width - 1] = True

    def blit(src, top, left):
        for y, row in enumerate(src):
            for x, v in enumerate(row):
                if v:
                    g[top + y][left + x] = True

    blit(t, 1 + pad, 1 + pad)
    blit(s, 1 + pad + len(t) + gap, 1 + pad)
    return g


def build():
    letters = [c for c in G.CHARS if c.isalpha()]
    order = [".notdef", "space"] + [f"g_{c}" for c in G.CHARS] + \
            [f"l_{c}" for c in letters] + [f"card_{k}" for k in CARDS]
    cmap, glyphs, advances = {}, {}, {}

    blank = [[False] * CW for _ in range(GRID_H)]
    glyphs[".notdef"] = pen_for(blank)
    advances[".notdef"] = (CW + 1) * CELL
    glyphs["space"] = pen_for(blank)
    advances["space"] = (CW + 1) * CELL
    cmap[0x20] = "space"

    for c in G.CHARS:
        name = f"g_{c}"
        glyphs[name] = pen_for(G.char_grid(c, CW, CH))
        advances[name] = (CW + 1) * CELL
        cmap[ord(c)] = name

    # Same shapes, separate glyphs. The ligatures are bound to these, so typing
    # a name in lowercase becomes a card and in uppercase stays as letters.
    for c in letters:
        lname = f"l_{c}"
        glyphs[lname] = pen_for(G.char_grid(c, CW, CH))
        advances[lname] = (CW + 1) * CELL
        cmap[ord(c.lower())] = lname

    for key, (title, sub) in CARDS.items():
        g = card_grid(title, sub)
        name = f"card_{key}"
        # sit the card on the baseline, extending upward
        glyphs[name] = pen_for(g, rows_above_baseline=len(g), cell=CARD_CELL)
        advances[name] = (len(g[0]) + 2) * CARD_CELL

    fb = FontBuilder(UPEM, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics({g: (advances[g], 0) for g in order})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({
        "familyName": FAMILY,
        "styleName": "Regular",
        "uniqueFontIdentifier": f"{FAMILY} {VERSION}",
        "fullName": FAMILY,
        "psName": FAMILY.replace(" ", ""),
        "version": VERSION,
        "designer": "Saksham Arora",
        "designerURL": "https://saksham.digital",
        "licenseDescription": "MIT",
    })
    fb.setupOS2(sTypoAscender=800, sTypoDescender=-200, usWinAscent=1600, usWinDescent=400)
    fb.setupPost()

    subs = []
    for key in CARDS:
        seq = " ".join(f"l_{c.upper()}" for c in key)
        subs.append(f"    sub {seq} by card_{key};")
    fea = "feature liga {\n" + "\n".join(subs) + "\n} liga;\n"
    addOpenTypeFeaturesFromString(fb.font, fea)

    os.makedirs("dist", exist_ok=True)
    out = "dist/SakshamCard.ttf"
    fb.save(out)
    return out, len(order), len(CARDS)


if __name__ == "__main__":
    path, n, cards = build()
    print(f"wrote {path}: {n} glyphs, {cards} ligature cards")
