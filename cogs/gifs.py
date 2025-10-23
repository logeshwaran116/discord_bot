import discord
from discord.ext import commands
import json
import random
import os

class Gifs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        base_dir = os.path.dirname(__file__)  
        json_path = os.path.join(base_dir, "Gif.json")
        # Load GIFs once from JSON
        with open(json_path, "r") as f:
            self.gif_dict = json.load(f)

        self.custom_messages = {
            "genjutsu": "{sender} puts {target} under a **Genjutsu**! 👁️",
            "rasengan": "{sender} blasts {target} with a powerful **Rasengan**! 💥",
            "bankai": "{sender} unleashes **Bankai** on {target}! ⚔️"
        }

        # Dynamically create commands for each action in gif.json
        for action in self.gif_dict.keys():
            self._create_gif_command(action)

    def _create_gif_command(self, action_name: str):
        """Dynamically create a command for each gif action"""

        async def command_func(ctx, member: discord.Member = None):
            if not member:
                await ctx.send(f"**Usage:** `!!{action_name} <mention>`")
                return

            sender_name = ctx.author.display_name
            target_name = member.display_name

            if sender_name == target_name:
                await ctx.send(f"You can't do that to yourself, {sender_name}! 😅")
                return
            if member == self.bot.user:
                await ctx.send(f"You can't do that to me, {sender_name}! 🤭")
                return

            gif_url = random.choice(self.gif_dict[action_name])

            if action_name in self.custom_messages:
                description = self.custom_messages[action_name].format(
                    sender=sender_name,
                    target=target_name
                )
            else:
                description = f"**{sender_name} delivers an {action_name} to {target_name}!**"
            
            embed = discord.Embed(
                description=description,
                color=discord.Color.red()
            )
            embed.set_image(url=gif_url)

            await ctx.send(embed=embed)

        # Register the command with discord.py
        self.bot.command(name=action_name)(command_func)

async def setup(bot):
    await bot.add_cog(Gifs(bot))
