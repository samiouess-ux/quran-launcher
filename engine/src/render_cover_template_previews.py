"""Render four preview-only Quran opening covers; never imported by production."""
from __future__ import annotations

import argparse
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps, features

WIDTH, HEIGHT = 1080, 1920
TEMPLATES = ("blue_royal", "emerald_arch", "ivory_classic", "midnight_cinematic")
PALETTES = {
    "blue_royal": ((8, 19, 43), (34, 53, 83), (224, 183, 103), (255, 246, 224)),
    "emerald_arch": ((4, 43, 37), (12, 82, 66), (222, 190, 112), (255, 248, 224)),
    "ivory_classic": ((247, 239, 218), (224, 207, 170), (137, 99, 49), (31, 57, 47)),
    "midnight_cinematic": ((4, 12, 31), (13, 31, 58), (224, 184, 105), (250, 247, 232)),
}


def _font_path() -> str:
    path = subprocess.check_output(
        ["fc-match", "-f", "%{file}", "Amiri:style=Bold"], text=True
    ).strip()
    if not path or not Path(path).is_file():
        raise RuntimeError("Amiri Bold font is required for Arabic cover previews.")
    return path


REFERENCE_IMAGE = Path("file_000000005e3481f4996a7ee6217f56c6.png")


def _reference_background(template: str) -> Image.Image:
    """Use the repository's supplied Quran template image as the actual cover art."""
    if not REFERENCE_IMAGE.is_file():
        raise FileNotFoundError(f"Reference cover image not found: {REFERENCE_IMAGE}")
    source = Image.open(REFERENCE_IMAGE).convert("RGB")
    image = ImageOps.fit(source, (WIDTH, HEIGHT), method=Image.Resampling.LANCZOS,
                         centering=(0.5, 0.5)).convert("RGBA")
    # Restrained color grading only; preserve the supplied artwork itself.
    tint = {
        "blue_royal": (15, 35, 78, 34),
        "emerald_arch": (4, 67, 48, 38),
        "ivory_classic": (255, 231, 185, 30),
        "midnight_cinematic": (3, 12, 35, 55),
    }[template]
    image = Image.alpha_composite(image, Image.new("RGBA", image.size, tint))
    # A gentle dark veil keeps the Arabic title legible without replacing the image.
    veil = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    veil_draw = ImageDraw.Draw(veil)
    for y in range(HEIGHT):
        distance = abs(y - 850) / 1100
        alpha = int(12 + min(34, distance * 34))
        veil_draw.line((0, y, WIDTH, y), fill=(0, 0, 0, alpha))
    return Image.alpha_composite(image, veil)


