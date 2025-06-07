from dotenv import load_dotenv
import os
from fastapi import FastAPI
import uvicorn
from bot import bot

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
app = FastAPI()
@app.get("/")
def read_root():
    return {"message": "Bot is running"}

@app.on_event("startup")
async def startup():
    await bot.start(TOKEN)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)