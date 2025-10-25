import discord
from discord.ext import commands
import asyncio
import time
import re

def is_gif_url(url: str) -> bool:
    clean_url = url.split("?")[0].lower()  # remove query params
    return clean_url.endswith(".gif") or "tenor.com" in clean_url or "giphy.com" in clean_url or "cdn.discordapp.com" in clean_url

def is_media_url(url: str) -> bool:
    """Check if a URL points to a media file."""
    clean_url = url.split("?")[0].lower()  # remove query params
    media_extensions = (".jpg", ".jpeg", ".png", ".mp4", ".mov", ".webm", ".mkv", ".bmp", ".tiff", ".heic", ".avi")
    return clean_url.endswith(media_extensions) or "cdn.discordapp.com" in clean_url

class channel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mute_tasks = {}
        self.mute_messages = {}
        self.debounce_tasks = {}
        self.ignore_debounce = set() 

    # 🔒 Lock channel
    @commands.command(name="lockchannel")
    @commands.has_permissions(manage_channels=True)
    async def lock_channel(self, ctx, channel_id: str = None):
        if channel_id:
            if not channel_id.isdigit():
                return await ctx.send("❌ Invalid channel ID. Please provide a numeric one.")
            target_channel = ctx.guild.get_channel(int(channel_id))
            if not target_channel:
                return await ctx.send("❌ Could not find a channel with that ID.")
        else:
            target_channel = ctx.channel
        overwrite = target_channel.overwrites_for(ctx.guild.default_role)
        if overwrite.send_messages is False:
            return await ctx.send(f"{target_channel.mention} is already Locked")
        overwrite.send_messages = False
        await target_channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(f"🔒 {target_channel.mention} is now locked. Members cannot send messages.")

    # 🔓 Unlock channel
    @commands.command(name="unlockchannel")
    @commands.has_permissions(manage_channels=True)
    async def unlock_channel(self, ctx, channel_id: str = None):
        if channel_id:
            if not channel_id.isdigit():
                return await ctx.send("❌ Invalid channel ID. Please provide a numeric one.")
            target_channel = ctx.guild.get_channel(int(channel_id))
            if not target_channel:
                return await ctx.send("❌ Could not find a channel with that ID.")
        else:
            target_channel = ctx.channel
        overwrite = target_channel.overwrites_for(ctx.guild.default_role)
        if overwrite.send_messages is True:
            return await ctx.send(f"#<{target_channel.mention}> is not locked")
        overwrite.send_messages = True
        if ctx.channel.id in self.mute_tasks:
            self.mute_tasks[ctx.channel.id].cancel()
            self.mute_tasks.pop(ctx.channel.id, None)
        if ctx.channel.id in self.mute_messages:
            try:
                mute_msg_id = self.mute_messages[ctx.channel.id]["message_id"]
                mute_msg = await ctx.fetch_message(mute_msg_id)
                await mute_msg.delete()
            except Exception:
                pass
            self.mute_messages.pop(ctx.channel.id, None)
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(f"🔓 {target_channel.mention} is now unlocked. Members can send messages again.")

    @commands.command(name="mutechannel")
    @commands.has_permissions(manage_channels=True)
    async def mute_channel(self, ctx, dur: str = "5m"):
        channel = ctx.channel 
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        if overwrite.send_messages is False:
            return await ctx.send("⚠️ This channel is already muted.")
        
        units = {"m":[1,"m"],"h":[60, "h"],"d":[1440, "d"]}
        dur=dur.strip().lower()
        matches = re.findall(r"(\d+)\s*([dhm])",dur)
        if not matches:
            return await ctx.send("Invalid format. Try : `45m`, `1h`, `1h30m`, `2d4h`")

        total_minutes = 0
        for value, unit in matches:
            if unit not in units:
                return await ctx.send(f"Unsupported unit `{unit}`. Use only d, h, or m.")
            multiplier = units[unit][0]
            minutes = int(value) * multiplier
            total_minutes += minutes
        overwrite.send_messages = False
        sec = total_minutes*60
        unix_time = int(time.time()) + sec

        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

        msg = await ctx.send(f"🔇 This channel is now muted. Members can send messages again <t:{unix_time}:R>",delete_after=sec-3)
        self.mute_messages[ctx.channel.id]={ "message_id": msg.id}

        if ctx.channel.id in self.mute_tasks:
            self.mute_tasks[ctx.channel.id].cancel()
        self.mute_tasks[ctx.channel.id] = asyncio.create_task(self.auto_unmute(ctx, sec-3))

    async def auto_unmute(self, ctx, delay: int):
        """Auto-unmute after the delay unless manually cancelled."""
        try:
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            return  # Manual unmute cancelled this timer

        channel = ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = True
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

        # Cleanup
        self.mute_messages.pop(ctx.channel.id, None)
        self.mute_tasks.pop(ctx.channel.id, None)

        await ctx.send("🔊 Channel Unmuted automatically. Members may now send messages.", delete_after=10)

    @commands.command(name="unmutechannel")
    @commands.has_permissions(manage_channels=True)
    async def unmute_channel(self, ctx):
        """Unmute the current channel immediately."""
        channel = ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)

        # If already unmuted, stop
        if overwrite.send_messages is not False:
            return await ctx.send("⚠️ This channel is not muted.")

        overwrite.send_messages = True
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

        # Cancel auto-unmute task if running
        if ctx.channel.id in self.mute_tasks:
            self.mute_tasks[ctx.channel.id].cancel()
            self.mute_tasks.pop(ctx.channel.id, None)

        # Delete mute message if it exists
        if ctx.channel.id in self.mute_messages:
            try:
                mute_msg_id = self.mute_messages[ctx.channel.id]["message_id"]
                mute_msg = await ctx.fetch_message(mute_msg_id)
                await mute_msg.delete()
            except Exception:
                pass
            self.mute_messages.pop(ctx.channel.id, None)

        await ctx.send("🔊 Channel Unmuted manually. Members may now send messages.", delete_after=10)


    @commands.command(name="lockthread")
    @commands.has_permissions(manage_threads=True)
    async def lock_thread(self, ctx):
        thread = ctx.channel if isinstance(ctx.channel, discord.Thread) else None
        if thread is None:
            await ctx.send("⚠️ This command must be used inside a thread.")
            return
        if ctx.channel.locked:
            await ctx.send("🔒 This thread is already locked.")
            return
        await ctx.channel.edit(locked=True)
        await ctx.send(f"🔒 {ctx.channel.mention} has been locked.")

    #unlock thread
    @commands.command(name="unlockthread")
    @commands.has_permissions(manage_threads=True)
    async def unlock_thread(self,ctx):
        thread = ctx.channel if isinstance(ctx.channel, discord.Thread) else None
        if thread is None:
            await ctx.send("This command must be used inside a thread.")
            return
        if not ctx.channel.locked:
            await ctx.send("🔓 This thread is already unlocked.")
            return
        else:
            await ctx.channel.edit(locked=False)
            await ctx.send(f"🔓 {ctx.channel.mention} has been unlocked.")

    @commands.command(name="mutethread")
    @commands.has_permissions(manage_threads=True)
    async def mute_thread(self, ctx, ):
        thread = ctx.channel if isinstance(ctx.channel, discord.Thread) else None
        if thread is None:
            await ctx.send("⚠️ This command must be used inside a thread.")
            return
        if ctx.channel.locked:
            await ctx.send("🔒 This thread is already locked.")
            return
        await ctx.channel.edit(locked=True)
        await ctx.send(f"🔒 {ctx.channel.mention} has been locked.")

    # ---------------- MEDIA ONLY ----------------
    @commands.command(name="mediaonly")
    @commands.has_permissions(manage_channels=True)
    async def set_media_only(self, ctx):
        data_cog = self.bot.get_cog("DataManager")
        if not data_cog:
            return await ctx.send("⚠️ datastore not loaded.")
        if ctx.channel.id in data_cog.text_only_channels:
            await ctx.send("⚠️This channel is already set to text-only. It can’t be both text and media-only. ")
        elif ctx.channel.id in data_cog.media_only_channels:
            await ctx.send("This channel is already a media-only channel 📸")
        else:
            await data_cog.add_media_channel(ctx.channel.id)
            await ctx.send("📸 Media-only mode enabled in this channel!")

    @commands.command(name="dbmediaonly")
    @commands.has_permissions(manage_channels=True)
    async def disable_media_only(self, ctx):
        data_cog = self.bot.get_cog("DataManager")
        if not data_cog:
            return await ctx.send("⚠️ datastore not loaded.")
        if ctx.channel.id not in data_cog.media_only_channels:
            return await ctx.send("This channel is not setted as media-only channel 📸")
        await data_cog.remove_media_channel(ctx.channel.id)
        await ctx.send("✅ Media-only mode disabled in this channel!")

    @commands.command(name="textonly")
    @commands.has_permissions(manage_channels=True)
    async def set_text_only(self, ctx):
        data_cog = self.bot.get_cog("DataManager")
        if not data_cog:
            return await ctx.send("⚠️ datastore not loaded.")
        if ctx.channel.id in data_cog.media_only_channels:
            await ctx.send("⚠️This channel is already set to media-only. It can’t be both media and text-only.")
        elif ctx.channel.id in data_cog.text_only_channels:
            await ctx.send("This channel is already a text-only channel 💬")
        else:
            await data_cog.add_text_only_channel(ctx.channel.id)
            await ctx.send("💬 Text-only mode enabled in this channel!")

    @commands.command(name="dbtextonly")
    @commands.has_permissions(manage_channels=True)
    async def disable_text_only(self, ctx):
        data_cog = self.bot.get_cog("DataManager")
        if not data_cog:
            return await ctx.send("⚠️ datastore not loaded.")
        if ctx.channel.id not in data_cog.text_only_channels:
            await ctx.send("This channel is not setted as text-only channel 💬")
        await data_cog.remove_text_only_channel(ctx.channel.id)
        await ctx.send("✅ Text-only mode disabled in this channel!")

    # ---------------- PINNED MESSAGE ----------------
    def cancel_debounce(self, channel_id: int):
        """Cancel and remove any pending debounce task for a channel."""
        task = self.debounce_tasks.pop(channel_id, None)
        if task and not task.done():
            task.cancel()


    @commands.command(name="setpinmsg")
    @commands.has_permissions(manage_messages=True)
    async def set_pinned(self, ctx, *, text: str=None):
        """Set or update the pinned message for this channel"""
        data_cog = self.bot.get_cog("DataManager")
        if not data_cog:
            return await ctx.send("⚠️ datastore not loaded.")
        if not text:
            await ctx.send(">>> **Usage: ** `!!setpinmsg` `<message>`")
            return
        channel_id = ctx.channel.id
        channel_key = str(ctx.channel.id)
        if channel_id in self.debounce_tasks:
            self.debounce_tasks[channel_id].cancel()
            del self.debounce_tasks[channel_id]
        old = data_cog.pinned_messages.get(channel_key)
        if old:
            try:
                old_msg = await ctx.channel.fetch_message(old["message_id"])
                await old_msg.delete()
            except (discord.NotFound, discord.Forbidden):
                pass

        new_msg = await ctx.send(f"**{text.upper()}**")
        await data_cog.set_pinned_message(channel_key, text, new_msg.id)
        self.ignore_debounce.discard(channel_id)

    @commands.command(name="rmpinmsg")
    @commands.has_permissions(manage_messages=True)
    async def remove_pinned(self, ctx):
        data_cog = self.bot.get_cog("DataManager")
        if not data_cog:
            return await ctx.send("⚠️ datastore not loaded.")
        channel_id = ctx.channel.id
        channel_key = str(ctx.channel.id)
        if channel_key not in data_cog.pinned_messages:
            await ctx.send("❌ No pinned message set in this channel.")
            return

        try:
            old_msg = await ctx.channel.fetch_message(data_cog.pinned_messages[channel_key]["message_id"])
            await old_msg.delete()
        except (discord.NotFound, discord.Forbidden):
            pass
        self.cancel_debounce(channel_id)
        await data_cog.remove_pinned_message(channel_key)
        await ctx.send("🗑️ Pinned message removed.", delete_after=5)

    @commands.command(name="clearmsg")
    @commands.has_permissions(manage_messages=True)
    async def cleanup(self, ctx, limit: int = None):
        if not limit:
            return await ctx.send("> **Usage:** `!!clearmsg` `[message count]`")
        if limit <= 0:
            await ctx.send("❌ Please specify a positive number of messages.")
            return
        deleted = await ctx.channel.purge(limit=limit+1)  # +1 includes the command message itself
        await ctx.send(f"🧹 Deleted {len(deleted)-1} messages.", delete_after=5)
        
    @commands.command(name="clearmsguser")
    @commands.has_permissions(manage_messages=True)
    async def cleanup_user(self, ctx, member: discord.Member, limit: int = 10):
        if not member:
            await ctx.send("**Usage:** !!clearmsguser <mention> [number]")
        if limit <= 0:
            await ctx.send("❌ Please specify a positive number of messages.")
            return
        deleted_count = 0
        async for message in ctx.channel.history(limit=500):  # fetch last 500 messages
            if message.author == member:
                await message.delete()
                deleted_count += 1
                if deleted_count >= limit:
                    break
        await ctx.send(
        f"🧹 Deleted {deleted_count} messages from {member.display_name} (searched last 500).",
        delete_after=5
    )

    # 🧹 Clear GIF messages
    @commands.command(name="cleargif")
    @commands.has_permissions(manage_messages=True)
    async def clear_gif(self, ctx, limit: int = 100):
        if limit <= 0:
            return await ctx.send("❌ Please specify a positive number of messages.")
        if limit > 2000:
            return ctx.send("❌ max limit is 2000")
        def is_gif(message: discord.Message):
            has_gif = (
                    any(is_gif_url(attach.url) for attach in message.attachments)
                    or is_gif_url(message.content)
                    )
            return has_gif
        deleted = await ctx.channel.purge(limit=limit, check=is_gif)
        await ctx.send(f"🧹 Deleted {len(deleted)} GIF messages.", delete_after=5)

    @commands.command(name="clearmedia")
    @commands.has_permissions(manage_messages=True)
    async def clear_media(self, ctx, limit: int = 100):
        if limit <= 0:
            return await ctx.send("❌ Please specify a positive number of messages.")
        if limit > 2000:
            return ctx.send("❌ max limit is 2000")
        def is_media(message: discord.Message):
            has_media = (
                any(is_media_url(attach.url) for attach in message.attachments)
                or is_media_url(message.content)
            )
            return has_media

        deleted = await ctx.channel.purge(limit=limit, check=is_media)
        await ctx.send(f"🧹 Deleted {len(deleted)} media messages.", delete_after=5)

    # 🚫 Disable GIFs
    @commands.command(name="dbgif")
    @commands.has_permissions(manage_channels=True)
    async def disable_gifs(self, ctx):
        data_cog = self.bot.get_cog("DataManager")
        if not data_cog:
            return await ctx.send("⚠️ datastore not loaded.")
        if ctx.channel.id in data_cog.gif_blocked_channels:
            return await ctx.send("⚠️ GIFs are already disabled here.")
        await data_cog.block_gifs_in_channel(ctx.channel.id)
        await ctx.send("🚫 GIFs are now disabled in this channel.")

    # ✅ Enable GIFs
    @commands.command(name="ebgif")
    @commands.has_permissions(manage_channels=True)
    async def enable_gifs(self, ctx):
        data_cog = self.bot.get_cog("DataManager")
        if not data_cog:
            return await ctx.send("⚠️ datastore not loaded.")
        if ctx.channel.id in data_cog.gif_blocked_channels:
            await data_cog.unblock_gifs_in_channel(ctx.channel.id)
            await ctx.send("✅ GIFs are now allowed in this channel.")
        else:
            await ctx.send("⚠️ GIFs are already enabled here.")

    # ---------------- LISTENER ----------------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        data_cog = self.bot.get_cog("DataManager")
        if message.author.bot:
            return

        channel_id = message.channel.id

        # --- MEDIA ONLY MODE ---
        if channel_id in data_cog.media_only_channels:
            if not message.attachments:
                await message.delete()
                return
        # text only
        if channel_id in data_cog.text_only_channels:
            if message.attachments:
                await message.delete()
                return

        # gif dlt
        if channel_id in data_cog.gif_blocked_channels:
            has_gif = (
                    any(is_gif_url(attach.url) for attach in message.attachments)
                    or is_gif_url(message.content)
                    )

            if has_gif:
                try:
                    await message.delete()
                except discord.Forbidden:
                    pass  # Bot doesn’t have permission
                except discord.NotFound:
                    pass  # Message already deleted

        # --- PINNED MESSAGE MODE ---
        channel_key = str(channel_id)
        if channel_key not in data_cog.pinned_messages:
            return
        if channel_id in self.ignore_debounce:  # 👈 skip if recently updated manually
            return
        if channel_id in self.debounce_tasks:
            self.debounce_tasks[channel_id].cancel()
        self.debounce_tasks[channel_id] = asyncio.create_task(
            self.delayed_update(channel_id, message.channel, data_cog)
        )
    async def delayed_update(self, channel_id, channel, data_cog):
        try:
            await asyncio.sleep(3)
            pinned_data = data_cog.pinned_messages[str(channel_id)]
            if not pinned_data:
                return 
            try:
                old_msg = await channel.fetch_message(pinned_data["message_id"])
                await old_msg.delete()
            except (discord.NotFound, discord.Forbidden):
                pass
            new_msg = await channel.send(f"**{data_cog.pinned_messages[str(channel_id)]['text'].upper()}**")
            data_cog.pinned_messages[str(channel_id)]["message_id"] = new_msg.id
            data_cog.save_data()
        except asyncio.CancelledError:
            pass

async def setup(bot):
    await bot.add_cog(channel(bot))
