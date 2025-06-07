import logging
from fastapi import FastAPI
from dotenv import load_dotenv
import discord
from discord.ext import commands
import os
from contextlib import asynccontextmanager
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
    # Log the user, timestamp, and command
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
    # Log the slash command
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
    await bot.start(TOKEN)
    yield
    await bot.close()

app = FastAPI(lifespan=lifespan)