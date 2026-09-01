"""Regenerate the GCA-branded square logo as GCG, plus arm-coloured variants.
Run once with the repo venv: venv/bin/python scratchpad/gen_logos.py
"""
from PIL import Image, ImageDraw, ImageFont

W, H = 914, 920
RADIUS = 90
FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Black.ttf"

VARIANTS = [
    # (output filename,      bg color,     text,   text color)
    ("Green Square.png",      (0, 212, 169), "GCG", (10, 12, 16)),   # parent — unchanged green, black text
    ("GCE Square.png",        (59, 130, 246), "GCE", (255, 255, 255)),  # education — blue, white text
    ("Arena Square.png",      (245, 158, 11), "ARENA", (20, 14, 2)),    # arena — gold, near-black text
    ("GCT Square.png",        (168, 85, 247), "GCT", (255, 255, 255)),  # tools — purple, white text
]

def rounded_square(bg):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, W - 1, H - 1], radius=RADIUS, fill=bg + (255,))
    return img

def fit_font(text, max_width, max_height, start_size=520):
    size = start_size
    while size > 40:
        font = ImageFont.truetype(FONT_PATH, size)
        bbox = font.getbbox(text)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        if w <= max_width and h <= max_height:
            return font, bbox
        size -= 4
    return font, bbox

for fname, bg, text, fg in VARIANTS:
    img = rounded_square(bg)
    draw = ImageDraw.Draw(img)
    max_w, max_h = W * 0.78, H * 0.34
    font, bbox = fit_font(text, max_w, max_h)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (W - w) / 2 - bbox[0]
    y = (H - h) / 2 - bbox[1]
    draw.text((x, y), text, font=font, fill=fg + (255,))
    out = f"static/logos/{fname}"
    img.save(out)
    print("wrote", out)
