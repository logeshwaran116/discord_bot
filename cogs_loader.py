import os
import asyncio

async def load_cogs(bot):
    """Auto-load all cogs from the cogs/ folder"""
    for filename in os.listdir("cogs"):
        if filename.endswith(".py") and not filename.startswith("__"):
            cog = f"cogs.{filename[:-3]}"  # remove .py
            try:
                await bot.load_extension(cog)
                print(f"✅ Loaded {cog}")
            except Exception as e:
                print(f"❌ Failed to load {cog}: {e}")
