# AI Plans Discord Bot

A configurable Discord bot that sends welcome messages and role-triggered messages with interactive button navigation. Each server gets its own JSON-based config, fully manageable through Discord admin commands.

## Features

- **Welcome messages** — send a message to a channel when a member joins, or when they receive a specific role
- **Role triggers** — map Discord roles to messages with priority support (if multiple roles are added at once, only the highest-priority message is sent)
- **Interactive buttons** — attach buttons to messages that navigate to other configured messages (ephemeral follow-ups)
- **Per-server config** — each guild stores its settings in `config/<guild_id>.json`
- **Admin commands** — all configuration is done through `!`-prefixed commands by server administrators

## Setup

### Prerequisites

- Python 3.8+
- [discord.py](https://github.com/Rapptz/discord.py) (`pip install discord.py`)

### Running

1. Set the bot token as an environment variable:
   ```
   CUSTOM_MESSAGE_DISCORD_BOT_TOKEN=your_token_here
   ```

2. Run the bot:
   ```
   python main.py
   ```

## Admin Commands

All commands require the **Administrator** permission. Run `!help` in any server channel to see the full list.

| Command | Description |
|---|---|
| `!init` | Initialize the bot config for this server |
| `!setwelcomechannel <#channel>` | Set the channel where welcome/role messages are sent |
| `!setwelcomerole <@role>` | Set a role whose assignment triggers the welcome message |
| `!welcomeonjoinenabled <true\|false>` | Enable or disable the automatic welcome on member join |
| `!setmessage <id> <text>` | Create or update a message. Use `welcome` as the ID for the join welcome. Use `<user>` in the text to mention the member. |
| `!listmessages` | List all configured messages and their buttons |
| `!deletemessage <id>` | Delete a configured message |
| `!setbutton <message_id> <target_message_id> <label>` | Add a button to a message that navigates to another message |
| `!deletebutton <message_id> <label>` | Remove a button from a message |
| `!sendmessage <id>` | Send a configured message to the current channel (for testing) |
| `!addroletrigger <@role> <message_id> <priority>` | Send a message when a role is assigned. Higher priority wins if multiple roles are added simultaneously. |
| `!deleteroletrigger <@role>` | Remove a role trigger |
| `!listroletriggers` | List all configured role triggers |

## Configuration

Server configs are stored as JSON files in the `config/` directory, named by guild ID (e.g. `config/123456789.json`). They are created automatically by `!init` and updated by admin commands.

Example config structure:

```json
{
    "server_id": 123456789,
    "welcome_channel_id": 987654321,
    "welcome_role_id": -1,
    "send_welcome_on_join": true,
    "messages": {
        "welcome": {
            "content": "Welcome to the server, <user>!",
            "buttons": [
                { "label": "Learn more", "target": "info" }
            ]
        },
        "info": {
            "content": "Here is some info about our server.",
            "buttons": []
        }
    },
    "role_triggers": {
        "111222333": {
            "message_id": "welcome",
            "priority": 10
        }
    }
}
```
