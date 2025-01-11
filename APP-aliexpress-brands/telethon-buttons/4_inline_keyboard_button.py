from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

# Define the command handler function
def start(update: Update, context: CallbackContext):
    # Define the keyboard layout
    keyboard = [
        [InlineKeyboardButton("Option 1", callback_data='1'),
         InlineKeyboardButton("Option 2", callback_data='2')],
        [InlineKeyboardButton("Option 3", callback_data='3'),
         InlineKeyboardButton("Option 4", callback_data='4')]
    ]
    # Create InlineKeyboardMarkup object
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the message with the inline keyboard
    update.message.reply_text('Choose an option:', reply_markup=reply_markup)

# Define the callback function for handling button clicks
def button_click(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    query.edit_message_text(text=f"Selected option: {query.data}")

def main():
    # Create the Updater
    updater = Updater("6465658634:AAFGxC8eHCZulj6TrA9Xstwc7Tefi3CxV0Y", use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add command handler
    dp.add_handler(CommandHandler("start", start))

    # Add callback query handler
    dp.add_handler(CallbackQueryHandler(button_click))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()