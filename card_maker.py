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
# CLEAN / SHARP TEXT EDITION
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
# OUTPUT SETTINGS
# ============================================================

# Smaller than the previous 1100px version.
#
# Discord shouldn't need to shrink this nearly as much,
# which should help the lettering stay sharper.
TARGET_WIDTH = 700

# Only NUKEM LABS animates.
FRAME_COUNT = 12

# About a 3.2 second loop.
FRAME_DURATION_MS = 270

# Maximum GIF palette.
GIF_COLORS = 256


# ============================================================
# COLORS
# ============================================================

WHITE = (
    248,
    248,
    248,
    255
)

MENTION_BLUE = (
    150,
    160,
    255,
    255
)

NUKEM_YELLOW = (
    255,
    211,
    0,
    255
)

MUTED_WHITE = (
    190,
    190,
    190,
    255
)

TEXT_EDGE = (
    0,
    0,
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
# FILE HELPERS
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
            font=font,
            stroke_width=1
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
# LOAD ARTWORK AT FINAL SIZE
# ============================================================

def load_master_frame():

    if not FRAME_FILE.exists():

        raise FileNotFoundError(
            f"Missing asset:\n"
            f"{FRAME_FILE}"
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
# NUKEM LABS SIGN FLICKER
# ============================================================

def add_nukem_labs_flicker(
    frame,
    frame_index
):

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

    # Mostly static.
    # Just two brief electrical flickers.
    flicker_pattern = [
        1.00,
        1.00,
        1.00,
        0.94,
        1.07,
        1.01,
        1.00,
        1.00,
        0.97,
        1.05,
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
    # SOFT SIGN GLOW
    # --------------------------------------------------------

    grayscale = brightened.convert(
        "L"
    )

    glow_mask = grayscale.point(
        lambda value:
        255
        if value > 135
        else 0
    )

    glow_mask = glow_mask.filter(
        ImageFilter.GaussianBlur(
            4
        )
    )

    glow_strength = int(
        42
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

    result = Image.alpha_composite(
        result,
        glow
    )

    result = Image.alpha_composite(
        result,
        brightened
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
# SHARP STATIC TEXT
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
    #
    # These are deliberately larger relative to the card
    # than the previous version.
    # --------------------------------------------------------

    username_font_size = max(
        17,
        int(
            width * 0.025
        )
    )

    roast_font_size = max(
        16,
        int(
            width * 0.023
        )
    )

    footer_font_size = max(
        10,
        int(
            width * 0.015
        )
    )


    # Username stays bold.
    username_font = load_font(
        username_font_size,
        bold=True
    )

    # BODY IS NOW BOLD.
    #
    # This is intentional.
    # Thin font strokes are what suffer most when Discord
    # shrinks the GIF.
    roast_font = load_font(
        roast_font_size,
        bold=True
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
    # TEXT AREA
    # --------------------------------------------------------

    text_x = int(
        width * 0.295
    )

    username_y = int(
        height * 0.292
    )

    roast_y = int(
        height * 0.375
    )

    # Give the joke more horizontal room.
    text_right = int(
        width * 0.750
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

    roast_text = clean_roast_for_card(
        display_username,
        roast_text
    )

    draw.text(
        (
            text_x,
            username_y
        ),
        display_username,
        font=username_font,
        fill=MENTION_BLUE,

        # Tiny dark edge.
        # This is NOT a glow.
        # It keeps the lettering separated from the image
        # when Discord scales it.
        stroke_width=1,
        stroke_fill=TEXT_EDGE
    )


    # --------------------------------------------------------
    # ROAST BODY
    # --------------------------------------------------------

    wrapped_lines = wrap_text_by_pixels(
        draw,
        roast_text,
        roast_font,
        max_text_width
    )

    current_y = roast_y

    line_spacing = int(
        roast_font_size
        * 1.45
    )

    for line in wrapped_lines[:5]:

        draw.text(
            (
                text_x,
                current_y
            ),
            line,
            font=roast_font,
            fill=WHITE,
            stroke_width=1,
            stroke_fill=TEXT_EDGE
        )

        current_y += (
            line_spacing
        )


    # --------------------------------------------------------
    # FOOTER DIVIDER
    # --------------------------------------------------------

    divider_y = int(
        height * 0.675
    )

    draw.line(
        (
            text_x,
            divider_y,
            text_right,
            divider_y
        ),
        fill=NUKEM_YELLOW,
        width=2
    )


    # --------------------------------------------------------
    # FOOTER
    # --------------------------------------------------------

    footer_y = int(
        height * 0.708
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

    footer_left_box = draw.textbbox(
        (
            text_x,
            footer_y
        ),
        FOOTER_LEFT,
        font=footer_bold_font
    )

    footer_right_x = (
        footer_left_box[2]
        + int(
            width * 0.012
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
        # ONLY ANIMATED ELEMENT
        # ----------------------------------------------------

        frame = add_nukem_labs_flicker(
            frame,
            frame_index
        )


        # ----------------------------------------------------
        # DRAW TEXT LAST
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
# BUILD SHARED GIF PALETTE
# ============================================================

def build_shared_palette(
    frames
):
    """
    Build one palette for the entire animation.

    We also force the important text colors into the palette
    so GIF quantization has less opportunity to muddy the
    username, roast, divider, and footer.
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

    # Extra space for forced color swatches.
    swatch_height = 40

    palette_strip = Image.new(
        "RGB",
        (
            sample_width,
            (
                sample_height
                * len(
                    sample_indexes
                )
            )
            + swatch_height
        ),
        (
            0,
            0,
            0
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


    # --------------------------------------------------------
    # FORCE IMPORTANT UI COLORS INTO PALETTE
    # --------------------------------------------------------

    swatch_draw = ImageDraw.Draw(
        palette_strip
    )

    forced_colors = [
        WHITE[:3],
        MENTION_BLUE[:3],
        NUKEM_YELLOW[:3],
        MUTED_WHITE[:3],
        TEXT_EDGE[:3],
    ]

    swatch_width = (
        sample_width
        // len(
            forced_colors
        )
    )

    for index, color in enumerate(
        forced_colors
    ):

        x1 = (
            index
            * swatch_width
        )

        x2 = (
            sample_width
            if index
            == len(
                forced_colors
            ) - 1
            else (
                x1
                + swatch_width
            )
        )

        swatch_draw.rectangle(
            (
                x1,
                current_y,
                x2,
                current_y
                + swatch_height
            ),
            fill=color
        )


    # --------------------------------------------------------
    # CREATE 256-COLOR MASTER PALETTE
    # --------------------------------------------------------

    palette = palette_strip.quantize(
        colors=GIF_COLORS,
        method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.NONE
    )

    return palette


# ============================================================
# SAVE GIF
# ============================================================

def save_gif(
    frames,
    username
):

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
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
    # ONE PALETTE FOR EVERY FRAME
    # --------------------------------------------------------

    shared_palette = build_shared_palette(
        frames
    )


    # --------------------------------------------------------
    # CONVERT FRAMES
    #
    # Dithering stays OFF.
    #
    # Dithering can be great for photographs, but around
    # small typography it can look like fuzzy pixels.
    # --------------------------------------------------------

    gif_frames = []

    for frame in frames:

        rgb_frame = frame.convert(
            "RGB"
        )

        paletted_frame = rgb_frame.quantize(
            palette=shared_palette,
            dither=Image.Dither.NONE
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
        append_images=gif_frames[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
        disposal=1,
        optimize=True
    )

    return output_path


# ============================================================
# PUBLIC BOT FUNCTION
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

    test_file = create_roast_card(
        "@DudeNukem",
        (
            "DudeNukem is the kind of guy who could "
            "get lost in a fucking revolving door and "
            "still blame the building."
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
        "SHARP TEXT NUKEM ROAST CARD COMPLETE"
    )

    print(
        "-------------------------------------"
    )

    print(
        f"Created: {test_file}"
    )

    print(
        f"Output width: {TARGET_WIDTH}px"
    )

    print(
        f"File size: {file_size_mb:.2f} MB"
    )

    print()