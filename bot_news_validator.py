import telegram
from telegram.ext import Updater, MessageHandler, Filters, ConversationHandler, CommandHandler, CallbackQueryHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from easygoogletranslate import EasyGoogleTranslate

TOKEN = '6898412840:AAGcGTa5G8gW0ePyXmuyTJBYOijkOfZ4xyU'
translator = EasyGoogleTranslate(source_language='he', target_language='en', timeout=10)

# Add your target chat ID here
TARGET_CHAT_ID = '-1001885191160'

# List of authorized user IDs
AUTHORIZED_USERS = ['516389439', 'user_id_2']  # Add user ids to whitelist
# States
SELECT_ACTION = 1
EDIT_CAPTION = 2

def start(update, context):
    user_id = str(update.message.from_user.id)
    if user_id not in AUTHORIZED_USERS:
        print(f"Unauthorized access attempt from user ID: {user_id}")
        return

    forwarded_message = update.message.reply_to_message
    translated_text = ""
    if update.message:
        translated_text = translator.translate(update.message.text)

    reply_keyboard = [[InlineKeyboardButton("Edit Caption", callback_data='edit'),
                      InlineKeyboardButton("Send Post", callback_data='send')]]
    update.message.reply_text(
        f"{translated_text}\n\nPlease select option:",
        reply_markup=InlineKeyboardMarkup(reply_keyboard)
    )
    return SELECT_ACTION

def button_click(update, context):
    query = update.callback_query
    user_id = str(query.from_user.id)
    message = query.message.reply_to_message
    if user_id not in AUTHORIZED_USERS:
        print(f"Unauthorized access attempt from user ID: {user_id}")
        return

    if query.data == 'edit':
        query.edit_message_text(text="Please enter the new caption:")
        return EDIT_CAPTION
    elif query.data == 'send':
        send_post(message, context)
        return ConversationHandler.END

def edit_caption(update, context):
    new_caption = update.message.text
    context.user_data['new_caption'] = new_caption
    update.message.reply_text(f"Preview post with edited caption:\n\n{new_caption}\n\nSend Post to publish.",
                              reply_markup=InlineKeyboardMarkup(
                                  [[InlineKeyboardButton("Send Post", callback_data='send')]])
                              )
    return SELECT_ACTION

def send_post(message, context):
    if 'new_caption' in context.user_data:
        message.caption = context.user_data['new_caption']

    translated_text = ""
    if message.text:
        translated_text = translator.translate(message.text).text

    if message.photo:
        # If it's a photo
        photo = message.photo[-1]
        caption = message.caption if message.caption else ''
        if caption:
            translation = translator.translate(caption)
            context.bot.send_photo(chat_id=TARGET_CHAT_ID, photo=photo.file_id, caption=f"{translation}\n\n{translated_text}")
        else:
            context.bot.send_photo(chat_id=TARGET_CHAT_ID, photo=photo.file_id, caption=translated_text)

    elif message.video:
        # If it's a video
        caption = message.caption if message.caption else ''
        if caption:
            translation = translator.translate(caption)
            context.bot.send_video(chat_id=TARGET_CHAT_ID, video=message.video.file_id, caption=f"{translation}\n\n{translated_text}")
        else:
            context.bot.send_video(chat_id=TARGET_CHAT_ID, video=message.video.file_id, caption=translated_text)

    elif message.document:
        # If it's a document
        caption = message.caption if message.caption else ''
        if caption:
            translation = translator.translate(caption)
            context.bot.send_document(chat_id=TARGET_CHAT_ID, document=message.document.file_id, caption=f"{translation}\n\n{translated_text}")
        else:
            context.bot.send_document(chat_id=TARGET_CHAT_ID, document=message.document.file_id, caption=translated_text)

    elif message.text:
        # If it's a text message
        text = message.text
        if text:
            translation = translator.translate(text)
            context.bot.send_message(chat_id=TARGET_CHAT_ID, text=f"{translation}\n\n{translated_text}")

def cancel(update, context):
    update.message.reply_text('Action canceled.')
    return ConversationHandler.END

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.forwarded, start)],
        states={
            SELECT_ACTION: [CallbackQueryHandler(button_click)],
            EDIT_CAPTION: [MessageHandler(Filters.text & ~Filters.command, edit_caption)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()