from telegram.ext import Updater, MessageHandler, Filters

# Replace 'YOUR_BOT_TOKEN' with your actual bot token
BOT_TOKEN = 'YOUR_BOT_TOKEN'

# Replace 'CHANNEL_CHAT_ID' with the chat ID of the channel you want to monitor
CHANNEL_CHAT_ID = -1001234567890  # Example format for a channel chat ID

# Your reaction emoji or text goes here
REACTION_TEXT = '👍'

# Initialize the bot
updater = Updater(token=BOT_TOKEN, use_context=True)

# Function to react to media group messages
def react_to_media_group(update, context):
    message = update.message
    chat_id = message.chat_id

    # Check if the message is part of a media group
    if message.media_group_id:
        # Repost the media group message with the reaction
        context.bot.send_media_group(chat_id=chat_id, media=message.media_group, caption=REACTION_TEXT)

# Create a message handler for media group messages
media_group_handler = MessageHandler(Filters.media_group, react_to_media_group)
updater.dispatcher.add_handler(media_group_handler)

# Start the Bot
updater.start_polling()
updater.idle()
