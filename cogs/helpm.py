import discord
from discord.ext import commands
class Help(commands.Cog):
    def __init__(self, bot):
            self.bot = bot

    @commands.command(name="help")
    async def help(self, ctx):
        embed = discord.Embed(
            title="**Help Center**",
            description="Fujiwara's available commands",
            color=discord.Color.dark_red()
        )

        embed.add_field(
            name="",
            value=(
            "**`!!about`** → Learn more about Fujiwara and its features\n\n"
            "**`!!moderation`** → Tools for managing members\n\n"
            "**`!!chmod`** → Channel Moderation commands\n\n"
            "**`!!actions`** → Fun interaction GIFs\n\n"
            "**`!!games`** → Play mini-games\n"),
            inline=False
        )
        await ctx.send(embed=embed)
        return
        

class About(commands.Cog):
    def __init__(self,bot):
          self.bot = bot
    @commands.command(name="about")
    async def about(self,ctx):
          
        embed = discord.Embed(
            title="**Chika Fujiwara**",
            description="Hey there! I’m **Fujiwara**, here to make your server more fun and easier to manage.\n\n"
                    "✨ Features:\n\n"
                    "• Smart moderation tools for channels & members 🔧\n"
                    "• Interactive action GIFs\n"
                    "• Play fun mini-games \n\n"
                    "Type `!!help` anytime to see my full command list!",
            color=discord.Color.blue()
        )
        embed.set_image(url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExaWVnZWJxeWUwOXBpaWRxZmlodGxyYmUxemF0M3M0bDk0a2E0OGNiMCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/RLJxQtX8Hs7XytaoyX/giphy.gif")
        await ctx.send(embed=embed)
        return
    
    @commands.command(name="actions")
    async def actions(self,ctx):
        embed = discord.Embed(
                title="**Action Center**",
                description="Here are my available action commands",
                color=discord.Color.magenta()
            )
        embed.add_field(
            name="**WWE**",
            value=("`rko` `spear` `chokeslam` `stunner` `f5` `pedigree` `suplex` `619` `aa` `tombstone` `submission` `supermanpunch`"),
            inline=False
            )
        embed.add_field(
            name="**Anime**",
            value=(
                  "`rasengan` `fireball` `amaterasu` `genjutsu` "
                  "`chidori` `kamehameha` `bankai` " 
                  "`pistol` `hk` `gatling` `sus`"),
                  inline=False
            )
        await ctx.send(embed=embed)
        return

    @commands.command(name="games")
    async def games(self,ctx):
        embed= discord.Embed(
            title="<a:con:1424357189212045313> **Games Center** <a:con:1424357189212045313>",
            description="Here are the games available",
            color=discord.Color.orange()
        )
        embed.add_field(
              name="<a:cf:1424302645945958461> **Coinflip**",
              value=(">>> Flip a coin and see if it lands on Heads or Tails\n" 
                     "`!!coinflip` `<t/h>`"),
                     inline= False
        )
        embed.add_field(
              name="<a:rps:1424365374048043190> **Rock paper Scissors**",
              value=">>> Test your luck in Rock–Paper–Scissors!\n"
                    "`!!rps` `<rock/paper/scissors>` → play vs bot\n"
                    "`!!rps` `<mention>` → challange a friend",
                    inline=False

        )
        embed.add_field(
              name="<a:num:1424363626646470726> **Guess the Number**",
              value=">>> Find the hidden number within the range\n"
              "`!!startguess` or `!!stg` `[min]` `[max]` `[chances]` → Start a new game\n"
              "`!!stopguess` or `!!spg` → Stop a running game\n"
              "`!!guesslb` → Guess the number Leaderboard\n",
              inline=False
        )
        embed.add_field(
              name="<a:word:1424366180126294026> **wordle**",
              value=(">>> "
                "Solve the 5-letter word puzzle\n"
              "`!!wordle` → Start the wordle game\n"
              "`!!stopwordle` → Stop a running game\n" 
              "`!!wordleboard` → Wordle Leaderboard\n"
              
              ),
              inline=False

        )
        await ctx.send(embed=embed)
        return
    
    @commands.command("moderation",aliases=["mod"])
    async def mod(self,ctx):
          emoji = "<a:row:1428010352146120744>"
          embed=discord.Embed(
                title="**Moderation Commands** <a:mod:1424455974613155961>",
                description= "Here are the General moderation commands",
                color=discord.Color.from_rgb(r=94,g=84,b=142)
          )
          embed.add_field(
               name="",
               value=f"{emoji} **kick** `<mention>`\n\n"
               f"{emoji} **ban** `<mention>`\n\n"
               f"{emoji} **unban** `<user ID/username>`\n\n"
               f"{emoji} **banlist**\n\n"
               f"{emoji} **mute** `<mention>` `[reason]`\n\n"
               f"{emoji} **unmute** `<mention>` \n\n"
               f"{emoji} **mutelist** \n\n"
               f"{emoji} **checkmute** `<mention>` \n\n"
               f"{emoji} **tm** `<mention>` `[duration]` `[reason]`\n\n"
               f"{emoji} **rmtm** `<mention>`\n\n"
               f"{emoji} **tmlist** \n\n"
               f"{emoji} **checktm** `<mention>`\n\n",
               inline=False
          )
          await ctx.send(embed=embed)

    @commands.command("chmod")
    async def chmod(self,ctx):
          emoji = "<a:row:1428010352146120744>"
          embed=discord.Embed(
                title="**Channel Moderation** <a:mod:1424455974613155961>",
                description= "Here are the Channel Moderation Commands",
                color=discord.Color.from_rgb(r=94,g=84,b=142)
          )
          embed.add_field(
               name="",
               value=f"{emoji} **lockchannel** `[channel id]`\n\n"
               f"{emoji} **unlockchannel** `[channel id]`\n\n"
               f"{emoji} **mutechannel** `[duration]`\n\n"
               f"{emoji} **unmutechannel**\n\n"
               f"{emoji} **lockthread** \n\n"
               f"{emoji} **unlockthread** \n\n"
               f"{emoji} **mutethread** \n\n"
               f"{emoji} **unmutethread**  \n\n"
               f"{emoji} **mediaonly** \n\n"
               f"{emoji} **dbmediaonly** \n\n"
               f"{emoji} **textonly** \n\n"
               f"{emoji} **dbtextonly** \n\n"
               f"{emoji} **setpinmsg** `<message>`\n\n"
               f"{emoji} **rmpinmsg** \n\n"
               f"{emoji} **clearmsg** `<message count>`\n\n"
               f"{emoji} **clearmsguser** `<mention>` `<message count>`\n\n"
               f"{emoji} **dbgif** \n\n"
               f"{emoji} **ebgif**\n\n"
               f"{emoji} **cleargif** [message limit]"
               f"{emoji} **clearmedia** [message limit]",
               inline=False
          )
          await ctx.send(embed=embed)


async def setup(bot):
      await bot.add_cog(Help(bot))
      await bot.add_cog(About(bot))