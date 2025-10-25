import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta, datetime, timezone
import re

class member(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member = None, *,  reason: str = "No reason"):
        if not member:
            return await ctx.send("**Usage:** `!!kick` `<mention>` `[reason]`")
        if member == ctx.author:
            return await ctx.send("❌ You cannot kick yourself.")
        else:
            try:
                await member.kick(reason=reason)
                await ctx.send(f"👢 {member} has been kicked. Reason: {reason}")
            except discord.Forbidden:
                await ctx.send(f"⚠️ I don’t have permission to kick {member}.")
            except discord.HTTPException:
                await ctx.send(f"❌ Failed to kick {member} due to an unexpected error.")

    # Ban a member
    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member = None, *,  reason: str = "No reason"):
        if not member:
            return await ctx.send("**Usage:** `!!ban` `<mention>` `[reason]`")
        if member == ctx.author:
            return await ctx.send("❌ You cannot ban yourself.")
        else:
            try:
                await member.ban(reason=reason)
                await ctx.send(f"🔨 {member} has been banned. Reason: {reason}")
            except discord.Forbidden:
                await ctx.send(f"⚠️ I don’t have permission to ban {member}.")
            except discord.HTTPException as e:
                await ctx.send(f"❌ Failed to ban {member} reason:{e}")

    # List banned members (prefix command)
    @commands.command(name="banlist")
    @commands.has_permissions(ban_members=True)
    async def banlist(self, ctx):
        try:
            banned_users = []
            async for entry in ctx.guild.bans():
                banned_users.append(entry)

            if not banned_users:
                await ctx.send("✅ No banned members in this server.")
                return

            embed = discord.Embed(
                title=f"🔨 Banned Members in {ctx.guild.name}",
                color=discord.Color.red()
            )

            for entry in banned_users[:10]:  # limit to 10
                embed.add_field(
                    name=f"🚫 {entry.user}",
                    value=f"ID: {entry.user.id}",
                    inline=False
                )

            embed.set_footer(text=f"Total banned: {len(banned_users)}")
            await ctx.send(embed=embed)

        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to view bans.")
        except discord.HTTPException as e:
            await ctx.send(f"⚠️ Failed to fetch ban list: {e}")

    '''@banlist.error
    async def banlist_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("🚫 You lack the `Ban Members` permission.")
        else:
            await ctx.send(f"⚠️ Error: {error}")'''

    # Unban a member
    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, user: str = None):
        if not user:
            return await ctx.send("**Usage:** `!!unban` `<user ID/username>`")
        banned_users = []
        async for entry in ctx.guild.bans():
            banned_users.append(entry)
        for ban_entry in banned_users:
            member = ban_entry.user
            if (f"{member.name}#{member.discriminator}" == user) or (member.name == user) or (str(member.id) == user):
                await ctx.guild.unban(ban_entry.user)
                await ctx.send(f"✅ Unbanned {user}")
                return
        await ctx.send(f"⚠️ User {user} not found in ban list.")


    async def ensure_muted_role(self, guild: discord.Guild):
        """Create Muted role if it doesn't exist, and set permissions."""
        role = discord.utils.get(guild.roles, name="Muted")
        if role:
            return role

        # Create role
        role = await guild.create_role(
            name="Muted",
            reason="Muted role for permanent mutes",
            colour=discord.Colour.dark_gray()
        )

        # Apply overwrites to all channels
        for channel in guild.channels:
            try:
                await channel.set_permissions(
                    role,
                    send_messages=False,
                    speak=False,
                    add_reactions=False
                )
            except Exception:
                pass

        return role

    # Timeout (mute) a member
    @commands.command(name="mute")
    @commands.has_permissions(moderate_members=True)
    async def mute(self, ctx, member: discord.Member = None, *, reason: str = "No reason"):
        if not member:
            return await ctx.send("**Usage:** `!!mute` `<mention>` `[reason]`")
        if member == ctx.author:
            return await ctx.send("❌ You cannot mute yourself.")
        if ctx.guild.me.top_role <= member.top_role:
            return await ctx.send("❌ I cannot mute this member due to role hierarchy.")

        role = await self.ensure_muted_role(ctx.guild)

        if role in member.roles:
            return await ctx.send("ℹ️ User is already muted.")

        try:
            await member.add_roles(role, reason=reason)
            await ctx.send(f"🔇 {member.mention} has been muted. Reason: {reason}")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to assign the Muted role.")
        except Exception as e:
            await ctx.send(f"⚠️ Error: {e}")


    # Timeout (mute) a member
    @commands.command(name="tm")
    @commands.has_permissions(moderate_members=True)
    async def tm(self, ctx, member: discord.Member = None, dur: str = "5m", *, reason: str = "No reason"):
        if not member:
            return await ctx.send("**Usage:** `!!tm` `<mention>`  `[duration]` `[reason]`")
        if member == ctx.author:
            return await ctx.send("You cannot timeout Yourself")

        units = {"m":[1,"m"],"h":[60, "h"],"d":[1440, "d"]}
        dur=dur.strip().lower()
        matches = re.findall(r"(\d+)\s*([dhm])",dur)
        if not matches:
            return await ctx.send("Invalid format. Try : `45m`, `1h`, `1h30m`, `2d4h`")

        total_minutes = 0
        parts = []
        for value, unit in matches:
            if unit not in units:
                return await ctx.send(f"Unsupported unit `{unit}`. Use only d, h, or m.")
            multiplier, suffix = units[unit]
            minutes = int(value) * multiplier
            total_minutes += minutes
            label = suffix
            parts.append(f"{value}{label}")
        try:
            duration = timedelta(minutes=total_minutes)
            await member.timeout(duration, reason=reason)
            await ctx.send(f"🔇 {member.mention} has been muted for {' '.join(parts)}. Reason: {reason}")
        except discord.Forbidden:
            await ctx.send("❌ I don’t have permission to mute this member.")
        except Exception as e:
            await ctx.send(f"⚠️ Error: {e}")

    # Remove timeout (unmute)
    @commands.command(name="unmute")
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, ctx, member: discord.Member = None):
        if not member:
            return await ctx.send("**Usage:** `!!unmute` `<mention>`")
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        removed_any = False
        if muted_role and muted_role in member.roles:
            try:
                await member.remove_roles(muted_role, reason="Unmuted")
                removed_any = True
            except Exception as e:
                await ctx.send(f"⚠️ Could not remove Muted role: {e}")

        if removed_any:
            await ctx.send(f"🔊 {member.mention} has been unmuted.")
        else:
            await ctx.send(f"ℹ️ {member.mention} is not muted.")

    @commands.command(name="checkmute")
    @commands.has_permissions(moderate_members=True)
    async def checkmute(self, ctx, member:discord.Member = None):
        if not member:
            return await ctx.send("**Usage:** `!!checkmute` `<mention>`")
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if muted_role and muted_role in member.roles:
            return await ctx.send (f"{member.display_name} is muted")
        else:
            return await ctx.send (f"{member.display_name} is not muted")

    @commands.command(name="rmtm")
    @commands.has_permissions(moderate_members=True)
    async def rmtm(self, ctx, member:discord.Member = None):
        if not member:
            return await ctx.send("**Usage:** `!!rmtm` `<mention>`")
        removed_any = False
        if member.timed_out_until is not None:
            try:
                await member.timeout(None, reason="Unmuted")
                removed_any = True
            except Exception as e:
                await ctx.send(f"⚠️ Could not remove timeout: {e}")
        if removed_any:
            await ctx.send(f"🔊 {member.mention} has been unmuted.")
        else:
            await ctx.send(f"ℹ️ {member.mention} is not muted.")

    @commands.command(name="checktm")
    @commands.has_permissions(moderate_members=True)
    async def checktimeout(self, ctx, member: discord.Member = None):
        if not member:
            return await ctx.send("**Usage:** `!!checktm` `<mention>`")
        if member.timed_out_until is None:
            await ctx.send(f"{member.display_name} is not timed out.")
        else:
            now = datetime.now(timezone.utc)
            remaining = member.timed_out_until - now

            if remaining.total_seconds() <= 0:
                await ctx.send(f"{member.display_name}'s timeout has already expired.")
            else:
                hours, remainder = divmod(int(remaining.total_seconds()), 3600)
                minutes, _ = divmod(remainder, 60)

                await ctx.send(
                    f"{member.display_name} is timed out for another {hours}h {minutes}m."
                )

    @commands.command(name="tmlist")
    @commands.has_permissions(moderate_members=True)
    async def timeout_list(self, ctx):

        tm_members = [member for member in ctx.guild.members 
                      if member.timed_out_until and member.timed_out_until > datetime.now(timezone.utc)]
        embed = discord.Embed(
        title="🔇 Timed-out Members",
        color=discord.Color.red()
        )

        if tm_members:
            desc = ""
            for m in tm_members:
                rem = m.timed_out_until - datetime.now(timezone.utc)
                hours, reminder = divmod(int(rem.total_seconds()),3600)
                minutes, _ = divmod(reminder,60)
                desc += (f"{m.mention} = {hours}h {minutes}m remaining\n")
            embed.description = desc
        else:
            embed.description = "✅ No one currently has the Timed-out."

        await ctx.send(embed=embed)

    @commands.command(name="mutelist")
    @commands.has_permissions(moderate_members=True)
    async def mute_list(self, ctx):
        """Show all members who have the Muted role."""
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")

        if not muted_role:
            return await ctx.send("⚠️ No 'Muted' role exists in this server.")

        muted_members = [member.mention for member in muted_role.members]

        embed = discord.Embed(
        title="🔇 Muted Members",
        color=discord.Color.red()
        )

        if muted_members:
            embed.description = "\n".join(muted_members)
        else:
            embed.description = "✅ No one currently has the Muted role."

        await ctx.send(embed=embed)

    # Server info
    @commands.command(name="serverinfo")
    async def serverinfo(self, ctx):
        guild = ctx.guild
        embed = discord.Embed(
            title=f"ℹ️ Server Info - {guild.name}",
            color=discord.Color.blue()
        )
        embed.add_field(name="👑 Owner", value=await self.bot.fetch_user(guild.owner_id), inline=False)
        embed.add_field(name="👥 Members", value=guild.member_count, inline=False)
        embed.add_field(name="📅 Created On", value=guild.created_at.strftime("%Y-%m-%d"), inline=False)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        await ctx.send(embed=embed)

