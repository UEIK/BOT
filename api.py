import os
import asyncio
import logging
from datetime import datetime, timezone

import discord
from discord.ext import commands
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
COMMAND_HISTORY_SIZE = int(os.getenv("COMMAND_HISTORY_SIZE", "20"))
PREFIX = "!"

# ─── Logger & In-Memory Buffer ─────────────────────────────────────
logger = logging.getLogger("bot-logger")
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s - %(user)s - %(command)s", "%Y-%m-%d %H:%M:%S")
)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

_logs = []

async def record(user: str, cmd: str):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    _logs.append({"time": now, "user": user, "command": cmd})
    if len(_logs) > COMMAND_HISTORY_SIZE:
        _logs.pop(0)
    logger.info("", extra={"user": user, "command": cmd})

# ─── Discord Bot Setup ───────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# Prefix commands
@bot.command()
async def ping(ctx):
    """Responds with Pong! to test the bot."""
    await record(f"{ctx.author.name}#{ctx.author.discriminator}", "ping")
    await ctx.send("🏓 Pong!")

@bot.command()
async def test(ctx):
    """Simple test command to verify registration."""
    await record(f"{ctx.author.name}#{ctx.author.discriminator}", "test")
    await ctx.send("🛠️ Test command executed successfully!")

# Slash commands
@bot.tree.command(name="ping", description="Respond with Pong!")
async def ping_slash(interaction: discord.Interaction):
    user = f"{interaction.user.name}#{interaction.user.discriminator}"
    await record(user, "ping")
    await interaction.response.send_message("🏓 Pong!", ephemeral=False)

@bot.tree.command(name="test", description="Verify logging functionality.")
async def test_slash(interaction: discord.Interaction):
    user = f"{interaction.user.name}#{interaction.user.discriminator}"
    await record(user, "test")
    await interaction.response.send_message("🛠️ Test command executed successfully!", ephemeral=False)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} is ready!")
    # sync slash commands
    await bot.tree.sync()

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    raise error

# ─── FastAPI App Setup ───────────────────────────────────────────────
app = FastAPI()

@app.on_event("startup")
async def start_bot():
    """Launch the Discord bot when FastAPI starts."""
    asyncio.create_task(bot.start(DISCORD_TOKEN))

@app.on_event("shutdown")
async def stop_bot():
    """Ensure the Discord bot closes on shutdown."""
    await bot.close()

@app.get("/logs", response_class=HTMLResponse)
async def get_logs(request: Request):
    """Render the last N commands as an HTML table."""
    rows = "\n".join(
        f"<tr><td>{e['time']}</td><td>{e['user']}</td><td>/{e['command']}</td></tr>"
        for e in _logs
    )
    html = f"""<!DOCTYPE html><html><head><meta charset=\"utf-8\"/>
    <title>Logs</title>
    <style>body{{font-family:sans-serif;padding:2rem}} table{{border-collapse:collapse;width:100%}} th,td{{border:1px solid #ddd;padding:0.5rem}} th{{background:#f0f0f0}}</style>
    </head><body>
      <h1>Last {COMMAND_HISTORY_SIZE} Commands</h1>
      <table><thead>
        <tr><th>Time (UTC)</th><th>User</th><th>Command</th></tr>
      </thead><tbody>
        {rows}
      </tbody></table>
    </body></html>"""
    return HTMLResponse(content=html)

# ─── Entry Point ─────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
