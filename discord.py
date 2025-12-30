import discord
from discord.ext import commands, tasks
import requests
import random
import datetime
import asyncio
import os

# =====================
# CONFIGURATION
# =====================

BOT_TOKEN = MTQ1NTU5OTk0NzMxODU2MjkwOQ.Gdk-v0.TzHB_0HIGoXCpPIGghVtUanoLyjcwsvAN8p5uY
DAILY_CHANNEL_ID = 1329895128973709486  # Replace with your channel ID

BASE_URL = "https://stepdatabase.maths.org/database/db/{X}/{X}-S{Y}-Q{Z}.png"

# =====================
# BOT SETUP
# =====================

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =====================
# UTILITIES
# =====================

def valid_X_values():
    xs = ["Spec"]
    xs += [f"{i:02d}" for i in range(87, 100)]
    xs += [f"{i:02d}" for i in range(0, 19)]
    return xs

def format_label(X, Y, Z):
    if X == "Spec":
        year_label = "Specimen"
    else:
        year_num = int(X)
        year_label = f"20{X}" if year_num <= 18 else f"19{X}"

    return f"STEP {Y} {year_label}, Question {Z}"

def image_exists(url):
    try:
        r = requests.head(url, timeout=5)
        return r.status_code == 200
    except requests.RequestException:
        return False

def random_question():
    X = random.choice(valid_X_values())
    Y = random.choice(["2", "3"])
    Z = random.randint(1, 16)
    return X, Y, Z

# =====================
# COMMANDS
# =====================

@bot.command(name="step")
async def step_command(ctx, *, arg=None):
    if arg is None or arg.lower() == "help":
        await ctx.send(
            "**STEP Bot Usage**\n"
            "`!step XX-SY-Z`\n\n"
            "Examples:\n"
            "`!step 97-S2-1`\n"
            "`!step Spec-S3-5`\n\n"
        )
        return

    try:
        left, z = arg.split("-Q") if "-Q" in arg else (arg.split("-")[0], arg.split("-")[1][1])
        X, sY = left.split("-S") if "-S" in left else (left.split("-")[0], left.split("-")[1][1])
        Y = sY
        Z = int(z)
    except Exception:
        await ctx.send("Invalid format. Use `!step XX-SY-QZ` (e.g. `97-S2-Q1`).")
        return

    if X not in valid_X_values() or Y not in {"2", "3"} or not (1 <= Z <= 16):
        await ctx.send("Invalid STEP question reference.")
        return

    url = BASE_URL.format(X=X, Y=Y, Z=Z)

    if not image_exists(url):
        await ctx.send("That STEP question could not be found.")
        return

    label = format_label(X, Y, Z)
    await ctx.send(label)
    await ctx.send(url)

# =====================
# DAILY TASK
# =====================

@tasks.loop(minutes=1)
async def daily_step():
    now = datetime.datetime.now()
    if now.hour == 12 and now.minute == 0:
        channel = bot.get_channel(DAILY_CHANNEL_ID)
        if channel is None:
            return

        for _ in range(50):  # retry until a valid question is found
            X, Y, Z = random_question()
            url = BASE_URL.format(X=X, Y=Y, Z=Z)
            if image_exists(url):
                label = format_label(X, Y, Z)
                await channel.send(label)
                await channel.send(url)
                break

        await asyncio.sleep(60)  # prevent double posting

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    daily_step.start()

# =====================
# RUN
# =====================

bot.run(BOT_TOKEN)
