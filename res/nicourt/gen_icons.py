# Regenerates every Nicourt icon, logo and installer bitmap from the star paths below.
# Run from the repository root:
#   uv run --with cairosvg --with pillow python3 res/nicourt/gen_icons.py
# Needs the cairo C library (macOS: brew install cairo). macOS AppIcon.icns needs iconutil.
import io
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageFilter


def _find_homebrew_cairo():
    # macOS strips DYLD_* variables, so cairocffi cannot see Homebrew's lib dir on its own.
    import ctypes.util
    find = ctypes.util.find_library
    for prefix in ("/opt/homebrew/lib", "/usr/local/lib"):
        lib = Path(prefix) / "libcairo.2.dylib"
        if lib.exists():
            ctypes.util.find_library = lambda name: str(lib) if "cairo" in name else find(name)
            return


if sys.platform == "darwin":
    _find_homebrew_cairo()

import cairosvg  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent

INK = "#0a0a0a"
PAPER = "#ffffff"
LIME = "#c7f03d"
SURFACE0 = "#f6f5f0"
SURFACE50 = "#edece6"
SURFACE100 = "#e5e4dd"

# From the WAAS admin: packages/core/src/branding/StarMark.tsx, viewBox 0 0 133.28 144.16.
STAR_W, STAR_H = 133.28, 144.16
RIM = "M44.823,96.562C43.994,95.643 43.145,94.747 42.273,93.874L21.884,97.92L32.581,85.711C23.417,79.259 12.557,74.715 0,72.08C12.557,69.445 23.417,64.901 32.581,58.449L21.884,46.24L42.273,50.286C43.145,49.413 43.994,48.517 44.823,47.598L40.8,27.324L52.472,37.55C59.114,27.193 63.837,14.676 66.64,0C69.443,14.676 74.166,27.193 80.809,37.55L92.48,27.324L88.457,47.598C89.286,48.517 90.136,49.413 91.006,50.286L111.396,46.24L100.699,58.449C109.863,64.901 120.724,69.445 133.28,72.08C120.724,74.715 109.863,79.259 100.699,85.711L111.396,97.92L91.006,93.874C90.136,94.747 89.286,95.643 88.457,96.562L92.48,116.836L80.809,106.61C74.166,116.967 69.443,129.484 66.64,144.16C63.837,129.484 59.114,116.967 52.472,106.61L40.8,116.836Z"
CORE = "M50.059,90.686C49.429,89.987 48.783,89.306 48.121,88.643L32.625,91.718L40.755,82.439C33.791,77.536 25.537,74.083 15.994,72.08C25.537,70.077 33.791,66.624 40.755,61.72L32.625,52.441L48.121,55.517C48.783,54.854 49.429,54.173 50.059,53.474L47.001,38.065L55.872,45.837C60.92,37.966 64.51,28.453 66.64,17.299C68.771,28.453 72.359,37.966 77.408,45.837L86.278,38.065L83.22,53.473C83.851,54.172 84.496,54.853 85.158,55.517L100.654,52.441L92.524,61.72C99.489,66.624 107.743,70.077 117.287,72.08C107.743,74.083 99.489,77.536 92.524,82.44L100.654,91.718L85.158,88.643C84.496,89.307 83.851,89.988 83.22,90.687L86.278,106.095L77.408,98.323C72.359,106.194 68.771,115.707 66.64,126.861C64.51,115.707 60.92,106.194 55.872,98.322L47.001,106.095Z"


def star(cx, cy, height, rim=INK, core=LIME, stroke=0.0):
    """Star centred on (cx, cy), `height` tall. `stroke` (star units) fattens the ink rim for tiny sizes."""
    s = height / STAR_H
    tx, ty = cx - STAR_W * s / 2, cy - STAR_H * s / 2
    outline = f' stroke="{rim}" stroke-width="{stroke:g}" stroke-linejoin="round"' if stroke else ""
    core_path = f'<path fill="{core}" d="{CORE}"/>' if core else ""
    return (f'<g transform="translate({tx:.3f} {ty:.3f}) scale({s:.5f})">'
            f'<path fill="{rim}"{outline} d="{RIM}"/>{core_path}</g>')


