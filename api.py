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
    logger.info(
        "",
        extra={
            "user": f"{ctx.author.name}#{ctx.author.discriminator} (ID: {ctx.author.id})",
            "command": ctx.message.content
        }
    )

@bot.tree.command(name="ping", description="Replies with Pong!")
async def ping(interaction: discord.Interaction):
    logger = logging.getLogger()
    logger.info(
        "",
        extra={
            "user": f"{interaction.user.name}#{interaction.user.discriminator} (ID: {interaction.user.id})",
            "command": "/ping"
        }
    )
    await interaction.response.send_message("pong")

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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)