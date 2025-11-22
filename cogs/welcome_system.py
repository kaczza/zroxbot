import discord
from discord.ext import commands
import json

with open("config.json", mode="r") as config_file:
    config = json.load(config_file)

WELCOME_CHANNEL = config.get("welcome_channel_id")
SERVER_ID = config["guild_id"]

class WelcomeSystem(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'WelcomeSystem cog loaded successfully')

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id != SERVER_ID:
            return

        welcome_channel = self.bot.get_channel(WELCOME_CHANNEL)
        if not welcome_channel:
            return

        embed = discord.Embed(
            title="🎉 Welcome to the Server!",
            description=f"Hello {member.mention}, welcome to **{member.guild.name}**!",
            color=discord.Colour.green()
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(
            name="Member Count",
            value=f"You are member #{member.guild.member_count}",
            inline=True
        )
        embed.add_field(
            name="Account Created",
            value=f"<t:{int(member.created_at.timestamp())}:R>",
            inline=True
        )
        embed.set_footer(text="Enjoy your stay!")

        await welcome_channel.send(embed=embed)

        try:
            welcome_dm = discord.Embed(
                title=f"Welcome to {member.guild.name}!",
                description="Thanks for joining our server! Please read the rules and enjoy your time here.",
                color=discord.Colour.blue()
            )
            await member.send(embed=welcome_dm)
        except:
            pass 

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.guild.id != SERVER_ID:
            return

        welcome_channel = self.bot.get_channel(WELCOME_CHANNEL)
        if not welcome_channel:
            return

        embed = discord.Embed(
            title="👋 Goodbye!",
            description=f"**{member.display_name}** has left the server.",
            color=discord.Colour.red()
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(
            name="Member Count",
            value=f"Now we have {member.guild.member_count} members",
            inline=True
        )
        embed.add_field(
            name="Joined Server",
            value=f"<t:{int(member.joined_at.timestamp())}:R>" if member.joined_at else "Unknown",
            inline=True
        )
        embed.set_footer(text="We'll miss you!")

        await welcome_channel.send(embed=embed)