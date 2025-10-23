import discord
from discord.ext import commands
import json
import os


class DataManager(commands.Cog):
    """
    Central data storage cog for the bot.
    Stores all persistent information in a single JSON file.
    """

    def __init__(self, bot, filename="data.json"):
        self.bot = bot
        base_dir = os.path.dirname(__file__) 
        self.filepath = os.path.join(base_dir, filename)

        # ---- Internal data structures ----
        self.media_only_channels = set()
        self.text_only_channels = set()
        self.gif_blocked_channels = set()
        self.pinned_messages = {}
        self.mute_messages = {}
        self.mute_tasks = {}
        self.wordleboard = {}
        self.wd_active_games = {}
        self.guessboard = {}
        self.guess_active_games = {}

        # Load data when the cog starts
        self.load_data()

    # ------------------------------------------------------------
    # Load & Save
    # ------------------------------------------------------------
    def load_data(self):
        if not os.path.exists(self.filepath):
            print(f"⚠️ Existing file not found: {self.filepath}")
            self.save_data() 
        try:
            with open(self.filepath, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print("⚠️ data.json is corrupted or empty. Resetting file.")
            data = {}
            self.save_data()

        # Convert lists -> sets for internal use
        self.media_only_channels = set(data.get("media_only_channels", []))
        self.text_only_channels = set(data.get("text_only_channels", []))
        self.gif_blocked_channels = set(data.get("gif_blocked_channels", []))
        self.pinned_messages = data.get("pinned_messages", {})
        self.mute_messages = data.get("mute_messages", {})
        self.mute_tasks = data.get("mute_tasks", {})
        self.wordleboard = data.get("wordleboard",{})
        self.wd_active_games = data.get("wd_active_games",{})
        self.guessboard = data.get("guessboard",{})
        self.guess_active_games = data.get("guess_active_games",{})

    def save_data(self):
        """Save all in-memory data to JSON."""
        data = {
            "media_only_channels": list(self.media_only_channels),
            "text_only_channels": list(self.text_only_channels),
            "gif_blocked_channels": list(self.gif_blocked_channels),
            "pinned_messages": self.pinned_messages,
            "mute_messages": self.mute_messages,
            "mute_tasks": self.mute_tasks,
            "wordleboard":self.wordleboard,
            "wd_active_games":self.wd_active_games,
            "guessboard" : self.guessboard,
            "guess_active_games":self.guess_active_games
        }

        with open(self.filepath, "w") as f:
            json.dump(data, f, indent=4)

    # helper methods

    async def add_media_channel(self, channel_id: int):
        """Add a channel to media-only list."""
        self.media_only_channels.add(channel_id)
        self.save_data()

    async def remove_media_channel(self, channel_id: int):
        """Remove a channel from media-only list."""
        self.media_only_channels.discard(channel_id)
        self.save_data()

    async def add_text_only_channel(self, channel_id: int):
        self.text_only_channels.add(channel_id)
        self.save_data()

    async def remove_text_only_channel(self, channel_id: int):
        self.text_only_channels.discard(channel_id)
        self.save_data()

    async def block_gifs_in_channel(self, channel_id: int):
        self.gif_blocked_channels.add(channel_id)
        self.save_data()

    async def unblock_gifs_in_channel(self, channel_id: int):
        self.gif_blocked_channels.discard(channel_id)
        self.save_data()

    async def set_pinned_message(self, channel_key: str, text: str, message_id: int):
        self.pinned_messages[channel_key] = {"text": text, "message_id": message_id}
        self.save_data()

    async def remove_pinned_message(self, channel_key : str):
        del self.pinned_messages[channel_key]
        self.save_data()


    async def cog_unload(self):
        """Ensure data is saved when bot unloads or restarts."""
        self.save_data()

# Cog setup
async def setup(bot):
    await bot.add_cog(DataManager(bot))

