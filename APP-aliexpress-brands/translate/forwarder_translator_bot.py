from time import sleep

from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters
from easygoogletranslate import EasyGoogleTranslate
import sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
import logging

#Manipulate DB
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        msg_type TEXT,
        content TEXT,
        caption TEXT
    )
    """)
    conn.commit()
    conn.close()
    logger.info("Database initialized.")
# Insert Message into DB
def save_message(msg_type, content, caption):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO messages (msg_type, content, caption) VALUES (?, ?, ?)",
                       (msg_type, content, caption))
        conn.commit()
        conn.close()
        logger.info(f"Message saved: {msg_type}, {caption}")
    except Exception as e:
        logger.error(f"Error saving message: {e}")
# Delete Message from DB
def delete_message(msg_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE id = ?", (msg_id,))
        conn.commit()
        conn.close()
        logger.info(f"Message with ID {msg_id} deleted.")
    except Exception as e:
        logger.error(f"Error deleting message: {e}")
# Delete Message Caption from DB
def update_caption(msg_id, new_caption):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE messages SET caption = ? WHERE id = ?", (new_caption, msg_id))
        conn.commit()
        conn.close()
        logger.info(f"Caption updated for ID {msg_id}.")
    except Exception as e:
        logger.error(f"Error updating caption: {e}")
# Fetch Message by ID
def fetch_message_by_id(msg_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, msg_type, content, caption FROM messages WHERE id = ?", (msg_id,))
        message = cursor.fetchone()
        conn.close()
        logger.info(f"Fetched message with ID {msg_id}.")
        return message
    except Exception as e:
        logger.error(f"Error fetching message by ID: {e}")
        return None
# Fetch All Messages
def fetch_messages():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, msg_type, content, caption FROM messages")
    messages = cursor.fetchall()
    conn.close()
    return messages


#Features
#persistent menu keyboard
def get_persistent_menu():
    keyboard = [
        ["/start"],  # A button to re-trigger the /start command
        # ["/delete", "/view"],  # Options for deletion and viewing posts
        # ["/help"]  # Add other commands as necessary
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
# Check if message is from you
def is_from_me(update):
    return update.message.from_user.id == MY_USER_ID

#functional methods

#callback methods
def edit_text_callback(update, context):
    query = update.callback_query
    msg_id = query.data.split(":")[1]
    query.answer("Please send the new text.")
    context.user_data['edit_msg_id'] = msg_id
def send_to_channel_callback(update, context):
    query = update.callback_query
    db_id, channel = query.data.split(":")[1], query.data.split(":")[2]  # Extract message ID and channel name from callback data
    query.answer("Sending post to the channel...")

    # Fetch the message from the database
    message = fetch_message_by_id(db_id)
    if message:
        msg_type, content, caption = message[1], message[2], message[3]
        try:
            # Send the message to the specified channel
            if msg_type == "photo":
                context.bot.send_photo(chat_id=channel, photo=content, caption=caption)
            elif msg_type == "video":
                context.bot.send_video(chat_id=channel, video=content, caption=caption)
            elif msg_type == "document":
                context.bot.send_document(chat_id=channel, document=content, caption=caption)
            elif msg_type == "forwarded_text":
                context.bot.send_message(chat_id=channel, text=content or caption)

            # query.answer(f"Message successfully sent to {channel}.")

            query.edit_message_text(f"Message successfully sent to {channel}.")
        except Exception as e:
            # query.answer(f"Failed to send the message to {channel}: {e}")
            query.edit_message_text(f"Failed to send the message to {channel}: {e}")
    else:
        # query.answer(f"Message with ID {db_id} not found.")
        query.edit_message_text(f"Message with ID {db_id} not found.")
def translate_callback(update, context):
    query = update.callback_query
    msg_id = query.data.split(":")[1]  # Extract the message ID from callback data
    query.answer("Translating...")

    # Fetch the message from the database
    message = fetch_message_by_id(msg_id)
    if message:
        db_id, msg_type, content, caption = message
        translated_caption = translator.translate(caption) if caption else "No caption to translate."

        # Update the caption in the database
        update_caption(msg_id, translated_caption)

        # Retrieve the sent message ID for editing
        sent_message_id = context.user_data.get(f"msg_{msg_id}")

        try:
            # Edit the original message caption or text
            if msg_type == "photo":
                context.bot.edit_message_caption(chat_id=query.message.chat_id,
                                                 message_id=sent_message_id,
                                                 caption=translated_caption)
            elif msg_type == "video":
                context.bot.edit_message_caption(chat_id=query.message.chat_id,
                                                 message_id=sent_message_id,
                                                 caption=translated_caption)
            elif msg_type == "document":
                context.bot.edit_message_caption(chat_id=query.message.chat_id,
                                                 message_id=sent_message_id,
                                                 caption=translated_caption)
            elif msg_type == "forwarded_text":
                context.bot.edit_message_text(chat_id=query.message.chat_id,
                                              message_id=sent_message_id,
                                              text=translated_caption)

            query.answer("Translation applied to the original post.")
        except Exception as e:
            logger.error(f"Failed to edit message: {e}")
            query.answer(f"Failed to edit the message: {e}")
    else:
        query.message.reply_text(f"Message with ID {msg_id} not found.")
def delete_callback(update, context):
    query = update.callback_query
    msg_id = query.data.split(":")[1]
    delete_message(msg_id)
    query.answer(f"Post ID {msg_id} deleted.")
    query.edit_message_text("This post has been deleted.")

#message handler methods
def receive_new_text(update, context):
    if 'edit_msg_id' in context.user_data:
        msg_id = context.user_data.pop('edit_msg_id')
        new_text = update.message.text
        update_caption(msg_id, new_text)
        update.message.reply_text(f"Caption for message ID {msg_id} updated.")
# Handle replies to the bot's request for a channel username


# Handle receiving the channel username (channel ID or @username)
# Handle Caption Update
def update_caption_command(update, context):
    if not is_from_me(update):
        return
    args = context.args
    if len(args) < 2:
        update.message.reply_text("Usage: /update <id> <new_caption>")
        return

    msg_id = int(args[0])
    new_caption = ' '.join(args[1:])
    update_caption(msg_id, new_caption)
    update.message.reply_text(f"Caption updated for ID {msg_id}.")


def error_handler(update, context):
    logger.error(f"Update {update} caused error {context.error}")

# Handle /start command
def start(update, context):
    logger.info("Received /start command.")
    if not is_from_me(update):
        return

    update.message.reply_text("Here is your post history. Use the buttons below each post to manage your posts:",
                              reply_markup=get_persistent_menu())

    messages = fetch_messages()
    if not messages:
        update.message.reply_text("No messages found.")
        return

    for db_id, msg_type, content, caption in messages:
        try:
            sent_message = None
            if msg_type == "photo":
                sent_message = context.bot.send_photo(chat_id=update.message.chat_id, photo=content, caption=caption)
            elif msg_type == "video":
                sent_message = context.bot.send_video(chat_id=update.message.chat_id, video=content, caption=caption)
            elif msg_type == "document":
                sent_message = context.bot.send_document(chat_id=update.message.chat_id, document=content,
                                                         caption=caption)
            elif msg_type == "forwarded_text":
                sent_message = context.bot.send_message(chat_id=update.message.chat_id, text=content or caption)

            if sent_message:
                # Save sent message ID to user_data for later edits
                context.user_data[f"msg_{db_id}"] = sent_message.message_id

            keyboard = [
                [InlineKeyboardButton("Edit Text", callback_data=f"edit:{db_id}"),
                 InlineKeyboardButton("Delete Post", callback_data=f"delete:{db_id}"),
                 InlineKeyboardButton("Translate", callback_data=f"translate:{db_id}")]
            ]

            channel_buttons = [InlineKeyboardButton(f"Send to {channel}", callback_data=f"send:{db_id}:{channel}")
                               for channel in SUGGESTED_CHANNELS]
            if channel_buttons:
                keyboard.append(channel_buttons)

            reply_markup = InlineKeyboardMarkup(keyboard)
            context.bot.send_message(chat_id=update.message.chat_id,
                                     text=f"Actions for DB Entry ID {db_id}:", reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"Error processing message ID {db_id}: {e}")
            update.message.reply_text(f"Error processing message ID {db_id}: {e}")


# Handle /delete command
def delete_command(update, context):
    if not is_from_me(update):
        return
    if not context.args:
        update.message.reply_text("Usage: /delete <id>")
        return

    try:
        msg_id = int(context.args[0])
        delete_message(msg_id)
        update.message.reply_text(f"Message with ID {msg_id} has been deleted.")
    except ValueError:
        update.message.reply_text("Please provide a valid numeric ID.")
    except Exception as e:
        update.message.reply_text(f"Error: {e}")
# Handle /view command
def view_command(update, context):
    if not is_from_me(update):
        return
    if not context.args:
        update.message.reply_text("Usage: /view <id>")
        return

    try:
        msg_id = int(context.args[0])
        message = fetch_message_by_id(msg_id)
        if message:
            msg_id, msg_type, content, caption = message
            text = f"ID: {msg_id}\nType: {msg_type}\nContent: {content}\nCaption: {caption or 'No caption'}"
            update.message.reply_text(text)
        else:
            update.message.reply_text(f"No message found with ID {msg_id}.")
    except ValueError:
        update.message.reply_text("Please provide a valid numeric ID.")
    except Exception as e:
        update.message.reply_text(f"Error: {e}")
# Forward and Save Media
def forward_media(update, context):
    message = update.message
    if not message:
        return  # Ignore if there's no message

    # Handle forwarded messages specifically
    if message.forward_date:
        if message.text:
            # Forwarded plain text message
            logger.info(f"Forwarded text: {message.text}")
            save_message("forwarded_text", None, message.text)
            update.message.reply_text("Forwarded text stored.")
        elif message.photo:
            # Forwarded photo
            logger.info("Forwarded photo detected.")
            save_message("photo", message.photo[-1].file_id, message.caption or "")
            update.message.reply_text("Forwarded photo stored.")
        elif message.video:
            # Forwarded video
            logger.info("Forwarded video detected.")
            save_message("video", message.video.file_id, message.caption or "")
            update.message.reply_text("Forwarded video stored.")
        elif message.document:
            # Forwarded document
            logger.info("Forwarded document detected.")
            save_message("document", message.document.file_id, message.caption or "")
            update.message.reply_text("Forwarded document stored.")
        else:
            # Unsupported forwarded content
            update.message.reply_text("Unsupported forwarded content.")

    # Handle non-forwarded messages
    elif message.text:
        logger.info(f"Regular text: {message.text}")
        save_message("text", None, message.text)
        update.message.reply_text("Text stored.")
    elif message.photo:
        logger.info("Regular photo detected.")
        save_message("photo", message.photo[-1].file_id, message.caption or "")
        update.message.reply_text("Photo stored.")
    elif message.video:
        logger.info("Regular video detected.")
        save_message("video", message.video.file_id, message.caption or "")
        update.message.reply_text("Video stored.")
    elif message.document:
        logger.info("Regular document detected.")
        save_message("document", message.document.file_id, message.caption or "")
        update.message.reply_text("Document stored.")
    else:
        update.message.reply_text("Unsupported message type.")

# Main function
def main():
    init_db()

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("update", update_caption_command))
    dp.add_handler(CommandHandler("delete", delete_command))
    dp.add_handler(CommandHandler("view", view_command))

    dp.add_handler(CallbackQueryHandler(edit_text_callback, pattern="^edit:"))
    dp.add_handler(CallbackQueryHandler(delete_callback, pattern="^delete:"))
    dp.add_handler(CallbackQueryHandler(send_to_channel_callback, pattern="^send:"))
    dp.add_handler(CallbackQueryHandler(translate_callback, pattern="^translate:"))

    dp.add_handler(MessageHandler(Filters.text & ~Filters.forwarded, receive_new_text))
    dp.add_handler(MessageHandler(Filters.photo | Filters.video | Filters.document | Filters.forwarded, forward_media))

    dp.add_error_handler(error_handler)

    updater.start_polling()
    logger.info("Bot started polling.")
    updater.idle()# Initialize Database
DB_PATH = "messages.db"
# Your bot token
TOKEN = '6793212722:AAEiE1tzn3nSRechCMj_LG8TYF7fk8A2C2M' #tester bot
MY_USER_ID = 516389439
translator = EasyGoogleTranslate(source_language='he', target_language='en', timeout=15)
# Predefined channels (optional, for suggestions)
SUGGESTED_CHANNELS = [
    "@israelstateisunderattack",
    "-1001885191160"]

# Initialize logging
logging.basicConfig(
    format='%(asctime)s | %(levelname)s | %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    main()