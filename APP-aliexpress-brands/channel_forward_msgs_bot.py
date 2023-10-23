import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext
from telegram import Update


# Replace with your own API token
API_TOKEN = ''

# Initialize the bot
updater = Updater(token=API_TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Enable logging (optional but helpful)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Global variables for settings
numerical_interval = 5  # Default interval in minutes
chat_id = None
validation_settings = None  # To store the validation settings

# Command handler to set numerical interval
def set_interval(update: Update, context: CallbackContext):
    global numerical_interval
    text = update.message.text.split()
    if len(text) != 2:
        update.message.reply_text("Invalid format. Use /setinterval [minutes]")
    else:
        try:
            numerical_interval = int(text[1])
            update.message.reply_text(f"Interval set to {numerical_interval} minutes.")
        except ValueError:
            update.message.reply_text("Invalid input. Please provide a valid number of minutes.")

# Command handler to set chat ID
def set_chat_id(update: Update, context: CallbackContext):
    global chat_id
    chat_id = update.message.chat_id
    update.message.reply_text(f"Chat ID set to {chat_id}.")

# Command handler to set validation settings
def set_validation(update: Update, context: CallbackContext):
    global validation_settings
    validation_settings = context.args
    update.message.reply_text(f"Validation settings updated: {', '.join(validation_settings)}")

# Message handler to forward messages based on validation settings
def forward_messages(update: Update, context: CallbackContext):
    if validation_settings:
        message = update.message
        text = message.text
        has_photo = len(message.photo) > 0
        has_video = message.video is not None

        if '1' in validation_settings and text and not has_photo and not has_video:
            send_message(update, context)
        elif '2' in validation_settings and text and (has_photo or has_video):
            send_message(update, context)
        elif '3' in validation_settings and text and has_video:
            send_message(update, context)
        elif '4' in validation_settings and (has_photo or has_video):
            send_message(update, context)

# Helper function to send a message
def send_message(update, context):
    if chat_id:
        update.message.forward(chat_id=chat_id)

# Add command handlers
dispatcher.add_handler(CommandHandler('setinterval', set_interval))
dispatcher.add_handler(CommandHandler('setchatid', set_chat_id))
dispatcher.add_handler(CommandHandler('setvalidation', set_validation, pass_args=True))

# Add message handler for forwarding messages
dispatcher.add_handler(MessageHandler(Filters.all & ~Filters.command, forward_messages))

# Start the bot
updater.start_polling()
updater.idle()
