import discord
from discord.ext import commands
from discord.commands import Option
import json
import asyncio

with open("config.json", mode="r") as config_file:
    config = json.load(config_file)

TEAM_ROLE = config["admin_role_id"]

class ClearChannel(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'ClearChannel cog loaded successfully')

    def has_team_role():
        async def predicate(ctx):
            if ctx.author.guild_permissions.administrator:
                return True
            team_role = ctx.guild.get_role(TEAM_ROLE)
            return team_role in ctx.author.roles
        return commands.check(predicate)

    class ConfirmView(discord.ui.View):
        def __init__(self, bot, author, amount):
            super().__init__(timeout=30)
            self.bot = bot
            self.author = author
            self.amount = amount
            self.value = None

        @discord.ui.button(label='✅ Confirm', style=discord.ButtonStyle.green)
        async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
            if interaction.user != self.author:
                await interaction.response.send_message("You are not authorized to confirm this action.", ephemeral=True)
                return
            
            self.value = True
            self.stop()
            deleted = 0
            try:
                if self.amount == "all":
                    def not_pinned(msg):
                        return not msg.pinned
                    
                    while True:
                        messages = await interaction.channel.purge(limit=100, check=not_pinned)
                        if len(messages) == 0:
                            break
                        deleted += len(messages)
                        await asyncio.sleep(1)
                else:
                    amount = int(self.amount)
                    if amount > 100:
                        amount = 100
                    
                    def not_pinned(msg):
                        return not msg.pinned
                    
                    messages = await interaction.channel.purge(limit=amount + 1, check=not_pinned) 
                    deleted = len(messages) - 1
                success_embed = discord.Embed(
                    description=f"✅ Successfully cleared **{deleted}** messages from {interaction.channel.mention}",
                    color=discord.Colour.green()
                )
                success_message = await interaction.response.edit_message(embed=success_embed, view=None)
                
                await asyncio.sleep(5)
                try:
                    await success_message.delete()
                except:
                    pass
                    
            except Exception as e:
                error_embed = discord.Embed(
                    description=f"❌ Error clearing messages: {str(e)}",
                    color=discord.Colour.red()
                )
                await interaction.response.edit_message(embed=error_embed, view=None)

        @discord.ui.button(label='❌ Cancel', style=discord.ButtonStyle.red)
        async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
            if interaction.user != self.author:
                await interaction.response.send_message("You are not authorized to cancel this action.", ephemeral=True)
                return
            
            self.value = False
            self.stop()
            
            cancel_embed = discord.Embed(
                description="❌ Channel clearing cancelled",
                color=discord.Colour.red()
            )
            await interaction.response.edit_message(embed=cancel_embed, view=None)

        async def on_timeout(self):
            if self.value is None:
                timeout_embed = discord.Embed(
                    description="⏰ Confirmation timed out",
                    color=discord.Colour.orange()
                )
                try:
                    await self.message.edit(embed=timeout_embed, view=None)
                except:
                    pass

    @commands.slash_command(name="clear", description="Clear messages from channel")
    @commands.guild_only()
    @commands.check_any(commands.has_permissions(administrator=True), has_team_role())
    async def clear(self, ctx,
                   amount: Option(str, description="Number of messages to clear or 'all'", required=True, choices=["1", "5", "10", "25", "50", "100", "all"])):
        
        embed = discord.Embed(
            title="🚨 Clear Channel Confirmation",
            description=f"You are about to clear messages from {ctx.channel.mention}",
            color=discord.Colour.orange()
        )
        
        if amount == "all":
            embed.add_field(
                name="Action",
                value="Clear **ALL** messages from this channel (except pinned)",
                inline=False
            )
            embed.add_field(
                name="Warning",
                value="This action cannot be undone!",
                inline=False
            )
        else:
            embed.add_field(
                name="Action",
                value=f"Clear **{amount}** messages from this channel",
                inline=False
            )
        
        embed.add_field(
            name="Channel",
            value=ctx.channel.mention,
            inline=True
        )
        embed.add_field(
            name="Requested by",
            value=ctx.author.mention,
            inline=True
        )
        
        embed.set_footer(text="This confirmation will timeout in 30 seconds")
        
        view = self.ConfirmView(self.bot, ctx.author, amount)
        message = await ctx.respond(embed=embed, view=view)
        view.message = message

    @commands.slash_command(name="clear_user", description="Clear messages from a specific user")
    @commands.guild_only()
    @commands.check_any(commands.has_permissions(administrator=True), has_team_role())
    async def clear_user(self, ctx,
                        user: Option(discord.Member, description="User whose messages to clear", required=True),
                        amount: Option(int, description="Number of messages to clear", required=True, min_value=1, max_value=100)):
        
        embed = discord.Embed(
            title="🚨 Clear User Messages Confirmation",
            description=f"You are about to clear messages from {user.mention}",
            color=discord.Colour.orange()
        )
        
        embed.add_field(
            name="Action",
            value=f"Clear **{amount}** messages from {user.mention}",
            inline=False
        )
        embed.add_field(
            name="Channel",
            value=ctx.channel.mention,
            inline=True
        )
        embed.add_field(
            name="Requested by",
            value=ctx.author.mention,
            inline=True
        )
        
        embed.set_footer(text="This confirmation will timeout in 30 seconds")
        
        view = self.ConfirmViewUser(self.bot, ctx.author, user, amount)
        message = await ctx.respond(embed=embed, view=view)
        view.message = message

    class ConfirmViewUser(discord.ui.View):
        def __init__(self, bot, author, user, amount):
            super().__init__(timeout=30)
            self.bot = bot
            self.author = author
            self.user = user
            self.amount = amount
            self.value = None

        @discord.ui.button(label='✅ Confirm', style=discord.ButtonStyle.green)
        async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
            if interaction.user != self.author:
                await interaction.response.send_message("You are not authorized to confirm this action.", ephemeral=True)
                return
            
            self.value = True
            self.stop()
            deleted = 0
            try:
                def is_user_message(msg):
                    return msg.author == self.user and not msg.pinned
                
                messages = await interaction.channel.purge(limit=self.amount, check=is_user_message)
                deleted = len(messages)
                
                success_embed = discord.Embed(
                    description=f"✅ Successfully cleared **{deleted}** messages from {self.user.mention}",
                    color=discord.Colour.green()
                )
                success_message = await interaction.response.edit_message(embed=success_embed, view=None)
                
                await asyncio.sleep(5)
                try:
                    await success_message.delete()
                except:
                    pass
                    
            except Exception as e:
                error_embed = discord.Embed(
                    description=f"❌ Error clearing messages: {str(e)}",
                    color=discord.Colour.red()
                )
                await interaction.response.edit_message(embed=error_embed, view=None)

        @discord.ui.button(label='❌ Cancel', style=discord.ButtonStyle.red)
        async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
            if interaction.user != self.author:
                await interaction.response.send_message("You are not authorized to cancel this action.", ephemeral=True)
                return
            
            self.value = False
            self.stop()
            
            cancel_embed = discord.Embed(
                description="❌ User message clearing cancelled",
                color=discord.Colour.red()
            )
            await interaction.response.edit_message(embed=cancel_embed, view=None)

        async def on_timeout(self):
            if self.value is None:
                timeout_embed = discord.Embed(
                    description="⏰ Confirmation timed out",
                    color=discord.Colour.orange()
                )
                try:
                    await self.message.edit(embed=timeout_embed, view=None)
                except:
                    pass