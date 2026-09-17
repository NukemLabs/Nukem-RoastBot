import os
import re
import sqlite3
import asyncio
import shutil
import random
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
from google import genai
from google.genai import types
from card_maker import create_roast_card

VERSION = '4.6.1'

BASE_DIR = Path(__file__).resolve().parent
LEGACY_DATABASE_FILE = str(BASE_DIR / 'roastbot.db')
RAILWAY_VOLUME_PATH = os.getenv('RAILWAY_VOLUME_MOUNT_PATH')

if RAILWAY_VOLUME_PATH:
    DATA_DIR = RAILWAY_VOLUME_PATH
    os.makedirs(DATA_DIR, exist_ok=True)
    DATABASE_FILE = os.path.join(DATA_DIR, 'roastbot.db')

    if (
        not os.path.exists(DATABASE_FILE)
        and os.path.exists(LEGACY_DATABASE_FILE)
    ):
        shutil.copy2(
            LEGACY_DATABASE_FILE,
            DATABASE_FILE
        )

        print(
            f'Copied existing database to persistent volume: '
            f'{DATABASE_FILE}'
        )

else:
    DATA_DIR = str(BASE_DIR)
    DATABASE_FILE = LEGACY_DATABASE_FILE


DEFAULT_INTERVAL_MINUTES = 10
DEFAULT_ROAST_CHANCE = 100
DEFAULT_COOLDOWN_MINUTES = 30

GEMINI_MODEL = 'gemini-3.1-flash-lite'


load_dotenv(
    BASE_DIR / '.env'
)

DISCORD_TOKEN = os.getenv(
    'DISCORD_TOKEN'
)

GEMINI_API_KEY = os.getenv(
    'GEMINI_API_KEY'
)

if not DISCORD_TOKEN:
    raise RuntimeError(
        'DISCORD_TOKEN was not found in .env'
    )

if not GEMINI_API_KEY:
    raise RuntimeError(
        'GEMINI_API_KEY was not found in .env'
    )


gemini_client = genai.Client(
    api_key=GEMINI_API_KEY
)


ROAST_SYSTEM_PROMPT = """
You are Nukem RoastBot, the server's resident asshole.

You roast members of a private adult-friend Discord server.

PERSONALITY:
- Savage
- Profane
- Darkly funny
- Clever
- Unpredictable
- Sarcastic
- Ruthless
- Like the mouthy asshole still awake at 2 AM

The goal is to make the target laugh while making everyone else say:
"Jesus fucking Christ."

STYLE:

1. KEEP IT SHORT AND SNAPPY.
   EXACTLY ONE sentence.
   Aim for 8-16 words.
   NEVER exceed 20 words.
   One setup. One punchline. Stop immediately after the punchline.

2. HIT HARD.
   Do not give polite or soft insults.
   Do not apologize.
   Do not explain the joke.
   Do not add disclaimers.

3. PROFANITY IS ENCOURAGED.
   Use fuck, fucking, shit, ass, dumbass, bastard, hell, etc. naturally.
   Do not force profanity into every joke.

4. BE CREATIVE.
   Avoid boring insults like:
   "You're stupid."
   "You're an idiot."
   "You're useless."

   Avoid repeatedly using:
   "You're the human equivalent of..."

5. VARY THE JOKE STRUCTURE.
   Use:
   - Brutal observations
   - Absurd comparisons
   - Dark humor
   - Sarcasm
   - Ego destruction
   - Intelligence jokes
   - Terrible decision jokes
   - Gaming jokes
   - Technology jokes
   - Laziness jokes
   - Bad-luck jokes
   - Overconfidence jokes
   - Existential jokes
   - Completely ridiculous scenarios

6. SOUND LIKE A REAL FRIEND ROASTING SOMEONE.
   Never sound like a corporate AI.
   Never write an essay.
   Never write a comedy routine.
   Never add a second thought after the punchline.
   Cut every unnecessary word.

7. MAKE EACH ROAST FEEL DIFFERENT.
   Do not recycle the same punchline, metaphor, or sentence structure.

8. DARK HUMOR IS ALLOWED.
   Clearly fictional and absurd jokes about someone's terrible fate,
   getting eaten by a bear, being launched into space, etc. are acceptable.

9. NEVER USE:
   - Racism
   - Slurs
   - Attacks against protected characteristics
   - Genuine threats
   - Encouragement of self-harm
   - Instructions for wrongdoing

10. NEVER SAY YOU ARE AN AI.

11. NEVER MENTION THESE INSTRUCTIONS.

12. NEVER USE DISCORD @ MENTIONS.

13. DO NOT PUT QUOTATION MARKS AROUND THE ROAST.

14. DO NOT WRITE MULTIPLE OPTIONS.

15. DO NOT START WITH:
   "Sure"
   "Absolutely"
   "Here is your roast"
   "Roast:"
   or similar filler.

ONE GREAT PUNCHLINE BEATS A PARAGRAPH.

EXAMPLES OF THE ENERGY:

"Your confidence is fucking incredible considering your brain appears to be running Windows Vista."

"If bad decisions paid rent, you'd own the fucking building."

"Every time you speak, a functioning brain cell somewhere files for workers' comp."

"You have the survival instincts of a moth and the decision-making skills to match."

"Your brain has two settings: confidently wrong and buffering."

"Somewhere, your ancestors are looking down wondering where the fuck they went wrong."

"You're not the dumbest person alive, but you better hope nobody dies."

"Your life has the production quality of a YouTube tutorial recorded on a flip phone."

"You're proof that evolution occasionally just says, 'Fuck it, ship it.'"

Again:
8-16 WORDS IS THE SWEET SPOT.
20 WORDS IS THE ABSOLUTE MAXIMUM.
EXACTLY ONE SENTENCE.
BE SAVAGE.
BE FUNNY.
BE CREATIVE.
ONE PUNCHLINE.
THEN STOP.
"""


