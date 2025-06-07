import os
import threading
import logging
from datetime import datetime
from dotenv import load_dotenv

# ─── LOAD .env CHO DEV LOCAL ─────────────────────────────────────────────────────
load_dotenv()

# ─── CẤU HÌNH ─────────────────────────────────────────────────────────────────────
DISCORD_TOKEN        = os.getenv("DISCORD_TOKEN")                # set trên Vercel
COMMAND_HISTORY_SIZE = int(os.getenv("COMMAND_HISTORY_SIZE", "20"))
PREFIX               = "!"                                       # prefix cho các lệnh bất kỳ

# ─── LOGGER ─────────────────────────────────────────────────────────────────────
logger = logging.getLogger("bot-logger")
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s - %(user)s - %(command)s", "%Y-%m-%d %H:%M:%S")
)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# ─── DISCORD BOT ─────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

_logs: list[dict] = []     # buffer lưu log

@bot.event
async def on_ready():
    print(f"✅ {bot.user} đã kết nối và sẵn sàng.")
    await bot.tree.sync()

# 1) Bắt slash-commands
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.application_command:
        now  = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        user = f"{interaction.user.name}#{interaction.user.discriminator}"
        cmd  = interaction.data["name"]
        _logs.append({"time": now, "user": user, "command": cmd})
        if len(_logs) > COMMAND_HISTORY_SIZE:
            _logs.pop(0)
        logger.info("", extra={"user": user, "command": cmd})

# 2) Bắt mọi prefix-commands (!whatever)
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    if message.content.startswith(PREFIX):
        now  = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        user = f"{message.author.name}#{message.author.discriminator}"
        # lấy tên lệnh (trước dấu space)
        cmd  = message.content[len(PREFIX):].split()[0]
        _logs.append({"time": now, "user": user, "command": cmd})
        if len(_logs) > COMMAND_HISTORY_SIZE:
            _logs.pop(0)
        logger.info("", extra={"user": user, "command": cmd})
    # vẫn xử lý các lệnh đã định nghĩa (nếu có)
    await bot.process_commands(message)

# 3) Thêm 1 command test để thử (không bắt buộc)
@bot.tree.command(name="test", description="🚀 Test xem log có chạy không")
async def test_command(interaction: discord.Interaction):
    await interaction.response.send_message("🛠️ Test thành công, bạn gõ lệnh gì cũng được!")

# 4) Khởi động bot (thread nền) ngay khi module được import
if DISCORD_TOKEN:
    threading.Thread(target=lambda: bot.run(DISCORD_TOKEN), daemon=True).start()

# ─── FASTAPI APP ─────────────────────────────────────────────────────────────────
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/logs", response_class=HTMLResponse)
async def get_logs():
    rows = "\n".join(
        f"<tr><td>{e['time']}</td>"
        f"<td>{e['user']}</td>"
        f"<td>/{e['command']}</td></tr>"
        for e in _logs
    )
    html = f"""
    <!DOCTYPE html><html><head>
      <meta charset="utf-8"/><title>Command Logs</title>
      <style>
        body{{font-family:sans-serif;padding:2rem}}
        table{{border-collapse:collapse;width:100%}}
        th,td{{border:1px solid #ddd;padding:0.5rem}}
        th{{background:#f0f0f0}}
      </style>
    </head><body>
      <h1>Last {COMMAND_HISTORY_SIZE} Commands</h1>
      <table>
        <thead><tr>
          <th>Thời gian (UTC)</th><th>User</th><th>Command</th>
        </tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </body></html>
    """
    return html

# ─── CHỈ CHẠY LOCAL KHI DEBUG ─────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8002")))
