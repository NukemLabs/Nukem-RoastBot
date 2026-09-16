import os
import re
from pathlib import Path
from datetime import datetime

from PIL import (
    Image,
    ImageDraw,
    ImageFont,
    ImageEnhance,
    ImageFilter,
)

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "generated_roasts"

# If your file has a different name, only change this line.
FRAME_FILE = ASSETS_DIR / "nukem_labs_industrial_overlay.png"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# OUTPUT SETTINGS
# ============================================================

MAX_OUTPUT_WIDTH = 760
FRAME_COUNT = 20
FRAME_DURATION_MS = 160  # smooth / subtle

# ============================================================
# COLORS
# ============================================================

WHITE = (235, 235, 235, 255)
MUTED_WHITE = (180, 180, 180, 255)
MENTION_BLUE = (135, 150, 255, 255)
NUKEM_YELLOW = (255, 210, 0, 255)

FOOTER_LEFT = "NukemLabs"
FOOTER_RIGHT = "•  We regret nothing."

# ============================================================
# FONT LOADING
# ============================================================

def load_font(size, bold=False):
    candidates = []

    if os.name == "nt":
        if bold:
            candidates.extend([
                r"C:\Windows\Fonts\segoeuib.ttf",
                r"C:\Windows\Fonts\arialbd.ttf",
                r"C:\Windows\Fonts\bahnschrift.ttf",
            ])
        else:
            candidates.extend([
                r"C:\Windows\Fonts\segoeui.ttf",
                r"C:\Windows\Fonts\arial.ttf",
                r"C:\Windows\Fonts\bahnschrift.ttf",
            ])

    if bold:
        candidates.extend([
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
        ])
    else:
        candidates.extend([
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        ])

    for font_path in candidates:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                pass

    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


# ============================================================
# HELPERS
# ============================================================

def safe_filename(text):
    text = re.sub(r"[^a-zA-Z0-9_-]+", "_", text)
    text = text.strip("_")
    return text or "user"


def clean_roast_for_card(username, roast_text):
    if not roast_text:
        return ""

    clean_username = username.lstrip("@").strip()
    text = roast_text.strip()

    patterns = [
        rf"^@{re.escape(clean_username)}\s*[,:\-–—]?\s*",
        rf"^{re.escape(clean_username)}\s*[,:\-–—]?\s*",
    ]

    name_removed = False

    for pattern in patterns:
        new_text = re.sub(
            pattern,
            "",
            text,
            count=1,
            flags=re.IGNORECASE
        )
        if new_text != text:
            text = new_text.strip()
            name_removed = True
            break

    if name_removed:
        replacements = [
            (r"^is\b", "You are"),
            (r"^was\b", "You were"),
            (r"^has\b", "You have"),
            (r"^had\b", "You had"),
            (r"^does\b", "You do"),
            (r"^did\b", "You did"),
            (r"^looks\b", "You look"),
            (r"^looked\b", "You looked"),
            (r"^seems\b", "You seem"),
            (r"^seemed\b", "You seemed"),
            (r"^sounds\b", "You sound"),
            (r"^acts\b", "You act"),
            (r"^walks\b", "You walk"),
            (r"^wanders\b", "You wander"),
            (r"^thinks\b", "You think"),
            (r"^makes\b", "You make"),
            (r"^brings\b", "You bring"),
            (r"^gives\b", "You give"),
            (r"^needs\b", "You need"),
            (r"^deserves\b", "You deserve"),
            (r"^plays\b", "You play"),
            (r"^runs\b", "You run"),
            (r"^tries\b", "You try"),
            (r"^keeps\b", "You keep"),
            (r"^somehow\b", "You somehow"),
            (r"^could\b", "You could"),
            (r"^would\b", "You would"),
            (r"^will\b", "You will"),
            (r"^can\b", "You can"),
            (r"^can't\b", "You can't"),
            (r"^won't\b", "You won't"),
        ]

        replaced = False

        for pattern, replacement in replacements:
            new_text = re.sub(
                pattern,
                replacement,
                text,
                count=1,
                flags=re.IGNORECASE
            )
            if new_text != text:
                text = new_text
                replaced = True
                break

        if not replaced and text:
            text = text[0].upper() + text[1:]

    elif text:
        text = text[0].upper() + text[1:]

    return text


def wrap_text_by_pixels(draw, text, font, max_width):
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        test_width = bbox[2] - bbox[0]

        if test_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines


# ============================================================
# SUBTLE NUKEM LABS FLICKER
# ============================================================