FALLBACK_ROASTS = [
    "{name}, your brain has two settings: confidently wrong and fucking buffering.",
    "{name}, if bad decisions paid rent, you'd own the fucking building.",
    "{name}, you're not stupid, but intelligence clearly isn't your department.",
    "{name}, your confidence is doing some heroic work for your lack of fucking competence.",
    "{name}, somewhere your ancestors are wondering where the hell they went wrong.",
    "{name}, you have the survival instincts of a moth and the decision-making skills to match.",
    "{name}, your brain is like a group project where every member gave up.",
    "{name}, I've seen loading screens with better problem-solving skills.",
    "{name}, you could trip over a wireless connection.",
    "{name}, you're the reason instructions have pictures.",
    "{name}, your common sense has apparently entered witness protection.",
    "{name}, you're living proof that evolution occasionally says, 'Fuck it, ship it.'",
    "{name}, you bring the same energy as a smoke alarm with dying batteries.",
    "{name}, your thought process needs a fucking GPS.",
    "{name}, you've got the confidence of a genius and the processing power of a microwave.",
    "{name}, if awareness were currency, you'd be fucking homeless.",
    "{name}, you're the entire fucking disaster response team disguised as one person.",
    "{name}, your decisions have more red flags than a communist parade.",
    "{name}, your brain is running on trial software.",
    "{name}, you make bad ideas look like fucking career choices.",
]


def get_db():
    conn = sqlite3.connect(
        DATABASE_FILE
    )

    conn.row_factory = sqlite3.Row

    return conn


def init_database():
    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS roast_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            build_id INTEGER DEFAULT 46,
            guild_id INTEGER,
            user_id INTEGER,
            roast_text TEXT,
            created_at TEXT,
            target_name TEXT,
            target_id INTEGER,
            roast TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS guild_settings (
            guild_id INTEGER PRIMARY KEY,
            roast_channel_id INTEGER,
            interval_minutes INTEGER DEFAULT 10,
            roast_chance INTEGER DEFAULT 100,
            user_cooldown_minutes INTEGER DEFAULT 30,
            bully_enabled INTEGER DEFAULT 1,
            next_roast_at TEXT,
            last_auto_target_id INTEGER
        )
    """)

    cursor.execute(
        'PRAGMA table_info(roast_history)'
    )

    existing_columns = {
        row['name']
        for row in cursor.fetchall()
    }

    migrations = [
        (
            'build_id',
            'ALTER TABLE roast_history '
            'ADD COLUMN build_id INTEGER DEFAULT 46'
        ),
        (
            'guild_id',
            'ALTER TABLE roast_history '
            'ADD COLUMN guild_id INTEGER'
        ),
        (
            'target_name',
            'ALTER TABLE roast_history '
            'ADD COLUMN target_name TEXT'
        ),
        (
            'target_id',
            'ALTER TABLE roast_history '
            'ADD COLUMN target_id INTEGER'
        ),
        (
            'roast',
            'ALTER TABLE roast_history '
            'ADD COLUMN roast TEXT'
        ),
    ]

    for column_name, sql in migrations:

        if column_name not in existing_columns:

            try:
                cursor.execute(sql)

            except sqlite3.OperationalError:
                pass

    cursor.execute(
        'PRAGMA table_info(guild_settings)'
    )

    existing_settings = {
        row['name']
        for row in cursor.fetchall()
    }

    settings_migrations = [
        (
            'roast_channel_id',
            'ALTER TABLE guild_settings '
            'ADD COLUMN roast_channel_id INTEGER'
        ),
        (
            'interval_minutes',
            'ALTER TABLE guild_settings '
            'ADD COLUMN interval_minutes INTEGER DEFAULT 10'
        ),
        (
            'roast_chance',
            'ALTER TABLE guild_settings '
            'ADD COLUMN roast_chance INTEGER DEFAULT 100'
        ),
        (
            'user_cooldown_minutes',
            'ALTER TABLE guild_settings '
            'ADD COLUMN user_cooldown_minutes INTEGER DEFAULT 30'
        ),
        (
            'bully_enabled',
            'ALTER TABLE guild_settings '
            'ADD COLUMN bully_enabled INTEGER DEFAULT 1'
        ),
        (
            'next_roast_at',
            'ALTER TABLE guild_settings '
            'ADD COLUMN next_roast_at TEXT'
        ),
        (
            'last_auto_target_id',
            'ALTER TABLE guild_settings '
            'ADD COLUMN last_auto_target_id INTEGER'
        ),
    ]

    for column_name, sql in settings_migrations:

        if column_name not in existing_settings:

            try:
                cursor.execute(sql)

            except sqlite3.OperationalError:
                pass

    try:
        cursor.execute("""
            UPDATE roast_history
            SET roast = roast_text
            WHERE roast IS NULL
              AND roast_text IS NOT NULL
        """)

    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("""
            UPDATE roast_history
            SET target_id = user_id
            WHERE target_id IS NULL
              AND user_id IS NOT NULL
        """)

    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("""
            UPDATE roast_history
            SET target_name = 'Unknown'
            WHERE target_name IS NULL
        """)

    except sqlite3.OperationalError:
        pass

    conn.commit()

    conn.close()


def ensure_guild_settings(
    guild_id
):
    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO guild_settings (
            guild_id,
            interval_minutes,
            roast_chance,
            user_cooldown_minutes,
            bully_enabled
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        guild_id,
        DEFAULT_INTERVAL_MINUTES,
        DEFAULT_ROAST_CHANCE,
        DEFAULT_COOLDOWN_MINUTES,
        1
    ))

    conn.commit()

    conn.close()


def get_guild_settings(
    guild_id
):
    ensure_guild_settings(
        guild_id
    )

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM guild_settings
        WHERE guild_id = ?
    """, (
        guild_id,
    ))

    row = cursor.fetchone()

    conn.close()

    return row


def update_setting(
    guild_id,
    field,
    value
):
    allowed_fields = {
        'roast_channel_id',
        'interval_minutes',
        'roast_chance',
        'user_cooldown_minutes',
        'bully_enabled',
        'next_roast_at',
        'last_auto_target_id',
    }

    if field not in allowed_fields:
        raise ValueError(
            'Invalid setting.'
        )

    ensure_guild_settings(
        guild_id
    )

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(
        f"""
        UPDATE guild_settings
        SET {field} = ?
        WHERE guild_id = ?
        """,
        (
            value,
            guild_id
        )
    )

    conn.commit()

    conn.close()


def save_roast(
    guild_id,
    user_id,
    target_name,
    roast_text
):
    conn = get_db()

    cursor = conn.cursor()

    now = datetime.now(
        timezone.utc
    ).isoformat()

    cursor.execute("""
        INSERT INTO roast_history (
            build_id,
            guild_id,
            user_id,
            roast_text,
            created_at,
            target_name,
            target_id,
            roast
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        46,
        guild_id,
        user_id,
        roast_text,
        now,
        target_name,
        user_id,
        roast_text
    ))

    conn.commit()

    conn.close()


def get_recent_roasts(
    guild_id,
    limit=20
):
    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT target_name, roast
        FROM roast_history
        WHERE guild_id = ?
        ORDER BY id DESC
        LIMIT ?
    """, (
        guild_id,
        limit
    ))

    rows = cursor.fetchall()

    conn.close()

    return [
        {
            'target_name': row['target_name'],
            'roast': row['roast']
        }
        for row in rows
    ]


