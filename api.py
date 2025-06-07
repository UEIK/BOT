# api.py
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

# Số log tối đa lưu lại
COMMAND_HISTORY_SIZE = int(os.getenv("COMMAND_HISTORY_SIZE", "20"))
_logs = []

app = FastAPI()

# Endpoint để bot gửi log qua POST
@app.post("/log")
async def receive_log(entry: dict):
    if not all(k in entry for k in ("time", "user", "command")):
        raise HTTPException(400, "Missing fields")
    _logs.append(entry)
    if len(_logs) > COMMAND_HISTORY_SIZE:
        _logs.pop(0)
    return {"status": "ok"}

# Endpoint hiển thị bảng HTML
@app.get("/logs", response_class=HTMLResponse)
async def get_logs():
    rows = "".join(
        f"<tr>"
        f"<td>{e['time']}</td>"
        f"<td>{e['user']}</td>"
        f"<td>/{e['command']}</td>"
        f"</tr>"
        for e in _logs
    )
    html = f"""
    <!DOCTYPE html>
    <html>
      <head><meta charset="utf-8"/><title>Bot Logs</title>
        <style>
          body {{font-family:sans-serif;padding:2rem}}
          table {{border-collapse:collapse;width:100%}}
          th,td {{border:1px solid #ddd;padding:0.5rem}}
          th {{background:#f0f0f0}}
        </style>
      </head>
      <body>
        <h1>Last {COMMAND_HISTORY_SIZE} Commands</h1>
        <table>
          <thead>
            <tr><th>Time (UTC)</th><th>User</th><th>Command</th></tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>
      </body>
    </html>
    """
    return html
