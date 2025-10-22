import os
from typing import Optional
import discord
import constants
from server_config import Server_config

# have a json file that acts as a config for the bot
# it should contain a list of messages and their message ID strings (which are human readable)
# each message should also have a list of customizable buttons that can link to another message
# all of this should be able to be edited by an admin user through discord commands

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.messages = True
intents.message_content = True
intents.presences = True

client = discord.Client(intents=intents)
server_configs = {}

# load all the server configs in config folder
for filename in os.listdir('config'):
    if filename.endswith('.json'):
        config = Server_config()
        config.load_config(int(filename[:-5]))
        server_configs[config.server_id] = config


@client.event
async def on_ready():
    print(f'{client.user.name} has connected to Discord!')


async def send_welcome_message(member: discord.Member, server_config: Server_config):
    channel = client.get_channel(server_config.welcome_channel_id)
    if channel and server_config.get_message('welcome'):
        await send_button_message(channel, 'welcome', member.guild.id, member)


@client.event
async def on_member_join(member):
    if member.bot:
        return

    server_config = server_configs.get(member.guild.id)
    if not server_config:
        print("no server config found for this guild id " + str(member.guild.id))
        return

    if not server_config.send_welcome_on_join or server_config.welcome_channel_id == -1:
        return

    await send_welcome_message(member, server_config)


@client.event
async def on_member_update(before: discord.Member, after: discord.Member):
    if after.bot:
        return

    server_config = server_configs.get(after.guild.id)
    if not server_config:
        print("no server config found for this guild id " + str(after.guild.id))
        return
    
    # roles added = after − before
    before_ids = {r.id for r in before.roles}
    after_ids  = {r.id for r in after.roles}
    added = after_ids - before_ids

    if not added:
        return

    highest_prio = -1_000_000_000
    highest_prio_trigger = -1
    for role in added:
        for role_trigger in server_config.role_triggers.items():
            role_id = int(role_trigger[0])
            message_id = role_trigger[1]['message_id']
            priority = role_trigger[1]['priority']
            if role == role_id and priority > highest_prio:
                highest_prio = priority
                highest_prio_trigger = message_id
    
    if highest_prio_trigger != -1:
        await send_button_message(
            target=client.get_channel(server_config.welcome_channel_id),
            message_id=highest_prio_trigger,
            guild_id=after.guild.id,
            addressed_user=after
        )


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
        # try to process command if user is admin
    if len(message.content) > 0 and message.content[0] == '!':
        is_admin = False
        if message.guild:
            member = message.guild.get_member(message.author.id)
            if member and member.guild_permissions.administrator:
                is_admin = True
        if is_admin:
            await process_command(message)


