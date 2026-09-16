import os
import re
from datetime import datetime

from PIL import (
    Image,
    ImageDraw,
    ImageFont,
    ImageFilter,
    ImageEnhance,
)


# ============================================================
# NUKEM ROASTBOT
# COMPACT DISCORD EDITION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

ASSETS_DIR = os.path.join(
    BASE_DIR,
    "assets"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "generated_roasts"
)

FRAME_FILE = os.path.join(
    ASSETS_DIR,
    "nukem_labs_industrial_overlay.png"
)


# ============================================================
# OUTPUT SETTINGS
# ============================================================

TARGET_WIDTH = 520

FRAME_COUNT = 8

FRAME_DURATIONS = [
    500,
    90,
    90,
    130,
    650,
    90,
    120,
    900,
]

GIF_COLORS = 256


# ============================================================
# COLORS
# ============================================================

USERNAME_COLOR = (
    145,
    155,
    255
)

BODY_COLOR = (
    245,
    245,
    245
)

FOOTER_GRAY = (
    180,
    180,
    180
)

NUKEM_YELLOW = (
    255,
    210,
    0
)

TEXT_EDGE = (
    0,
    0,
    0
)


# ============================================================
# DIRECTORY SETUP
# ============================================================

def ensure_dirs():

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )


# ============================================================
# SAFE FILENAMES
# ============================================================

