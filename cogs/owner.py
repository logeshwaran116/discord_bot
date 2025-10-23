import discord
from discord.ext import commands
import time
from datetime import timedelta

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()

    #owner help
    @commands.command("owner")
    @commands.is_owner()
    async def owner_help(self,ctx):
        embed = discord.Embed(
            title="**Sanji's Bot Owner's Command**",
            description="Here are my available commands for Owner",
            color=discord.Color.og_blurple()
        )

        embed.add_field(
            name=None,
            value="`!!shutdown` → Disconnects the bot from discord \n\n"
                "`!!cogs` → List of cogs \n\n "
                "`!!load` → Load a new cog \n\n "
                "`!!reload` → Reload a available cog \n\n" 
                "`!!unload` → Unload a available cog \n\n"
                "`!!reloadall` → reload all available cogs\n\n"
                "`!!stats` → Stats of bot ",
                inline=False   
        )
        await ctx.send(embed=embed)
        return

    # ✅ Load a new cog
    @commands.command()
    @commands.is_owner()
    async def load(self, ctx, cog: str):
        try:
            cog_path=f"cogs.{cog}"
            await self.bot.load_extension(cog_path)
            await ctx.send(f"✅ Loaded `{cog}` successfully!")
        except Exception as e:
            await ctx.send(f"⚠️ Failed to load `{cog}`:\n```{e}```")

    # 🔄 Reload an existing cog
    @commands.command()
    @commands.is_owner()
    async def reload(self, ctx, cog: str):
        try:
            cog_path=f"cogs.{cog}"
            await self.bot.reload_extension(cog_path)
            await ctx.send(f"🔄 Reloaded `{cog}` successfully!")
        except Exception as e:
            await ctx.send(f"⚠️ Failed to reload `{cog}`:\n```{e}```")

    @commands.command(name="reloadall")
    @commands.is_owner()
    async def reload_all(self, ctx):
        success = []
        failed = []

        for cog in list(self.bot.extensions.keys()):
            try:
                await self.bot.reload_extension(cog)
                success.append(f"✅ {cog}")
            except Exception as e:
                failed.append(f"❌ {cog} → `{e}`")

        embed = discord.Embed(
            title="🔄 Reload All Cogs",
            color=discord.Color.green() if not failed else discord.Color.orange()
        )

        if success:
            embed.add_field(
                name="Reloaded Successfully",
                value="\n".join(success),
                inline=False
            )
        if failed:
            embed.add_field(
                name="Failed to Reload",
                value="\n".join(failed),
                inline=False
            )

        await ctx.send(embed=embed)



    # ❌ Unload a cog
    @commands.command()
    @commands.is_owner()
    async def unload(self, ctx, cog: str):
        try:
            cog_path=f"cogs.{cog}"
            await self.bot.unload_extension(cog_path)
            await ctx.send(f"❌ Unloaded `{cog}` successfully!")
        except Exception as e:
            await ctx.send(f"⚠️ Failed to unload `{cog}`:\n```{e}```")

    @commands.command(name="shutdown")
    @commands.is_owner()
    async def shutdown(self, ctx):
        await ctx.send("🛑 Shutting down...")
        await self.bot.close()

    @commands.command(name="cogs")
    @commands.is_owner()
    async def list_cogs(self, ctx):
        cogs = list(self.bot.extensions.keys())
        if not cogs:
            await ctx.send("ℹ️ No cogs are currently loaded.")
        else:
            await ctx.send("📦 Loaded cogs:\n" + "\n".join(f"→ {c}" for c in cogs))

    @commands.command(name="stats")
    @commands.is_owner()
    async def stats(self, ctx):
        uptime = str(timedelta(seconds=int(time.time() - self.start_time)))
        latency = round(self.bot.latency * 1000)  # ms
        embed = discord.Embed(title="🤖 Bot Stats", color=discord.Color.gold())
        embed.add_field(name="⏳ Uptime", value=uptime, inline=False)
        embed.add_field(name="📡 Latency", value=f"{latency} ms", inline=False)
        embed.add_field(name="📦 Loaded Cogs", value=len(self.bot.cogs), inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="sync")
    @commands.is_owner()
    async def sync_commands(self, ctx):
        synced = await self.bot.tree.sync()
        await ctx.send(f"✅ Synced {len(synced)} commands to Discord.")

async def setup(bot):
    await bot.add_cog(Admin(bot))
