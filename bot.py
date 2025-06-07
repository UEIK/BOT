# bot.py

import os
from datetime import datetime, timezone
import requests
from dotenv import load_dotenv

import discord
from discord.ext import commands

# ─── LOAD .env (chỉ để dev local; Heroku/Railway sẽ đọc ENV vars từ dashboard) ───
load_dotenv()

# ─── CẤU HÌNH ─────────────────────────────────────────────────────────────────────
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")      # phải set trên Heroku/Railway
LOG_URL       = os.getenv("LOG_URL")            # ví dụ: https://your-vercel-domain/log
PREFIX        = "!"                             # prefix bất kỳ

# ─── KHỞI TẠO BOT ────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

async def send_log(user: str, cmd: str):
    """
    Gửi POST về Vercel để ghi log.
    """
    entry = {
        "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "user": user,
        "command": cmd
    }
    try:
        requests.post(LOG_URL, json=entry, timeout=5)
    except Exception as e:
        print("⛔️ Gửi log thất bại:", e)

# ─── SỰ KIỆN BOT ────────────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"✅ {bot.user} is ready!")

@bot.event
async def on_interaction(interaction: discord.Interaction):
    # Bắt slash-commands (/...)
    if interaction.type == discord.InteractionType.application_command:
        user = f"{interaction.user.name}#{interaction.user.discriminator}"
        raw  = interaction.data.get("name", "")
        cmd  = str(raw)  # ép kiểu thành str để khỏi warning
        await send_log(user, cmd)

@bot.event
async def on_message(message: discord.Message):
    # Bắt prefix-commands (!...)
    if message.author.bot:
        return
    if message.content.startswith(PREFIX):
        user = f"{message.author.name}#{message.author.discriminator}"
        cmd  = message.content[len(PREFIX):].split()[0]
        await send_log(user, cmd)
    await bot.process_commands(message)

# ─── CHẠY BOT ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not DISCORD_TOKEN or not LOG_URL:
        print("❌ Thiếu biến môi trường DISCORD_TOKEN hoặc LOG_URL")
    else:
        bot.run(DISCORD_TOKEN)
