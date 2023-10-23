from telegram import InputMediaPhoto, InputMediaVideo
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext


# Replace 'YOUR_BOT_TOKEN' with your actual bot token
bot_token = 'YOUR_BOT_TOKEN'

def send_media_group(update, context):
    chat_id = update.message.chat_id
    media = [
        InputMediaPhoto('URL_TO_PHOTO_1', caption='Caption 1'),
        InputMediaPhoto('URL_TO_PHOTO_2', caption='Caption 2'),
        InputMediaVideo('URL_TO_VIDEO', caption='Video Caption')
    ]

    context.bot.send_media_group(chat_id=chat_id, media=media)

def main():
    updater = Updater(token=bot_token, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, send_media_group))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()