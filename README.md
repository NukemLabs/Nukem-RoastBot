# Nukem RoastBot

Nukem RoastBot is an AI-powered Discord roast bot designed for adult friend groups, gaming communities, and social servers.

The bot generates personalized AI-powered roasts and presents manual roast responses through custom NukemLabs-branded image cards rather than standard Discord embeds.

Developed by NukemLabs.

---

## Add Nukem RoastBot to Discord

Install Nukem RoastBot directly to your Discord server:

[Add Nukem RoastBot to Discord](https://discord.com/oauth2/authorize?client_id=1548537008085799012)

The installer requests only the permissions needed for normal operation:

- View Channels
- Send Messages
- Embed Links
- Attach Files
- Read Message History
- Create application commands

Administrator permission is not required.

---

## Features

- AI-generated roasts
- Custom high-resolution roast cards
- Manual member roasting
- Self-roasting
- Automatic server roasting
- Per-server configuration
- Adjustable automatic roast interval
- Adjustable roast probability
- Member roast cooldowns
- Persistent server settings
- Multi-server support
- Discord slash commands
- Traditional prefix commands
- Railway deployment support
- SQLite persistent storage
- Fallback roasts if the AI service is temporarily unavailable

---

## Commands

### Slash Commands

| Command | Description |
|---|---|
| `/roast @user` | Roast another server member |
| `/roastme` | Roast yourself |
| `/roastchannel` | Set the channel used for automatic roasts |
| `/roastinterval` | Change how often RoastBot checks for a target |
| `/roastchance` | Change the probability of an automatic roast |
| `/roastbully` | Enable or disable automatic roasting |
| `/roaststatus` | View the current server roast settings |

Traditional prefix-command equivalents are also supported.

---

## Automatic Roast Mode

Nukem RoastBot can automatically select members from a configured Discord server channel and roast them without requiring a manual command.

Each Discord server has its own configuration.

Default automatic roast settings:

```text
Roast interval:   10 minutes
Roast chance:     100%
Member cooldown:  30 minutes
```

Server settings are stored persistently so they survive bot restarts and production redeployments.

---

## Roast Style

Nukem RoastBot is designed to generate roasts that feel more like humor from a friend group than responses from a general-purpose utility bot.

The intended style is:

- Dark
- Profane
- Absurd
- Creative
- Personalized
- Unpredictable
- Concise enough for Discord

The bot is designed to avoid:

- Racist content
- Attacks based on protected characteristics
- Genuine threats
- Encouragement of self-harm
- Instructions for wrongdoing

---

## Custom Roast Cards

Manual roasts are rendered as custom NukemLabs roast cards.

The production card system includes:

- High-resolution PNG rendering
- Automatic text wrapping
- Automatic font sizing
- Protected text boundaries
- Railway-compatible font handling
- Lossless image output
- Custom NukemLabs industrial artwork

Longer roast text is automatically resized or trimmed when necessary so the text remains inside the designated card area.

---

## AI

Nukem RoastBot uses Google's Gemini API to generate roast responses.

The Gemini model and generation settings are configured inside `bot.py`.

If the AI service temporarily fails, the bot includes fallback roast responses so basic roasting functionality can continue.

---

## Technology

Nukem RoastBot is built with:

```text
Python
discord.py
Google Gemini
google-genai
Pillow
SQLite
python-dotenv
Railway
GitHub
```

---

## Project Structure

```text
Nukem-RoastBot/
│
├── bot.py
├── card_maker.py
├── requirements.txt
├── README.md
├── PRIVACY.md
├── TERMS.md
├── LICENSE
├── .env.example
├── .gitignore
│
├── assets/
│   └── roast_frame.png
│
└── generated_roasts/
```

### bot.py

Contains the main Discord bot logic, commands, automatic roasting system, Gemini integration, database management, and server configuration.

### card_maker.py

Generates the custom high-resolution roast card images used for manual roast responses.

### assets/roast_frame.png

Contains the primary Nukem RoastBot card artwork.

### generated_roasts/

Temporary output directory for generated roast card images.

This directory should not be committed to Git.

---

## Requirements

Python 3 is required.

Install project dependencies with:

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Nukem RoastBot requires two private credentials:

```env
DISCORD_TOKEN=your_discord_bot_token
GEMINI_API_KEY=your_gemini_api_key
```

For local development, place these values in a `.env` file.

Example:

```env
DISCORD_TOKEN=YOUR_DISCORD_BOT_TOKEN
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

Never commit a real `.env` file.

The repository includes `.env.example` as a safe configuration reference.

---

## Running Locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the bot:

```bash
python bot.py
```

Once connected, Nukem RoastBot will log into Discord and register its available commands.

---

## Discord Bot Setup

To run your own instance, create a Discord application and bot through the Discord Developer Portal.

Store the bot token as:

```text
DISCORD_TOKEN
```

Recommended installation scopes:

```text
applications.commands
bot
```

Recommended permissions:

```text
View Channels
Send Messages
Embed Links
Attach Files
Read Message History
```

Administrator permission is not required.

### Gateway Intents

The current bot configuration uses:

```text
Server Members Intent:  Enabled
Message Content Intent: Enabled
Presence Intent:        Disabled
```

Server Members Intent supports member-related features and automatic roasting.

Message Content Intent is used for traditional prefix commands.

---

## Railway Deployment

Nukem RoastBot is designed to run continuously on Railway.

### Required Variables

Add:

```text
DISCORD_TOKEN
GEMINI_API_KEY
```

to the Railway service variables.

Do not place private API credentials directly in source code.

---

## Persistent Storage

Nukem RoastBot uses SQLite for persistent server configuration.

For production use on Railway, attach a persistent volume so configuration survives deployments and restarts.

Persistent data can include:

- Selected automatic roast channel
- Automatic roasting enabled or disabled state
- Roast interval
- Roast probability
- Member cooldown information
- Server-specific configuration

---

## GitHub Deployment

The production Railway service can be connected directly to the GitHub repository.

Current production branch:

```text
master
```

Railway can automatically deploy changes pushed to the production branch.

If an automatic deployment does not trigger, open the Railway command palette:

```text
Ctrl + K
```

Then select:

```text
Deploy Latest Commit
```

---

## Running Multiple Bot Instances

Do not run the local bot and Railway production bot at the same time using the same Discord bot token.

Running multiple instances simultaneously can result in:

- Duplicate responses
- Discord interaction errors
- Competing automatic roast loops
- `Unknown interaction` errors

When testing locally, stop the production deployment first.

When the Railway production deployment is active, keep the local bot offline.

---

## Testing Changes

Before deploying changes to `bot.py`, run:

```bash
python -m py_compile bot.py
```

Before deploying changes to `card_maker.py`, run:

```bash
python -m py_compile card_maker.py
```

No output means the file passed the Python syntax check.

---

## Git Workflow

A typical update workflow is:

```bash
git status
git add <changed-files>
git commit -m "Describe the change"
git push
```

Avoid committing:

- `.env`
- Generated roast cards
- SQLite database files
- Python cache files
- Temporary development files

---

## Git Ignore

The repository should ignore generated and private files such as:

```text
.env
__pycache__/
*.pyc
*.db
generated_roasts/
```

---

## Security

Never publicly share:

- Discord bot tokens
- Gemini API keys
- `.env` contents
- Private deployment credentials

If a credential is accidentally exposed, rotate it immediately through the appropriate provider.

---

## Privacy

Nukem RoastBot processes only the information reasonably necessary to provide its Discord functionality, server configuration, AI-generated responses, and roast cards.

Full Privacy Policy:

[Privacy Policy](https://github.com/NukemLabs/Nukem-RoastBot/blob/master/PRIVACY.md)

---

## Terms of Service

Use of Nukem RoastBot is subject to the project's Terms of Service.

Full Terms:

[Terms of Service](https://github.com/NukemLabs/Nukem-RoastBot/blob/master/TERMS.md)

---

## Intended Use

Nukem RoastBot is intended for entertainment in communities where members understand and welcome roast-style humor.

Server owners are responsible for configuring and using the bot appropriately for their communities.

Automatic roasting should only be enabled in servers where this style of interaction is appropriate.

---

## Design Philosophy

Nukem RoastBot is built around several core ideas:

1. The roast should be entertaining before it is complicated.
2. The bot should have a recognizable personality and visual identity.
3. Server owners should control how frequently automatic roasting occurs.
4. Generated responses should feel varied rather than repetitive.
5. Visual presentation should feel like part of the product rather than an afterthought.
6. Manual roast commands should be simple and immediately understandable.

---

## NukemLabs

Nukem RoastBot is a NukemLabs project.

The project combines AI-generated humor, Discord automation, persistent server configuration, and custom visual presentation into a single bot designed for social communities.

---

## License

See the included `LICENSE` file for licensing information.