def user_on_cooldown(
    guild_id,
    user_id,
    cooldown_minutes
):
    conn = get_db()

    cursor = conn.cursor()

    cutoff = (
        datetime.now(
            timezone.utc
        )
        - timedelta(
            minutes=cooldown_minutes
        )
    ).isoformat()

    cursor.execute("""
        SELECT id
        FROM roast_history
        WHERE guild_id = ?
          AND user_id = ?
          AND created_at >= ?
        ORDER BY id DESC
        LIMIT 1
    """, (
        guild_id,
        user_id,
        cutoff
    ))

    row = cursor.fetchone()

    conn.close()

    return row is not None


def clean_roast_output(
    text,
    target_name
):
    if not text:
        return None

    text = text.strip()

    text = text.replace(
        '```',
        ''
    )

    prefixes = [
        'Roast:',
        'ROAST:',
        'Here is your roast:',
        "Here's your roast:",
        'Sure!',
        'Sure,',
    ]

    for prefix in prefixes:

        if text.lower().startswith(
            prefix.lower()
        ):
            text = text[
                len(prefix):
            ].strip()

    text = re.sub(
        r'<@!?\d+>',
        '',
        text
    )

    text = re.sub(
        r'\s+',
        ' ',
        text
    ).strip()

    if len(text) >= 2:

        if (
            (
                text.startswith('"')
                and text.endswith('"')
            )
            or
            (
                text.startswith("'")
                and text.endswith("'")
            )
        ):
            text = text[
                1:-1
            ].strip()

    text = text.replace(
        '[NAME]',
        target_name
    )

    text = text.replace(
        '{name}',
        target_name
    )

    if not text:
        return None

    return text


def roast_word_count(
    text
):
    return len(
        re.findall(
            r"\b[\w’'-]+\b",
            text
        )
    )


def roast_has_multiple_sentences(
    text
):
    sentence_endings = re.findall(
        r'[.!?]+(?:\s|$)',
        text
    )

    return len(
        sentence_endings
    ) > 1


def roast_is_short_and_snappy(
    text
):
    if not text:
        return False

    if roast_word_count(
        text
    ) > 20:
        return False

    if roast_has_multiple_sentences(
        text
    ):
        return False

    return True


def generate_gemini_roast(
    target_name,
    recent_roasts=None
):
    recent_roasts = (
        recent_roasts
        or []
    )

    history_text = ''

    if recent_roasts:

        history_text = """
RECENT ROASTS:
These are previous jokes. DO NOT repeat them or closely imitate
their wording, metaphor, punchline, or structure.

"""

        for item in recent_roasts[:20]:

            previous = item.get(
                'roast'
            )

            if previous:

                history_text += (
                    f'- {previous}\n'
                )

    prompt = f"""
TARGET:
{target_name}

Write ONE savage roast about this person.

Make it feel spontaneous and original.

Use profanity when it makes the joke better.

Make the punchline hit hard.

Keep it SHORT AND SNAPPY:
Aim for 8-16 words.
NEVER exceed 20 words.

Write EXACTLY ONE sentence.
Use one setup and one punchline.
Stop immediately after the punchline.

Do not write an introduction.
Do not explain the joke.
Do not give multiple options.
Do not use a Discord mention.
Do not use quotation marks.

{history_text}
"""

    last_error = None

    for attempt in range(3):

        try:

            response = (
                gemini_client
                .models
                .generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=ROAST_SYSTEM_PROMPT,
                        temperature=1.15,
                        max_output_tokens=60,
                    ),
                )
            )

            text = getattr(
                response,
                'text',
                None
            )

            cleaned = clean_roast_output(
                text,
                target_name
            )

            if cleaned:

                if roast_is_short_and_snappy(
                    cleaned
                ):
                    return cleaned

                last_error = (
                    'Generated roast was too long '
                    'or used more than one sentence.'
                )

                continue

        except Exception as exc:

            last_error = exc

            error_text = str(
                exc
            ).upper()

            if (
                '503' in error_text
                or 'UNAVAILABLE' in error_text
                or '429' in error_text
                or 'RESOURCE_EXHAUSTED' in error_text
            ):
                time.sleep(
                    2
                    + attempt * 2
                )

                continue

            break

    print(
        f'Gemini roast generation failed: '
        f'{last_error}'
    )

    fallback = random.choice(
        FALLBACK_ROASTS
    )

    return fallback.format(
        name=target_name
    )


async def generate_roast(
    target_name,
    guild_id
):
    recent_roasts = get_recent_roasts(
        guild_id
    )

    roast = await asyncio.to_thread(
        generate_gemini_roast,
        target_name,
        recent_roasts
    )

    return roast


intents = discord.Intents.default()

intents.members = True

intents.message_content = True


bot = commands.Bot(
    command_prefix='!',
    intents=intents,
    help_command=None
)


NUKEM_YELLOW = discord.Color.from_rgb(
    255,
    204,
    0
)


def manual_roast_embed(
    member,
    roast
):
    embed = discord.Embed(
        title='☢️ ROASTBOT ☢️',
        description=(
            f'{member.mention}, '
            f'{roast}'
        ),
        color=NUKEM_YELLOW
    )

    embed.set_footer(
        text='NukemLabs • We regret nothing.'
    )

    return embed


def automatic_roast_embed(
    member,
    roast
):
    embed = discord.Embed(
        title='☢️ TARGET ACQUIRED ☢️',
        description=(
            f'{member.mention}, '
            f'{roast}'
        ),
        color=NUKEM_YELLOW
    )

    embed.set_footer(
        text='NukemLabs • We regret nothing.'
    )

    return embed


async def build_roast_card(
    member_name,
    roast
):
    return await asyncio.to_thread(
        create_roast_card,
        member_name,
        roast
    )


def cleanup_generated_card(
    card_path
):
    if not card_path:
        return

    try:

        path = Path(
            card_path
        )

        if path.exists():
            path.unlink()

    except Exception as exc:

        print(
            f'Could not remove temporary roast card: '
            f'{exc}'
        )


