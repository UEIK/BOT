from interactions import Client, Intents, listen, slash_command, SlashContext

# Khởi tạo bot
intents = Intents.DEFAULT
bot = Client(intents=intents)

# Định nghĩa slash command
@slash_command(name="ping", description="Replies with Pong!")
async def ping(ctx: SlashContext):
    await ctx.send("Pong from Vercel!")

def verify_signature(raw_body, signature, timestamp, public_key):
    from interactions import verify_key
    return verify_key(raw_body, signature, timestamp, public_key)