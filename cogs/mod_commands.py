import discord
from discord.ext import commands
from discord.commands import Option
import json
import datetime
import re
import asyncio

with open("config.json", mode="r") as config_file:
    config = json.load(config_file)

TEAM_ROLE = config["admin_role_id"]
LOG_CHANNEL = config["log_channel_id"]
MUTE_ROLE_ID = config.get("mute_role_id")

ANTI_CAPS_ENABLED = config.get("anti_caps_enabled", False)
CAPS_PERCENTAGE = config.get("caps_percentage", 80)
MIN_MESSAGE_LENGTH = config.get("min_message_length", 10)
ANTI_LINKS_ENABLED = config.get("anti_links_enabled", False)
ALLOWED_LINKS_CHANNELS = config.get("allowed_links_channels", [])
ALLOWED_DOMAINS = config.get("allowed_domains", ["discord.com", "discord.gg"])

class ModCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.muted_users = {}  

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'ModCommands cog loaded successfully')
        print(f'Anti-caps: {ANTI_CAPS_ENABLED}, Anti-links: {ANTI_LINKS_ENABLED}')
        print(f'Mute role ID: {MUTE_ROLE_ID}')

    def has_team_role():
        async def predicate(ctx):
            if ctx.author.guild_permissions.administrator:
                return True
            team_role = ctx.guild.get_role(TEAM_ROLE)
            return team_role in ctx.author.roles
        return commands.check(predicate)
    
    async def is_excessive_caps(self, text):
        """Ellenőrzi, hogy az üzenet túl sok nagybetűt tartalmaz-e"""
        text = re.sub(r'http\S+', '', text)
        text = re.sub(r'`[^`]*`', '', text)
        text = re.sub(r'\*\*[^*]*\*\*', '', text)
        text = re.sub(r'\*[^*]*\*', '', text)
        
        letters = [char for char in text if char.isalpha()]
        
        if len(letters) < MIN_MESSAGE_LENGTH:
            return False
        
        if not letters:
            return False
        
        upper_count = sum(1 for char in letters if char.isupper())
        caps_percentage = (upper_count / len(letters)) * 100
        
        return caps_percentage >= CAPS_PERCENTAGE
    
    async def contains_links(self, text):
        for domain in ALLOWED_DOMAINS:
            text = re.sub(rf'https?://(?:www\.)?{re.escape(domain)}/\S+', '', text)
        
        link_pattern = r'https?://\S+'
        return bool(re.search(link_pattern, text))

    async def send_auto_mod_dm(self, member, reason, original_message):
        """Privát üzenet küldése automod esetén"""
        try:
            embed = discord.Embed(
                title="⚠️ Message Deleted",
                description=f"Your message was deleted because: {reason}",
                color=discord.Colour.orange()
            )
            embed.add_field(
                name="Original Message",
                value=f"```{original_message[:100]}{'...' if len(original_message) > 100 else ''}```",
                inline=False
            )
            await member.send(embed=embed)
            return True
        except discord.Forbidden:
            return False
        except Exception as e:
            print(f"Error sending automod DM: {e}")
            return False

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        if MUTE_ROLE_ID:
            mute_role = message.guild.get_role(MUTE_ROLE_ID)
            if mute_role and mute_role in message.author.roles:
                try:
                    await message.delete()
                    return  
                except:
                    pass

        team_role = message.guild.get_role(TEAM_ROLE) if message.guild else None
        has_admin_role = team_role in message.author.roles if team_role else False
        
        if message.author.guild_permissions.administrator or has_admin_role:
            return  
        if ANTI_CAPS_ENABLED:
            if await self.is_excessive_caps(message.content):
                try:
                    await message.delete()
                    await self.send_auto_mod_dm(
                        message.author, 
                        "it contained excessive capitalization", 
                        message.content
                    )
                    return
                except Exception as e:
                    print(f"Error in anti-caps: {e}")

        if ANTI_LINKS_ENABLED:
            if message.channel.id not in ALLOWED_LINKS_CHANNELS:
                if await self.contains_links(message.content):
                    try:
                        await message.delete()
                        await self.send_auto_mod_dm(
                            message.author, 
                            "links are not allowed in this channel", 
                            message.content
                        )
                        return
                    except Exception as e:
                        print(f"Error in anti-links: {e}")

    async def send_log(self, action: str, member: discord.Member, moderator: discord.Member, reason: str, duration: str = None):
        log_channel = self.bot.get_channel(LOG_CHANNEL)
        if not log_channel:
            return

        embed = discord.Embed(
            title=f"🔨 {action}",
            color=discord.Colour.orange() if action == "Mute" else discord.Colour.red() if action == "Ban" else discord.Colour.orange(),
            timestamp=datetime.datetime.utcnow()
        )
        
        embed.add_field(name="User", value=f"{member.mention} ({member.id})", inline=True)
        embed.add_field(name="Moderator", value=f"{moderator.mention}", inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        
        if duration:
            embed.add_field(name="Duration", value=duration, inline=True)
        
        embed.add_field(name="Account Created", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
        
        if member.joined_at:
            embed.add_field(name="Joined Server", value=f"<t:{int(member.joined_at.timestamp())}:R>", inline=True)
        
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"User ID: {member.id}")

        await log_channel.send(embed=embed)

    async def send_pm_to_user(self, member: discord.Member, action: str, reason: str, moderator: discord.Member, duration: str = None):
        try:
            embed = discord.Embed(
                title=f"🔨 You have been {action.lower()}ed",
                color=discord.Colour.red() if action == "Ban" else discord.Colour.orange(),
                timestamp=datetime.datetime.utcnow()
            )
            
            embed.add_field(name="Server", value=member.guild.name, inline=True)
            embed.add_field(name="Moderator", value=f"{moderator.display_name}", inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            
            if duration:
                embed.add_field(name="Duration", value=duration, inline=True)
            
            embed.add_field(name="Date", value=f"<t:{int(datetime.datetime.utcnow().timestamp())}:F>", inline=True)
            
            if action == "Ban":
                embed.add_field(name="Appeal", value="If you believe this was a mistake, contact the server staff.", inline=False)
            elif action == "Mute":
                embed.add_field(name="Note", value="You will not be able to send messages until the mute expires.", inline=False)
            
            embed.set_footer(text=f"Server: {member.guild.name}")

            await member.send(embed=embed)
            return True
        except discord.Forbidden:
            return False
        except Exception as e:
            print(f"Error sending PM: {e}")
            return False

    async def unmute_user(self, member_id: int, guild_id: int):
        """Automatikus unmute időzítő"""
        await asyncio.sleep(1)  
        
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return
        
        member = guild.get_member(member_id)
        if not member:
            return
        
        if not MUTE_ROLE_ID:
            return
        
        mute_role = guild.get_role(MUTE_ROLE_ID)
        if not mute_role:
            return
        
        if mute_role in member.roles:
            try:
                await member.remove_roles(mute_role, reason="Mute duration expired")
                
                # DM küldése
                try:
                    embed = discord.Embed(
                        title="🔈 Mute Expired",
                        description="Your mute has expired and you can now send messages again.",
                        color=discord.Colour.green(),
                        timestamp=datetime.datetime.utcnow()
                    )
                    embed.add_field(name="Server", value=guild.name, inline=True)
                    await member.send(embed=embed)
                except:
                    pass
                
                # Log küldése
                log_channel = self.bot.get_channel(LOG_CHANNEL)
                if log_channel:
                    embed = discord.Embed(
                        title="🔈 Mute Expired",
                        description=f"{member.mention}'s mute has expired",
                        color=discord.Colour.green(),
                        timestamp=datetime.datetime.utcnow()
                    )
                    embed.add_field(name="User", value=f"{member.mention} ({member.id})", inline=True)
                    await log_channel.send(embed=embed)
                
                print(f"User {member.name} ({member.id}) unmuted (duration expired)")
                
            except Exception as e:
                print(f"Error unmuting user {member_id}: {e}")

class ModCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.muted_users = {}

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'ModCommands cog loaded successfully')
        print(f'Anti-caps: {ANTI_CAPS_ENABLED}, Anti-links: {ANTI_LINKS_ENABLED}')

    def has_team_role():
        async def predicate(ctx):
            if ctx.author.guild_permissions.administrator:
                return True
            team_role = ctx.guild.get_role(TEAM_ROLE)
            return team_role in ctx.author.roles
        return commands.check(predicate)
    
    async def unmute_user(self, member_id: int, guild_id: int, seconds: int):
        await asyncio.sleep(seconds)
        
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return
        
        member = guild.get_member(member_id)
        if not member:
            return
        
        if not MUTE_ROLE_ID:
            return
        
        mute_role = guild.get_role(MUTE_ROLE_ID)
        if not mute_role:
            return
        
        if mute_role in member.roles:
            try:
                await member.remove_roles(mute_role, reason="Mute duration expired")
                
                try:
                    embed = discord.Embed(
                        title="🔈 Mute Expired",
                        description="Your mute has expired and you can now send messages again.",
                        color=discord.Colour.green(),
                        timestamp=datetime.datetime.utcnow()
                    )
                    embed.add_field(name="Server", value=guild.name, inline=True)
                    await member.send(embed=embed)
                except:
                    pass
                
                log_channel = self.bot.get_channel(LOG_CHANNEL)
                if log_channel:
                    embed = discord.Embed(
                        title="🔈 Mute Expired",
                        description=f"{member.mention}'s mute has expired",
                        color=discord.Colour.green(),
                        timestamp=datetime.datetime.utcnow()
                    )
                    embed.add_field(name="User", value=f"{member.mention} ({member.id})", inline=True)
                    await log_channel.send(embed=embed)
                
            except Exception as e:
                print(f"Error unmuting user: {e}")

    async def send_log(self, action: str, member: discord.Member, moderator: discord.Member, reason: str, duration: str = None):
        log_channel = self.bot.get_channel(LOG_CHANNEL)
        if not log_channel:
            return

        embed = discord.Embed(
            title=f"🔨 {action}",
            color=discord.Colour.orange() if action == "Mute" else discord.Colour.red() if action == "Ban" else discord.Colour.orange(),
            timestamp=datetime.datetime.utcnow()
        )
        
        embed.add_field(name="User", value=f"{member.mention} ({member.id})", inline=True)
        embed.add_field(name="Moderator", value=f"{moderator.mention}", inline=True)
        embed.add_field(name="Reason", value=str(reason)[:500], inline=False)
        
        if duration:
            embed.add_field(name="Duration", value=duration, inline=True)
        
        embed.add_field(name="Account Created", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
        
        if member.joined_at:
            embed.add_field(name="Joined Server", value=f"<t:{int(member.joined_at.timestamp())}:R>", inline=True)
        
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"User ID: {member.id}")

        await log_channel.send(embed=embed)

    async def send_pm_to_user(self, member: discord.Member, action: str, reason: str, moderator: discord.Member, duration: str = None):
        try:
            embed = discord.Embed(
                title=f"🔨 You have been {action.lower()}ed",
                color=discord.Colour.red() if action == "Ban" else discord.Colour.orange(),
                timestamp=datetime.datetime.utcnow()
            )
            
            embed.add_field(name="Server", value=member.guild.name, inline=True)
            embed.add_field(name="Moderator", value=f"{moderator.display_name}", inline=True)
            embed.add_field(name="Reason", value=str(reason)[:300], inline=False)
            
            if duration:
                embed.add_field(name="Duration", value=duration, inline=True)
            
            embed.add_field(name="Date", value=f"<t:{int(datetime.datetime.utcnow().timestamp())}:F>", inline=True)
            
            if action == "Ban":
                embed.add_field(name="Appeal", value="If you believe this was a mistake, contact the server staff.", inline=False)
            elif action == "Mute":
                embed.add_field(name="Note", value="You will not be able to send messages until the mute expires.", inline=False)
            
            embed.set_footer(text=f"Server: {member.guild.name}")

            await member.send(embed=embed)
            return True
        except discord.Forbidden:
            return False
        except Exception as e:
            print(f"Error sending PM: {e}")
            return False

    @commands.slash_command(name="mute", description="Mute a member")
    @commands.guild_only()
    @commands.check_any(commands.has_permissions(administrator=True), has_team_role())
    async def mute(self, ctx,
                  member: Option(discord.Member, description="Member to mute", required=True),
                  time: Option(str, description="Mute duration (e.g., 10m, 2h, 1d)", required=True),
                  reason: Option(str, description="Reason for mute", required=False, default="No reason provided")):
        
        if not MUTE_ROLE_ID:
            embed = discord.Embed(
                description="❌ Mute role is not configured. Please add 'mute_role_id' to config.json",
                color=discord.colour.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        if member == ctx.author:
            embed = discord.Embed(description="You cannot mute yourself", color=discord.colour.Color.red())
            await ctx.respond(embed=embed, ephemeral=True)
            return

        if member == self.bot.user:
            embed = discord.Embed(description="I cannot mute myself", color=discord.colour.Color.red())
            await ctx.respond(embed=embed, ephemeral=True)
            return

        if member.guild_permissions.administrator:
            embed = discord.Embed(description="Cannot mute administrators", color=discord.colour.Color.red())
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        mute_role = ctx.guild.get_role(MUTE_ROLE_ID)
        if not mute_role:
            embed = discord.Embed(
                description=f"❌ Mute role not found (ID: {MUTE_ROLE_ID})",
                color=discord.colour.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        time_lower = time.lower()
        seconds = 0
        
        try:
            if time_lower.endswith('s'):
                seconds = int(time_lower[:-1])
            elif time_lower.endswith('m'):
                seconds = int(time_lower[:-1]) * 60
            elif time_lower.endswith('h'):
                seconds = int(time_lower[:-1]) * 60 * 60
            elif time_lower.endswith('d'):
                seconds = int(time_lower[:-1]) * 60 * 60 * 24
            elif time_lower.endswith('w'):
                seconds = int(time_lower[:-1]) * 60 * 60 * 24 * 7
            else:
                seconds = int(time_lower) * 60
        except ValueError:
            embed = discord.Embed(
                description="❌ Invalid time format. Use: 10m, 2h, 1d, 1w",
                color=discord.colour.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        if seconds < 60:
            embed = discord.Embed(
                description="❌ Minimum mute time is 1 minute",
                color=discord.colour.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        if seconds > 60 * 60 * 24 * 7 * 4:
            embed = discord.Embed(
                description="❌ Maximum mute time is 4 weeks",
                color=discord.colour.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        if seconds < 60:
            duration_str = f"{seconds}s"
        elif seconds < 3600:
            duration_str = f"{seconds // 60}m"
        elif seconds < 86400:
            duration_str = f"{seconds // 3600}h"
        else:
            duration_str = f"{seconds // 86400}d"
        
        unmute_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=seconds)
        unmute_timestamp = int(unmute_time.timestamp())
        
        try:
            if mute_role in member.roles:
                embed = discord.Embed(
                    description=f"❌ {member.mention} is already muted",
                    color=discord.colour.Color.red()
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return
            
            safe_reason = str(reason)[:200]
            await member.add_roles(mute_role, reason=f"{safe_reason} | Muted by {ctx.author} for {duration_str}")
            
            pm_sent = await self.send_pm_to_user(
                member, 
                "Mute", 
                safe_reason, 
                ctx.author, 
                f"{duration_str} (expires: <t:{unmute_timestamp}:R>)"
            )
            
            await self.send_log("Mute", member, ctx.author, safe_reason, f"{duration_str} (expires: <t:{unmute_timestamp}:R>)")
            
            asyncio.create_task(self.unmute_user(member.id, ctx.guild.id, seconds))
            
            embed = discord.Embed(
                description=f"🔇 {member.mention} has been muted for **{duration_str}**\n**Reason:** {safe_reason}\n**Expires:** <t:{unmute_timestamp}:R>",
                color=discord.colour.Color.orange()
            )
            embed.set_footer(text=f"User ID: {member.id}")
            
            if not pm_sent:
                embed.add_field(name="Note", value="Could not send DM to user", inline=False)
            
            await ctx.respond(embed=embed)
            
        except discord.Forbidden:
            embed = discord.Embed(
                description="❌ I don't have permission to mute that member",
                color=discord.colour.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                description=f"❌ An error occurred: {str(e)[:100]}",
                color=discord.colour.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)

    @commands.slash_command(name="unmute", description="Unmute a member")
    @commands.guild_only()
    @commands.check_any(commands.has_permissions(administrator=True), has_team_role())
    async def unmute(self, ctx,
                    member: Option(discord.Member, description="Member to unmute", required=True),
                    reason: Option(str, description="Reason for unmute", required=False, default="No reason provided")):
        
        if not MUTE_ROLE_ID:
            embed = discord.Embed(
                description="❌ Mute role is not configured",
                color=discord.colour.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        mute_role = ctx.guild.get_role(MUTE_ROLE_ID)
        if not mute_role:
            embed = discord.Embed(
                description=f"❌ Mute role not found (ID: {MUTE_ROLE_ID})",
                color=discord.colour.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        if mute_role not in member.roles:
            embed = discord.Embed(
                description=f"❌ {member.mention} is not muted",
                color=discord.colour.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        try:
            safe_reason = str(reason)[:200]
            await member.remove_roles(mute_role, reason=f"{safe_reason} | Unmuted by {ctx.author}")
            
            log_channel = self.bot.get_channel(LOG_CHANNEL)
            if log_channel:
                embed = discord.Embed(
                    title="🔈 Unmute",
                    color=discord.Colour.green(),
                    timestamp=datetime.datetime.utcnow()
                )
                embed.add_field(name="User", value=f"{member.mention} ({member.id})", inline=True)
                embed.add_field(name="Moderator", value=f"{ctx.author.mention}", inline=True)
                embed.add_field(name="Reason", value=safe_reason, inline=False)
                await log_channel.send(embed=embed)
            
            embed = discord.Embed(
                description=f"🔈 {member.mention} has been unmuted\n**Reason:** {safe_reason}",
                color=discord.colour.Color.green()
            )
            await ctx.respond(embed=embed)
            
        except discord.Forbidden:
            embed = discord.Embed(
                description="❌ I don't have permission to unmute that member",
                color=discord.colour.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                description=f"❌ An error occurred: {str(e)[:100]}",
                color=discord.colour.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
    @commands.slash_command(name="unmute", description="Unmute a member")
    @commands.guild_only()
    @commands.check_any(commands.has_permissions(administrator=True), has_team_role())
    async def unmute(self, ctx,
                    member: Option(discord.Member, description="Member to unmute", required=True),
                    reason: Option(str, description="Reason for unmute", required=False, default="No reason provided")):
        
        if not MUTE_ROLE_ID:
            embed = discord.Embed(
                description="❌ Mute role is not configured",
                color=discord.colour.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        mute_role = ctx.guild.get_role(MUTE_ROLE_ID)
        if not mute_role:
            embed = discord.Embed(
                description=f"❌ Mute role not found (ID: {MUTE_ROLE_ID})",
                color=discord.colour.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        if mute_role not in member.roles:
            embed = discord.Embed(
                description=f"❌ {member.mention} is not muted",
                color=discord.colour.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        try:
            await member.remove_roles(mute_role, reason=f"{reason} | Unmuted by {ctx.author}")

            log_channel = self.bot.get_channel(LOG_CHANNEL)
            if log_channel:
                embed = discord.Embed(
                    title="🔈 Unmute",
                    color=discord.Colour.green(),
                    timestamp=datetime.datetime.utcnow()
                )
                embed.add_field(name="User", value=f"{member.mention} ({member.id})", inline=True)
                embed.add_field(name="Moderator", value=f"{ctx.author.mention}", inline=True)
                embed.add_field(name="Reason", value=reason, inline=False)
                await log_channel.send(embed=embed)

            embed = discord.Embed(
                description=f"🔈 {member.mention} has been unmuted\n**Reason:** {reason}",
                color=discord.colour.Color.green()
            )
            await ctx.respond(embed=embed)
            
        except discord.Forbidden:
            embed = discord.Embed(
                description="❌ I don't have permission to unmute that member",
                color=discord.colour.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                description=f"❌ An error occurred while trying to unmute the member: {str(e)}",
                color=discord.colour.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)

    @commands.slash_command(name="kick", description="Kick a member from the server")
    @commands.guild_only()
    @commands.check_any(commands.has_permissions(administrator=True), has_team_role())
    async def kick(self, ctx, 
                  member: Option(discord.Member, description="Member to kick", required=True),
                  reason: Option(str, description="Reason for kick", required=False, default="No reason provided")):
        
        if member == ctx.author:
            embed = discord.Embed(description="You cannot kick yourself", color=discord.colour.Color.red())
            await ctx.respond(embed=embed, ephemeral=True)
            return

        if member == self.bot.user:
            embed = discord.Embed(description="I cannot kick myself", color=discord.colour.Color.red())
            await ctx.respond(embed=embed, ephemeral=True)
            return

        if member.guild_permissions.administrator:
            embed = discord.Embed(description="Cannot kick administrators", color=discord.colour.Color.red())
            await ctx.respond(embed=embed, ephemeral=True)
            return

        try:
            pm_sent = await self.send_pm_to_user(member, "Kick", reason, ctx.author)
            
            await member.kick(reason=f"{reason} | Kicked by {ctx.author}")
            
            await self.send_log("Kick", member, ctx.author, reason)
            
            embed = discord.Embed(
                description=f"✅ {member.mention} has been kicked\n**Reason:** {reason}",
                color=discord.colour.Color.green()
            )
            if not pm_sent:
                embed.add_field(name="Note", value="Could not send DM to user", inline=False)
                
            await ctx.respond(embed=embed)
            
        except discord.Forbidden:
            embed = discord.Embed(description="I don't have permission to kick that member", color=discord.colour.Color.red())
            await ctx.respond(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(description=f"An error occurred while trying to kick the member: {str(e)}", color=discord.colour.Color.red())
            await ctx.respond(embed=embed, ephemeral=True)

    @commands.slash_command(name="ban", description="Ban a member from the server")
    @commands.guild_only()
    @commands.check_any(commands.has_permissions(administrator=True), has_team_role())
    async def ban(self, ctx, 
                 member: Option(discord.Member, description="Member to ban", required=True),
                 reason: Option(str, description="Reason for ban", required=False, default="No reason provided"),
                 delete_days: Option(int, description="Delete message history (days)", required=False, default=0, choices=[0, 1, 7])):
        
        if member == ctx.author:
            embed = discord.Embed(description="You cannot ban yourself", color=discord.colour.Color.red())
            await ctx.respond(embed=embed, ephemeral=True)
            return

        if member == self.bot.user:
            embed = discord.Embed(description="I cannot ban myself", color=discord.colour.Color.red())
            await ctx.respond(embed=embed, ephemeral=True)
            return

        if member.guild_permissions.administrator:
            embed = discord.Embed(description="Cannot ban administrators", color=discord.colour.Color.red())
            await ctx.respond(embed=embed, ephemeral=True)
            return

        try:
            pm_sent = await self.send_pm_to_user(member, "Ban", reason, ctx.author)
            
            delete_seconds = delete_days * 24 * 60 * 60
            await member.ban(
                reason=f"{reason} | Banned by {ctx.author}", 
                delete_message_seconds=delete_seconds
            )
            
            await self.send_log("Ban", member, ctx.author, reason)
            
            embed = discord.Embed(
                description=f"✅ {member.mention} has been banned\n**Reason:** {reason}",
                color=discord.colour.Color.green()
            )
            if delete_days > 0:
                embed.add_field(name="Messages Deleted", value=f"{delete_days} day(s) of message history", inline=False)
            if not pm_sent:
                embed.add_field(name="Note", value="Could not send DM to user", inline=False)
                
            await ctx.respond(embed=embed)
            
        except discord.Forbidden:
            embed = discord.Embed(description="I don't have permission to ban that member", color=discord.colour.Color.red())
            await ctx.respond(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(description=f"An error occurred while trying to ban the member: {str(e)}", color=discord.colour.Color.red())
            await ctx.respond(embed=embed, ephemeral=True)

    @commands.slash_command(name="unban", description="Unban a user from the server")
    @commands.guild_only()
    @commands.check_any(commands.has_permissions(administrator=True), has_team_role())
    async def unban(self, ctx,
                   user_id: Option(str, description="User ID to unban", required=True),
                   reason: Option(str, description="Reason for unban", required=False, default="No reason provided")):
        
        try:
            user_id = int(user_id)
            user = await self.bot.fetch_user(user_id)
            
            await ctx.guild.unban(user, reason=f"{reason} | Unbanned by {ctx.author}")
            
            log_channel = self.bot.get_channel(LOG_CHANNEL)
            if log_channel:
                embed = discord.Embed(
                    title="🔓 Unban",
                    color=discord.Colour.green(),
                    timestamp=datetime.datetime.utcnow()
                )
                embed.add_field(name="User", value=f"{user.mention} ({user.id})", inline=True)
                embed.add_field(name="Moderator", value=f"{ctx.author.mention}", inline=True)
                embed.add_field(name="Reason", value=reason, inline=False)
                await log_channel.send(embed=embed)
            
            embed = discord.Embed(
                description=f"✅ {user.mention} has been unbanned\n**Reason:** {reason}",
                color=discord.colour.Color.green()
            )
            await ctx.respond(embed=embed)
            
        except ValueError:
            embed = discord.Embed(description="Please provide a valid user ID", color=discord.colour.Color.red())
            await ctx.respond(embed=embed, ephemeral=True)
        except discord.NotFound:
            embed = discord.Embed(description="User is not banned or user ID is invalid", color=discord.colour.Color.red())
            await ctx.respond(embed=embed, ephemeral=True)
        except discord.Forbidden:
            embed = discord.Embed(description="I don't have permission to unban that user", color=discord.colour.Color.red())
            await ctx.respond(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(description=f"An error occurred: {str(e)}", color=discord.colour.Color.red())
            await ctx.respond(embed=embed, ephemeral=True)