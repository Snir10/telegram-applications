from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

# Start command
def start(update: Update, context):
    # Initial number and character
    number = 1
    character = 'a'

    # Keyboard for the number buttons
    number_keyboard = [
        [InlineKeyboardButton("1", callback_data=f'number_1')],
        [InlineKeyboardButton("2", callback_data=f'number_2')],
    ]
    number_markup = InlineKeyboardMarkup(number_keyboard)

    # Keyboard for the character buttons
    char_keyboard = [
        [InlineKeyboardButton("a", callback_data=f'char_a')],
        [InlineKeyboardButton("b", callback_data=f'char_b')],
    ]
    char_markup = InlineKeyboardMarkup(char_keyboard)

    # Send the two messages
    msg_number = update.message.reply_text(f"Current number: {number}", reply_markup=number_markup)
    msg_char = update.message.reply_text(f"Current character: {character}", reply_markup=char_markup)

    # Store message IDs for later editing
    context.user_data['msg_number_id'] = msg_number.message_id
    context.user_data['msg_char_id'] = msg_char.message_id
    context.user_data['number_markup'] = number_markup  # Store the keyboard
    context.user_data['char_markup'] = char_markup  # Store the keyboard

# Handle button clicks
def button_handler(update: Update, context):
    query = update.callback_query
    query.answer('thinking')  # Acknowledge the button click

    # Determine which button was clicked and update the message
    if query.data.startswith('number_'):
        new_number = query.data.split('_')[1]
        msg_number_id = context.user_data['msg_number_id']
        number_markup = context.user_data['number_markup']  # Retrieve the saved keyboard
        query.bot.edit_message_text(
            text=f"Current number: {new_number}",
            chat_id=query.message.chat_id,
            message_id=msg_number_id,
            reply_markup=number_markup  # Keep the buttons visible
        )

    elif query.data.startswith('char_'):
        new_char = query.data.split('_')[1]
        msg_char_id = context.user_data['msg_char_id']
        char_markup = context.user_data['char_markup']  # Retrieve the saved keyboard
        query.bot.edit_message_text(
            text=f"Current character: {new_char}",
            chat_id=query.message.chat_id,
            message_id=msg_char_id,
            reply_markup=char_markup  # Keep the buttons visible
        )

def main():
    # Replace 'YOUR_TOKEN_HERE' with your Telegram Bot Token
    updater = Updater("7887654568:AAE38OGqlb46abFe9Jflq5DMT3X3Vcd30Xo", use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_handler))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
