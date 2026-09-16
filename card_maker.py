from pathlib import Path
from datetime import datetime
import re

from PIL import Image, ImageDraw, ImageFont


BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "generated_roasts"
FRAME_FILE = ASSETS_DIR / "roast_frame.png"


def load_font(size, bold=False):
    """
    Try a few common Windows fonts first, then fall back safely.
    """
    candidates = []

    if bold:
        candidates += [
            r"C:\Windows\Fonts\arialbd.ttf",
            r"C:\Windows\Fonts\seguisb.ttf",
            r"C:\Windows\Fonts\segoeuib.ttf",
            r"C:\Windows\Fonts\tahomabd.ttf",
        ]
    else:
        candidates += [
            r"C:\Windows\Fonts\arial.ttf",
            r"C:\Windows\Fonts\segoeui.ttf",
            r"C:\Windows\Fonts\tahoma.ttf",
        ]

    # Also try generic names in case Pillow can resolve them
    candidates += [
        "arialbd.ttf" if bold else "arial.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ]

    for font_path in candidates:
        try:
            return ImageFont.truetype(font_path, size=size)
        except Exception:
            continue

    return ImageFont.load_default()


def text_size(draw, text, font):
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return right - left, bottom - top


def wrap_text(draw, text, font, max_width):
    words = text.split()
    if not words:
        return [""]

    lines = []
    current = words[0]

    for word in words[1:]:
        test_line = current + " " + word
        w, _ = text_size(draw, test_line, font)
        if w <= max_width:
            current = test_line
        else:
            lines.append(current)
            current = word

    lines.append(current)
    return lines


def fit_text_block(draw, text, max_width, max_height, start_size=22, min_size=17, line_gap=8):
    """
    Finds the biggest readable font size that fits the roast box.
    """
    for size in range(start_size, min_size - 1, -1):
        font = load_font(size, bold=True)
        lines = wrap_text(draw, text, font, max_width)

        _, line_h = text_size(draw, "Ag", font)
        total_h = len(lines) * line_h + (len(lines) - 1) * line_gap

        if total_h <= max_height:
            return font, lines, line_h, line_gap

    # Final fallback: smallest size, then trim if still too tall
    font = load_font(min_size, bold=True)
    lines = wrap_text(draw, text, font, max_width)
    _, line_h = text_size(draw, "Ag", font)

    max_lines = max(1, (max_height + line_gap) // (line_h + line_gap))
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        if lines:
            last = lines[-1]
            while last and text_size(draw, last + "...", font)[0] > max_width:
                last = last[:-1]
            lines[-1] = (last.rstrip() + "...") if last else "..."

    return font, lines, line_h, line_gap


def draw_shadow_text(draw, xy, text, font, fill, shadow_fill=(0, 0, 0, 180), shadow_offset=2):
    x, y = xy
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=shadow_fill)
    draw.text((x, y), text, font=font, fill=fill)


def safe_name(value):
    value = re.sub(r"[^a-zA-Z0-9_-]+", "_", value.strip())
    return value[:40] if value else "user"


def create_roast_card(username, roast_text):
    """
    Main function used by the bot.
    Returns the full path to the created PNG roast card.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not FRAME_FILE.exists():
        raise FileNotFoundError(
            f"Missing asset:\n{FRAME_FILE}\n\nPut roast_frame.png inside the assets folder."
        )

    img = Image.open(FRAME_FILE).convert("RGBA")
    draw = ImageDraw.Draw(img)

    w, h = img.size

    # Main text area tuned for sharper Discord readability
    username_x = int(w * 0.265)
    username_y = int(h * 0.305)

    text_x = username_x
    text_y = username_y + int(h * 0.085)

    text_box_width = int(w * 0.39)
    text_box_height = int(h * 0.32)

    username_font = load_font(int(h * 0.055), bold=True)
    body_font, body_lines, line_h, line_gap = fit_text_block(
        draw,
        roast_text,
        max_width=text_box_width,
        max_height=text_box_height,
        start_size=int(h * 0.055),
        min_size=int(h * 0.042),
        line_gap=max(6, int(h * 0.012))
    )

    footer_brand_font = load_font(int(h * 0.030), bold=True)
    footer_text_font = load_font(int(h * 0.027), bold=False)

    # Colors
    username_color = (120, 140, 255, 255)
    body_color = (245, 245, 245, 255)
    brand_color = (255, 210, 0, 255)
    footer_color = (210, 210, 210, 255)
    divider_color = (255, 210, 0, 255)

    # Draw username
    draw_shadow_text(draw, (username_x, username_y), f"@{username}", username_font, username_color)

    # Draw roast body
    current_y = text_y
    for line in body_lines:
        draw_shadow_text(draw, (text_x, current_y), line, body_font, body_color)
        current_y += line_h + line_gap

    # Divider line
    divider_y = current_y + int(h * 0.030)
    divider_x1 = text_x
    divider_x2 = text_x + int(text_box_width * 0.88)
    draw.rounded_rectangle(
        [(divider_x1, divider_y), (divider_x2, divider_y + 3)],
        radius=2,
        fill=divider_color
    )

    # Footer
    footer_y = divider_y + int(h * 0.028)

    brand_text = "NukemLabs"
    brand_w, _ = text_size(draw, brand_text, footer_brand_font)
    draw_shadow_text(draw, (text_x, footer_y), brand_text, footer_brand_font, brand_color)

    bullet_text = " • We regret nothing."
    bullet_x = text_x + brand_w + 8
    draw_shadow_text(draw, (bullet_x, footer_y), bullet_text, footer_text_font, footer_color)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = OUTPUT_DIR / f"roast_{safe_name(username)}_{timestamp}.png"

    # Save as sharp PNG
    img.save(out_file, format="PNG", optimize=False, compress_level=1)

    return str(out_file)


if __name__ == "__main__":
    test_username = "DudeNukem"
    test_roast = (
        "You wander through life with the confused, blank-faced focus of a man "
        "attempting to perform surgery on a blender with nothing but a rusty "
        "fucking spork and blind faith."
    )

    created = create_roast_card(test_username, test_roast)
    print("NUKEM ROAST CARD CREATED")
    print(created)