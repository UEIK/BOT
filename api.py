# api.py

from dotenv import load_dotenv
import os
import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn
import logging
from datetime import datetime
import discord
from discord.ext import commands

# --- Load environment variables ---
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
APP_ID = int(os.getenv("DISCORD_APP_ID", "0"))

# --- Configure logger to stdout (Vercel will collect these logs) ---
logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s',  # chỉ giữ message
    datefmt='%Y-%m-%d %H:%M:%S'
))
logger.addHandler(handler)

# --- In-memory log buffer (keep last 10 entries) ---
logs = []

# --- Discord bot setup ---
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    application_id=APP_ID
)

@bot.event
async def on_ready():
    print(f"{bot.user} ONLINE! Syncing commands globally…")
    await bot.tree.sync()
    print("Commands synced globally.")

@bot.event
async def on_command(ctx):
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    entry = {
        "user": f"{ctx.author.name}#{ctx.author.discriminator} (ID:{ctx.author.id})",
        "command": ctx.message.content,
        "time": now
    }
    logs.append(entry)
    if len(logs) > 10:
        logs.pop(0)
    # In toàn bộ info trong message
    logger.info(f"User: {entry['user']} | Command: {entry['command']} | Time: {entry['time']}")

@bot.tree.command(name="ping", description="Replies with Pong! + timestamp")
async def ping(interaction: discord.Interaction):
    await interaction.response.defer()
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    entry = {
        "user": f"{interaction.user.name}#{interaction.user.discriminator} (ID:{interaction.user.id})",
        "command": "/ping",
        "time": now
    }
    logs.append(entry)
    if len(logs) > 10:
        logs.pop(0)
    logger.info(f"User: {entry['user']} | Command: {entry['command']} | Time: {entry['time']}")
    await interaction.followup.send(
        f"```json\n{{\"message\":\"pong\",\"date\":\"{now}\"}}\n```"
    )

# --- FastAPI app with lifespan to run the bot ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    bot_task = asyncio.create_task(bot.start(TOKEN))
    yield
    await bot.close()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def health_check():
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    return {"message": "Bot is running", "date": now}

@app.get("/logs")
async def get_logs():
    return {"logs": logs}

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