def add_nukem_labs_flicker(frame, frame_index):
    """
    Only the left NUKEM LABS panel flickers.
    No other motion.
    """

    width, height = frame.size

    # Left sign region
    left = int(width * 0.020)
    top = int(height * 0.105)
    right = int(width * 0.235)
    bottom = int(height * 0.465)

    panel_box = (left, top, right, bottom)

    # Gentle, irregular flicker
    flicker_pattern = [
        1.00, 1.01, 1.00, 0.99, 1.02,
        1.00, 0.97, 1.04, 1.00, 1.01,
        1.00, 0.98, 0.95, 1.05, 1.00,
        1.00, 1.02, 1.00, 0.99, 1.01,
    ]

    brightness = flicker_pattern[frame_index % len(flicker_pattern)]

    panel = frame.crop(panel_box).convert("RGBA")
    brightened = ImageEnhance.Brightness(panel).enhance(brightness)

    # Create glow mainly from bright yellow lettering/details
    grayscale = brightened.convert("L")
    glow_mask = grayscale.point(lambda v: 255 if v > 125 else 0)
    glow_mask = glow_mask.filter(ImageFilter.GaussianBlur(7))

    glow_alpha = int(65 + max(0, (brightness - 1.0)) * 70)

    glow = Image.new(
        "RGBA",
        brightened.size,
        (220, 255, 50, glow_alpha)
    )
    glow.putalpha(glow_mask)

    panel_result = Image.new("RGBA", brightened.size, (0, 0, 0, 0))
    panel_result = Image.alpha_composite(panel_result, glow)
    panel_result = Image.alpha_composite(panel_result, brightened)

    frame.paste(panel_result, (left, top), panel_result)
    return frame


# ============================================================
# STATIC ROAST TEXT
# ============================================================

def add_roast_text(frame, username, roast_text):
    draw = ImageDraw.Draw(frame)
    width, height = frame.size

    username_font_size = max(18, int(width * 0.022))
    roast_font_size = max(15, int(width * 0.0185))
    footer_font_size = max(12, int(width * 0.014))

    username_font = load_font(username_font_size, bold=True)
    roast_font = load_font(roast_font_size, bold=False)
    footer_bold_font = load_font(footer_font_size, bold=True)
    footer_font = load_font(footer_font_size, bold=False)

    # Slightly more breathing room
    text_x = int(width * 0.295)
    username_y = int(height * 0.292)
    roast_y = int(height * 0.375)
    text_right = int(width * 0.720)

    max_text_width = text_right - text_x

    display_username = username if username.startswith("@") else "@" + username
    roast_text = clean_roast_for_card(display_username, roast_text)

    # Username
    draw.text(
        (text_x, username_y),
        display_username,
        font=username_font,
        fill=MENTION_BLUE
    )

    # Roast body
    wrapped_lines = wrap_text_by_pixels(
        draw,
        roast_text,
        roast_font,
        max_text_width
    )

    current_y = roast_y
    line_spacing = int(roast_font_size * 1.42)

    for line in wrapped_lines[:6]:
        draw.text(
            (text_x, current_y),
            line,
            font=roast_font,
            fill=WHITE
        )
        current_y += line_spacing

    # Footer divider
    divider_y = int(height * 0.675)
    draw.line(
        (text_x, divider_y, text_right, divider_y),
        fill=NUKEM_YELLOW,
        width=max(2, int(width * 0.002))
    )

    # Footer
    footer_y = int(height * 0.708)

    draw.text(
        (text_x, footer_y),
        FOOTER_LEFT,
        font=footer_bold_font,
        fill=NUKEM_YELLOW
    )

    footer_left_box = draw.textbbox(
        (text_x, footer_y),
        FOOTER_LEFT,
        font=footer_bold_font
    )

    footer_right_x = footer_left_box[2] + int(width * 0.012)

    draw.text(
        (footer_right_x, footer_y),
        FOOTER_RIGHT,
        font=footer_font,
        fill=MUTED_WHITE
    )

    return frame


# ============================================================
# BUILD FRAMES
# ============================================================

def make_card_frames(username, roast_text):
    if not FRAME_FILE.exists():
        raise FileNotFoundError(
            f"Missing asset:\n{FRAME_FILE}\n\n"
            f"Put nukem_labs_industrial_overlay.png in the assets folder."
        )

    base = Image.open(FRAME_FILE).convert("RGBA")

    if base.width > MAX_OUTPUT_WIDTH:
        ratio = MAX_OUTPUT_WIDTH / base.width
        new_height = int(base.height * ratio)
        base = base.resize(
            (MAX_OUTPUT_WIDTH, new_height),
            Image.Resampling.LANCZOS
        )

    frames = []

    for frame_index in range(FRAME_COUNT):
        frame = base.copy()

        # Only animation
        frame = add_nukem_labs_flicker(frame, frame_index)

        # Static text
        frame = add_roast_text(frame, username, roast_text)

        frames.append(frame)

    return frames


# ============================================================
# SAVE GIF
# ============================================================

def save_gif(frames, username):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    name_part = safe_filename(username.replace("@", ""))

    output_path = OUTPUT_DIR / f"roast_{name_part}_{timestamp}.gif"

    gif_frames = []
    for frame in frames:
        gif_frame = frame.convert(
            "P",
            palette=Image.Palette.ADAPTIVE,
            colors=128
        )
        gif_frames.append(gif_frame)

    gif_frames[0].save(
        output_path,
        save_all=True,
        append_images=gif_frames[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
        disposal=2,
        optimize=True
    )

    return output_path


# ============================================================
# PUBLIC FUNCTION
# ============================================================

def create_roast_card(username, roast_text):
    frames = make_card_frames(username, roast_text)
    return save_gif(frames, username)


generate_roast_card = create_roast_card
make_roast_card = create_roast_card


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":
    test_file = create_roast_card(
        "@DudeNukem",
        "DudeNukem is the kind of guy who could get lost in a fucking revolving door and still blame the building."
    )

    print()
    print("CLEAN NUKEM ROAST CARD COMPLETE")
    print("--------------------------------")
    print(f"Created: {test_file}")
    print()