async def send_roast_card_interaction(
    interaction,
    member,
    roast
):
    card_path = None

    discord_file = None

    try:

        card_path = await build_roast_card(
            member.display_name,
            roast
        )

        discord_file = discord.File(
            str(card_path),
            filename='nukem_roast.png'
        )

        await interaction.followup.send(
            file=discord_file
        )

    except Exception as exc:

        print(
            f'Animated roast card error: '
            f'{exc}'
        )

        embed = manual_roast_embed(
            member,
            roast
        )

        await interaction.followup.send(
            embed=embed,
            allowed_mentions=discord.AllowedMentions(
                users=True
            )
        )

    finally:

        if discord_file:

            try:
                discord_file.close()

            except Exception:
                pass

        cleanup_generated_card(
            card_path
        )


async def send_roast_card_ctx(
    ctx,
    member,
    roast
):
    card_path = None

    discord_file = None

    try:

        card_path = await build_roast_card(
            member.display_name,
            roast
        )

        discord_file = discord.File(
            str(card_path),
            filename='nukem_roast.png'
        )

        await ctx.send(
            file=discord_file
        )

    except Exception as exc:

        print(
            f'Animated prefix roast card error: '
            f'{exc}'
        )

        embed = manual_roast_embed(
            member,
            roast
        )

        await ctx.send(
            embed=embed,
            allowed_mentions=discord.AllowedMentions(
                users=True
            )
        )

    finally:

        if discord_file:

            try:
                discord_file.close()

            except Exception:
                pass

        cleanup_generated_card(
            card_path
        )


async def send_roast_card_channel(
    channel,
    member,
    roast
):
    card_path = None

    discord_file = None

    try:

        card_path = await build_roast_card(
            member.display_name,
            roast
        )

        discord_file = discord.File(
            str(card_path),
            filename='nukem_roast.png'
        )

        await channel.send(
            file=discord_file
        )

    except Exception as exc:

        print(
            f'Animated automatic roast card error: '
            f'{exc}'
        )

        embed = automatic_roast_embed(
            member,
            roast
        )

        await channel.send(
            embed=embed,
            allowed_mentions=discord.AllowedMentions(
                users=True
            )
        )

    finally:

        if discord_file:

            try:
                discord_file.close()

            except Exception:
                pass

        cleanup_generated_card(
            card_path
        )


def build_setup_embed(
    setup_view,
    complete=False
):
    channel_text = (
        f'<#{setup_view.channel_id}>'
        if setup_view.channel_id
        else 'Not configured'
    )

    auto_text = (
        '☢️ ON'
        if setup_view.bully_enabled
        else '😇 OFF'
    )

    if complete:

        title = (
            '☢️ NUKEM ROASTBOT SETUP COMPLETE'
        )

        description = (
            'Configuration saved. '
            'This server is ready for controlled destruction.'
        )

    else:

        title = (
            '☢️ NUKEM ROASTBOT SETUP'
        )

        description = (
            'Configure automatic roasting for this server.\n\n'
            'Use the menus below, then press **Finish Setup**.\n'
            'Nothing is saved until you finish.'
        )

    embed = discord.Embed(
        title=title,
        description=description,
        color=NUKEM_YELLOW
    )

    embed.add_field(
        name='Roast Channel',
        value=channel_text,
        inline=False
    )

    embed.add_field(
        name='Auto Roast',
        value=auto_text,
        inline=True
    )

    embed.add_field(
        name='Interval',
        value=(
            f'{setup_view.interval_minutes} minutes'
        ),
        inline=True
    )

    embed.add_field(
        name='Roast Chance',
        value=(
            f'{setup_view.roast_chance}%'
        ),
        inline=True
    )

    embed.add_field(
        name='User Cooldown',
        value=(
            f'{setup_view.user_cooldown_minutes} minutes'
        ),
        inline=True
    )

    if complete:

        if setup_view.bully_enabled:

            embed.add_field(
                name='Status',
                value=(
                    'Automatic roasting is armed. '
                    'The first attempt will happen after '
                    f'{setup_view.interval_minutes} minutes.'
                ),
                inline=False
            )

        else:

            embed.add_field(
                name='Status',
                value=(
                    'Automatic roasting is disabled. '
                    'Manual `/roast` and `/roastme` commands '
                    'still work.'
                ),
                inline=False
            )

        embed.set_footer(
            text=(
                f'NukemLabs • Setup saved • v{VERSION}'
            )
        )

    else:

        embed.set_footer(
            text=(
                'Only the admin who opened setup '
                'can use these controls.'
            )
        )

    return embed