async def process_command(message: discord.Message):
    command = message.content.split(" ")
    if command[0] == "!help":
        help_message = (
            "Available commands:\n"
            "!init - Initialize server config (only if not already initialized).\n"
            "!setwelcomechannel <channel_id> - Set the welcome channel by ID.\n"
            "!setwelcomerole <role_id> - Set the welcome role by ID. Welcome message will be sent in reaction to role addition.\n"
            "!setmessage <message_id> <message> - Set a message by ID (ID \"welcome\" is the welcome message that gets sent into the specified welcome channel). Use \"<user>\" in the message text to mention the user.\n"
            "!listmessages - List all configured messages.\n"
            "!setbutton <message_id> <target_message_id> <button_label> - Add a button to a message.\n"
            "!sendmessage <message_id> - Send a configured message to the current channel for debugging.\n"
            "!deletemessage <message_id> - Delete a configured message by ID.\n"
            "!deletebutton <message_id> <button_label> - Delete a button from a message by its label.\n"
            "!welcomeonjoinenabled <true|false> - Enable or disable welcome messages on member join.\n"
            "!addroletrigger <role_id> <message_id> <priority (int)> - Send a message when a user is given a specific role, if multiple roles get added at once the highest prio one gets sent.\n"
            "!deleteroletrigger <role_id> - Delete a role trigger.\n"
            "!listroletriggers - List all role triggers for this server.\n"
        )
        await message.channel.send(help_message)
    elif command[0] == "!init":
        server_config = server_configs.get(message.guild.id)
        if server_config:
            await message.channel.send("Server config already initialized.")
        else:
            config = Server_config()
            config.server_id = message.guild.id
            config.welcome_channel_id = -1
            config.welcome_role_id = -1
            config.send_welcome_on_join = True
            config.messages = {}
            config.save_config()
            server_configs[message.guild.id] = config
            await message.channel.send("Server config initialized, please use `!setmessage welcome <message>` to set the welcome message and `!setwelcomechannel <channel_id>` to set the welcome channel.")
    elif command[0] == "!setwelcomechannel":
        if len(command) < 2:
            await message.channel.send("Please provide a channel ID.")
            return
        try:
            channel_id = int(command[1].replace("<#", "").replace(">", ""))
            channel = client.get_channel(channel_id)
            if channel and channel.guild.id == message.guild.id:
                server_config = server_configs.get(message.guild.id)
                if server_config:
                    server_config.welcome_channel_id = channel_id
                    server_config.save_config()
                    await message.channel.send(f"Welcome channel set to: {channel.name}")
                else:
                    await message.channel.send("Server config not found.")
            else:
                await message.channel.send("Invalid channel ID or channel does not belong to this server.")
        except ValueError:
            await message.channel.send("Please provide a valid channel ID.")
    elif command[0] == "!setwelcomerole":
        if len(command) < 2:
            await message.channel.send("Please provide a role ID.")
            return
        try:
            if command[1] == "-1":
                role_id = -1
            else:
                role_id = int(command[1].replace("<@&", "").replace(">", ""))
            server_config = server_configs.get(message.guild.id)
            if server_config:
                if role_id != -1:
                    role = message.guild.get_role(role_id)
                    if role:
                        server_config.welcome_role_id = role_id
                        server_config.save_config()
                        await message.channel.send(f"Welcome role set to: {role.name}")
                    else:
                        await message.channel.send("Invalid role ID.")
                else:
                    server_config.welcome_role_id = role_id
                    server_config.save_config()
                    await message.channel.send("Welcome role cleared.")
            else:
                await message.channel.send("Server config not found.")
        except ValueError:
            await message.channel.send("Please provide a valid role ID.")
    elif command[0] == "!listmessages":
        server_config = server_configs.get(message.guild.id)
        if server_config:
            if not server_config.messages:
                await message.channel.send("No messages configured.")
            else:
                lines = ["Configured messages:"]
                for msg_id, msg in server_config.messages.items():
                    content = msg.get("content", "")
                    preview = content[:30] + ("..." if len(content) > 30 else "")
                    lines.append(f"`{msg_id}`: {preview}")
                    buttons = msg.get("buttons", [])
                    if buttons:
                        for idx, btn in enumerate(buttons, start=1):
                            label = btn.get("label", "(no label)")
                            target = btn.get("target", "(no target)")
                            lines.append(f"- [{idx}] {label} -> {target}")
                await message.channel.send("\n".join(lines))
        else:
            await message.channel.send("Server config not found.")
    elif command[0] == "!setmessage":
        if len(command) < 3:
            await message.channel.send("Usage: !setmessage <message_id> <message>")
            return
        message_id = command[1]
        message_content = " ".join(command[2:])
        server_config = server_configs.get(message.guild.id)
        if server_config:
            server_config.set_message(message_id, message_content)
            await message.channel.send(f"Message '{message_id}' set to: {message_content}")
        else:
            await message.channel.send("Server config not found.")
    elif command[0] == "!setbutton":
        if len(command) < 4:
            await message.channel.send("Usage: !setbutton <message_id> <target_message_id> <button_label>")
            return
        message_id = command[1]
        target_message_id = command[2]
        button_label = " ".join(command[3:])
        server_config = server_configs.get(message.guild.id)
        if server_config:
            if server_config.get_message(message_id):
                server_config.set_button(message_id, button_label, target_message_id)
                await message.channel.send(f"Button '{button_label}' added to message '{message_id}' linking to '{target_message_id}'.")
            else:
                await message.channel.send(f"Message ID '{message_id}' not found.")
        else:
            await message.channel.send("Server config not found.")
    elif command[0] == "!sendmessage":
        if len(command) < 2:
            await message.channel.send("Usage: !sendmessage <message_id>")
            return
        message_id = command[1]
        server_config = server_configs.get(message.guild.id)
        if server_config:
            msg = server_config.get_message(message_id)
            if msg:
                await send_button_message(message.channel, message_id)
            else:
                await message.channel.send(f"Message ID '{message_id}' not found.")
        else:
            await message.channel.send("Server config not found.")
    elif command[0] == "!deletemessage":
        if len(command) < 2:
            await message.channel.send("Usage: !deletemessage <message_id>")
            return
        message_id = command[1]
        server_config = server_configs.get(message.guild.id)
        if server_config:
            if server_config.get_message(message_id):
                del server_config.messages[message_id]
                server_config.save_config()
                await message.channel.send(f"Message ID '{message_id}' deleted.")
            else:
                await message.channel.send(f"Message ID '{message_id}' not found.")
        else:
            await message.channel.send("Server config not found.")
    elif command[0] == "!deletebutton":
        if len(command) < 3:
            await message.channel.send("Usage: !deletebutton <message_id> <button_label>")
            return
        message_id = command[1]
        button_label = " ".join(command[2:])
        server_config = server_configs.get(message.guild.id)
        if server_config:
            msg = server_config.get_message(message_id)
            if msg:
                buttons = msg.get("buttons", [])
                new_buttons = [btn for btn in buttons if btn.get("label") != button_label]
                if len(new_buttons) != len(buttons):
                    server_config.set_message(message_id, msg.get("content", ""), new_buttons)
                    await message.channel.send(f"Button '{button_label}' deleted from message '{message_id}'.")
                else:
                    await message.channel.send(f"Button '{button_label}' not found in message '{message_id}'.")
            else:
                await message.channel.send(f"Message ID '{message_id}' not found.")
        else:
            await message.channel.send("Server config not found.")
    elif command[0] == "!welcomeonjoinenabled":
        if len(command) < 2:
            await message.channel.send("Usage: !welcomeonjoinenabled <true|false>")
            return
        value = command[1].lower()
        if value not in ("true", "false"):
            await message.channel.send("Please provide 'true' or 'false'.")
            return
        enabled = value == "true"
        server_config = server_configs.get(message.guild.id)
        if server_config:
            server_config.send_welcome_on_join = enabled
            server_config.save_config()
            status = "enabled" if enabled else "disabled"
            await message.channel.send(f"Welcome on join has been {status}.")
        else:
            await message.channel.send("Server config not found.")
    elif command[0] == "!addroletrigger":
        if len(command) < 4:
            await message.channel.send("Usage: !addroletrigger <role_id> <message_id> <priority (int)>")
            return
        try:
            role_id = int(command[1].replace("<@&", "").replace(">", ""))
            message_id = command[2]
            priority = int(command[3])
            server_config = server_configs.get(message.guild.id)
            if server_config:
                server_config.set_role_trigger(role_id, message_id, priority)
                await message.channel.send(f"Role trigger added: Role ID '{role_id}' will send message '{message_id}' with priority {priority}.")
            else:
                await message.channel.send("Server config not found.")
        except ValueError:
            await message.channel.send("Please provide valid role ID and priority.")
    elif command[0] == "!deleteroletrigger":
        if len(command) < 2:
            await message.channel.send("Usage: !deleteroletrigger <role_id>")
            return
        try:
            role_id = int(command[1].replace("<@&", "").replace(">", ""))
            server_config = server_configs.get(message.guild.id)
            if server_config:
                if str(role_id) in server_config.role_triggers:
                    del server_config.role_triggers[str(role_id)]
                    server_config.save_config()
                    await message.channel.send(f"Role trigger for Role ID '{role_id}' deleted.")
                else:
                    await message.channel.send(f"No role trigger found for Role ID '{role_id}'.")
            else:
                await message.channel.send("Server config not found.")
        except ValueError:
            await message.channel.send("Please provide a valid role ID.")
    elif command[0] == "!listroletriggers":
        server_config = server_configs.get(message.guild.id)
        if server_config:
            if not server_config.role_triggers:
                await message.channel.send("No role triggers configured.")
            else:
                lines = ["Configured role triggers:"]
                for role_id, trigger in server_config.role_triggers.items():
                    message_id = trigger.get("message_id", "(no message)")
                    priority = trigger.get("priority", 0)
                    role = message.guild.get_role(int(role_id))
                    role_name = role.name if role else f"Role ID {role_id}"
                    lines.append(f"- {role_name} (ID: {role_id}): Message ID '{message_id}', Priority {priority}")
                await message.channel.send("\n".join(lines))
        else:
            await message.channel.send("Server config not found.")


