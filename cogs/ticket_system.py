import discord
import asyncio
import pytz
import json
import sqlite3
from datetime import datetime
import chat_exporter
import io
from discord.ext import commands

with open("config.json", mode="r") as config_file:
    config = json.load(config_file)

GUILD_ID = config["guild_id"]
TICKET_CHANNEL = config["ticket_channel_id"] 
CATEGORY_ID1 = config["category_id_1"]
CATEGORY_ID2 = config["category_id_2"] 
TEAM_ROLE1 = config["admin_role_id"] 
TEAM_ROLE2 = config["support_team_role_id"]
LOG_CHANNEL = config["log_channel_id"]
TIMEZONE = config["timezone"]
EMBED_TITLE = config["embed_title"]
EMBED_DESCRIPTION = config["embed_description"]

conn = sqlite3.connect('Database.db')
cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS ticket 
           (id INTEGER PRIMARY KEY AUTOINCREMENT, discord_name TEXT, discord_id INTEGER, ticket_channel TEXT, ticket_created TIMESTAMP)""")
conn.commit()

class TicketSystem(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'TicketSystem cog loaded successfully')
        self.bot.add_view(TicketMenu(bot=self.bot))
        self.bot.add_view(CloseTicket(bot=self.bot))
        self.bot.add_view(TicketActions(bot=self.bot))

    @commands.Cog.listener()
    async def on_bot_shutdown():
        cur.close()
        conn.close()

class TicketMenu(discord.ui.View):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(timeout=None)

    @discord.ui.select(
        custom_id="support",
        placeholder="Select ticket type",
        options=[
            discord.SelectOption(
                label="Requests",
                description="Get help here",
                emoji="❓",
                value="support1"
            ),
            discord.SelectOption(
                label="Support",
                description="Ask questions here",
                emoji="📛",
                value="support2"
            )
        ]
    )
    async def callback(self, select, interaction):
        await interaction.response.defer()
        timezone = pytz.timezone(TIMEZONE)
        creation_date = datetime.now(timezone).strftime('%Y-%m-%d %H:%M:%S')
        user_name = interaction.user.name
        user_id = interaction.user.id

        cur.execute("SELECT discord_id FROM ticket WHERE discord_id=?", (user_id,))
        existing_ticket = cur.fetchone()

        if existing_ticket is not None:
            embed = discord.Embed(title="You already have an open ticket", color=0xff0000)
            await interaction.followup.send(embed=embed, ephemeral=True)
            embed = discord.Embed(title=EMBED_TITLE, description=EMBED_DESCRIPTION, color=discord.colour.Color.blue())
            await interaction.message.edit(embed=embed, view=TicketMenu(bot=self.bot))
            return

        if interaction.channel.id != TICKET_CHANNEL:
            return

        selected_option = interaction.data['values'][0]
        guild = self.bot.get_guild(GUILD_ID)

        cur.execute("INSERT INTO ticket (discord_name, discord_id, ticket_created) VALUES (?, ?, ?)", 
                   (user_name, user_id, creation_date))
        conn.commit()
        
        await asyncio.sleep(1)
        cur.execute("SELECT id FROM ticket WHERE discord_id=?", (user_id,))
        ticket_number = cur.fetchone()[0]

        if selected_option == "support1":
            category = self.bot.get_channel(CATEGORY_ID1)
            team_role = TEAM_ROLE1
            welcome_message = f'Welcome {interaction.user.mention},\ndescribe your Problem and our Support will help you soon.'
        else:
            category = self.bot.get_channel(CATEGORY_ID2)
            team_role = TEAM_ROLE2
            welcome_message = f'Welcome {interaction.user.mention},\nhow can i help you?'

        ticket_channel = await guild.create_text_channel(
            f"ticket-{ticket_number}", 
            category=category,
            topic=f"{interaction.user.id}"
        )

        await ticket_channel.set_permissions(
            guild.get_role(team_role), 
            send_messages=True, read_messages=True, add_reactions=False,
            embed_links=True, attach_files=True, read_message_history=True,
            external_emojis=True
        )
        await ticket_channel.set_permissions(
            interaction.user, 
            send_messages=True, read_messages=True, add_reactions=False,
            embed_links=True, attach_files=True, read_message_history=True,
            external_emojis=True
        )
        await ticket_channel.set_permissions(
            guild.default_role, 
            send_messages=False, read_messages=False, view_channel=False
        )
        
        embed = discord.Embed(description=welcome_message, color=discord.colour.Color.blue())
        await ticket_channel.send(embed=embed, view=CloseTicket(bot=self.bot))

        channel_id = ticket_channel.id
        cur.execute("UPDATE ticket SET ticket_channel = ? WHERE id = ?", (channel_id, ticket_number))
        conn.commit()

        embed = discord.Embed(description=f'📬 Ticket created: {ticket_channel.mention}', color=discord.colour.Color.green())
        await interaction.followup.send(embed=embed, ephemeral=True)
        
        embed = discord.Embed(title=EMBED_TITLE, description=EMBED_DESCRIPTION, color=discord.colour.Color.blue())
        await interaction.message.edit(embed=embed, view=TicketMenu(bot=self.bot))

class CloseTicket(discord.ui.View):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(timeout=None)

    @discord.ui.button(label="Delete Ticket 🎫", style=discord.ButtonStyle.blurple, custom_id="close")
    async def close(self, button: discord.ui.Button, interaction: discord.Interaction):
        embed = discord.Embed(title="Delete Ticket 🎫", description="Confirm ticket deletion", color=discord.colour.Color.green())
        await interaction.response.send_message(embed=embed, view=TicketActions(bot=self.bot))
        await interaction.message.edit(view=self)

class TicketActions(discord.ui.View):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(timeout=None)

    @discord.ui.button(label="Delete Ticket 🎫", style=discord.ButtonStyle.red, custom_id="delete")
    async def delete_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        guild = self.bot.get_guild(GUILD_ID)
        log_channel = self.bot.get_channel(LOG_CHANNEL)
        ticket_id = interaction.channel.id

        cur.execute("SELECT id, discord_id, ticket_created FROM ticket WHERE ticket_channel=?", (ticket_id,))
        ticket_data = cur.fetchone()
        id, ticket_creator_id, ticket_created = ticket_data
        ticket_creator = guild.get_member(ticket_creator_id)

        ticket_created_unix = self.convert_to_unix_timestamp(ticket_created)
        timezone = pytz.timezone(TIMEZONE)
        ticket_closed = datetime.now(timezone).strftime('%Y-%m-%d %H:%M:%S')
        ticket_closed_unix = self.convert_to_unix_timestamp(ticket_closed)

        military_time = True
        transcript = await chat_exporter.export(interaction.channel, limit=200, tz_info=TIMEZONE, military_time=military_time, bot=self.bot)
        
        transcript_file = discord.File(
            io.BytesIO(transcript.encode()),
            filename=f"transcript-{interaction.channel.name}.html")
        transcript_file2 = discord.File(
            io.BytesIO(transcript.encode()),
            filename=f"transcript-{interaction.channel.name}.html")
        
        embed = discord.Embed(description='Ticket deleting in 5 seconds', color=0xff0000)
        transcript_info = discord.Embed(title=f"Ticket Deleted | {interaction.channel.name}", color=discord.colour.Color.blue())
        transcript_info.add_field(name="ID", value=id, inline=True)
        transcript_info.add_field(name="Opened by", value=ticket_creator.mention, inline=True)
        transcript_info.add_field(name="Closed by", value=interaction.user.mention, inline=True)
        transcript_info.add_field(name="Ticket Created", value=f"<t:{ticket_created_unix}:f>", inline=True)
        transcript_info.add_field(name="Ticket Closed", value=f"<t:{ticket_closed_unix}:f>", inline=True)

        await interaction.response.send_message(embed=embed)
        try:
            await ticket_creator.send(embed=transcript_info, file=transcript_file)
        except:
            transcript_info.add_field(name="Error", value="Could not DM ticket creator", inline=True)

        await log_channel.send(embed=transcript_info, file=transcript_file2)
        await asyncio.sleep(3)
        await interaction.channel.delete(reason="Ticket deleted")
        cur.execute("DELETE FROM ticket WHERE discord_id=?", (ticket_creator_id,))
        conn.commit()

    def convert_to_unix_timestamp(self, date_string):
        date_format = "%Y-%m-%d %H:%M:%S"
        dt_obj = datetime.strptime(date_string, date_format)
        berlin_tz = pytz.timezone('Europe/Berlin')
        dt_obj = berlin_tz.localize(dt_obj)
        dt_obj_utc = dt_obj.astimezone(pytz.utc)
        return int(dt_obj_utc.timestamp())