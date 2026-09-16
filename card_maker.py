from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import re

PROJECT_ROOT = Path(__file__).resolve().parent
ASSETS_DIR = PROJECT_ROOT / "assets"
OUTPUT_DIR = PROJECT_ROOT / "generated_roasts"
FRAME_FILE = ASSETS_DIR / "roast_frame.png"

OUTPUT_DIR.mkdir(exist_ok=True)


def safe_name(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip())
    return value[:40] or "user"


def get_font(size: int, bold: bool = False):
    candidates = []

    if bold:
        candidates.extend([
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ])
    else:
        candidates.extend([
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ])

    for font_path in candidates:
        if Path(font_path).exists():
            return ImageFont.truetype(font_path, size=size)

    return ImageFont.load_default()


def text_width(draw, text, font):
    if not text:
        return 0
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def line_height(draw, font):
    box = draw.textbbox((0, 0), "Ag", font=font)
    return box[3] - box[1]


def wrap_text(draw, text, font, max_width):
    words = text.split()
    if not words:
        return [""]

    lines = []
    current = words[0]

    for word in words[1:]:
        test = current + " " + word
        if text_width(draw, test, font) <= max_width:
            current = test
        else:
            lines.append(current)
            current = word

    lines.append(current)
    return lines


def choose_body_font_and_lines(draw, roast_text, max_width, max_height):
    # Bigger text first. Only shrink if needed.
    for size in [18, 17, 16]:
        font = get_font(size, bold=True)
        lines = wrap_text(draw, roast_text, font, max_width)
        lh = line_height(draw, font)
        spacing = max(5, int(size * 0.32))
        total_height = (len(lines) * lh) + ((len(lines) - 1) * spacing)

        if total_height <= max_height:
            return font, lines, spacing

    # Worst case fallback
    font = get_font(16, bold=True)
    lines = wrap_text(draw, roast_text, font, max_width)
    spacing = 5
    return font, lines, spacing


def create_roast_card(username: str, roast_text: str) -> str:
    if not FRAME_FILE.exists():
        raise FileNotFoundError(
            f"Missing asset:\n{FRAME_FILE}\n\nPut roast_frame.png inside the assets folder."
        )

    frame = Image.open(FRAME_FILE).convert("RGBA")
    img = frame.copy()
    draw = ImageDraw.Draw(img)

    # Base design was tuned around 520px width.
    scale = img.width / 520.0

    def sx(value):
        return int(value * scale)

    def sy(value):
        return int(value * scale)

    # -------- COLORS --------
    USERNAME_COLOR = (112, 132, 255)
    BODY_COLOR = (255, 255, 255)
    BRAND_COLOR = (248, 214, 38)
    FOOTER_COLOR = (215, 215, 215)
    LINE_COLOR = (239, 203, 18)

    # -------- FONTS --------
    username_font = get_font(sx(17), bold=True)
    brand_font = get_font(sx(10), bold=True)
    footer_font = get_font(sx(9), bold=False)

    # -------- TEXT AREA --------
    # Slightly higher so it sits better visually.
    username_x = sx(120)
    username_y = sy(90)

    body_x = sx(120)
    body_y = sy(122)
    body_max_width = sx(270)
    body_max_height = sy(118)

    body_font, roast_lines, body_spacing = choose_body_font_and_lines(
        draw,
        roast_text,
        body_max_width,
        body_max_height
    )

    # -------- FOOTER --------
    divider_x1 = sx(120)
    divider_x2 = sx(390)
    divider_y = sy(250)

    brand_x = sx(120)
    brand_y = sy(258)

    # -------- DRAW USERNAME --------
    draw.text(
        (username_x, username_y),
        username,
        font=username_font,
        fill=USERNAME_COLOR
    )

    # -------- DRAW ROAST --------
    lh = line_height(draw, body_font)
    current_y = body_y
    for line in roast_lines:
        draw.text(
            (body_x, current_y),
            line,
            font=body_font,
            fill=BODY_COLOR
        )
        current_y += lh + body_spacing

    # -------- DIVIDER --------
    draw.line(
        [(divider_x1, divider_y), (divider_x2, divider_y)],
        fill=LINE_COLOR,
        width=max(2, sx(2))
    )

    # -------- FOOTER --------
    brand_text = "NukemLabs"
    footer_text = "•  We regret nothing."

    draw.text(
        (brand_x, brand_y),
        brand_text,
        font=brand_font,
        fill=BRAND_COLOR
    )

    brand_w = text_width(draw, brand_text, brand_font)

    draw.text(
        (brand_x + brand_w + sx(8), brand_y + sy(1)),
        footer_text,
        font=footer_font,
        fill=FOOTER_COLOR
    )

    # -------- SAVE --------
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"roast_{safe_name(username)}_{timestamp}.png"
    output_path = OUTPUT_DIR / filename

    img.save(output_path, format="PNG", optimize=True)
    return str(output_path)


if __name__ == "__main__":
    test_username = "@DudeNukem"
    test_roast = (
        "Carries the frantic, disheveled energy of a man trying to explain "
        "quantum physics to a toaster while actively forgetting how to fucking breathe."
    )

    result = create_roast_card(test_username, test_roast)

    print("NUKEM ROAST CARD CREATED")
    print("-" * 28)
    print(result)