from telethon import TelegramClient
from telethon.tl.types import InputPeerChannel
from telethon.tl.types import KeyboardButtonUrl
from telethon.tl.types import ReplyKeyboardMarkup
from telethon.errors.rpcerrorlist import PeerFloodError

# Your API credentials
api_id = '17597358'
api_hash = '63ec84ff6b319b6fb87da66c5d3d2d29'

# Your phone number
phone_number = '972507610755'

# The channel's username or chat_id
channel_username = 'zara_express'  # Replace with your channel's username
channel_chat_id = -1002050595478  # Replace with your actual channel's chat_id

# Connect to Telegram
client = TelegramClient('session_name', api_id, api_hash)
client.start()


# Start the conversation with the channel
async def send_message():
    try:
        # Define the button text and URL
        button_text = 'ZARAExpress'
        button_url = 'https://t.me/zara_express'

        button_text_2 = 'AliExpress Hidden Links'
        button_url_2 = 'https://t.me/best_of_ali_expresss'

        # Create the message text with the button link
        message_text = f'new groups\n[{button_text}]({button_url})'
        message_text2 = f'new groups\n[{button_text_2}]({button_url_2})'

        # Send the message with the button link
        await client.send_message(entity=channel_username, message=message_text, parse_mode='markdown')
        await client.send_message(entity=channel_username, message=message_text2, parse_mode='markdown')

        print("Message sent successfully!")
    except PeerFloodError:
        print("Flood limit exceeded. Please try again later.")


with client:
    client.loop.run_until_complete(send_message())