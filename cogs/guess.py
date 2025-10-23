import discord
from discord.ext import commands
import random
import asyncio

class Guess(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.timeout_tasks = {}

    def cog_unload(self):
        data_cog = self.bot.get_cog("DataManager")
        if data_cog:
            for channel_id in list(data_cog.guess_active_games.keys()):
                try:
                    del data_cog.guess_active_games[channel_id]
                except KeyError:
                    pass
            data_cog.save_data()
        for task in getattr(self, "timeout_tasks", {}).values():
            if not task.done():
                task.cancel()
        self.timeout_tasks.clear()

    @commands.command(name="startguess",aliases=["stg"])
    async def start_guess(self, ctx, min_num: int = 1, max_num: int = 100, chances: int = 7):
        data_cog = self.bot.get_cog("DataManager")
        if not data_cog:
            return await ctx.send("datastore not loaded")
        if ctx.channel.id in data_cog.guess_active_games:
            await ctx.send("⚠️ A game is already running in this channel!")
            return
        if chances >10 :
            await ctx.send("Bro 🫵 thinks he got unlimited lives… max is 10, clown.")
            return
        if (max_num - min_num) < 99:
            await ctx.send("❌ Bro 🫵 set a baby range… at least 100 numbers needed (try 1–100, noob)")
            return

        number = random.randint(min_num, max_num)
        game = {
            "number": number,
            "range": (min_num, max_num),
            "chances_left": chances,
        }
        data_cog.guess_active_games[ctx.channel.id] = game
        data_cog.save_data()

        await ctx.send(f"🎲 Guess the Number started! Range: **{min_num}-{max_num}**, Chances: **{chances}**\nType your guesses!")
        task = asyncio.create_task(self.end_game_after_timeout(ctx.channel.id, 180, ctx))
        self.timeout_tasks[ctx.channel.id] = task

    async def end_game_after_timeout(self, channel_id: int, timeout: int, ctx):
        try:
            await asyncio.sleep(timeout)
        except asyncio.CancelledError:
            return
        data_cog = self.bot.get_cog("DataManager")
        if not data_cog:
            return
        if channel_id in data_cog.guess_active_games:
            number = data_cog.guess_active_games[channel_id]["number"]
            del data_cog.guess_active_games[channel_id]
            data_cog.save_data()
            await ctx.send(f"⏰ Time’s up! The correct number was **{number}**.")
        self.timeout_tasks.pop(channel_id, None)

    @commands.command(name="stopguess",aliases=["spg"])
    async def stop_guess(self, ctx):
        data_cog = self.bot.get_cog("DataManager")
        user_id = ctx.author.id
        if not data_cog:
            return await ctx.send("datastore not loaded")
        game = data_cog.guess_active_games.pop(ctx.channel.id, None)
        if not game:
            await ctx.send("❌ No active game to stop.")
            return

        task = self.timeout_tasks.pop(ctx.channel.id, None)
        if task and not task.done():
            task.cancel()
        data_cog.save_data()
        await ctx.send("🛑 Guess the Number stopped.")

    @commands.command(name="guesslb",aliases=["glb"])
    async def guess_leaderboard(self, ctx):
        data_cog = self.bot.get_cog("DataManager")
        if not data_cog:
            return await ctx.send("datastore not loaded")
        if not data_cog.guessboard:
            await ctx.send("📉 No winners yet!")
            return

        sorted_lb = sorted(data_cog.guessboard.items(), key=lambda x: x[1], reverse=True)
        lines = []
        for i, (uid, wins) in enumerate(sorted_lb[:10]):
            user = ctx.guild.get_member(int(uid)) or await self.bot.fetch_user(int(uid))
            name = user.display_name if user else f"Unknown User ({uid})"
            lines.append(f"**{i+1}.** {name} — {wins} wins")
        desc = "\n".join(lines)

        embed = discord.Embed(title="🏆 Guess the Number Leaderboard", description=desc, color=discord.Color.gold())
        await ctx.send(embed=embed)

    @commands.command(name="resetglb",aliases=["rsglb"])
    @commands.has_permissions(administrator=True)
    async def reset_leaderboard(self, ctx):
        data_cog = self.bot.get_cog("DataManager")
        if not data_cog:
            return await ctx.send("datastore not loaded")
        data_cog.guessboard = {}
        data_cog.save_data()
        await ctx.send("🔄 Leaderboard has been reset.")

    # Message Listener for Guesses
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        data_cog = self.bot.get_cog("DataManager")
        if not data_cog:
            return

        if message.author.bot:
            return
        game = data_cog.guess_active_games.get(message.channel.id)
        if not game:
            return
        try:
            guess = int(message.content.strip())
        except ValueError:
            return  # ignore non-numeric text

        # Reduce shared chances
        game["chances_left"] -= 1
        data_cog.save_data()

        number = game["number"]
        if guess == number:
            await message.channel.send(f"🎉 Correct! {message.author.mention} guessed the number **{number}**! 🎉")
            # Update leaderboard
            user_id = str(message.author.id)
            data_cog.guessboard[user_id] = data_cog.guessboard.get(user_id, 0) + 1
            data_cog.save_data()

            task = self.timeout_tasks.pop(message.channel.id, None)
            if task and not task.done():
                task.cancel()
            data_cog.guess_active_games.pop(message.channel.id, None)
            data_cog.save_data()

        elif game["chances_left"] <= 0:
        # No chances left → only this message
            task = self.timeout_tasks.pop(message.channel.id, None)
            if task and not task.done():
                task.cancel()
            data_cog.save_data()
            answer = game["number"]
            del data_cog.guess_active_games[message.channel.id]
            data_cog.save_data()
            await message.channel.send(f"0️⃣ No chances left! The number was **{answer}**.")

        elif guess < number:
            await message.channel.send(f"🔼 Too low! ({game['chances_left']} chances left)")
        else:
            await message.channel.send(f"🔽 Too high! ({game['chances_left']} chances left)")
# Stop Game
async def setup(bot):
    await bot.add_cog(Guess(bot))
