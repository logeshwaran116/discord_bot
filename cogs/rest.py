import discord
from discord.ext import commands

class Restrict(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.restricted_users = set()

        # register the global check
        bot.add_check(self.restrict_check)

    # Global check runs before any command
    async def restrict_check(self, ctx):
        if ctx.author.id in self.restricted_users:
            await ctx.send("❌ You are restricted from using this bot.")
            return False  # block the command
        return True

    @commands.command(name="restrict")
    @commands.is_owner()
    async def restrict_user(self, ctx, member: discord.Member):
        if member.id in self.restricted_users:
            await ctx.send(f"⚠️ {member.display_name} is already restricted.")
            return

        self.restricted_users.add(member.id)
        await ctx.send(f"🚫 {member.display_name} has been restricted from using the bot.")

    @commands.command(name="unrestrict")
    @commands.is_owner()
    async def unrestrict_user(self, ctx, member: discord.Member):
        if member.id not in self.restricted_users:
            await ctx.send(f"ℹ️ {member.display_name} is not restricted.")
            return

        self.restricted_users.remove(member.id)
        await ctx.send(f"✅ {member.display_name} can now use the bot again.")

async def setup(bot):
    await bot.add_cog(Restrict(bot))
