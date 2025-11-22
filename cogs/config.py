import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
TOKEN = os.getenv('TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))

# Channel IDs
WELCOME_CHANNEL_ID = int(os.getenv('WELCOME_CHANNEL_ID'))
TICKET_CHANNEL_ID = int(os.getenv('TICKET_CHANNEL_ID'))
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID'))
ANNOUNCE_CHANNEL_ID = int(os.getenv('ANNOUNCE_CHANNEL_ID'))

# Category IDs
CATEGORY_ID_1 = int(os.getenv('CATEGORY_ID_1'))
CATEGORY_ID_2 = int(os.getenv('CATEGORY_ID_2'))

# Role IDs
ADMIN_ROLE_ID = int(os.getenv('ADMIN_ROLE_ID'))
SUPPORT_TEAM_ROLE_ID = int(os.getenv('SUPPORT_TEAM_ROLE_ID'))
AUTO_ROLE_ID = int(os.getenv('AUTO_ROLE_ID'))
OWNER_ROLE_ID = int(os.getenv('OWNER_ROLE_ID'))

# Ticket System
TIMEZONE = os.getenv('TIMEZONE')
EMBED_TITLE = os.getenv('EMBED_TITLE')
EMBED_DESCRIPTION = os.getenv('EMBED_DESCRIPTION')

# Auto Moderation
ANTI_CAPS_ENABLED = os.getenv('ANTI_CAPS_ENABLED', 'false').lower() == 'true'
MIN_MESSAGE_LENGTH = int(os.getenv('MIN_MESSAGE_LENGTH', 10))
ANTI_LINKS_ENABLED = os.getenv('ANTI_LINKS_ENABLED', 'false').lower() == 'true'
ALLOWED_LINKS_CHANNELS = [int(x.strip()) for x in os.getenv('ALLOWED_LINKS_CHANNELS', '').split(',') if x.strip()]
ALLOWED_DOMAINS = [x.strip() for x in os.getenv('ALLOWED_DOMAINS', '').split(',') if x.strip()]

# Auto Role
AUTO_ROLE_ENABLED = os.getenv('AUTO_ROLE_ENABLED', 'false').lower() == 'true'