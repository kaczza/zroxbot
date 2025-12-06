[![Typing SVG](https://readme-typing-svg.demolab.com?font=Helvetica&pause=1000&color=E6F745&random=true&width=435&lines=THIS+BOT+IS+WRITTEN+IN+PY-CORD)](https://git.io/typing-svg)

# 🧩 ZroxBot  
### A lightweight, open-source Discord bot that just works.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![discord.py](https://img.shields.io/badge/discord.py-2.3+-blue.svg)](https://discordpy.readthedocs.io)
[![License](https://img.shields.io/github/license/kaczza/zroxbot)](LICENSE)

---

## ✨ Features
| Module         | Description                                                                 |
|----------------|-----------------------------------------------------------------------------|
| 🎫 **Ticket**   | Create private support channels on demand with one reaction.                |
| 📢 **Announcement** | Send embed announcements to any channel via slash-command.              |
| 👋 **Welcome**  | Greet newcomers with a fully-customizable embed.                            |
| 🏷️ **AutoRole** | Automatically assign roles when a member joins.                             |
| 🔨 **Kick/Ban** | Moderation commands with audit-proof logs.                                  |
| 🔇 **Mute**     | Time-out members (native Discord timeout) or role-based mute.               |
| 🧹 **Clear**    | Deletes Number of messages                                                  |
| 🔗 **AntiLink** | Deletes invite/URL spam unless the domain is whitelisted.                   |

---

## 🚀 Quick Start
1. Clone & enter the repo
   ```bash
   git clone https://github.com/your-username/zrox.git && cd zrox
   ```
2. Install dependencies
   ```bash
   python -m pip install -r requirements.txt
   ```
3. Configure
   - Paste your **Bot Token** (`token`) and **Guild ID** (`guild_id`)
4. Run
   ```bash
   python -m main.py
   ```
   The bot registers slash-commands automatically on startup.

---

## ⚙️ Config Cheat-Sheet
```json
 "token": "ZGUHDFO%=SF74FDSF",
  "guild_id": 14085877462413276808,
  "welcome_channel_id": 1408587744779598856,
  "ticket_channel_id": 1441861458790060224,
  "category_id_1": 1441862501463348958,
  "category_id_2": 1441862501460348958,
  "admin_role_id": 1408587746213236813, 
  "support_team_role_id": 1408287746213236812,
  "log_channel_id": 1408587747140509726,
  "timezone": "CET",
  "embed_title": "Support-Tickets",
  "embed_description": "Here you can open a Support Ticket!",
  "anti_caps_enabled": true,
  "min_message_length": 10,
  "anti_links_enabled": true,
  "allowed_links_channels": [1408592016924868721,1408587746779598854],
  "allowed_domains": ["youtube.com", "github.com"],
  "auto_role_enabled": true,
  "auto_role_id": 1408587746313236809,
  "mute_role_id": 1446857611877953402,
  "owner_role_id": 1408587747213236813,
  "announce_channel_id": 1402592016924868721
```

---

## 📐 Commands (all slash)
| Command      | Permission | Options | Example |
|--------------|------------|---------|---------|
| `/announce`  | Manage Messages | `channel` `title` `message` | `/announce #news "Update" "We just reset the server!"` |
| `/kick`      | Kick Members | `member` `reason` | `/kick @user Spam` |
| `/ban`       | Ban Members | `member` `reason` | `/ban @user Raid` |
| `/unban`       | Ban Members | `member` `reason` | `/ban @user Wrong Person` |
| `/mute`      | Moderate Members | `member` `duration` `reason` | `/mute @user 10m Calm down` |
| `/unmute`      | Moderate Members | `member` `duration` `reason` | `/umute @user Just Kidding` |
| `/send_ticket_menu`    | Send Embed Messages | `/send_ticket_menu` *(send the ticket menu to the configured channel)* |
| `/clear` | Manage Messages | `ammount of messages` | `/clear 20` |

---

## 🛠️ Extending Zrox
- **Cogs** This way the code s much easier to read.  
- **Updates** The zrox project has upcomming updates! 
- **Support** you can allways ask questions on the discord server

---

## 📊 Logging & Audit
All mod-actions are posted to the channel defined in `LOG_CHANNEL_ID` with:
- Who did it
- Target user
- Reason & timestamp

---

## 🤝 Contributing
1. Fork the repo
2. Create your feature branch (`git checkout -b feat/my-idea`)
3. Commit with [Conventional Commits](https://conventionalcommits.org)
4. Push and open a Pull Request

---

## 📄 License
MIT © [kaczza](https://github.com/kaczza/zroxbot/blob/main/LICENSE) – feel free to use ZroxBot in your own projects.

---

## 🔗 Links
Documentation Comming soon!
[Issue Tracker](https://github.com/kaczza/zroxbot/issues) •  
[Discord Support](https://discord.gg/UTxb2Dk9jQ)
