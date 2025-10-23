import discord 
import random
from discord.ext import commands
import asyncio
#--coinflip--
class Coinflip(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    @commands.command(name="coinflip",aliases=["cf"])
    async def coinflip(self, ctx, choice: str=None):
        options = ["heads", "tails"]
        bot_choice = random.choice(options)

        # Case 1: No choice provided
        if not choice:
            await ctx.send("**Usage:** `!!coinflip <h/t>`")
            return
        
        choice = choice.lower().strip()

        # Map short forms
        if choice in ["h", "head"]:
            choice = "heads"
        elif choice in ["t", "tail"]:
            choice = "tails"

        # Case 2: Invalid choice
        if choice not in options:
            await ctx.send("**Usage:** `!!coinflip <h/t>`")
            return
    
        # First send spinning message
        embed = discord.Embed(
            title="**Coinflip**",
            description="The coin spins <a:cf:1424302645945958461> ...",
            color=discord.Color.purple()
        )
        msg = await ctx.send(embed=embed)
        # Wait 2 seconds
        await asyncio.sleep(2)

        # Decide winner
        if choice == bot_choice:
            result = ("You won 🎉")
        else:
            result = ("You lost 😔")

        # Edit the same embed to show result
        embed.description = f"The coin spins 🪙... and it’s **{bot_choice}**\n\n**{result}**"
        await msg.edit(embed=embed)
        return
        
async def setup(bot):
    await bot.add_cog(Coinflip(bot))
