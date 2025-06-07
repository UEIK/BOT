from dotenv import load_dotenv
import os
from fastapi import FastAPI
import uvicorn
import discord
from discord.ext import commands
from contextlib import asynccontextmanager
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - User: %(user)s - Command: %(command)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# In-memory log storage (limited by function lifespan)
logs = []

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} ONLINE!")
    await bot.tree.sync()

@bot.event
async def on_command(ctx):
    logger = logging.getLogger()
    current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    log_entry = {
        "time": current_time,
        "user": f"{ctx.author.name}#{ctx.author.discriminator} (ID: {ctx.author.id})",
        "command": ctx.message.content
    }
    logs.append(log_entry)
    if len(logs) > 10:  # Giới hạn 10 log gần đây
        logs.pop(0)
    logger.info("", extra=log_entry)

@bot.tree.command(name="ping", description="Replies with current status and date")
async def ping(interaction: discord.Interaction):
    logger = logging.getLogger()
    current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    log_entry = {
        "time": current_time,
        "user": f"{interaction.user.name}#{interaction.user.discriminator} (ID: {interaction.user.id})",
        "command": "/ping"
    }
    logs.append(log_entry)
    if len(logs) > 10:  # Giới hạn 10 log gần đây
        logs.pop(0)
    logger.info("", extra=log_entry)
    await interaction.response.send_message('```json\n{"message": "Bot is running", "date": "' + current_time + '"}\n```')

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting bot...")
    await bot.start(TOKEN)
    yield
    print("Closing bot...")
    await bot.close()

app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root():
    current_date = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    return {"message": "Bot is running", "date": current_date}

@app.get("/logs")
def get_logs():
    return {"logs": logs}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)