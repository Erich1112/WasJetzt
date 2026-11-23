"""Generează pictograma aplicației (sursa pictogramei): app.png (256x256) și app.ico (16-256 px).

Rulare: python scripts/make_icon.py   (necesită Pillow, din requirements-dev.txt)
Design: pătrat rotunjit albastru, cadran alb de ceas cu limbi groase, lizibil și la 16 px.
"""
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "src" / "wasjetzt" / "resources"
BLUE = (37, 99, 235, 255)
WHITE = (255, 255, 255, 255)
DARK = (30, 41, 59, 255)


def draw(size: int = 1024) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=int(size * 0.22), fill=BLUE)
    c = size // 2
    r = int(size * 0.34)
    d.ellipse([c - r, c - r, c + r, c + r], fill=WHITE)
    w = int(size * 0.07)
    d.line([c, c, c, c - int(r * 0.72)], fill=DARK, width=w)               # minutar
    d.line([c, c, c + int(r * 0.5), c + int(r * 0.2)], fill=DARK, width=w)  # orar
    d.ellipse([c - w, c - w, c + w, c + w], fill=DARK)
    return img


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    big = draw()
    png = big.resize((256, 256), Image.LANCZOS)
    png.save(OUT / "app.png")
    big.save(OUT / "app.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("Generat:", OUT / "app.png", OUT / "app.ico")


if __name__ == "__main__":
    main()
