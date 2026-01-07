import os
import random
import requests
import datetime
import discord
from discord.ext import commands, tasks

# =====================
# CONFIGURATION
# =====================

BOT_TOKEN = os.environ["DISCORD_TOKEN"]
DAILY_CHANNEL_ID = 1329895128973709486

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

# =====================
# QUESTION UTILITIES
# =====================

def valid_X_values():
    xs = ["Spec"]
    xs += [f"{i:02d}" for i in range(87, 100)]
    xs += [f"{i:02d}" for i in range(0, 19)]
    return xs

def format_label(X, Y, Z):
    if X == "Spec":
        year = "Specimen"
    else:
        n = int(X)
        year = f"20{X}" if n <= 18 else f"19{X}"

    return f"STEP {Y} {year}, Question {Z}"

def image_exists(url):
    try:
        r = requests.head(url, timeout=5)
        return r.status_code == 200
    except requests.RequestException:
        return False

def random_question(include_step1=False):
    Y_choices = ["2", "3"] if not include_step1 else ["1", "2", "3"]

    while True:
        X = random.choice(valid_X_values())
        Y = random.choice(Y_choices)
        Z = random.randint(1, 16)

        url = BASE_URL.format(X=X, Y=Y, Z=Z)
        if image_exists(url):
            return X, Y, Z, url

# =====================
# COMMANDS
# =====================

@bot.command(name="step")
async def step(ctx, *, arg=None):
    if arg is None or arg.lower() == "help":
        await ctx.send(
            "**STEP Bot Commands**\n\n"
            "`!step XX-SY-QZ` — show a specific question\n"
            "`!step random` — show a random STEP 2 or 3 question\n"
            "`!step help` — show this message\n\n"
            "Examples:\n"
            "`!step 97-S2-Q1`\n"
            "`!step Spec-S1-Q4`"
        )
        return

    if arg.lower() == "random":
        X, Y, Z, url = random_question(include_step1=False)
        await ctx.send(format_label(X, Y, Z))
        await ctx.send(url)
        return

    try:
        part1, part2, part3 = arg.split("-")
        X = part1
        Y = part2[1:]
        Z = int(part3[1:])
    except Exception:
        await ctx.send("Invalid format. Use `!step XX-SY-QZ`.")
        return

    if X not in valid_X_values() or Y not in {"1", "2", "3"} or not (1 <= Z <= 16):
        await ctx.send("Invalid STEP question reference.")
        return

    url = BASE_URL.format(X=X, Y=Y, Z=Z)
    if not image_exists(url):
        await ctx.send("That STEP question could not be found.")
        return

    await ctx.send(format_label(X, Y, Z))
    await ctx.send(url)

# =====================
# DAILY TASK
# =====================

@tasks.loop(time=datetime.time(hour=12, tzinfo=TIMEZONE))
async def daily_step():
    channel = bot.get_channel(DAILY_CHANNEL_ID)
    if channel is None:
        return

    X, Y, Z, url = random_question(include_step1=False)
    await channel.send(format_label(X, Y, Z))
    await channel.send(url)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    if not daily_step.is_running():
        daily_step.start()

# =====================
# RUN
# =====================

bot.run(BOT_TOKEN)
