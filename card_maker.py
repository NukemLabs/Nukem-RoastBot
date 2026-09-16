import os
import re
from datetime import datetime

from PIL import (
    Image,
    ImageDraw,
    ImageFont,
    ImageEnhance,
)


# ============================================================
# NUKEM ROASTBOT
# HIGH-DPI PRODUCTION EDITION
#
# FINAL CARD DESIGN
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
    "roast_frame.png"
)


# ============================================================
# HIGH-DPI OUTPUT
# ============================================================

# Discord displays this at roughly half size.
# 1040px source = approximately 520px visual footprint.
TARGET_WIDTH = 1040


# ============================================================
# COLORS
# ============================================================

USERNAME_COLOR = (
    150,
    165,
    255
)

BODY_COLOR = (
    255,
    255,
    255
)

NUKEM_YELLOW = (
    255,
    210,
    0
)

FOOTER_GRAY = (
    205,
    205,
    205
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


    # --------------------------------------------------------
    # WINDOWS
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # LINUX / RAILWAY
    # --------------------------------------------------------

    if bold:

        candidates.extend([
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",

            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",

            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",

            "DejaVuSans-Bold.ttf",
        ])

    else:

        candidates.extend([
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans.ttf",

            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",

            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",

            "DejaVuSans.ttf",
        ])


    # --------------------------------------------------------
    # TRY REAL TTF FONTS
    # --------------------------------------------------------

    for font_path in candidates:

        try:

            return ImageFont.truetype(
                font_path,
                size
            )

        except Exception:

            pass


    # --------------------------------------------------------
    # SCALABLE PILLOW FALLBACK
    # --------------------------------------------------------

    try:

        return ImageFont.load_default(
            size=size
        )

    except TypeError:

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
        font=font
    )

    return (
        bbox[2] - bbox[0],
        bbox[3] - bbox[1]
    )


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
# HIGH-DPI AUTO FIT
# ============================================================

def fit_roast_text(
    draw,
    text,
    max_width,
    max_height
):

    # Approximately at Discord display size:
    #
    # 36px -> ~18px
    # 34px -> ~17px
    # 32px -> ~16px
    # 30px -> ~15px

    for font_size in [
        36,
        34,
        32,
        30,
        28,
    ]:

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


        _, glyph_height = text_size(
            draw,
            "Ag",
            font
        )


        line_gap = max(
            8,
            int(
                font_size
                * 0.25
            )
        )


        total_height = (
            len(lines)
            * glyph_height
            + max(
                0,
                len(lines) - 1
            )
            * line_gap
        )


        if (
            len(lines) <= 5
            and total_height <= max_height
        ):

            return (
                font,
                lines,
                glyph_height,
                line_gap
            )


    # --------------------------------------------------------
    # LONG ROAST FALLBACK
    # --------------------------------------------------------

    font = load_font(
        28,
        bold=True
    )


    lines = wrap_text(
        draw,
        text,
        font,
        max_width
    )


    _, glyph_height = text_size(
        draw,
        "Ag",
        font
    )


    line_gap = 8


    max_lines = int(
        (
            max_height
            + line_gap
        )
        / (
            glyph_height
            + line_gap
        )
    )


    max_lines = max(
        1,
        max_lines
    )


    lines = lines[
        :max_lines
    ]


    return (
        font,
        lines,
        glyph_height,
        line_gap
    )


# ============================================================
# LOAD BACKGROUND
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
        "RGB"
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
            1.05
        )
    )


    return base


# ============================================================
# DRAW CARD CONTENT
# ============================================================

def add_roast_content(
    image,
    username,
    roast_text
):

    draw = ImageDraw.Draw(
        image
    )


    width, height = image.size


    # ========================================================
    # FINAL LAYOUT
    # ========================================================

    text_left = int(
        width * 0.295
    )


    # FINAL POLISH:
    #
    # Previous production version:
    #     0.800
    #
    # Final version:
    #     0.815
    #
    # This adds roughly 3% more usable line width without
    # changing any typography or vertical positioning.
    text_right = int(
        width * 0.815
    )


    username_y = int(
        height * 0.270
    )


    body_top = int(
        height * 0.365
    )


    divider_y = int(
        height * 0.700
    )


    footer_y = int(
        height * 0.725
    )


    max_text_width = (
        text_right
        - text_left
    )


    max_body_height = (
        divider_y
        - body_top
        - 24
    )


    # ========================================================
    # USERNAME
    # ========================================================

    username_font = load_font(
        32,
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


    draw.text(
        (
            text_left,
            username_y
        ),
        display_username,
        font=username_font,
        fill=USERNAME_COLOR,
        stroke_width=1,
        stroke_fill=USERNAME_COLOR
    )


    # ========================================================
    # ROAST BODY
    # ========================================================

    (
        roast_font,
        roast_lines,
        glyph_height,
        line_gap
    ) = fit_roast_text(
        draw,
        roast_text,
        max_text_width,
        max_body_height
    )


    current_y = body_top


    for line in roast_lines:

        draw.text(
            (
                text_left,
                current_y
            ),
            line,
            font=roast_font,
            fill=BODY_COLOR,
            stroke_width=1,
            stroke_fill=BODY_COLOR
        )


        current_y += (
            glyph_height
            + line_gap
        )


    # ========================================================
    # DIVIDER
    # ========================================================

    draw.line(
        (
            text_left,
            divider_y,
            text_right,
            divider_y
        ),
        fill=NUKEM_YELLOW,
        width=4
    )


    # ========================================================
    # FOOTER
    # ========================================================

    footer_brand_font = load_font(
        18,
        bold=True
    )


    footer_font = load_font(
        17,
        bold=False
    )


    brand_text = (
        "NukemLabs"
    )


    draw.text(
        (
            text_left,
            footer_y
        ),
        brand_text,
        font=footer_brand_font,
        fill=NUKEM_YELLOW
    )


    brand_width, _ = text_size(
        draw,
        brand_text,
        footer_brand_font
    )


    draw.text(
        (
            text_left
            + brand_width
            + 14,
            footer_y
        ),
        "•  We regret nothing.",
        font=footer_font,
        fill=FOOTER_GRAY
    )


    return image


# ============================================================
# SAVE LOSSLESS PNG
# ============================================================

def save_png(
    image,
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
            f"{timestamp}.png"
        )
    )


    image.save(
        output_path,
        format="PNG",
        optimize=False,
        compress_level=1
    )


    return output_path


# ============================================================
# PUBLIC BOT FUNCTION
# ============================================================

def create_roast_card(
    username,
    roast_text
):

    base = load_base_frame()


    card = add_roast_content(
        base,
        username,
        roast_text
    )


    return save_png(
        card,
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
        "DudeNukem radiates the frantic energy "
        "of a man trying to defuse a ticking bomb "
        "by aggressively arguing with the timer "
        "about its fucking tone of voice."
    )


    result = create_roast_card(
        test_username,
        test_roast
    )


    file_size_kb = (
        os.path.getsize(
            result
        )
        / 1024
    )


    print()

    print(
        "FINAL NUKEM ROASTBOT CARD CREATED"
    )

    print(
        "---------------------------------"
    )

    print(
        result
    )

    print(
        f"Width: {TARGET_WIDTH}px"
    )

    print(
        f"File size: "
        f"{file_size_kb:.0f} KB"
    )

    print()