def svg(w, h, body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{body}</svg>'


def tile_svg(side=1024, star_frac=0.70, radius_frac=0.22, stroke=0.0):
    r = side * radius_frac
    return svg(side, side, f'<rect width="{side}" height="{side}" rx="{r:g}" fill="{SURFACE0}"/>'
               + star(side / 2, side / 2, side * star_frac, stroke=stroke))


# Below 48px the 12 points blur together and the 1-2px rim vanishes: grow the star and fatten the rim.
SMALL = {16: dict(star_frac=0.94, radius_frac=0.18, stroke=10),
         24: dict(star_frac=0.90, radius_frac=0.20, stroke=8),
         32: dict(star_frac=0.86, radius_frac=0.20, stroke=6)}


def render(svg_text, w, h=None):
    png = cairosvg.svg2png(bytestring=svg_text.encode(), output_width=w, output_height=h or w)
    return Image.open(io.BytesIO(png)).convert("RGBA")


def icon_px(size):
    return render(tile_svg(**SMALL.get(size, {})), size)


def write_ico(path, sizes):
    """32bpp BMP entries below 256px and a PNG entry at 256, as Windows' own icons do."""
    entries = []
    for size in sizes:
        im = icon_px(size)
        if size >= 256:
            buf = io.BytesIO()
            im.save(buf, "PNG")
            data = buf.getvalue()
        else:
            px = im.tobytes("raw", "BGRA")
            rows = [px[y * size * 4:(y + 1) * size * 4] for y in range(size)][::-1]
            mask_row = ((size + 31) // 32) * 4
            header = struct.pack("<IiiHHIIiiII", 40, size, size * 2, 1, 32, 0, 0, 0, 0, 0, 0)
            data = header + b"".join(rows) + b"\0" * mask_row * size
        entries.append((size, data))
    out = struct.pack("<HHH", 0, 1, len(entries))
    offset = 6 + 16 * len(entries)
    for size, data in entries:
        d = 0 if size >= 256 else size
        out += struct.pack("<BBBBHHII", d, d, 0, 0, 1, 32, len(data), offset)
        offset += len(data)
    out += b"".join(data for _, data in entries)
    path.write_bytes(out)


def write_png(path, size):
    icon_px(size).save(path, "PNG", optimize=True)


def mac_icon():
    # Apple grid: 824px tile on a 1024 canvas with a soft drop shadow.
    side, tile, off = 1024, 824, 100
    body = (f'<rect x="{off}" y="{off}" width="{tile}" height="{tile}" rx="{tile * 0.225:g}" fill="{SURFACE0}"/>'
            + star(side / 2, side / 2, tile * 0.70))
    art = render(svg(side, side, body), side)
    shadow = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    alpha = art.getchannel("A").point(lambda a: a * 0.35)
    shadow.putalpha(alpha)
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.alpha_composite(shadow, (0, 10))
    canvas.alpha_composite(art)
    return canvas


def mac_tray(path, canvas, pad, colour):
    # Template image: only the alpha matters, macOS recolours it for the menu bar.
    content = canvas - 2 * pad
    body = star(canvas / 2, canvas / 2, content, rim=colour, core=None)
    render(svg(canvas, canvas, body), canvas).save(path, "PNG", optimize=True)


def icns(path):
    with tempfile.TemporaryDirectory() as tmp:
        iconset = Path(tmp) / "AppIcon.iconset"
        iconset.mkdir()
        big = mac_icon()
        for pt in (16, 32, 128, 256, 512):
            for scale in (1, 2):
                px = pt * scale
                name = f"icon_{pt}x{pt}{'@2x' if scale == 2 else ''}.png"
                big.resize((px, px), Image.LANCZOS).save(iconset / name)
        subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(path)], check=True)


def bmp24(path, w, h, body, background):
    im = render(svg(w, h, body), w, h)
    flat = Image.new("RGB", (w, h), background)
    flat.paste(im, mask=im.getchannel("A"))
    flat.save(path, "BMP")


def msi_bitmaps(out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    # Banner: WiX draws the title and description in black on the left; keep the star clear of it.
    bmp24(out_dir / "WixUIBannerBmp.bmp", 493, 58,
          f'<rect width="493" height="58" fill="{PAPER}"/>' + star(493 - 34, 29, 42), PAPER)
    # Dialog: WiX writes the welcome text on the right from x=164, so the left panel carries the star.
    bmp24(out_dir / "WixUIDialogBmp.bmp", 493, 312,
          f'<rect width="493" height="312" fill="{PAPER}"/>'
          f'<rect width="164" height="312" fill="{SURFACE0}"/>'
          f'<rect x="163" width="1" height="312" fill="{SURFACE100}"/>'
          + star(82, 156, 112), PAPER)


def logo_header_svg():
    # README header. The wordmark font is not bundled, so viewers without Space Grotesk get a fallback.
    w, h = 1000, 286.6
    return svg(w, h, f'<rect width="{w}" height="{h}" fill="{SURFACE0}"/>'
               + star(190, h / 2, 190)
               + f'<text x="310" y="{h / 2 + 52:g}" font-family="Space Grotesk, Helvetica, Arial, sans-serif"'
                 f' font-weight="700" font-size="150" fill="{INK}">nicourt.</text>')


def main():
    res = ROOT / "res"
    tile = tile_svg()
    (HERE / "icon.svg").write_text(tile + "\n")
    for p in (res / "scalable.svg", res / "logo.svg", ROOT / "flutter/assets/icon.svg"):
        p.write_text(tile + "\n")
    (res / "logo-header.svg").write_text(logo_header_svg() + "\n")

    write_png(res / "icon.png", 1024)
    write_png(res / "32x32.png", 32)
    write_png(res / "64x64.png", 64)
    write_png(res / "128x128.png", 128)
    write_png(res / "128x128@2x.png", 256)

    ico_sizes = [16, 24, 32, 48, 64, 128, 256]
    write_ico(res / "icon.ico", ico_sizes)
    shutil.copyfile(res / "icon.ico", ROOT / "flutter/windows/runner/resources/app_icon.ico")
    write_ico(res / "tray-icon.ico", [16, 32])

    msi_bitmaps(res / "msi/Package/Resources")

    mac_icon().save(res / "mac-icon.png", "PNG", optimize=True)
    mac_tray(res / "mac-tray-dark-x2.png", 60, 6, "#000000")
    mac_tray(res / "mac-tray-light-x2.png", 48, 0, "#ffffff")
    if sys.platform == "darwin":
        icns(ROOT / "flutter/macos/Runner/AppIcon.icns")
    else:
        print("skipped AppIcon.icns: iconutil is macOS only")


if __name__ == "__main__":
    main()
