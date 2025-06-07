import os, threading, logging
from datetime import datetime, timezone

import discord
from discord.ext import commands
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN        = os.getenv("DISCORD_TOKEN")
COMMAND_HISTORY_SIZE = int(os.getenv("COMMAND_HISTORY_SIZE", "20"))
PREFIX               = "!"

# ─── Logger & in‐memory buffer ────────────────────────────────────────
logger = logging.getLogger("bot-logger")
h = logging.StreamHandler()
h.setFormatter(logging.Formatter("%(asctime)s - %(user)s - %(command)s",
                                 "%Y-%m-%d %H:%M:%S"))
logger.addHandler(h)
logger.setLevel(logging.INFO)

_logs = []

async def record(user: str, cmd: str):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    _logs.append({"time": now, "user": user, "command": cmd})
    if len(_logs) > COMMAND_HISTORY_SIZE:
        _logs.pop(0)
    logger.info("", extra={"user": user, "command": cmd})

# ─── Discord Bot ────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} ready!")
    await bot.tree.sync()

@bot.event
async def on_interaction(interaction: discord.Interaction):
    # Bắt và reply slash-commands
    if interaction.type == discord.InteractionType.application_command:
        cmd = str(interaction.data.get("name", ""))
        user = f"{interaction.user.name}#{interaction.user.discriminator}"
        await record(user, cmd)
        # <-- thêm reply ở đây
        await interaction.response.send_message(f"🛠️ Đã ghi log lệnh `/{cmd}`!")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.content.startswith(PREFIX):
        cmd = message.content[len(PREFIX):].split()[0]
        user = f"{message.author.name}#{message.author.discriminator}"
        await record(user, cmd)
        # <-- thêm reply prefix
        await message.channel.send(f"🛠️ Đã ghi log lệnh `{PREFIX}{cmd}`!")

    # vẫn cho bot xử lý @bot.command() nếu có
    await bot.process_commands(message)

# khởi bot background thread
threading.Thread(target=lambda: bot.run(DISCORD_TOKEN), daemon=True).start()

# ─── FastAPI UI ────────────────────────────────────────────────────────────
app = FastAPI()

@app.get("/logs", response_class=HTMLResponse)
async def get_logs():
    rows = "\n".join(
        f"<tr><td>{e['time']}</td><td>{e['user']}</td><td>/{e['command']}</td></tr>"
        for e in _logs
    )
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"/>
    <title>Logs</title>
    <style>body{{font-family:sans-serif;padding:2rem}}
           table{{border-collapse:collapse;width:100%}}
           th,td{{border:1px solid #ddd;padding:0.5rem}}
           th{{background:#f0f0f0}}</style>
    </head><body>
      <h1>Last {COMMAND_HISTORY_SIZE} Commands</h1>
      <table><thead>
        <tr><th>Time (UTC)</th><th>User</th><th>Command</th></tr>
      </thead><tbody>
        {rows}
      </tbody></table>
    </body></html>"""

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
