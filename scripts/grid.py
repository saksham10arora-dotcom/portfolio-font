"""
Pixel grids for every glyph.

Hand-authoring 40 bitmaps invites typos, so each character is rasterised from
a real bold face into a small boolean grid instead. Rendering large and
downsampling keeps the letterforms honest at this size.
"""
from PIL import Image, ImageDraw, ImageFont

CW, CH = 6, 9                     # cell grid per character
BOLD = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]
CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-.:/+"


def _font(size):
    for p in BOLD:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    raise SystemExit("no bold font found")


def char_grid(ch, cw=CW, ch_h=CH):
    """Boolean grid for one character, True where ink."""
    S = 16                                   # supersample factor
    img = Image.new("L", (cw * S, ch_h * S), 0)
    d = ImageDraw.Draw(img)
    f = _font(int(ch_h * S * 0.88))
    bb = f.getbbox(ch)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    if w == 0 or h == 0:
        return [[False] * cw for _ in range(ch_h)]
    scale = min((cw * S * 0.92) / w, (ch_h * S * 0.86) / h)
    f = _font(max(8, int(ch_h * S * 0.88 * scale)))
    bb = f.getbbox(ch)
    d.text(((cw * S - (bb[2] - bb[0])) / 2 - bb[0],
            (ch_h * S - (bb[3] - bb[1])) / 2 - bb[1]), ch, font=f, fill=255)
    small = img.resize((cw, ch_h), Image.LANCZOS)
    px = small.load()
    return [[px[x, y] > 108 for x in range(cw)] for y in range(ch_h)]


def text_grid(text, cw=CW, ch_h=CH, tracking=1):
    """Lay characters side by side into one wide grid."""
    grids = [char_grid(c, cw, ch_h) if c != " " else [[False] * cw for _ in range(ch_h)]
             for c in text]
    width = len(grids) * cw + tracking * max(0, len(grids) - 1)
    out = [[False] * width for _ in range(ch_h)]
    x = 0
    for g in grids:
        for y in range(ch_h):
            for i in range(cw):
                out[y][x + i] = g[y][i]
        x += cw + tracking
    return out


def show(grid):
    return "\n".join("".join("#" if v else "." for v in row) for row in grid)


if __name__ == "__main__":
    for word in ("SAKSHAM", "GITRADE"):
        print(word); print(show(text_grid(word))); print()
