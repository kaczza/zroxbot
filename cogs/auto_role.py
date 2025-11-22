import discord
from discord.ext import commands
import json

with open("config.json", mode="r") as config_file:
    config = json.load(config_file)

AUTO_ROLE_ENABLED = config.get("auto_role_enabled", False)
AUTO_ROLE_ID = config.get("auto_role_id")

class AutoRole(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'AutoRole cog loaded successfully - Enabled: {AUTO_ROLE_ENABLED}')

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if not AUTO_ROLE_ENABLED:
            return
        
        if not AUTO_ROLE_ID:
            return
        
        try:
            role = member.guild.get_role(AUTO_ROLE_ID)
            if role:
                await member.add_roles(role)
                print(f"Auto role assigned to {member.name}")
        except Exception as e:
            print(f"Error assigning auto role: {e}")