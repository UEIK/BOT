# bot.py
import os
import requests
from datetime import datetime

import discord
from discord.ext import commands

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
LOG_URL      = os.getenv("LOG_URL")    # ví dụ: https://your-vercel-domain.log
PREFIX       = "!"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

async def send_log(user: str, cmd: str):
    entry = {
        "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "user": user,
        "command": cmd
    }
    try:
        requests.post(LOG_URL, json=entry, timeout=5)
    except Exception as e:
        print("⛔️ Gửi log thất bại:", e)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} is ready!")

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.application_command:
        u = f"{interaction.user.name}#{interaction.user.discriminator}"
        await send_log(u, interaction.data["name"])

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    if message.content.startswith(PREFIX):
        u = f"{message.author.name}#{message.author.discriminator}"
        cmd = message.content[len(PREFIX):].split()[0]
        await send_log(u, cmd)
    await bot.process_commands(message)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
