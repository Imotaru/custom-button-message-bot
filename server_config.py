class Server_config:
	messages = {}
	welcome_channel_id = -1
	server_id = -1

	def __init__(self):
		pass

	def load_config(self, server_id):
		import json
		with open(f'config/{server_id}.json', 'r') as f:
			config = json.load(f)
		self.messages = config.get('messages', {})
		self.welcome_channel_id = config.get('welcome_channel_id', -1)
		self.server_id = config.get('server_id', -1)

	def save_config(self):
		import json
		with open(f'config/{self.server_id}.json', 'w') as f:
			json.dump({
				'messages': self.messages,
				'welcome_channel_id': self.welcome_channel_id,
				'server_id': self.server_id
			}, f, indent=4)

	def get_message(self, message_id):
		return self.messages.get(message_id)

	def set_message(self, message_id, content, buttons=None):
		self.messages[message_id] = {
			'content': content,
			'buttons': buttons or []
		}
		self.save_config()

	def add_button(self, message_id, button_label, target_message_id):
		message = self.get_message(message_id)
		if message:
			message['buttons'].append({
				'label': button_label,
				'target': target_message_id
			})
			self.set_message(message_id, message['content'], message['buttons'])