def safe_filename(text):

    text = re.sub(
        r"[^a-zA-Z0-9_-]+",
        "_",
        text
    )

    text = text.strip("_")

    return text or "user"


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
                r"C:\Windows\Fonts\verdanab.ttf",
                r"C:\Windows\Fonts\bahnschrift.ttf",
            ])

        else:

            candidates.extend([
                r"C:\Windows\Fonts\segoeui.ttf",
                r"C:\Windows\Fonts\arial.ttf",
                r"C:\Windows\Fonts\verdana.ttf",
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

    return ImageFont.load_default()


# ============================================================
# TEXT MEASUREMENT
# ============================================================

def text_size(
    draw,
    text,
    font
):

    bbox = draw.textbbox(
        (0, 0),
        text,
        font=font,
        stroke_width=1
    )

    return (
        bbox[2] - bbox[0],
        bbox[3] - bbox[1]
    )


# ============================================================
# CLEAN ROAST
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

def wrap_text(
    draw,
    text,
    font,
    max_width
):

    words = text.split()

    if not words:

        return [""]

    lines = []

    current = words[0]

    for word in words[1:]:

        test = (
            current
            + " "
            + word
        )

        width, _ = text_size(
            draw,
            test,
            font
        )

        if width <= max_width:

            current = test

        else:

            lines.append(
                current
            )

            current = word

    if current:

        lines.append(
            current
        )

    return lines


# ============================================================
# AUTOMATIC ROAST FONT FITTING
# ============================================================

def fit_roast_text(
    draw,
    text,
    max_width,
    max_height
):

    for font_size in range(
        15,
        10,
        -1
    ):

        font = load_font(
            font_size,
            bold=True
        )

        lines = wrap_text(
            draw,
            text,
            font,
            max_width
        )

        line_height = (
            font_size
            + 5
        )

        total_height = (
            len(lines)
            * line_height
        )

        if (
            len(lines) <= 5
            and
            total_height <= max_height
        ):

            return (
                font,
                lines,
                line_height
            )

    font = load_font(
        10,
        bold=True
    )

    lines = wrap_text(
        draw,
        text,
        font,
        max_width
    )

    return (
        font,
        lines[:5],
        15
    )


# ============================================================
# SHARP TEXT
# ============================================================

def draw_sharp_text(
    draw,
    position,
    text,
    font,
    fill
):

    draw.text(
        position,
        text,
        font=font,
        fill=fill,
        stroke_width=1,
        stroke_fill=TEXT_EDGE
    )


# ============================================================
# BASE IMAGE
# ============================================================

def load_base_frame():

    if not os.path.exists(
        FRAME_FILE
    ):

        raise FileNotFoundError(
            f"Missing asset:\n"
            f"{FRAME_FILE}"
        )

    base = Image.open(
        FRAME_FILE
    ).convert(
        "RGBA"
    )

    scale = (
        TARGET_WIDTH
        / base.width
    )

    target_height = int(
        round(
            base.height
            * scale
        )
    )

    base = base.resize(
        (
            TARGET_WIDTH,
            target_height
        ),
        Image.Resampling.LANCZOS
    )

    base = (
        ImageEnhance
        .Sharpness(
            base
        )
        .enhance(
            1.08
        )
    )

    return base


# ============================================================
# NUKEM LABS FLICKER
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

    flicker_values = [
        1.00,
        0.93,
        1.07,
        1.01,
        1.00,
        0.96,
        1.05,
        1.00,
    ]

    brightness = (
        flicker_values[
            frame_index
            % len(
                flicker_values
            )
        ]
    )

    panel = frame.crop(
        panel_box
    ).convert(
        "RGBA"
    )

    panel = (
        ImageEnhance
        .Brightness(
            panel
        )
        .enhance(
            brightness
        )
    )

    grayscale = panel.convert(
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
        38
        + max(
            0,
            brightness - 1.0
        )
        * 220
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
        panel.size,
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
        panel.size,
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
        panel
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
# STATIC TEXT LAYER
# ============================================================

def make_text_layer(
    size,
    username,
    roast_text
):

    width, height = size

    layer = Image.new(
        "RGBA",
        size,
        (
            0,
            0,
            0,
            0
        )
    )

    draw = ImageDraw.Draw(
        layer
    )


    # --------------------------------------------------------
    # LAYOUT
    # --------------------------------------------------------

    text_left = int(
        width * 0.295
    )

    text_right = int(
        width * 0.770
    )


    # --------------------------------------------------------
    # MOVED UP
    #
    # Previous:
    # username_y = 0.300
    # body_top   = 0.390
    #
    # New:
    # about 8 pixels higher on this 520px card.
    # --------------------------------------------------------

    username_y = int(
        height * 0.273
    )

    body_top = int(
        height * 0.363
    )


    # Footer stays exactly where we liked it.
    divider_y = int(
        height * 0.685
    )

    footer_y = int(
        height * 0.718
    )


    max_text_width = (
        text_right
        - text_left
    )

    max_body_height = (
        divider_y
        - body_top
        - 9
    )


    # --------------------------------------------------------
    # USERNAME
    # --------------------------------------------------------

    username_font = load_font(
        15,
        bold=True
    )

    display_username = (
        username
        if username.startswith("@")
        else "@"
        + username
    )

    roast_text = clean_roast_for_card(
        display_username,
        roast_text
    )

    draw_sharp_text(
        draw,
        (
            text_left,
            username_y
        ),
        display_username,
        username_font,
        USERNAME_COLOR
    )


    # --------------------------------------------------------
    # ROAST BODY
    # --------------------------------------------------------

    (
        roast_font,
        roast_lines,
        line_height
    ) = fit_roast_text(
        draw,
        roast_text,
        max_text_width,
        max_body_height
    )

    current_y = body_top

    for line in roast_lines:

        draw_sharp_text(
            draw,
            (
                text_left,
                current_y
            ),
            line,
            roast_font,
            BODY_COLOR
        )

        current_y += (
            line_height
        )


    # --------------------------------------------------------
    # DIVIDER
    # --------------------------------------------------------

    draw.line(
        (
            text_left,
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

    footer_bold_font = load_font(
        9,
        bold=True
    )

    footer_font = load_font(
        9,
        bold=False
    )

    draw.text(
        (
            text_left,
            footer_y
        ),
        "NukemLabs",
        font=footer_bold_font,
        fill=NUKEM_YELLOW
    )

    nukem_width, _ = text_size(
        draw,
        "NukemLabs",
        footer_bold_font
    )

    draw.text(
        (
            text_left
            + nukem_width
            + 6,
            footer_y
        ),
        "•  We regret nothing.",
        font=footer_font,
        fill=FOOTER_GRAY
    )

    return layer


# ============================================================
# BUILD FRAMES
# ============================================================

def build_frames(
    username,
    roast_text
):

    base = load_base_frame()

    text_layer = make_text_layer(
        base.size,
        username,
        roast_text
    )

    frames = []

    for frame_index in range(
        FRAME_COUNT
    ):

        frame = base.copy()

        frame = add_nukem_labs_flicker(
            frame,
            frame_index
        )

        frame = Image.alpha_composite(
            frame,
            text_layer
        )

        frames.append(
            frame
        )

    return frames


# ============================================================
# SAVE GIF
# ============================================================

def save_gif(
    frames,
    username
):

    ensure_dirs()

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    clean_name = safe_filename(
        username.replace(
            "@",
            ""
        )
    )

    output_path = os.path.join(
        OUTPUT_DIR,
        (
            f"roast_"
            f"{clean_name}_"
            f"{timestamp}.gif"
        )
    )

    first_rgb = frames[0].convert(
        "RGB"
    )

    first_paletted = first_rgb.quantize(
        colors=GIF_COLORS,
        method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.NONE
    )

    gif_frames = [
        first_paletted
    ]

    for frame in frames[1:]:

        rgb_frame = frame.convert(
            "RGB"
        )

        paletted_frame = rgb_frame.quantize(
            palette=first_paletted,
            dither=Image.Dither.NONE
        )

        gif_frames.append(
            paletted_frame
        )

    gif_frames[0].save(
        output_path,
        save_all=True,
        append_images=gif_frames[1:],
        duration=FRAME_DURATIONS,
        loop=0,
        disposal=1,
        optimize=False
    )

    return output_path


# ============================================================
# PUBLIC FUNCTION FOR BOT.PY
# ============================================================

def create_roast_card(
    username,
    roast_text
):

    frames = build_frames(
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

    test_username = (
        "@DudeNukem"
    )

    test_roast = (
        "DudeNukem carries the frantic, disheveled "
        "energy of a man trying to explain quantum "
        "physics to a toaster while actively forgetting "
        "how to fucking breathe."
    )

    result = create_roast_card(
        test_username,
        test_roast
    )

    file_size_mb = (
        os.path.getsize(
            result
        )
        / (
            1024
            * 1024
        )
    )

    print()

    print(
        "COMPACT NUKEM ROAST CARD CREATED"
    )

    print(
        "--------------------------------"
    )

    print(
        result
    )

    print(
        f"Width: {TARGET_WIDTH}px"
    )

    print(
        f"File size: "
        f"{file_size_mb:.2f} MB"
    )

    print()