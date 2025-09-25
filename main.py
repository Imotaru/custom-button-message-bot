import os
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


@client.event
async def on_member_join(member):
    server_config = server_configs.get(member.guild.id)
    if not server_config:
        print("no server config found for this guild id " + str(member.guild.id))
        return
    
    # send a welcome message to the welcome channel
    channel = client.get_channel(server_config.welcome_channel_id)
    if channel and server_config.get_message('welcome'):
        await send_button_message(channel, 'welcome')

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
            "!setwelcome <message> - Set the welcome message.\n"
            "!setwelcomechannel <channel_id> - Set the welcome channel by ID.\n"
            "!setmessage <message_id> <message> - Set a message by ID.\n"
            "!listmessages - List all configured messages.\n"
            "!addbutton <message_id> <button_label> <target_message_id> - Add a button to a message.\n"
            "!sendmessage <message_id> - Send a configured message to the current channel.\n"
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
            config.messages = {}
            config.save_config()
            server_configs[message.guild.id] = config
            await message.channel.send("Server config initialized, please use !setwelcome <message> to set the welcome message and !setwelcomechannel <channel_id> to set the welcome channel.")
    elif command[0] == "!setwelcome":
        if len(command) < 2:
            await message.channel.send("Please provide a welcome message.")
            return
        welcome_message = " ".join(command[1:])
        server_config = server_configs.get(message.guild.id)
        if server_config:
            server_config.set_message('welcome', welcome_message)
            await message.channel.send(f"Welcome message set to: {welcome_message}")
        else:
            await message.channel.send("Server config not found.")
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
    elif command[0] == "!listmessages":
        server_config = server_configs.get(message.guild.id)
        if server_config:
            if not server_config.messages:
                await message.channel.send("No messages configured.")
            else:
                msg_list = "\n".join([f"{msg_id}: {msg['content']}" for msg_id, msg in server_config.messages.items()])
                await message.channel.send(f"Configured messages:\n{msg_list}")
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
    elif command[0] == "!addbutton":
        if len(command) < 4:
            await message.channel.send("Usage: !addbutton <message_id> <button_label> <target_message_id>")
            return
        message_id = command[1]
        button_label = command[2]
        target_message_id = command[3]
        server_config = server_configs.get(message.guild.id)
        if server_config:
            if server_config.get_message(message_id):
                server_config.add_button(message_id, button_label, target_message_id)
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

# sends the message with buttons you can click, once clicked it sends the target message
async def send_button_message(channel, message_id):
    server_config = server_configs.get(channel.guild.id)
    if not server_config:
        return
    msg = server_config.get_message(message_id)
    if not msg:
        return

    buttons = msg.get('buttons', [])
    if buttons:
        view = discord.ui.View()
        for button in buttons:
            async def button_callback(interaction, target=button['target']):
                await interaction.response.defer()
                await send_button_message(interaction.channel, target)
            btn = discord.ui.Button(label=button['label'], style=discord.ButtonStyle.primary)
            btn.callback = button_callback
            view.add_item(btn)
        await channel.send(content=msg['content'], view=view)
    else:
        await channel.send(content=msg['content'])

client.run(os.environ.get(constants.BOT_TOKEN_VARIABLE))

