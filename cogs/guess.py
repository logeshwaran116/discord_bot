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

    @commands.command(name="guess")
    async def guess(self,ctx):
        await ctx.send("`!!startguess` or `!!stg` `[min]` `[max]` `[chances]` → Start a new game\n"
              "`!!stopguess` or `!!spg` → Stop a running game\n"
              "`!!guessboard` or `!!gb` → Guess the number Leaderboard\n")
        return

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
        if (max_num - min_num) > 10000:
            await ctx.send("❌ Slow down, pro-wannabe! The limit is 10,000 (try 1 to 10,000).")
        number = random.randint(min_num, max_num)
        game = {
            "number": number,
            "range": (min_num, max_num),
            "chances_left": chances,
            "started_by": ctx.author.id,
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
        if not data_cog:
            return await ctx.send("datastore not loaded")
        game = data_cog.guess_active_games.get(ctx.channel.id)
        if not game:
            await ctx.send("❌ No active game to stop.")
            return
        if ctx.author.id != game.get("started_by"):
            return await ctx.send("❌ Only the game starter can stop this game.")
        task = self.timeout_tasks.pop(ctx.channel.id, None)
        if task and not task.done():
            task.cancel()
        data_cog.save_data()
        await ctx.send("🛑 Guess the Number stopped.")

    @commands.command(name="guessboard",aliases=["gb"])
    async def guess_leaderboard(self, ctx):
        data_cog = self.bot.get_cog("DataManager")
        if not data_cog:
            return await ctx.send("datastore not loaded")
        guild_id = str(ctx.guild.id)
        guild_board = data_cog.guessboard.get(guild_id)
        if not guild_board:
            return await ctx.send("🏁 No one has played yet in this server!")
        sorted_lb = sorted(guild_board.items(), key=lambda x: x[1], reverse=True)
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
            guild_id = str(message.guild.id)
            if guild_id not in data_cog.guessboard:
                data_cog.guessboard[guild_id] = {}
            data_cog.guessboard[guild_id][user_id] = data_cog.guessboard[guild_id].get(user_id, 0) + 1
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