async def send_button_message(
    target: discord.abc.Messageable,
    message_id: str,
    guild_id: Optional[int] = None,
    addressed_user: Optional[discord.User] = None,
    interaction: Optional[discord.Interaction] = None,
    ephemeral: bool = False,
):
    """
    Send a message (with optional buttons).
    - Normal path: sends to `target` (channel or user).
    - On button press: reply with an ephemeral message in the channel instead of DMing.
    """

    # Resolve guild id (prefer interaction guild if present)
    resolved_guild_id = guild_id
    if interaction and interaction.guild:
        resolved_guild_id = interaction.guild.id
    if resolved_guild_id is None:
        guild = getattr(target, "guild", None)
        if guild is not None:
            resolved_guild_id = guild.id

    if resolved_guild_id is None:
        return

    server_config = server_configs.get(resolved_guild_id)
    if not server_config:
        return

    msg = server_config.get_message(message_id)
    if not msg:
        return

    buttons = msg.get("buttons", [])
    view = None
    if buttons:
        view = discord.ui.View()
        for button in buttons:
            next_id = button.get("target")
            label = button.get("label", "Next")

            async def button_callback(cb_interaction: discord.Interaction, next_id=next_id):
                await send_button_message(
                    target=None,
                    message_id=next_id,
                    guild_id=cb_interaction.guild.id if cb_interaction.guild else resolved_guild_id,
                    addressed_user=cb_interaction.user,
                    interaction=cb_interaction,
                    ephemeral=True,
                )

            btn = discord.ui.Button(label=label, style=discord.ButtonStyle.primary)
            btn.callback = button_callback
            view.add_item(btn)

    content = msg["content"]
    if addressed_user:
        content = content.replace("<user>", f"<@{addressed_user.id}>")

    # If coming from an interaction and ephemeral requested, respond ephemerally
    if interaction is not None and ephemeral:
        send_kwargs = {"content": content, "ephemeral": True}
        if view is not None:
            send_kwargs["view"] = view

        if not interaction.response.is_done():
            await interaction.response.send_message(**send_kwargs)
        else:
            await interaction.followup.send(**send_kwargs)
        return

    # Fallback: normal send to target (public message)
    if target is not None:
        if view is None:
            await target.send(content=content)
        else:
            await target.send(content=content, view=view)


client.run(os.environ.get(constants.BOT_TOKEN_VARIABLE))

