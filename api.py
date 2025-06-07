import os
import asyncio
import logging
from datetime import datetime
from contextlib import asynccontextmanager

import discord
from discord.ext import commands
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
import uvicorn
from dotenv import load_dotenv

# Tải biến môi trường
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
COMMAND_HISTORY_SIZE = int(os.getenv("COMMAND_HISTORY_SIZE", "20"))
PREFIX = "!"

# ─── Thiết lập Logger và bộ nhớ tạm ─────────────────────────────────
logger = logging.getLogger("bot-logger")
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s - %(user)s - %(command)s", "%Y-%m-%d %H:%M:%S")
)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

_logs = []          # Danh sách các bản ghi lệnh gần nhất
_log_listeners = set()  # Các listener SSE

async def record(user: str, cmd: str):
    """Ghi nhận lệnh và gửi tới các listener SSE"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {"time": now, "user": user, "command": cmd}
    _logs.append(entry)
    if len(_logs) > COMMAND_HISTORY_SIZE:
        _logs.pop(0)
    logger.info("", extra={"user": user, "command": cmd})
    # Phát sự kiện SSE cho các listener
    for queue in list(_log_listeners):
        await queue.put(entry)

# ─── Cấu hình Discord Bot ─────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

@bot.command()
async def ping(ctx):
    """Phản hồi Pong! để kiểm tra bot."""
    await record(f"{ctx.author.name}#{ctx.author.discriminator}", "ping")
    await ctx.send("🏓 Pong!")

@bot.command()
async def test(ctx):
    """Lệnh test đơn giản."""
    await record(f"{ctx.author.name}#{ctx.author.discriminator}", "test")
    await ctx.send("🛠️ Lệnh test thực thi thành công!")

# Slash commands
@bot.tree.command(name="ping", description="Phản hồi Pong!")
async def ping_slash(interaction: discord.Interaction):
    user = f"{interaction.user.name}#{interaction.user.discriminator}"
    await record(user, "ping")
    await interaction.response.send_message("🏓 Pong!", ephemeral=False)

@bot.tree.command(name="test", description="Kiểm tra chức năng ghi log.")
async def test_slash(interaction: discord.Interaction):
    user = f"{interaction.user.name}#{interaction.user.discriminator}"
    await record(user, "test")
    await interaction.response.send_message("🛠️ Lệnh test thực thi thành công!", ephemeral=False)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} đã sẵn sàng!")
    await bot.tree.sync()

# ─── Ứng dụng FastAPI với Lifespan & SSE ──────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi động bot khi FastAPI start
    asyncio.create_task(bot.start(DISCORD_TOKEN))
    yield
    # Đóng bot khi FastAPI shutdown
    await bot.close()

app = FastAPI(lifespan=lifespan)

@app.get("/logs", response_class=HTMLResponse)
async def get_logs(request: Request):
    """Trang HTML hiển thị lịch sử lệnh (cập nhật trực tiếp)."""
    html = f"""<!DOCTYPE html>
<html><head><meta charset=\"utf-8\"/>
<title>Lịch sử lệnh</title>
<style>
  body {{ font-family: sans-serif; padding: 2rem; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border: 1px solid #ddd; padding: 0.5rem; }}
  th {{ background: #f0f0f0; }}
</style>
</head><body>
  <h1>Lịch sử {COMMAND_HISTORY_SIZE} lệnh gần nhất (Trực tiếp)</h1>
  <table>
    <thead>
      <tr><th>Thời gian</th><th>Người dùng</th><th>Lệnh</th></tr>
    </thead>
    <tbody id=\"logs-body\">{''.join(f"<tr><td>{e['time']}</td><td>{e['user']}</td><td>/{e['command']}</td></tr>" for e in _logs)}</tbody>
  </table>
<script>
  const evtSource = new EventSource('/logs/stream');
  const tbody = document.getElementById('logs-body');
  evtSource.onmessage = e => {
    const data = JSON.parse(e.data);
    const row = document.createElement('tr');
    row.innerHTML = `<td>${data.time}</td><td>${data.user}</td><td>/${data.command}</td>`;
    tbody.appendChild(row);
  };
</script>
</body></html>"""
    return HTMLResponse(content=html)

@app.get('/logs/stream')
async def stream_logs():
    """SSE endpoint phát sự kiện log mới."""
    async def event_generator():
        queue = asyncio.Queue()
        _log_listeners.add(queue)
        try:
            while True:
                entry = await queue.get()
                yield f"data: {entry!r}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            _log_listeners.discard(queue)

    return StreamingResponse(event_generator(), media_type='text/event-stream')

# ─── Điểm vào ứng dụng ─────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