class SetupChannelSelect(
    discord.ui.ChannelSelect
):

    def __init__(
        self
    ):
        super().__init__(
            placeholder=(
                '1. Choose the automatic roast channel'
            ),
            channel_types=[
                discord.ChannelType.text
            ],
            min_values=1,
            max_values=1,
            row=0
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        setup_view = self.view

        if not isinstance(
            setup_view,
            SetupView
        ):
            return

        selected_channel = self.values[0]

        setup_view.channel_id = (
            selected_channel.id
        )

        await interaction.response.edit_message(
            embed=build_setup_embed(
                setup_view
            ),
            view=setup_view
        )


class SetupIntervalSelect(
    discord.ui.Select
):

    def __init__(
        self,
        current_interval
    ):
        interval_choices = [
            5,
            10,
            15,
            30,
            60,
            120,
            240,
            360,
            720,
            1440
        ]

        if current_interval not in interval_choices:

            interval_choices.append(
                current_interval
            )

            interval_choices.sort()

        options = []

        for minutes in interval_choices:

            if minutes < 60:

                label = (
                    f'{minutes} minutes'
                )

            elif minutes == 60:

                label = '1 hour'

            elif minutes % 60 == 0:

                label = (
                    f'{minutes // 60} hours'
                )

            else:

                label = (
                    f'{minutes} minutes'
                )

            options.append(
                discord.SelectOption(
                    label=label,
                    value=str(minutes),
                    default=(
                        minutes
                        == current_interval
                    )
                )
            )

        super().__init__(
            placeholder=(
                '2. Choose automatic roast interval'
            ),
            options=options,
            min_values=1,
            max_values=1,
            row=1
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        setup_view = self.view

        if not isinstance(
            setup_view,
            SetupView
        ):
            return

        setup_view.interval_minutes = int(
            self.values[0]
        )

        for option in self.options:

            option.default = (
                option.value
                == self.values[0]
            )

        await interaction.response.edit_message(
            embed=build_setup_embed(
                setup_view
            ),
            view=setup_view
        )


class SetupChanceSelect(
    discord.ui.Select
):

    def __init__(
        self,
        current_chance
    ):
        chance_choices = [
            0,
            25,
            50,
            75,
            100
        ]

        if current_chance not in chance_choices:

            chance_choices.append(
                current_chance
            )

            chance_choices.sort()

        options = []

        for chance in chance_choices:

            if chance == 0:

                description = (
                    'Never fires automatically'
                )

            elif chance == 100:

                description = (
                    'Fires every scheduled attempt'
                )

            else:

                description = (
                    f'{chance}% chance each '
                    f'scheduled attempt'
                )

            options.append(
                discord.SelectOption(
                    label=f'{chance}%',
                    value=str(chance),
                    description=description,
                    default=(
                        chance
                        == current_chance
                    )
                )
            )

        super().__init__(
            placeholder=(
                '3. Choose automatic roast chance'
            ),
            options=options,
            min_values=1,
            max_values=1,
            row=2
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        setup_view = self.view

        if not isinstance(
            setup_view,
            SetupView
        ):
            return

        setup_view.roast_chance = int(
            self.values[0]
        )

        for option in self.options:

            option.default = (
                option.value
                == self.values[0]
            )

        await interaction.response.edit_message(
            embed=build_setup_embed(
                setup_view
            ),
            view=setup_view
        )


class SetupAutoRoastButton(
    discord.ui.Button
):

    def __init__(
        self,
        enabled
    ):
        super().__init__(
            label=(
                'Auto Roast: ON'
                if enabled
                else 'Auto Roast: OFF'
            ),
            style=(
                discord.ButtonStyle.danger
                if enabled
                else discord.ButtonStyle.secondary
            ),
            row=3
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        setup_view = self.view

        if not isinstance(
            setup_view,
            SetupView
        ):
            return

        setup_view.bully_enabled = (
            not setup_view.bully_enabled
        )

        self.label = (
            'Auto Roast: ON'
            if setup_view.bully_enabled
            else 'Auto Roast: OFF'
        )

        self.style = (
            discord.ButtonStyle.danger
            if setup_view.bully_enabled
            else discord.ButtonStyle.secondary
        )

        await interaction.response.edit_message(
            embed=build_setup_embed(
                setup_view
            ),
            view=setup_view
        )


class SetupFinishButton(
    discord.ui.Button
):

    def __init__(
        self
    ):
        super().__init__(
            label='Finish Setup',
            style=discord.ButtonStyle.success,
            row=3
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        setup_view = self.view

        if not isinstance(
            setup_view,
            SetupView
        ):
            return

        if not setup_view.channel_id:

            await interaction.response.send_message(
                '☠️ Pick a roast channel before '
                'finishing setup.',
                ephemeral=True
            )

            return

        channel = setup_view.guild.get_channel(
            setup_view.channel_id
        )

        if not isinstance(
            channel,
            discord.TextChannel
        ):

            await interaction.response.send_message(
                '☠️ That roast channel no longer exists. '
                'Pick another one.',
                ephemeral=True
            )

            return

        bot_member = setup_view.guild.me

        if bot_member:

            permissions = channel.permissions_for(
                bot_member
            )

            missing_permissions = []

            if not permissions.view_channel:

                missing_permissions.append(
                    'View Channel'
                )

            if not permissions.send_messages:

                missing_permissions.append(
                    'Send Messages'
                )

            if not permissions.attach_files:

                missing_permissions.append(
                    'Attach Files'
                )

            if not permissions.read_message_history:

                missing_permissions.append(
                    'Read Message History'
                )

            if missing_permissions:

                missing_text = ', '.join(
                    missing_permissions
                )

                await interaction.response.send_message(
                    "☠️ I can't use that channel yet. "
                    'I need these permissions there: '
                    f'**{missing_text}**.',
                    ephemeral=True
                )

                return

        guild_id = setup_view.guild.id

        update_setting(
            guild_id,
            'roast_channel_id',
            setup_view.channel_id
        )

        update_setting(
            guild_id,
            'interval_minutes',
            setup_view.interval_minutes
        )

        update_setting(
            guild_id,
            'roast_chance',
            setup_view.roast_chance
        )

        update_setting(
            guild_id,
            'bully_enabled',
            (
                1
                if setup_view.bully_enabled
                else 0
            )
        )

        if setup_view.bully_enabled:

            next_time = (
                datetime.now(
                    timezone.utc
                )
                + timedelta(
                    minutes=(
                        setup_view.interval_minutes
                    )
                )
            )

            update_setting(
                guild_id,
                'next_roast_at',
                next_time.isoformat()
            )

        else:

            update_setting(
                guild_id,
                'next_roast_at',
                None
            )

        for child in setup_view.children:

            child.disabled = True

        setup_view.stop()

        await interaction.response.edit_message(
            embed=build_setup_embed(
                setup_view,
                complete=True
            ),
            view=setup_view
        )


class SetupView(
    discord.ui.View
):

    def __init__(
        self,
        guild,
        owner_id
    ):
        super().__init__(
            timeout=900
        )

        self.guild = guild

        self.owner_id = owner_id

        self.message = None

        settings = get_guild_settings(
            guild.id
        )

        self.channel_id = (
            int(
                settings[
                    'roast_channel_id'
                ]
            )
            if settings[
                'roast_channel_id'
            ]
            else None
        )

        self.interval_minutes = int(
            settings[
                'interval_minutes'
            ]
        )

        self.roast_chance = int(
            settings[
                'roast_chance'
            ]
        )

        self.user_cooldown_minutes = int(
            settings[
                'user_cooldown_minutes'
            ]
        )

        self.bully_enabled = (
            bool(
                settings[
                    'bully_enabled'
                ]
            )
            if self.channel_id
            else False
        )

        self.add_item(
            SetupChannelSelect()
        )

        self.add_item(
            SetupIntervalSelect(
                self.interval_minutes
            )
        )

        self.add_item(
            SetupChanceSelect(
                self.roast_chance
            )
        )

        self.add_item(
            SetupAutoRoastButton(
                self.bully_enabled
            )
        )

        self.add_item(
            SetupFinishButton()
        )

    async def interaction_check(
        self,
        interaction: discord.Interaction
    ):

        if (
            interaction.user.id
            != self.owner_id
        ):

            await interaction.response.send_message(
                '☠️ This setup panel belongs to the '
                'admin who opened it. Run `/setup` '
                'to open your own.',
                ephemeral=True
            )

            return False

        return True

    async def on_timeout(
        self
    ):

        for child in self.children:

            child.disabled = True

        if self.message:

            try:

                await self.message.edit(
                    view=self
                )

            except Exception:
                pass


@tasks.loop(
    minutes=1
)
async def automatic_bully_loop():

    now = datetime.now(
        timezone.utc
    )

    for guild in bot.guilds:

        try:

            settings = get_guild_settings(
                guild.id
            )

            if not settings:
                continue

            if not settings[
                'bully_enabled'
            ]:
                continue

            channel_id = settings[
                'roast_channel_id'
            ]

            if not channel_id:
                continue

            next_roast_at = settings[
                'next_roast_at'
            ]

            if next_roast_at:

                try:

                    next_time = (
                        datetime.fromisoformat(
                            next_roast_at
                        )
                    )

                    if next_time.tzinfo is None:

                        next_time = (
                            next_time.replace(
                                tzinfo=timezone.utc
                            )
                        )

                    if now < next_time:
                        continue

                except Exception:
                    pass

            interval = max(
                1,
                int(
                    settings[
                        'interval_minutes'
                    ]
                )
            )

            chance = max(
                0,
                min(
                    100,
                    int(
                        settings[
                            'roast_chance'
                        ]
                    )
                )
            )

            next_time = (
                now
                + timedelta(
                    minutes=interval
                )
            )

            update_setting(
                guild.id,
                'next_roast_at',
                next_time.isoformat()
            )

            if (
                random.randint(
                    1,
                    100
                )
                > chance
            ):
                continue

            channel = guild.get_channel(
                channel_id
            )

            if not channel:
                continue

            cooldown = max(
                0,
                int(
                    settings[
                        'user_cooldown_minutes'
                    ]
                )
            )

            last_target_id = settings[
                'last_auto_target_id'
            ]

            candidates = []

            members = guild.members[:]

            random.shuffle(
                members
            )

            for member in members:

                if member.bot:
                    continue

                if member.id == last_target_id:
                    continue

                if user_on_cooldown(
                    guild.id,
                    member.id,
                    cooldown
                ):
                    continue

                candidates.append(
                    member
                )

            if not candidates:

                for member in members:

                    if member.bot:
                        continue

                    if user_on_cooldown(
                        guild.id,
                        member.id,
                        cooldown
                    ):
                        continue

                    candidates.append(
                        member
                    )

            if not candidates:
                continue

            target = random.choice(
                candidates
            )

            roast = await generate_roast(
                target.display_name,
                guild.id
            )

            save_roast(
                guild.id,
                target.id,
                target.display_name,
                roast
            )

            update_setting(
                guild.id,
                'last_auto_target_id',
                target.id
            )

            await send_roast_card_channel(
                channel,
                target,
                roast
            )

            print(
                f'[AUTO ROAST] '
                f'{guild.name} -> '
                f'{target.display_name}: '
                f'{roast}'
            )

        except Exception as exc:

            print(
                f'[AUTO BULLY ERROR] '
                f'{guild.name}: '
                f'{exc}'
            )


@automatic_bully_loop.before_loop
async def before_automatic_bully_loop():

    await bot.wait_until_ready()


@bot.event
async def on_ready():

    print()

    print(
        '=' * 60
    )

    print(
        f'NUKEM ROASTBOT {VERSION}'
    )

    print(
        'SHORT & SAVAGE EDITION'
    )

    print(
        '=' * 60
    )

    print(
        f'Logged in as: '
        f'{bot.user}'
    )

    print(
        f'Connected to '
        f'{len(bot.guilds)} '
        f'server(s)'
    )

    print(
        f'Database: '
        f'{os.path.abspath(DATABASE_FILE)}'
    )

    print(
        f'Gemini model: '
        f'{GEMINI_MODEL}'
    )

    print(
        f'Default bully interval: '
        f'{DEFAULT_INTERVAL_MINUTES} '
        f'minutes'
    )

    print(
        f'Default roast chance: '
        f'{DEFAULT_ROAST_CHANCE}%'
    )

    print(
        f'Default user cooldown: '
        f'{DEFAULT_COOLDOWN_MINUTES} '
        f'minutes'
    )

    try:

        for guild in bot.guilds:

            bot.tree.copy_global_to(
                guild=guild
            )

            synced = await bot.tree.sync(
                guild=guild
            )

            print(
                f'Slash commands synced to '
                f'{guild.name}: '
                f'{len(synced)} commands'
            )

    except Exception as exc:

        print(
            f'Slash command sync failed: '
            f'{exc}'
        )

    if not automatic_bully_loop.is_running():

        automatic_bully_loop.start()

    print(
        'Automatic server bully: ONLINE'
    )

    print(
        'Animated roast cards: ONLINE'
    )

    print(
        '=' * 60
    )

    print()


@bot.event
async def on_command_error(
    ctx,
    error
):

    if isinstance(
        error,
        commands.CommandNotFound
    ):
        return

    if isinstance(
        error,
        commands.MissingPermissions
    ):

        await ctx.send(
            "☠️ You don't have permission "
            'to fuck with that setting.',
            delete_after=8
        )

        return

    if isinstance(
        error,
        commands.MissingRequiredArgument
    ):

        await ctx.send(
            "☠️ You're missing an argument, genius.",
            delete_after=8
        )

        return

    print(
        f'Command error: '
        f'{error}'
    )


@bot.tree.command(
    name='setup',
    description=(
        'Configure Nukem RoastBot for this server.'
    )
)
@app_commands.guild_only()
@app_commands.default_permissions(
    manage_guild=True
)
async def slash_setup(
    interaction: discord.Interaction
):

    if not interaction.guild:

        await interaction.response.send_message(
            '☠️ `/setup` only works inside a server.',
            ephemeral=True
        )

        return

    member = interaction.user

    if not isinstance(
        member,
        discord.Member
    ):

        await interaction.response.send_message(
            "☠️ I couldn't verify your "
            'server permissions.',
            ephemeral=True
        )

        return

    if not member.guild_permissions.manage_guild:

        await interaction.response.send_message(
            '☠️ You need **Manage Server** permission '
            'to run setup.',
            ephemeral=True
        )

        return

    setup_view = SetupView(
        interaction.guild,
        interaction.user.id
    )

    await interaction.response.send_message(
        embed=build_setup_embed(
            setup_view
        ),
        view=setup_view,
        ephemeral=True
    )

    try:

        setup_view.message = (
            await interaction.original_response()
        )

    except Exception:

        setup_view.message = None


@bot.tree.command(
    name='roast',
    description='Roast a specific member.'
)
@app_commands.describe(
    member=(
        'The unfortunate bastard '
        'you want roasted.'
    )
)
async def slash_roast(
    interaction: discord.Interaction,
    member: discord.Member
):

    if member.bot:

        await interaction.response.send_message(
            "☠️ I'm not wasting a perfectly "
            'good roast on a bot.',
            ephemeral=True
        )

        return

    await interaction.response.defer()

    try:

        roast = await generate_roast(
            member.display_name,
            interaction.guild.id
        )

        save_roast(
            interaction.guild.id,
            member.id,
            member.display_name,
            roast
        )

        await send_roast_card_interaction(
            interaction,
            member,
            roast
        )

    except Exception as exc:

        print(
            f'/roast error: '
            f'{exc}'
        )

        await interaction.followup.send(
            '☠️ The roast machine caught fire. '
            'Try again.',
            ephemeral=True
        )


@bot.tree.command(
    name='roastme',
    description=(
        'Volunteer yourself for psychological damage.'
    )
)
async def slash_roastme(
    interaction: discord.Interaction
):

    await interaction.response.defer()

    member = interaction.user

    try:

        roast = await generate_roast(
            member.display_name,
            interaction.guild.id
        )

        save_roast(
            interaction.guild.id,
            member.id,
            member.display_name,
            roast
        )

        await send_roast_card_interaction(
            interaction,
            member,
            roast
        )

    except Exception as exc:

        print(
            f'/roastme error: '
            f'{exc}'
        )

        await interaction.followup.send(
            '☠️ The roast machine exploded. '
            'Congratulations.',
            ephemeral=True
        )


@bot.tree.command(
    name='roastchannel',
    description=(
        'Set the channel where automatic roasts happen.'
    )
)
@app_commands.describe(
    channel=(
        'The channel where the bot should unleash hell.'
    )
)
@app_commands.checks.has_permissions(
    manage_guild=True
)
async def slash_roastchannel(
    interaction: discord.Interaction,
    channel: discord.TextChannel
):

    update_setting(
        interaction.guild.id,
        'roast_channel_id',
        channel.id
    )

    await interaction.response.send_message(
        f'☠️ Roast channel set to '
        f'{channel.mention}. '
        f"Someone's having a terrible "
        f'fucking day soon.'
    )


@bot.tree.command(
    name='roastinterval',
    description=(
        'Set how often the automatic bully strikes.'
    )
)
@app_commands.describe(
    minutes=(
        'Minutes between automatic roast attempts.'
    )
)
@app_commands.checks.has_permissions(
    manage_guild=True
)
async def slash_roastinterval(
    interaction: discord.Interaction,
    minutes: app_commands.Range[
        int,
        1,
        1440
    ]
):

    update_setting(
        interaction.guild.id,
        'interval_minutes',
        minutes
    )

    next_time = (
        datetime.now(
            timezone.utc
        )
        + timedelta(
            minutes=minutes
        )
    )

    update_setting(
        interaction.guild.id,
        'next_roast_at',
        next_time.isoformat()
    )

    await interaction.response.send_message(
        f'☠️ Automatic bullying interval set to '
        f'**{minutes} minute(s)**.'
    )


@bot.tree.command(
    name='roastchance',
    description=(
        'Set the percentage chance of a roast firing.'
    )
)
@app_commands.describe(
    chance=(
        'Chance from 0 to 100 percent.'
    )
)
@app_commands.checks.has_permissions(
    manage_guild=True
)
async def slash_roastchance(
    interaction: discord.Interaction,
    chance: app_commands.Range[
        int,
        0,
        100
    ]
):

    update_setting(
        interaction.guild.id,
        'roast_chance',
        chance
    )

    await interaction.response.send_message(
        f'☠️ Roast chance set to '
        f'**{chance}%**.'
    )


@bot.tree.command(
    name='roastbully',
    description=(
        'Turn automatic server bullying on or off.'
    )
)
@app_commands.describe(
    enabled=(
        'Whether automatic bullying should be enabled.'
    )
)
@app_commands.checks.has_permissions(
    manage_guild=True
)
async def slash_roastbully(
    interaction: discord.Interaction,
    enabled: bool
):

    update_setting(
        interaction.guild.id,
        'bully_enabled',
        (
            1
            if enabled
            else 0
        )
    )

    if enabled:

        settings = get_guild_settings(
            interaction.guild.id
        )

        interval = int(
            settings[
                'interval_minutes'
            ]
        )

        next_time = (
            datetime.now(
                timezone.utc
            )
            + timedelta(
                minutes=interval
            )
        )

        update_setting(
            interaction.guild.id,
            'next_roast_at',
            next_time.isoformat()
        )

        message = (
            '☢️ **SERVER BULLY: ONLINE**\n'
            'NukemLabs has resumed its bullshit.'
        )

    else:

        message = (
            '😇 **SERVER BULLY: OFFLINE**\n'
            'Enjoy the peace while it lasts.'
        )

    await interaction.response.send_message(
        message
    )


@bot.tree.command(
    name='roaststatus',
    description=(
        'Show the current RoastBot settings.'
    )
)
async def slash_roaststatus(
    interaction: discord.Interaction
):

    settings = get_guild_settings(
        interaction.guild.id
    )

    channel_id = settings[
        'roast_channel_id'
    ]

    if channel_id:

        channel = (
            interaction.guild.get_channel(
                channel_id
            )
        )

        channel_text = (
            channel.mention
            if channel
            else f'<#{channel_id}>'
        )

    else:

        channel_text = (
            'Not configured'
        )

    bully_status = (
        '☢️ ONLINE'
        if settings[
            'bully_enabled'
        ]
        else '😇 OFFLINE'
    )

    embed = discord.Embed(
        title='☢️ NUKEM ROASTBOT',
        description=(
            '**SERVER BULLY STATUS**'
        ),
        color=NUKEM_YELLOW
    )

    embed.add_field(
        name='Bully',
        value=bully_status,
        inline=True
    )

    embed.add_field(
        name='Interval',
        value=(
            f"{settings['interval_minutes']} minutes"
        ),
        inline=True
    )

    embed.add_field(
        name='Chance',
        value=(
            f"{settings['roast_chance']}%"
        ),
        inline=True
    )

    embed.add_field(
        name='User Cooldown',
        value=(
            f"{settings['user_cooldown_minutes']} minutes"
        ),
        inline=True
    )

    embed.add_field(
        name='Roast Channel',
        value=channel_text,
        inline=True
    )

    embed.add_field(
        name='Model',
        value=GEMINI_MODEL,
        inline=True
    )

    embed.set_footer(
        text=(
            f'NukemLabs • '
            f'We regret nothing. • '
            f'v{VERSION}'
        )
    )

    await interaction.response.send_message(
        embed=embed
    )


@bot.command(
    name='roast'
)
async def prefix_roast(
    ctx,
    member: discord.Member = None
):

    if member is None:

        await ctx.send(
            '☠️ Tag someone, genius. '
            '`!roast @person`',
            delete_after=8
        )

        return

    if member.bot:

        await ctx.send(
            "☠️ I'm not wasting a perfectly "
            'good roast on a bot.',
            delete_after=8
        )

        return

    try:

        roast = await generate_roast(
            member.display_name,
            ctx.guild.id
        )

        save_roast(
            ctx.guild.id,
            member.id,
            member.display_name,
            roast
        )

        await send_roast_card_ctx(
            ctx,
            member,
            roast
        )

    except Exception as exc:

        print(
            f'!roast error: '
            f'{exc}'
        )


@bot.command(
    name='roastme'
)
async def prefix_roastme(
    ctx
):

    member = ctx.author

    try:

        roast = await generate_roast(
            member.display_name,
            ctx.guild.id
        )

        save_roast(
            ctx.guild.id,
            member.id,
            member.display_name,
            roast
        )

        await send_roast_card_ctx(
            ctx,
            member,
            roast
        )

    except Exception as exc:

        print(
            f'!roastme error: '
            f'{exc}'
        )


@bot.command(
    name='roastchannel'
)
@commands.has_permissions(
    manage_guild=True
)
async def prefix_roastchannel(
    ctx,
    channel: discord.TextChannel = None
):

    if channel is None:

        channel = ctx.channel

    update_setting(
        ctx.guild.id,
        'roast_channel_id',
        channel.id
    )

    await ctx.send(
        f'☠️ Roast channel set to '
        f'{channel.mention}. '
        f"Someone's about to have a "
        f'fucking bad evening.'
    )


@bot.command(
    name='roastinterval'
)
@commands.has_permissions(
    manage_guild=True
)
async def prefix_roastinterval(
    ctx,
    minutes: int = None
):

    if minutes is None:

        await ctx.send(
            '☠️ Usage: '
            '`!roastinterval 10`',
            delete_after=8
        )

        return

    if (
        minutes < 1
        or minutes > 1440
    ):

        await ctx.send(
            '☠️ Pick something between '
            '1 and 1440 minutes.',
            delete_after=8
        )

        return

    update_setting(
        ctx.guild.id,
        'interval_minutes',
        minutes
    )

    next_time = (
        datetime.now(
            timezone.utc
        )
        + timedelta(
            minutes=minutes
        )
    )

    update_setting(
        ctx.guild.id,
        'next_roast_at',
        next_time.isoformat()
    )

    await ctx.send(
        f'☠️ Automatic bullying interval set to '
        f'**{minutes} minute(s)**.'
    )


@bot.command(
    name='roastchance'
)
@commands.has_permissions(
    manage_guild=True
)
async def prefix_roastchance(
    ctx,
    chance: int = None
):

    if chance is None:

        await ctx.send(
            '☠️ Usage: '
            '`!roastchance 100`',
            delete_after=8
        )

        return

    if (
        chance < 0
        or chance > 100
    ):

        await ctx.send(
            '☠️ Chance has to be between '
            '0 and 100.',
            delete_after=8
        )

        return

    update_setting(
        ctx.guild.id,
        'roast_chance',
        chance
    )

    await ctx.send(
        f'☠️ Roast chance set to '
        f'**{chance}%**.'
    )


@bot.command(
    name='roastbully'
)
@commands.has_permissions(
    manage_guild=True
)
async def prefix_roastbully(
    ctx,
    state: str = None
):

    if state is None:

        await ctx.send(
            '☠️ Usage: '
            '`!roastbully on` '
            'or `!roastbully off`',
            delete_after=8
        )

        return

    state = state.lower()

    if state not in (
        'on',
        'off'
    ):

        await ctx.send(
            '☠️ Use `on` or `off`.',
            delete_after=8
        )

        return

    enabled = (
        state == 'on'
    )

    update_setting(
        ctx.guild.id,
        'bully_enabled',
        (
            1
            if enabled
            else 0
        )
    )

    if enabled:

        settings = get_guild_settings(
            ctx.guild.id
        )

        interval = int(
            settings[
                'interval_minutes'
            ]
        )

        next_time = (
            datetime.now(
                timezone.utc
            )
            + timedelta(
                minutes=interval
            )
        )

        update_setting(
            ctx.guild.id,
            'next_roast_at',
            next_time.isoformat()
        )

        await ctx.send(
            '☢️ **SERVER BULLY: ONLINE**\n'
            'NukemLabs has resumed its bullshit.'
        )

    else:

        await ctx.send(
            '😇 **SERVER BULLY: OFFLINE**\n'
            'Enjoy the peace while it lasts.'
        )


@bot.command(
    name='roaststatus'
)
async def prefix_roaststatus(
    ctx
):

    settings = get_guild_settings(
        ctx.guild.id
    )

    channel_id = settings[
        'roast_channel_id'
    ]

    if channel_id:

        channel = ctx.guild.get_channel(
            channel_id
        )

        channel_text = (
            channel.mention
            if channel
            else f'<#{channel_id}>'
        )

    else:

        channel_text = (
            'Not configured'
        )

    bully_status = (
        '☢️ ONLINE'
        if settings[
            'bully_enabled'
        ]
        else '😇 OFFLINE'
    )

    embed = discord.Embed(
        title='☢️ NUKEM ROASTBOT',
        description=(
            '**SERVER BULLY STATUS**'
        ),
        color=NUKEM_YELLOW
    )

    embed.add_field(
        name='Bully',
        value=bully_status,
        inline=True
    )

    embed.add_field(
        name='Interval',
        value=(
            f"{settings['interval_minutes']} minutes"
        ),
        inline=True
    )

    embed.add_field(
        name='Chance',
        value=(
            f"{settings['roast_chance']}%"
        ),
        inline=True
    )

    embed.add_field(
        name='User Cooldown',
        value=(
            f"{settings['user_cooldown_minutes']} minutes"
        ),
        inline=True
    )

    embed.add_field(
        name='Roast Channel',
        value=channel_text,
        inline=True
    )

    embed.add_field(
        name='Model',
        value=GEMINI_MODEL,
        inline=True
    )

    embed.set_footer(
        text=(
            f'NukemLabs • '
            f'We regret nothing. • '
            f'v{VERSION}'
        )
    )

    await ctx.send(
        embed=embed
    )


if __name__ == '__main__':

    init_database()

    print()

    print(
        'Starting Nukem RoastBot 4.6.1...'
    )

    print()

    bot.run(
        DISCORD_TOKEN
    )