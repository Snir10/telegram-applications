
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, Filters

# Define the command handler function
def start(update: Update, context: CallbackContext):
    # Define the keyboard layout
    keyboard = [
        ['Option 1', 'Option 2'],
        ['Option 3', 'Option 4']
    ]
    # Create ReplyKeyboardMarkup object
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    # Send the message with the custom keyboard
    update.message.reply_text('Choose an option:', reply_markup=reply_markup)

# Define the message handler function
def echo(update: Update, context: CallbackContext):
    if update.message:
        # Echo the user's message
        update.message.reply_text(update.message.text)

def main():
    # Create the Updater
    updater = Updater("6898412840:AAGcGTa5G8gW0ePyXmuyTJBYOijkOfZ4xyU")

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add command handler
    dp.add_handler(CommandHandler("start", start))

    # Add message handler
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()