class Restrictor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.restricted_mentions = {"global": set(), "channel": {}}  # store user IDs who are restricted

    @commands.command(name="rtmentions")
    @commands.has_permissions(administrator=True)
    async def restrict_mentions(self, ctx, member: discord.Member=None, scope : str = None):
        if not member:
            await ctx.send(">>> **Usage:** `!!rtmentions <mention>`")
            return
        if member == ctx.author:
            await ctx.send("You cannot restrict Yourself")
            return

        if scope and scope.lower() == "all":
            if member.id in self.restricted_mentions["global"]:
                return await ctx.send(f"{member.mention} is already restricted from mentioning anyone in all channels")
            self.restricted_mentions["global"].add(member.id)
            return await ctx.send(f"🚫 {member.mention} is now restricted from mentioning anyone in all channels.")
        else:
            channel_id = ctx.channel.id
            if channel_id not in self.restricted_mentions["channel"]:
                self.restricted_mentions["channel"][channel_id] = set()
            if member.id in self.restricted_mentions["global"]:
                return await ctx.send(f"{member.mention} is already restricted from mentioning anyone in all channels")
            if member.id in self.restricted_mentions["channel"][channel_id]:
                return await ctx.send(f"{member.mention} is already restricted from mentioning in this channel")
            self.restricted_mentions["channel"][channel_id].add(member.id)
            await ctx.send(f"🚫 {member.mention} is now restricted from mentioning anyone in this channel.")

    @commands.command(name="alwmentions")
    @commands.has_permissions(administrator=True)
    async def allow_mentions(self, ctx, member: discord.Member=None):
        if not member:
            return await ctx.send("**Usaga:** `!!alwmentions <mention>`")
        if member == ctx.author:
            return await ctx.send("You cannot use this command on yourself")
        channel_id = ctx.channel.id
        user_id = member.id
        globally_restricted = user_id in self.restricted_mentions["global"]
        channel_restricted = user_id in self.restricted_mentions["channel"].get(channel_id, set())

        if not globally_restricted and not channel_restricted:
            return await ctx.send("This user is already allowed to mention others")

        if globally_restricted:
            self.restricted_mentions["global"].discard(user_id)

        if channel_restricted:
            self.restricted_mentions["channel"][channel_id].discard(user_id)

        await ctx.send(f"✅ {member.mention} can mention again.")

    @commands.command(name="chkrtmentions")
    @commands.has_permissions(administrator=True)
    async def checkrt_mentions(self,ctx, member : discord.Member = None):
        if not member:
            return await ctx.send("**Usage:** `chkrtmentions <mention>`")
        user_id = member.id
        restricted_channels = []
        if user_id in self.restricted_mentions["global"]:
            return await ctx.send(f"{member.mention}is restricted from mentioning anyone in all channels")
        for channel_id, users in self.restricted_mentions["channel"].items():
            if user_id in users:
                restricted_channels.append(f"<#{channel_id}>")
        if restricted_channels:
            channels_text = "\n".join(restricted_channels)
            return await ctx.send(f"🚫 {member.mention} is restricted from mentioning anyone in: \n{channels_text}")
        await ctx.send(f"{member.mention} has no restriction from mentioning")

    @commands.command(name="rtdmentionslist")
    @commands.has_permissions(administrator=True)
    async def rtdmnlist(self, ctx, scope = None):
        if not scope:
            return await ctx.send("**Usage:** `rtdmentionlist <channel/global>`")

        if scope.lower() in ["global","g"]:
            if not self.restricted_mentions["global"]:
                return await ctx.send("No users are globally restricted from mentioning")
            rt_users_g = [f"<@{user}>" for user in self.restricted_mentions["global"]]
            return await ctx.send("🚫 Globally restricted users:\n" + "\n".join(rt_users_g))
        
        if scope.lower() in ["channel","c"]:
            if not self.restricted_mentions["channel"]:
                return await ctx.send("No users are channel restricted.")
            msg_lines = []
            for channel_id, user_ids in self.restricted_mentions["channel"].items():
                if user_ids:
                    users = [f"<@{u}>" for u in user_ids]
                    msg_lines.append(f"📌 <#{channel_id}>:\n" + "\n".join(users))

            if msg_lines:
                return await ctx.send("🚫 Channel restrictions:\n\n" + "\n\n".join(msg_lines))
            else:
                return await ctx.send("No users are channel restricted.")
        
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        
        user_id = message.author.id
        channel_id = message.channel.id

        globally_restricted = user_id in self.restricted_mentions.get("global", set())
        channel_restricted = user_id in self.restricted_mentions.get("channel", {}).get(channel_id, set())

        if (globally_restricted or channel_restricted) and (
        message.mentions or message.role_mentions or message.mention_everyone
        ):
            await message.delete()

async def setup(bot):
    await bot.add_cog(member(bot))
    await bot.add_cog(Restrictor(bot))
