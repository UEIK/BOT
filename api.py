from fastapi import FastAPI, Request, Response
from dotenv import load_dotenv
import os
from bot import bot, verify_signature \


load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
PUBLIC_KEY = os.getenv("PUBLIC_KEY")\


app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Bot is running"}



@app.post("/interactions")
async def interactions_endpoint(request: Request):
    raw_body = await request.body()
    headers = request.headers
    signature = headers.get("X-Signature-Ed25519")
    timestamp = headers.get("X-Signature-Timestamp")

    if not verify_signature(raw_body, signature, timestamp, PUBLIC_KEY):
        return Response(status_code=401, content="Invalid request signature")

    interaction = await bot._process_interaction(raw_body)
    return interaction

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)