def _gradient(top: tuple, bottom: tuple) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)
    for y in range(HEIGHT):
        t = y / (HEIGHT - 1)
        color = tuple(round(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
        draw.line((0, y, WIDTH, y), fill=color)
    return image.convert("RGBA")


def _star(draw: ImageDraw.ImageDraw, x: int, y: int, radius: int, color: tuple) -> None:
    draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=color)

def _ornate_medallion(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int, gold: tuple) -> None:
    """Layered floral geometry used as a detailed ornamental centerpiece."""
    for i in range(16):
        a = i * math.pi / 8
        x, y = cx + math.cos(a)*r*.55, cy + math.sin(a)*r*.55
        rr = r*.34
        draw.ellipse((x-rr, y-rr, x+rr, y+rr), outline=(*gold, 145), width=3)
    _eight_point_star(draw, cx, cy, r, (*gold, 220), 3)
    draw.ellipse((cx-r*.24, cy-r*.24, cx+r*.24, cy+r*.24),
                 outline=(*gold, 220), width=3)


def _hanging_lantern(draw: ImageDraw.ImageDraw, x: int, y: int, gold: tuple, scale: float = 1.0) -> None:
    w, h = int(48*scale), int(92*scale)
    draw.line((x, y-90*scale, x, y), fill=(*gold, 210), width=3)
    draw.polygon([(x-w//2,y), (x+w//2,y), (x+w//3,y+h), (x-w//3,y+h)],
                 fill=(255,190,85,45), outline=(*gold,230))
    draw.line((x-w//2+7,y+8,x-w//3+4,y+h-8), fill=(*gold,190), width=2)
    draw.line((x+w//2-7,y+8,x+w//3-4,y+h-8), fill=(*gold,190), width=2)
    draw.arc((x-w//2,y+h-14,x+w//2,y+h+16), 0, 180, fill=(*gold,230), width=3)


def _deep_arch(draw: ImageDraw.ImageDraw, gold: tuple, fill: tuple) -> None:
    # Nested, filled arch bands give the composition architectural depth.
    for inset, top, bottom, width in ((82,205,1590,10),(101,225,1570,4),(122,247,1548,2)):
        draw.rounded_rectangle((inset,top,WIDTH-inset,bottom), radius=390,
                               fill=(*fill,24) if width == 10 else None,
                               outline=(*gold,210 if width == 10 else 125), width=width)
    draw.arc((145,270,WIDTH-145,800), 180, 360, fill=(*gold,130), width=3)
    _ornate_medallion(draw, WIDTH//2, 240, 42, gold)
    for x in (145, WIDTH-145):
        for y in range(520,1450,155):
            _eight_point_star(draw,x,y,19,(*gold,175),2)


def _eight_point_star(draw: ImageDraw.ImageDraw, cx: int, cy: int, radius: int,
                     color: tuple, width: int = 3) -> None:
    """Draw a restrained eight-point Islamic star with a fine inner rosette."""
    outer, inner = [], []
    for i in range(16):
        angle = -math.pi / 2 + i * math.pi / 8
        r = radius if i % 2 == 0 else radius * 0.43
        outer.append((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
    for i in range(8):
        angle = -math.pi / 2 + i * math.pi / 4
        inner.append((cx + math.cos(angle) * radius * 0.30,
                      cy + math.sin(angle) * radius * 0.30))
    draw.polygon(outer, outline=color, width=width)
    draw.ellipse((cx-radius*.19, cy-radius*.19, cx+radius*.19, cy+radius*.19),
                 outline=color, width=max(1, width-1))
    for point in inner:
        draw.line((cx, cy, point[0], point[1]), fill=color, width=max(1, width-1))


def _ornamental_frame(draw: ImageDraw.ImageDraw, accent: tuple,
                      subdued: tuple) -> None:
    """Layered fine borders, corner stars and side rosettes."""
    for inset, stroke in ((34, 4), (52, 2), (76, 1)):
        draw.rounded_rectangle((inset, inset, WIDTH-inset, HEIGHT-inset),
                               radius=34, outline=(*accent, 205), width=stroke)
    for x in (112, WIDTH-112):
        for y in (150, 1770):
            _eight_point_star(draw, x, y, 43, (*accent, 225), 3)
        for y in range(360, 1561, 240):
            _eight_point_star(draw, x, y, 25, (*subdued, 150), 2)
    # Delicate repeating diamonds along the upper and lower rails.
    for x in range(210, 900, 86):
        draw.polygon(((x, 62), (x+13, 76), (x, 90), (x-13, 76)),
                     outline=(*accent, 150), width=2)
        draw.polygon(((x, HEIGHT-62), (x+13, HEIGHT-76),
                      (x, HEIGHT-90), (x-13, HEIGHT-76)),
                     outline=(*accent, 150), width=2)


def _mosque_silhouette(draw: ImageDraw.ImageDraw, color: tuple, y: int) -> None:
    # Restrained distant skyline; the title and verse range remain unobstructed.
    draw.rectangle((0, y+105, WIDTH, HEIGHT), fill=color)
    for cx, radius in ((180, 105), (540, 145), (900, 95)):
        draw.rectangle((cx-radius, y+35, cx+radius, y+115), fill=color)
        draw.pieslice((cx-radius, y- radius//2, cx+radius, y+radius+35),
                      180, 360, fill=color)
        draw.rectangle((cx-5, y-radius//2-35, cx+5, y-radius//2+5), fill=color)
        draw.polygon([(cx, y-radius//2-55), (cx-13, y-radius//2-32),
                      (cx+13, y-radius//2-32)], fill=color)
    for x in (65, 360, 720, 1015):
        draw.rectangle((x-13, y-5, x+13, HEIGHT), fill=color)
        draw.polygon([(x, y-75), (x-18, y-5), (x+18, y-5)], fill=color)


def _arch(draw: ImageDraw.ImageDraw, accent: tuple, inset: int = 105) -> None:
    draw.rounded_rectangle((inset, 170, WIDTH-inset, 1660), radius=390,
                           outline=accent, width=7)
    draw.line((inset, 560, inset, 1580), fill=accent, width=5)
    draw.line((WIDTH-inset, 560, WIDTH-inset, 1580), fill=accent, width=5)
    draw.arc((inset+28, 198, WIDTH-inset-28, 900), 180, 360,
             fill=accent, width=3)


def _background_decor(image: Image.Image, template: str, accent: tuple) -> None:
    draw = ImageDraw.Draw(image, "RGBA")
    _ornamental_frame(draw, accent, tuple(max(0, c-35) for c in accent))
    _deep_arch(draw, accent, (4, 13, 31) if template != "ivory_classic" else (247,239,218))
    if template == "blue_royal":
        _hanging_lantern(draw, 175, 385, accent, 1.05)
        _hanging_lantern(draw, 905, 385, accent, 1.05)
        _ornate_medallion(draw, 540, 425, 58, accent)
        _mosque_silhouette(draw, (5, 12, 28, 125), 1650)
    elif template == "emerald_arch":
        for y in range(320,1510,115):
            for x in (75,1005):
                _ornate_medallion(draw,x,y,24,accent)
        _hanging_lantern(draw,175,410,accent,.9)
        _hanging_lantern(draw,905,410,accent,.9)
    elif template == "ivory_classic":
        for x in (125, WIDTH-125):
            for y in (145, HEIGHT-145):
                _ornate_medallion(draw,x,y,68,accent)
        _hanging_lantern(draw,175,410,accent,.85)
        _hanging_lantern(draw,905,410,accent,.85)
    else:
        draw.ellipse((785,245,915,375), fill=(*accent,245))
        draw.ellipse((830,210,960,340), fill=(7,18,40,255))
        _hanging_lantern(draw,180,420,accent,.95)
        _hanging_lantern(draw,900,420,accent,.95)
        _mosque_silhouette(draw,(1,6,19,155),1640)


def _draw_title_panel(draw: ImageDraw.ImageDraw, template: str, accent: tuple) -> tuple:
    panel = (105, 650, 975, 990)
    if template == "blue_royal":
        draw.rounded_rectangle(panel, radius=52, fill=(4, 13, 31, 205),
                               outline=(*accent, 255), width=6)
        draw.rounded_rectangle((125, 670, 955, 970), radius=40,
                               outline=(*accent, 125), width=2)
        return (255, 242, 211, 255)
    if template == "emerald_arch":
        draw.rounded_rectangle(panel, radius=155, fill=(2, 35, 30, 190),
                               outline=(*accent, 255), width=5)
        return (255, 248, 224, 255)
    if template == "ivory_classic":
        draw.rectangle(panel, fill=(255, 250, 235, 232),
                       outline=(*accent, 255), width=5)
        draw.rectangle((125, 670, 955, 970), outline=(*accent, 145), width=2)
        return (31, 57, 47, 255)
    draw.rounded_rectangle(panel, radius=24, fill=(1, 7, 20, 195),
                           outline=(*accent, 240), width=4)
    return (255, 247, 224, 255)


def render_cover(surah_title: str, start_ayah: int, end_ayah: int,
                 template: str, destination: Path) -> None:
    """Render one opening cover. Title must include correct Arabic diacritics."""
    if not features.check("raqm"):
        raise RuntimeError("Pillow RAQM support is required for safe Arabic shaping.")
    if template not in TEMPLATES:
        raise ValueError(f"Unknown cover template: {template}")
    if not isinstance(surah_title, str) or not surah_title.strip():
        raise ValueError("A fully vocalized Arabic surah title is required.")
    if start_ayah < 1 or end_ayah < start_ayah:
        raise ValueError("Ayah range must be positive and ordered.")

    top, bottom, accent, _ = PALETTES[template]
    image = _reference_background(template)
    draw = ImageDraw.Draw(image, "RGBA")
    title_color = _draw_title_panel(draw, template, accent)

    font_path = _font_path()
    identity_font = ImageFont.truetype(
        font_path, 62, layout_engine=ImageFont.Layout.RAQM
    )
    identity_color = (*accent, 255) if template == "ivory_classic" else title_color
    draw.text((540, 505), "الْقُرْآنُ الْكَرِيمُ", font=identity_font,
              fill=identity_color, anchor="mm", direction="rtl", language="ar")
    draw.line((330, 565, 750, 565), fill=(*accent, 220), width=3)
    _eight_point_star(draw, 310, 565, 13, (*accent, 235), 2)
    _eight_point_star(draw, 770, 565, 13, (*accent, 235), 2)

    title_font = None
    for size in (112, 104, 96, 88, 80, 72, 64):
        candidate = ImageFont.truetype(font_path, size, layout_engine=ImageFont.Layout.RAQM)
        bounds = draw.textbbox((540, 805), surah_title, font=candidate,
                               anchor="mm", direction="rtl", language="ar")
        if bounds[2] - bounds[0] <= 760 and bounds[3] - bounds[1] <= 170:
            title_font = candidate
            break
    if title_font is None:
        raise ValueError("Vocalized surah title cannot fit without clipping.")
    draw.text((540, 805), surah_title, font=title_font, fill=title_color,
              anchor="mm", direction="rtl", language="ar")
    # Fine inner cartouche ornaments frame the surah name without touching glyphs.
    for x in (155, 925):
        _eight_point_star(draw, x, 805, 22, (*accent, 230), 2)

    digits = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
    first, last = str(start_ayah).translate(digits), str(end_ayah).translate(digits)
    label = f"الآيات {first}" if start_ayah == end_ayah else f"الآيات {first} - {last}"
    range_font = ImageFont.truetype(font_path, 55, layout_engine=ImageFont.Layout.RAQM)
    range_color = (*accent, 255) if template == "ivory_classic" else title_color
    draw.rounded_rectangle((260, 1080, 820, 1190), radius=28,
                           fill=(0, 0, 0, 42) if template != "ivory_classic"
                           else (255, 250, 235, 210),
                           outline=(*accent, 220), width=3)
    draw.text((540, 1135), label, font=range_font, fill=range_color,
              anchor="mm", direction="rtl", language="ar")
    image.save(destination)


def render_all(surah_title: str, start_ayah: int, end_ayah: int,
               output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for template in TEMPLATES:
        path = output_dir / f"{template}.png"
        render_cover(surah_title, start_ayah, end_ayah, template, path)
        outputs.append(path)
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--surah-title", required=True,
                        help="Fully vocalized Arabic title from an approved source")
    parser.add_argument("--start-ayah", type=int, required=True)
    parser.add_argument("--end-ayah", type=int, required=True)
    parser.add_argument("--output-dir", type=Path,
                        default=Path("output/cover_templates_review"))
    args = parser.parse_args()
    outputs = render_all(args.surah_title, args.start_ayah, args.end_ayah,
                         args.output_dir)
    print("PREVIEW ONLY — these covers are not connected to production.")
    for path in outputs:
        print(path)


if __name__ == "__main__":
    main()
