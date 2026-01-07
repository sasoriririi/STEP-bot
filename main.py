import os
import random
import datetime
import asyncio

import discord
from discord.ext import commands, tasks
import aiohttp

# =====================
# CONFIGURATION
# =====================

BOT_TOKEN = os.getenv("DISCORD_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN environment variable is not set. "
        "Add it to your deployment environment."
    )

DAILY_CHANNEL_ID = 123456789012345678  # replace with your channel ID

BASE_URL = (
    "https://github.com/sasoriririi/STEP-bot/blob/main/"
    "question_images/{X}-S{Y}-Q{Z}.png?raw=true"
)

TIMEZONE = datetime.timezone.utc  # change if needed

# =====================
# BOT SETUP
# =====================

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

http_session: aiohttp.ClientSession | None = None

# =====================
# STEP UTILITIES
# =====================

def valid_X_values():
    xs = ["Spec"]
    xs += [f"{i:02d}" for i in range(87, 100)]
    xs += [f"{i:02d}" for i in range(0, 19)]
    return xs

def format_label(X: str, Y: str, Z: int) -> str:
    if X == "Spec":
        year = "Specimen"
    else:
        n = int(X)
        year = f"20{X}" if n <= 18 else f"19{X}"

    return f"STEP {Y} {year}, Question {Z}"

async def image_exists(url: str) -> bool:
    try:
        async with http_session.head(
            url,
            timeout=aiohttp.ClientTimeout(total=5),
            allow_redirects=True
        ) as resp:
            return resp.status == 200
    except aiohttp.ClientError:
        return False

async def random_question(include_step1: bool = False):
    Y_choices = ["2", "3"] if not include_step1 else ["1", "2", "3"]

    for _ in range(50):  # bounded retries
        X = random.choice(valid_X_values())
        Y = random.choice(Y_choices)
        Z = random.randint(1, 16)

        url = BASE_URL.format(X=X, Y=Y, Z=Z)
        if await image_exists(url):
            return X, Y, Z, url

    raise RuntimeError("Unable to find a valid STEP question.")

# =====================
# COMMANDS
# =====================

@bot.command(name="step")
async def step(ctx, *, arg: str | None = None):
    if arg is None or arg.lower() == "help":
        await ctx.send(
            "**STEP Bot Commands**\n\n"
            "`!step XX-SY-QZ` — show a specific question\n"
            "`!step random` — random STEP 2 or 3 question\n"
            "`!step help` — show this message\n\n"
            "Examples:\n"
            "`!step 97-S2-Q1`\n"
            "`!step Spec-S1-Q4`\n\n"
        )
        return

    if arg.lower() == "random":
        try:
            X, Y, Z, url = await random_question(include_step1=False)
        except RuntimeError:
            await ctx.send("Failed to find a valid STEP question.")
            return

        await ctx.send(format_label(X, Y, Z))
        await ctx.send(url)
        return

    try:
        X, sY, qZ = arg.split("-")
        Y = sY[1:]
        Z = int(qZ[1:])
    except Exception:
        await ctx.send("Invalid format. Use `!step XX-SY-QZ`.")
        return

    if X not in valid_X_values() or Y not in {"1", "2", "3"} or not (1 <= Z <= 16):
        await ctx.send("Invalid STEP question reference.")
        return

    url = BASE_URL.format(X=X, Y=Y, Z=Z)
    if not await image_exists(url):
        await ctx.send("That STEP question could not be found.")
        return

    await ctx.send(format_label(X, Y, Z))
    await ctx.send(url)

# =====================
# DAILY QUESTION TASK
# =====================

@tasks.loop(time=datetime.time(hour=12, tzinfo=TIMEZONE))
async def daily_step():
    channel = bot.get_channel(DAILY_CHANNEL_ID)
    if channel is None:
        return

    try:
        X, Y, Z, url = await random_question(include_step1=False)
    except RuntimeError:
        return

    await channel.send(format_label(X, Y, Z))
    await channel.send(url)

# =====================
# LIFECYCLE EVENTS
# =====================

@bot.event
async def on_ready():
    global http_session
    if http_session is None:
        http_session = aiohttp.ClientSession()

    if not daily_step.is_running():
        daily_step.start()

    print(f"Logged in as {bot.user}")

@bot.event
async def on_disconnect():
    print("Bot disconnected.")

@bot.event
async def on_resumed():
    print("Bot resumed.")

@bot.event
async def close():
    if http_session:
        await http_session.close()

# =====================
# RUN
# =====================

bot.run(BOT_TOKEN)
