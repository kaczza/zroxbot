import discord
import json
import asyncio
from discord.ext import commands, tasks
from cogs.ticket_system import TicketSystem
from cogs.ticket_commands import TicketCommands
from cogs.mod_commands import ModCommands
from cogs.welcome_system import WelcomeSystem
from cogs.clear_channel import ClearChannel
from cogs.auto_role import AutoRole
from cogs.announcement import Announcement

with open("config.json", "r") as config_file:
    settings = json.load(config_file)

TOKEN = settings["token"]
SERVER_ID = settings["guild_id"]
TICKET_CATEGORY_1 = settings["category_id_1"]
TICKET_CATEGORY_2 = settings["category_id_2"]

client = commands.Bot(intents=discord.Intents.all())

@client.event
async def on_ready():
    print(f"Bot started: {client.user.display_name}")
    await status_update_loop.start()

@tasks.loop(minutes=1)
async def status_update_loop():
    server = client.get_guild(SERVER_ID)
    category_one = discord.utils.get(server.categories, id=int(TICKET_CATEGORY_1))
    category_two = discord.utils.get(server.categories, id=int(TICKET_CATEGORY_2))
    
    total_tickets = len(category_one.channels) + len(category_two.channels)
    
    await client.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"Open src on github"
        )
    )

client.add_cog(TicketSystem(client))
client.add_cog(TicketCommands(client))
client.add_cog(ModCommands(client))
client.add_cog(WelcomeSystem(client))
client.add_cog(ClearChannel(client))
client.add_cog(AutoRole(client))
client.add_cog(Announcement(client))
if __name__ == "__main__":
    client.run(TOKEN)