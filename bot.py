from fastapi import FastAPI
from dotenv import load_dotenv
import discord
from discord.ext import commands
import os
from contextlib import asynccontextmanager

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

@bot.tree.command(name="ping", description="Replies with Pong!")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("pong")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await bot.start(TOKEN)
    yield
    await bot.close()

app = FastAPI(lifespan=lifespan)
