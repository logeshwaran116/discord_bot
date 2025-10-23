import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv
from cogs_loader import load_cogs
# --- CONFIG ---
load_dotenv()
DISCORD_TOKEN = os.getenv("TOKEN")
if not DISCORD_TOKEN:
    raise SystemExit("error")

# --- DISCORD SETUP ---
intents = discord.Intents.default()
intents.message_content = True
intents.bans=True
intents.guilds=True
intents.members = True
bot = commands.Bot(command_prefix=("!! ","!!"),intents=intents,case_insensitive=True,help_command=None)

@bot.event
async def on_ready():
    print(f"✅ Bot logged in as {bot.user} (ID: {bot.user.id})")

async def main():
    async with bot:
        await load_cogs(bot)
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Bot stopped manually")