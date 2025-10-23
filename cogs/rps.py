import discord
from discord.ext import commands
import random
from typing import Optional

class RPS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="rps")
    async def rps(self, ctx, *, arg: Optional[str] = None):
        """
        Usage:
         - !!rps rock     -> play vs bot
         - !!rps @member  -> challenge member
        """
        options = ["rock", "paper", "scissors"]

        if not arg:
            await ctx.send(
                ">>> **Usage:**\n"
                "`!!rps <rock/paper/scissors>` → Play vs bot\n"
                "`!!rps <mention>` → Challenge a friend"
            )
            return

        tokens = arg.split()
        first = tokens[0]

        # Try to detect a member from the first token (mention, id, name)
        member = None
        try:
            member = await commands.MemberConverter().convert(ctx, first)
        except Exception:
            member = None

        # If we found a member -> challenge flow
        if member:
            if len(tokens) > 1:
                await ctx.send("❌ Invalid usage. To challenge: `!!rps @member` (no extra args).")
                return

            if member.bot:
                await ctx.send("⚠️ You can’t challenge a bot.")
                return
            if member == ctx.author:
                await ctx.send("⚠️ You can’t challenge yourself.")
                return

            view = ChallengeView(ctx.author, member)
            embed = discord.Embed(
                title="🎮 Rock–Paper–Scissors Challenge!",
                description=f"{ctx.author.mention} has challenged {member.mention}!\n"
                            "Click **Accept** or **Decline**.",
                color=discord.Color.blurple(),
            )
            msg = await ctx.send(embed=embed, view=view)
            view.message = msg
            return

        # Otherwise treat as choice vs bot
        choice = first.lower().strip()
        if choice not in options:
            await ctx.send("**Usage:** `!!rps <rock/paper/scissors>` → or `!!rps @member` to challenge someone.")
            return

        bot_choice = random.choice(options)
        if choice == bot_choice:
            result = "It's a tie! 😐"
        elif (
            (choice == "rock" and bot_choice == "scissors")
            or (choice == "paper" and bot_choice == "rock")
            or (choice == "scissors" and bot_choice == "paper")
        ):
            result = f"You win! 🎉 {choice.capitalize()} beats {bot_choice.capitalize()}"
        else:
            result = f"I win! 🫵 {bot_choice.capitalize()} beats {choice.capitalize()}"

        embed = discord.Embed(
            title="✊ Rock 🖐 Paper ✌ Scissors",
            description=(
                f"**You:** {choice.capitalize()}\n"
                f"**Bot:** {bot_choice.capitalize()}\n\n"
                f"**{result}**"
            ),
            color=discord.Color.purple(),
        )
        await ctx.send(embed=embed)


