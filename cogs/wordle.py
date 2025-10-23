import discord
from discord.ext import commands
import random
import time
import os
import json
import asyncio
class EmojiWordle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.timeout_tasks = {}
        
        base_dir = os.path.dirname(__file__)  
        json_path = os.path.join(base_dir, "words.json")
        if not os.path.exists(json_path):
            raise FileNotFoundError("words.json not found in cog directory.")

        with open(json_path, "r") as f:
            self.words = json.load(f)

        self.flag = dict(zip("abcdefghijklmnopqrstuvwxyz", ["🄰","🄱","🄲","🄳","🄴","🄵","🄶","🄷","🄸","🄹","🄺","🄻","🄼","🄽","🄾","🄿","🅀","🅁","🅂","🅃","🅄","🅅","🅆","🅇","🅈","🅉"]))
        self.outlined = dict(zip("abcdefghijklmnopqrstuvwxyz", ["🅐","🅑","🅒","🅓","🅔","🅕","🅖","🅗","🅘","🅙","🅚","🅛","🅜","🅝","🅞","🅟","🅠","🅡","🅢","🅣","🅤","🅥","🅦","🅧","🅨","🅩"]))
        self.bold = dict(zip("abcdefghijklmnopqrstuvwxyz", ["🇦","🇧","🇨","🇩","🇪","🇫","🇬","🇭","🇮","🇯","🇰","🇱","🇲","🇳","🇴","🇵","🇶","🇷","🇸","🇹","🇺","🇻","🇼","🇽","🇾","🇿"]))
    
    async def cog_unload(self):
        data_cog = self.bot.get_cog("DataManager")
        if data_cog:
            # End all running games gracefully
            for user_id in list(data_cog.wd_active_games.keys()):
                try:
                    del data_cog.wd_active_games[user_id]
                except KeyError:
                    pass
            data_cog.save_data()

        # Cancel all timeout tasks
        for task in getattr(self, "timeout_tasks", {}).values():
            task.cancel()
        self.timeout_tasks.clear()

    def get_feedback(self, guess, target):
        feedback = []
        target_letters = list(target)
        used = [False] * 5

        # First pass
        for i in range(5):
            if guess[i] == target[i]:
                feedback.append(self.bold[guess[i]])
                used[i] = True
            else:
                feedback.append(None)

        # Second pass
        for i in range(5):
            if feedback[i] is None:
                if guess[i] in target_letters:
                    for j in range(5):
                        if guess[i] == target_letters[j] and not used[j]:
                            feedback[i] = self.outlined[guess[i]]
                            used[j] = True
                            break
                if feedback[i] is None:
                    feedback[i] = self.flag[guess[i]]

        return feedback

    async def wordle_timeout(self, ctx, user_id):
        await asyncio.sleep(300)
        data_cog = self.bot.get_cog("DataManager")
        if not data_cog:
            return
        if user_id not in data_cog.wd_active_games:
            return
        game = data_cog.wd_active_games[user_id]
        target = game["target"]
        await ctx.send(f"⏳ Time's up! The Wordle game has ended.\nThe word was: **{target}**")
        if user_id in self.timeout_tasks:
            self.timeout_tasks[user_id].cancel()
            del self.timeout_tasks[user_id]
        del data_cog.wd_active_games[user_id]
        data_cog.save_data()


    @commands.command(name="wordle")
    async def wordle(self, ctx):
        await ctx.send(f">>> `!!startwordle` or `!!stw` → Start the wordle game\n"
              "`!!stopwordle` or `!!spw` → Stop a running game\n" 
              "`!!wordleboard` or `!!wb` → Wordle Leaderboard\n")

    @commands.command(name="startwordle",aliases=["stw"])
    async def start_wordle(self, ctx):
        data_cog = self.bot.get_cog("DataManager")
        if not data_cog:
            return await ctx.send("⚠️ datastore not loaded.")
        user_id = ctx.author.id
        if user_id in data_cog.wd_active_games:
            game = data_cog.wd_active_games[user_id]
            if game["channel_id"] != ctx.channel.id:
                await ctx.send("🚫 You already have a game running in another channel. Please continue there.")
                return
            await ctx.send("🕹️ You're already playing! Type your 5-letter guess.")
            return

        target = random.choice(self.words["words"])
        data_cog.wd_active_games[user_id] = {"target": target, "attempts": [], "channel_id":ctx.channel.id}
        data_cog.save_data()
        await ctx.send(f"🎯 Emoji Wordle started! for {ctx.author.mention} Type your 5-letter guess.\nTips :" \
            "\n🇦 - letter is in word and in correct position " \
            "\n🅐 - letter is in word but in incorrect position \n🄰 - letter not in word")
        self.timeout_tasks[user_id] = asyncio.create_task(self.wordle_timeout(ctx, user_id))

    @commands.command(name="stopwordle",aliases=["spw"])
    async def stop_wordle(self, ctx):
        data_cog = self.bot.get_cog("DataManager")
        if not data_cog:
            return await ctx.send("⚠️ datastore not loaded.")
        user_id =  ctx.author.id
        if user_id not in data_cog.wd_active_games:
            await ctx.send("❌ You are not currently Playing wordle")
            return
        target = data_cog.wd_active_games[user_id]["target"]
        await ctx.send(f"🛑 The game stopped manually \nThe word was: **{target}**")
        if user_id in self.timeout_tasks:
            self.timeout_tasks[user_id].cancel()
            del self.timeout_tasks[user_id]
        del data_cog.wd_active_games[user_id]
        data_cog.save_data()

    @commands.command(name="wordleboard", aliases=["wb"])
    async def wordle_leaderboard(self, ctx):
        data_cog = self.bot.get_cog("DataManager")
        if not data_cog:
            return await ctx.send("datastore not loaded")
        if not data_cog.wordleboard:
            await ctx.send("📉 No one has won a game yet!")
            return

        sorted_board = sorted(data_cog.wordleboard.items(), key=lambda x: x[1], reverse=True)
        lines = []
        for i, (user_id, wins) in enumerate(sorted_board[:10], start=1):
            user = ctx.guild.get_member(int(user_id)) or await self.bot.fetch_user(int(user_id))
            name = user.display_name if user else f"User {user_id}"
            lines.append(f"{i}. {name} — {wins} win{'s' if wins > 1 else ''}")
        desc = "\n".join(lines)

        embed = discord.Embed(title="🏆 Wordle Leaderboard", description=desc, color=discord.Color.gold())
        await ctx.send(embed=embed)

    @commands.command(name="resetwordleboard",aliases=["rswlb"])
    @commands.has_permissions(administrator=True)
    async def reset_wordleboard(self,ctx):
        data_cog = self.bot.get_cog("DataManager")
        if not data_cog:
            return await ctx.send("datastore not loaded")
        if not data_cog.wordleboard:
            return await ctx.send("⚠️ No data to reset")
        data_cog.wordleboard = {}
        data_cog.save_data()
        await ctx.send("✅ Wordleboard reset successfully.")

    @commands.command(name="resetwordleboarduser",aliases=["rswlbm"])
    @commands.has_permissions(administrator=True)
    async def reset_wordleboard_user(self,ctx, member: discord.Member = None):
        data_cog = self.bot.get_cog("DataManager")
        if not member:
            return await ctx.send(">>> **Usage:** `!!resetwordleboarduser` `<mention>`")
        if not data_cog:
            return await ctx.send("datastore not loaded")
        if member.id not in data_cog.wordleboard:
            return await ctx.send("⚠️ user has no data to reset")   
        del data_cog.wordleboard[member.id]
        data_cog.save_data()
        await ctx.send("✅ User data reset successfully")

    @commands.Cog.listener()
    async def on_message(self, message):
        data_cog = self.bot.get_cog("DataManager")
        if message.author.bot:
            return

        user_id = message.author.id
        if user_id not in data_cog.wd_active_games:
            return

        game = data_cog.wd_active_games[user_id]
        if message.channel.id != game["channel_id"]:
            return
        
        guess = message.content.lower()
        if len(guess) != 5 or not guess.isalpha():
            if len(guess) == 4 or len(guess) == 6:
                await message.channel.send("❗ Please enter a valid 5-letter word.")
                return
            else:
                return
        if guess not in self.words["words"]:
            await message.channel.send("❌ Word not in list. Enter a valid word!")
            return
        
        target = game["target"]
        game["attempts"].append(guess)
        data_cog.save_data()

        feedback = self.get_feedback(guess, target)
        str_user_id = str(user_id)
        if guess == target:
            data_cog.wordleboard[str_user_id] = data_cog.wordleboard.get(str_user_id, 0) + 1
            data_cog.save_data()
            await message.channel.send(f"{message.author.display_name}: {' '.join(feedback)}\n🎉 You guessed it!")
            if user_id in self.timeout_tasks:
                self.timeout_tasks[user_id].cancel()
                del self.timeout_tasks[user_id]
            del data_cog.wd_active_games[user_id]
            data_cog.save_data()
        elif len(game["attempts"]) >= 6:
            await message.channel.send(f"{message.author.display_name}: {' '.join(feedback)}\n😢 Out of attempts! The word was: **{target}**")
            if user_id in self.timeout_tasks:
                self.timeout_tasks[user_id].cancel()
                del self.timeout_tasks[user_id]
            del data_cog.wd_active_games[user_id]
            data_cog.save_data()
        else:
            attempts_left = 6 - len(game["attempts"])
            await message.channel.send(f"{message.author.display_name}: {' '.join(feedback)}\n🧠 Attempts left: {attempts_left}")

async def setup(bot):
    await bot.add_cog(EmojiWordle(bot))
