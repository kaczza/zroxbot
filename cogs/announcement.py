import discord
from discord.ext import commands
from discord.commands import Option
import json

with open("config.json", mode="r") as config_file:
    config = json.load(config_file)

OWNER_ROLE_ID = config.get("owner_role_id")
ANNOUNCE_CHANNEL_ID = config.get("announce_channel_id")

class Announcement(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Announcement cog loaded successfully')

    def is_owner():
        async def predicate(ctx):
            if ctx.author.guild_permissions.administrator:
                return True
            if OWNER_ROLE_ID:
                owner_role = ctx.guild.get_role(OWNER_ROLE_ID)
                return owner_role in ctx.author.roles
            return False
        return commands.check(predicate)

    @commands.slash_command(name="announce", description="Make an announcement")
    @commands.guild_only()
    @commands.check(is_owner())
    async def announce(self, ctx,
                      title: Option(str, description="Announcement title", required=True),
                      message: Option(str, description="Announcement message", required=True),
                      ping: Option(str, description="Ping everyone?", required=False, choices=["Yes", "No"], default="No")):
        
        announce_channel = self.bot.get_channel(ANNOUNCE_CHANNEL_ID)
        if not announce_channel:
            embed = discord.Embed(
                description="❌ Announce channel not found. Please check the configuration.",
                color=discord.Colour.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        try:
            embed = discord.Embed(
                title=f"📢 {title}",
                description=message,
                color=discord.Colour.gold(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text=f"Announced by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)

            if ping == "Yes":
                content = "@everyone"
            else:
                content = None

            await announce_channel.send(content=content, embed=embed)
            
            success_embed = discord.Embed(
                description=f"✅ Announcement sent to {announce_channel.mention}",
                color=discord.Colour.green()
            )
            await ctx.respond(embed=success_embed, ephemeral=True)

        except Exception as e:
            error_embed = discord.Embed(
                description=f"❌ Error sending announcement: {str(e)}",
                color=discord.Colour.red()
            )
            await ctx.respond(embed=error_embed, ephemeral=True)

    @commands.slash_command(name="announce_embed", description="Make an announcement with custom embed color")
    @commands.guild_only()
    @commands.check(is_owner())
    async def announce_embed(self, ctx,
                           title: Option(str, description="Announcement title", required=True),
                           message: Option(str, description="Announcement message", required=True),
                           color: Option(str, description="Embed color (hex code)", required=False, default="#FFD700")):
        
        announce_channel = self.bot.get_channel(ANNOUNCE_CHANNEL_ID)
        if not announce_channel:
            embed = discord.Embed(
                description="❌ Announce channel not found. Please check the configuration.",
                color=discord.Colour.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        try:
            color_value = discord.Colour.from_str(color)
            
            embed = discord.Embed(
                title=f"📢 {title}",
                description=message,
                color=color_value,
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text=f"Announced by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)

            await announce_channel.send(embed=embed)
            
            success_embed = discord.Embed(
                description=f"✅ Announcement sent to {announce_channel.mention}",
                color=discord.Colour.green()
            )
            await ctx.respond(embed=success_embed, ephemeral=True)

        except ValueError:
            error_embed = discord.Embed(
                description="❌ Invalid color format. Please use hex format (e.g., #FF0000 for red).",
                color=discord.Colour.red()
            )
            await ctx.respond(embed=error_embed, ephemeral=True)
        except Exception as e:
            error_embed = discord.Embed(
                description=f"❌ Error sending announcement: {str(e)}",
                color=discord.Colour.red()
            )
            await ctx.respond(embed=error_embed, ephemeral=True)