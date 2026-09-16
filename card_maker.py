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
# HIGH-DPI PRODUCTION CARD
#
# FINAL SAFE-BOUNDS EDITION
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

# Discord displays this around half size.
# 1040px source gives us much sharper text in chat.
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
#
# Works on:
# - Windows
# - Railway / Linux
# - Pillow scalable fallback
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
    # TRY REAL TTF FONT
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

def text_bbox(
    draw,
    text,
    font
):

    return draw.textbbox(
        (0, 0),
        text,
        font=font
    )


def text_width(
    draw,
    text,
    font
):

    bbox = text_bbox(
        draw,
        text,
        font
    )

    return (
        bbox[2]
        - bbox[0]
    )


def text_height(
    draw,
    text,
    font
):

    bbox = text_bbox(
        draw,
        text,
        font
    )

    return (
        bbox[3]
        - bbox[1]
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

    current_line = words[0]


    for word in words[1:]:

        test_line = (
            current_line
            + " "
            + word
        )


        if (
            text_width(
                draw,
                test_line,
                font
            )
            <= max_width
        ):

            current_line = test_line

        else:

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
# BLOCK HEIGHT
# ============================================================

def calculate_block_height(
    draw,
    lines,
    font,
    line_gap
):

    if not lines:

        return 0


    total = 0


    for index, line in enumerate(
        lines
    ):

        total += text_height(
            draw,
            line,
            font
        )


        if index < len(lines) - 1:

            total += line_gap


    return total


# ============================================================
# LONG TEXT TRIMMER
# ============================================================

def trim_text_to_fit(
    draw,
    text,
    font,
    max_width,
    max_height,
    line_gap,
    max_lines=5
):

    words = text.split()


    while words:

        candidate = (
            " ".join(words)
            .rstrip()
        )


        lines = wrap_text(
            draw,
            candidate,
            font,
            max_width
        )


        block_height = (
            calculate_block_height(
                draw,
                lines,
                font,
                line_gap
            )
        )


        if (
            len(lines) <= max_lines
            and
            block_height <= max_height
        ):

            if candidate != text:

                last_line = lines[-1]


                while (
                    last_line
                    and
                    text_width(
                        draw,
                        last_line + "...",
                        font
                    )
                    > max_width
                ):

                    last_line = (
                        last_line[:-1]
                        .rstrip()
                    )


                if last_line:

                    lines[-1] = (
                        last_line
                        + "..."
                    )


            return lines


        words.pop()


    return ["..."]


# ============================================================
# BULLETPROOF AUTO-FIT
#
# This guarantees the roast stays inside the safe area.
# ============================================================

def fit_roast_text(
    draw,
    text,
    max_width,
    max_height
):

    font_sizes = [
        36,
        34,
        32,
        30,
        28,
        26,
        24,
    ]


    for font_size in font_sizes:

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


        line_gap = max(
            7,
            int(
                font_size
                * 0.23
            )
        )


        block_height = (
            calculate_block_height(
                draw,
                lines,
                font,
                line_gap
            )
        )


        if (
            len(lines) <= 5
            and
            block_height <= max_height
        ):

            return (
                font,
                lines,
                line_gap
            )


    # --------------------------------------------------------
    # EXTREME LONG-ROAST FALLBACK
    #
    # Never leave the box.
    # --------------------------------------------------------

    font = load_font(
        24,
        bold=True
    )


    line_gap = 7


    lines = trim_text_to_fit(
        draw,
        text,
        font,
        max_width,
        max_height,
        line_gap,
        max_lines=5
    )


    return (
        font,
        lines,
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
# DRAW CARD
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
    # SAFE CONTENT AREA
    #
    # These bounds deliberately stop BEFORE the green frame.
    # ========================================================

    text_left = int(
        width * 0.295
    )


    # Pulled back slightly from the previous version.
    #
    # This guarantees text stays inside the black panel.
    text_right = int(
        width * 0.775
    )


    username_y = int(
        height * 0.270
    )


    body_top = int(
        height * 0.355
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


    # Extra safety gap above divider.
    max_body_height = (
        divider_y
        - body_top
        - 30
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
            text_height(
                draw,
                line,
                roast_font
            )
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


    brand_width = text_width(
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


    # Deliberately long test roast so we can prove the
    # auto-fit system keeps everything inside the panel.
    test_roast = (
        "DudeNukem carries the frantic energy of a man "
        "trying to explain the history of the universe "
        "to a brick wall while somehow remaining entirely "
        "convinced he's the smartest bastard in the room "
        "despite all available evidence suggesting otherwise."
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
        "FINAL SAFE-BOUNDS ROAST CARD CREATED"
    )

    print(
        "------------------------------------"
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