# --- View for Accept / Decline ---
class ChallengeView(discord.ui.View):
    def __init__(self, challenger, opponent):
        super().__init__(timeout=60)
        self.challenger = challenger
        self.opponent = opponent
        self.message: Optional[discord.Message] = None

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(content="⌛ Challenge timed out (no response).", embed=None, view=None)
                await self.message.delete(delay=3)
            except discord.NotFound:
                pass

    @discord.ui.button(label="✅ Accept", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.opponent:
            await interaction.response.send_message("⚠️ This challenge isn’t for you!", ephemeral=True)
            return

        embed = discord.Embed(
            title="✊ Rock 🖐 Paper ✌ Scissors",
            description=f"Both players, choose your move!",
            color=discord.Color.purple()
        )
        view = RPSGameView(self.challenger, self.opponent)
        await interaction.response.edit_message(embed=embed, view=view)
        # store the message object for timeout handling
        try:
            view.message = await interaction.original_response()
        except Exception:
            # fallback: interaction.message may also work in some contexts
            view.message = interaction.message

    @discord.ui.button(label="❌ Decline", style=discord.ButtonStyle.red)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.opponent:
            await interaction.response.send_message("⚠️ This challenge isn’t for you!", ephemeral=True)
            return
        await interaction.response.edit_message(content="❌ Challenge declined.", embed=None, view=None)


# --- Actual Game View ---
class RPSGameView(discord.ui.View):
    def __init__(self, player1, player2):
        super().__init__(timeout=60)
        self.player1 = player1
        self.player2 = player2
        self.choices = {}  # {user_id: "rock"/"paper"/"scissors"}
        self.message: Optional[discord.Message] = None

    async def handle_choice(self, interaction: discord.Interaction, choice: str):
        user = interaction.user

        if user.id not in [self.player1.id, self.player2.id]:
            await interaction.response.send_message("⚠️ You’re not part of this game!", ephemeral=True)
            return

        if user.id in self.choices:
            await interaction.response.send_message("❗ You already chose!", ephemeral=True)
            return

        self.choices[user.id] = choice

        p1_status = "✅ Chose" if self.player1.id in self.choices else "❌ Waiting"
        p2_status = "✅ Chose" if self.player2.id in self.choices else "❌ Waiting"

        embed = discord.Embed(
            title="✊ Rock 🖐 Paper ✌ Scissors",
            description=(
                f"**{self.player1.display_name}:** {p1_status}\n"
                f"**{self.player2.display_name}:** {p2_status}"
            ),
            color=discord.Color.blurple()
        )

        if len(self.choices) < 2:
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await self.declare_winner(interaction, embed)

    async def declare_winner(self, interaction, embed):
        p1_choice = self.choices.get(self.player1.id)
        p2_choice = self.choices.get(self.player2.id)

        # safety: if something missing, cancel
        if p1_choice is None or p2_choice is None:
            await interaction.response.edit_message(content="⚠️ Error: missing choices.", view=None)
            return

        if p1_choice == p2_choice:
            result = "It's a tie! 😐"
        elif (
            (p1_choice == "rock" and p2_choice == "scissors")
            or (p1_choice == "paper" and p2_choice == "rock")
            or (p1_choice == "scissors" and p2_choice == "paper")
        ):
            result = f"🏆 {self.player1.mention} wins! ({p1_choice.capitalize()} beats {p2_choice.capitalize()})"
        else:
            result = f"🏆 {self.player2.mention} wins! ({p2_choice.capitalize()} beats {p1_choice.capitalize()})"

        embed.description = (
            f"**{self.player1.display_name}:** {p1_choice.capitalize()}\n"
            f"**{self.player2.display_name}:** {p2_choice.capitalize()}\n\n"
            f"**{result}**"
        )

        # disable old move buttons
        for child in list(self.children):
            child.disabled = True

        # add a play again button (enabled)
        self.add_item(PlayAgainButton(self.player1, self.player2))

        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(content="⌛ Game cancelled — no one chose in time.", embed=None, view=None)
                await self.message.delete(delay=3)
            except discord.NotFound:
                pass

    # --- Buttons for moves ---
    @discord.ui.button(label="✊ Rock", style=discord.ButtonStyle.gray)
    async def rock(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_choice(interaction, "rock")

    @discord.ui.button(label="🖐 Paper", style=discord.ButtonStyle.blurple)
    async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_choice(interaction, "paper")

    @discord.ui.button(label="✌ Scissors", style=discord.ButtonStyle.green)
    async def scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_choice(interaction, "scissors")


# --- Play Again Button ---
class PlayAgainButton(discord.ui.Button):
    def __init__(self, player1, player2):
        super().__init__(label="🔁 Play Again", style=discord.ButtonStyle.success)
        self.player1 = player1
        self.player2 = player2

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id not in [self.player1.id, self.player2.id]:
            await interaction.response.send_message("⚠️ Only the players can restart the game!", ephemeral=True)
            return

        # Acknowledge the click (ephemeral confirmation)
        await interaction.response.defer(ephemeral=True)

        # Stop the old view's internal listener (cancels its timeout task)
        if self.view:
            self.view.stop()
        

        # Delete the old message (optional: helps keep channel clean and fully resets state)
        try:
            await interaction.message.delete()
        except Exception:
            # already deleted or unable to delete — ignore
            pass
        except discord.Forbidden:
        # Bot doesn’t have permission to delete, handle it
            pass

        embed = discord.Embed(
            title="✊ Rock 🖐 Paper ✌ Scissors",
            description="Both players, choose your move!",
            color=discord.Color.purple(),
        )
        new_view = RPSGameView(self.player1, self.player2)
        msg = await interaction.followup.send(embed=embed, view=new_view)
        new_view.message = msg
       

# --- Setup function for Cog ---
async def setup(bot):
    await bot.add_cog(RPS(bot))
