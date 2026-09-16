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
# NUKEM ROASTBOT
# HIGH-QUALITY ANIMATED ROAST CARD
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "generated_roasts"

FRAME_FILE = (
    ASSETS_DIR
    / "nukem_labs_industrial_overlay.png"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# QUALITY SETTINGS
# ============================================================

# Render significantly larger than Discord's preview.
# Discord will scale it down, which should keep the text
# and edges considerably sharper.
TARGET_WIDTH = 1100

# Only one animation remains:
# the subtle NUKEM LABS sign flicker.
FRAME_COUNT = 14

# 14 x 220ms = about a 3-second loop.
FRAME_DURATION_MS = 220

# GIF's maximum practical palette.
GIF_COLORS = 256


# ============================================================
# COLORS
# ============================================================

WHITE = (
    242,
    242,
    242,
    255
)

MUTED_WHITE = (
    188,
    188,
    188,
    255
)

MENTION_BLUE = (
    145,
    155,
    255,
    255
)

NUKEM_YELLOW = (
    255,
    210,
    0,
    255
)


# ============================================================
# FOOTER
# ============================================================

FOOTER_LEFT = "NukemLabs"

FOOTER_RIGHT = (
    "•  We regret nothing."
)


# ============================================================
# FONT LOADING
# ============================================================

def load_font(
    size,
    bold=False
):

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

        if os.path.exists(
            font_path
        ):

            try:

                return ImageFont.truetype(
                    font_path,
                    size
                )

            except Exception:

                pass

    try:

        return ImageFont.load_default(
            size=size
        )

    except TypeError:

        return ImageFont.load_default()


# ============================================================
# SAFE FILENAMES
# ============================================================

def safe_filename(
    text
):

    text = re.sub(
        r"[^a-zA-Z0-9_-]+",
        "_",
        text
    )

    text = text.strip(
        "_"
    )

    return text or "user"


# ============================================================
# CLEAN ROAST TEXT
# ============================================================

def clean_roast_for_card(
    username,
    roast_text
):

    if not roast_text:

        return ""

    clean_username = (
        username
        .lstrip("@")
        .strip()
    )

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

            text = (
                text[0].upper()
                + text[1:]
            )

    elif text:

        text = (
            text[0].upper()
            + text[1:]
        )

    return text


# ============================================================
# WORD WRAPPING
# ============================================================

def wrap_text_by_pixels(
    draw,
    text,
    font,
    max_width
):

    words = text.split()

    lines = []

    current_line = ""

    for word in words:

        test_line = (
            current_line
            + (
                " "
                if current_line
                else ""
            )
            + word
        )

        bbox = draw.textbbox(
            (0, 0),
            test_line,
            font=font
        )

        test_width = (
            bbox[2]
            - bbox[0]
        )

        if test_width <= max_width:

            current_line = test_line

        else:

            if current_line:

                lines.append(
                    current_line
                )

            current_line = word

    if current_line:

        lines.append(
            current_line
        )

    return lines


# ============================================================
# LOAD MASTER ART
# ============================================================

def load_master_frame():

    if not FRAME_FILE.exists():

        raise FileNotFoundError(
            f"Missing asset:\n"
            f"{FRAME_FILE}\n\n"
            f"Put "
            f"nukem_labs_industrial_overlay.png "
            f"in the assets folder."
        )

    base = Image.open(
        FRAME_FILE
    ).convert(
        "RGBA"
    )

    ratio = (
        TARGET_WIDTH
        / base.width
    )

    target_height = int(
        round(
            base.height
            * ratio
        )
    )

    if base.width != TARGET_WIDTH:

        base = base.resize(
            (
                TARGET_WIDTH,
                target_height
            ),
            Image.Resampling.LANCZOS
        )

    return base


# ============================================================
# ONLY ANIMATION:
# NUKEM LABS FLICKER
# ============================================================

def add_nukem_labs_flicker(
    frame,
    frame_index
):
    """
    Only the left NUKEM LABS sign moves.

    Most of the loop is completely stable.
    There are only a couple of quick electrical dips
    and brighter pulses.
    """

    width, height = frame.size

    left = int(
        width * 0.020
    )

    top = int(
        height * 0.105
    )

    right = int(
        width * 0.235
    )

    bottom = int(
        height * 0.465
    )

    panel_box = (
        left,
        top,
        right,
        bottom
    )

    # Mostly stable, with a few quick flickers.
    flicker_pattern = [
        1.00,
        1.00,
        1.01,
        1.00,
        0.94,
        1.06,
        1.01,
        1.00,
        1.00,
        0.97,
        1.04,
        1.00,
        1.00,
        1.00,
    ]

    brightness = (
        flicker_pattern[
            frame_index
            % len(
                flicker_pattern
            )
        ]
    )

    panel = frame.crop(
        panel_box
    ).convert(
        "RGBA"
    )

    brightened = (
        ImageEnhance
        .Brightness(
            panel
        )
        .enhance(
            brightness
        )
    )


    # --------------------------------------------------------
    # SMALL NEON BLOOM
    # --------------------------------------------------------

    grayscale = (
        brightened
        .convert(
            "L"
        )
    )

    glow_mask = grayscale.point(
        lambda value:
        255
        if value > 135
        else 0
    )

    glow_mask = glow_mask.filter(
        ImageFilter.GaussianBlur(
            max(
                5,
                int(
                    width
                    * 0.006
                )
            )
        )
    )

    # Keep the glow restrained.
    glow_strength = int(
        48
        + max(
            0,
            brightness - 1.0
        )
        * 250
    )

    glow_alpha = glow_mask.point(
        lambda value:
        int(
            value
            * min(
                1.0,
                glow_strength
                / 255.0
            )
        )
    )

    glow = Image.new(
        "RGBA",
        brightened.size,
        (
            220,
            255,
            45,
            0
        )
    )

    glow.putalpha(
        glow_alpha
    )

    result = Image.new(
        "RGBA",
        brightened.size,
        (
            0,
            0,
            0,
            0
        )
    )

    result = (
        Image.alpha_composite(
            result,
            glow
        )
    )

    result = (
        Image.alpha_composite(
            result,
            brightened
        )
    )

    frame.paste(
        result,
        (
            left,
            top
        ),
        result
    )

    return frame


# ============================================================
# STATIC ROAST CONTENT
# ============================================================

def add_roast_text(
    frame,
    username,
    roast_text
):

    draw = ImageDraw.Draw(
        frame
    )

    width, height = frame.size


    # --------------------------------------------------------
    # FONT SIZES
    # --------------------------------------------------------

    username_font_size = max(
        24,
        int(
            width
            * 0.023
        )
    )

    roast_font_size = max(
        20,
        int(
            width
            * 0.019
        )
    )

    footer_font_size = max(
        15,
        int(
            width
            * 0.014
        )
    )


    username_font = load_font(
        username_font_size,
        bold=True
    )

    roast_font = load_font(
        roast_font_size,
        bold=False
    )

    footer_bold_font = load_font(
        footer_font_size,
        bold=True
    )

    footer_font = load_font(
        footer_font_size,
        bold=False
    )


    # --------------------------------------------------------
    # LAYOUT
    # --------------------------------------------------------

    text_x = int(
        width
        * 0.295
    )

    username_y = int(
        height
        * 0.292
    )

    roast_y = int(
        height
        * 0.375
    )

    text_right = int(
        width
        * 0.735
    )

    max_text_width = (
        text_right
        - text_x
    )


    # --------------------------------------------------------
    # USERNAME
    # --------------------------------------------------------

    display_username = (
        username
        if username.startswith(
            "@"
        )
        else "@"
        + username
    )

    roast_text = (
        clean_roast_for_card(
            display_username,
            roast_text
        )
    )

    draw.text(
        (
            text_x,
            username_y
        ),
        display_username,
        font=username_font,
        fill=MENTION_BLUE
    )


    # --------------------------------------------------------
    # ROAST
    # --------------------------------------------------------

    wrapped_lines = (
        wrap_text_by_pixels(
            draw,
            roast_text,
            roast_font,
            max_text_width
        )
    )

    current_y = roast_y

    line_spacing = int(
        roast_font_size
        * 1.43
    )

    for line in wrapped_lines[:6]:

        draw.text(
            (
                text_x,
                current_y
            ),
            line,
            font=roast_font,
            fill=WHITE
        )

        current_y += (
            line_spacing
        )


    # --------------------------------------------------------
    # FOOTER DIVIDER
    # --------------------------------------------------------

    divider_y = int(
        height
        * 0.675
    )

    draw.line(
        (
            text_x,
            divider_y,
            text_right,
            divider_y
        ),
        fill=NUKEM_YELLOW,
        width=max(
            3,
            int(
                width
                * 0.002
            )
        )
    )


    # --------------------------------------------------------
    # FOOTER
    # --------------------------------------------------------

    footer_y = int(
        height
        * 0.708
    )

    draw.text(
        (
            text_x,
            footer_y
        ),
        FOOTER_LEFT,
        font=footer_bold_font,
        fill=NUKEM_YELLOW
    )

    footer_left_box = (
        draw.textbbox(
            (
                text_x,
                footer_y
            ),
            FOOTER_LEFT,
            font=footer_bold_font
        )
    )

    footer_right_x = (
        footer_left_box[2]
        + int(
            width
            * 0.012
        )
    )

    draw.text(
        (
            footer_right_x,
            footer_y
        ),
        FOOTER_RIGHT,
        font=footer_font,
        fill=MUTED_WHITE
    )

    return frame


# ============================================================
# BUILD FRAMES
# ============================================================

def make_card_frames(
    username,
    roast_text
):

    base = load_master_frame()

    frames = []

    for frame_index in range(
        FRAME_COUNT
    ):

        frame = base.copy()


        # ----------------------------------------------------
        # ONLY MOVING ELEMENT
        # ----------------------------------------------------

        frame = (
            add_nukem_labs_flicker(
                frame,
                frame_index
            )
        )


        # ----------------------------------------------------
        # EVERYTHING ELSE STAYS STATIC
        # ----------------------------------------------------

        frame = add_roast_text(
            frame,
            username,
            roast_text
        )

        frames.append(
            frame
        )

    return frames


# ============================================================
# SHARED 256-COLOR PALETTE
# ============================================================

def build_shared_palette(
    frames
):
    """
    The old version made a separate 128-color palette
    for every frame.

    This version builds ONE 256-color palette from several
    frames and uses it throughout the animation.

    That keeps the artwork and text from changing colors
    or becoming muddy between frames.
    """

    sample_indexes = sorted({
        0,
        len(frames) // 3,
        (
            len(frames)
            * 2
        ) // 3,
        len(frames) - 1,
    })

    width, height = (
        frames[0].size
    )

    sample_width = max(
        1,
        width // 2
    )

    sample_height = max(
        1,
        height // 2
    )

    palette_strip = Image.new(
        "RGB",
        (
            sample_width,
            sample_height
            * len(
                sample_indexes
            )
        )
    )

    current_y = 0

    for index in sample_indexes:

        sample = (
            frames[index]
            .convert(
                "RGB"
            )
            .resize(
                (
                    sample_width,
                    sample_height
                ),
                Image.Resampling.LANCZOS
            )
        )

        palette_strip.paste(
            sample,
            (
                0,
                current_y
            )
        )

        current_y += (
            sample_height
        )

    palette = (
        palette_strip
        .quantize(
            colors=GIF_COLORS,
            method=(
                Image
                .Quantize
                .MEDIANCUT
            ),
            dither=(
                Image
                .Dither
                .NONE
            )
        )
    )

    return palette


# ============================================================
# SAVE HIGH-QUALITY GIF
# ============================================================

def save_gif(
    frames,
    username
):

    timestamp = (
        datetime.now()
        .strftime(
            "%Y%m%d_%H%M%S_%f"
        )
    )

    name_part = safe_filename(
        username.replace(
            "@",
            ""
        )
    )

    output_path = (
        OUTPUT_DIR
        / (
            f"roast_"
            f"{name_part}_"
            f"{timestamp}.gif"
        )
    )


    # --------------------------------------------------------
    # BUILD ONE SHARED PALETTE
    # --------------------------------------------------------

    shared_palette = (
        build_shared_palette(
            frames
        )
    )


    # --------------------------------------------------------
    # CONVERT EVERY FRAME USING SAME PALETTE
    # --------------------------------------------------------

    gif_frames = []

    for frame in frames:

        rgb_frame = (
            frame.convert(
                "RGB"
            )
        )

        paletted_frame = (
            rgb_frame.quantize(
                palette=shared_palette,
                dither=(
                    Image
                    .Dither
                    .NONE
                )
            )
        )

        gif_frames.append(
            paletted_frame
        )


    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    gif_frames[0].save(
        output_path,
        save_all=True,
        append_images=(
            gif_frames[1:]
        ),
        duration=(
            FRAME_DURATION_MS
        ),
        loop=0,
        disposal=1,
        optimize=True
    )

    return output_path


# ============================================================
# PUBLIC FUNCTION USED BY BOT.PY
# ============================================================

def create_roast_card(
    username,
    roast_text
):

    frames = make_card_frames(
        username,
        roast_text
    )

    return save_gif(
        frames,
        username
    )


generate_roast_card = (
    create_roast_card
)

make_roast_card = (
    create_roast_card
)


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    test_file = (
        create_roast_card(
            "@DudeNukem",
            (
                "DudeNukem is the kind of guy "
                "who could get lost in a fucking "
                "revolving door and still blame "
                "the building."
            )
        )
    )

    file_size_mb = (
        Path(
            test_file
        ).stat().st_size
        / (
            1024
            * 1024
        )
    )

    print()

    print(
        "HIGH-QUALITY NUKEM ROAST CARD COMPLETE"
    )

    print(
        "---------------------------------------"
    )

    print(
        f"Created: {test_file}"
    )

    print(
        f"File size: "
        f"{file_size_mb:.2f} MB"
    )

    print()