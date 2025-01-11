import telegram
from telegram.ext import Updater, MessageHandler, Filters
from easygoogletranslate import EasyGoogleTranslate

# Your bot token
TOKEN = '7887654568:AAE38OGqlb46abFe9Jflq5DMT3X3Vcd30Xo'
chat_id = '-1001885191160'  # Your target channel or group
# chat_id = '-1001907459539'
translator = EasyGoogleTranslate(source_language='he', target_language='en', timeout=10)

# Your user ID (replace this with your actual user ID)
MY_USER_ID = 516389439  # Replace with your actual user ID


# Function to check if the message is from you
def is_from_me(update):
    x = update.message.from_user.id == MY_USER_ID
    if x:
        print('MSG from ME')
    return x

# Function to get your user ID
def get_user_id(update, context):
    if is_from_me(update):
        user_id = update.message.from_user.id
        update.message.reply_text(f"Your User ID is: {user_id}")
    else:
        print(f"Blocked User")



# Function to translate and forward media
def forward_media(update, context):
    message = update.message
    if not is_from_me(update):
        return  # Ignore messages from other users

    if message.photo:
        # Forward photo with caption
        print('Photo Detected')

        caption = message.caption if message.caption else ''
        if caption:
            translation = translator.translate(caption)
            update.message.reply_text(translation)  # Optional: reply with translated caption
            context.bot.send_photo(chat_id=chat_id, photo=message.photo[-1].file_id, caption=translation)
        else:
            context.bot.send_photo(chat_id=chat_id, photo=message.photo[-1].file_id)

    elif message.video:
        # Forward video with caption
        print('Video Detected')
        caption = message.caption if message.caption else ''
        if caption:
            translation = translator.translate(caption)
            update.message.reply_text(translation)  # Optional: reply with translated caption
            context.bot.send_video(chat_id=chat_id, video=message.video.file_id, caption=translation)
        else:
            context.bot.send_video(chat_id=chat_id, video=message.video.file_id)

    elif message.document:
        print('DOC Detected')

        # Forward document with caption
        caption = message.caption if message.caption else ''
        if caption:
            translation = translator.translate(caption)
            update.message.reply_text(translation)  # Optional: reply with translated caption
            context.bot.send_document(chat_id=chat_id, document=message.document.file_id, caption=translation)
        else:
            context.bot.send_document(chat_id=chat_id, document=message.document.file_id)

    elif message.text:
        # Handle text message and translation
        text = message.text
        if text:
            translation = translator.translate(text)
            update.message.reply_text(translation)  # Reply with the translated text
            context.bot.send_message(chat_id=chat_id, text=translation)


# Main function
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Get User ID handler
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, get_user_id))  # Get User ID on text messages
    # Forward media handler
    dp.add_handler(
        MessageHandler(Filters.photo | Filters.video | Filters.document | Filters.text, forward_media))  # Handle media

    # Start the bot
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
