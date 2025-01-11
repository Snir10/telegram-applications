import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from easygoogletranslate import EasyGoogleTranslate
import sqlite3

# Initialize Database
DB_PATH = "messages.db"

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

# Insert Message into DB
def save_message(msg_type, content, caption):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (msg_type, content, caption) VALUES (?, ?, ?)",
                   (msg_type, content, caption))
    conn.commit()
    conn.close()

# Fetch All Messages
def fetch_messages():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, msg_type, content, caption FROM messages")
    messages = cursor.fetchall()
    conn.close()
    return messages

# Update Caption
def update_caption(msg_id, new_caption):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE messages SET caption = ? WHERE id = ?", (new_caption, msg_id))
    conn.commit()
    conn.close()

# Your bot token
TOKEN = '6793212722:AAEzIblbhY6umTW9V9AlxVjS-k_Msa219J8'
MY_USER_ID = 516389439
translator = EasyGoogleTranslate(source_language='he', target_language='en', timeout=10)

# Check if message is from you
def is_from_me(update):
    return update.message.from_user.id == MY_USER_ID


# Handle `/start` command
def start(update, context):
    if not is_from_me(update):
        return
    messages = fetch_messages()
    if not messages:
        update.message.reply_text("No messages found.")
        return

    for msg_id, msg_type, content, caption in messages:
        caption_text = f"ID: {msg_id}\nTEXT: {caption or 'No caption'}"

        # Send message based on type
        try:
            if msg_type == "photo":
                context.bot.send_photo(chat_id=update.message.chat_id, photo=content, caption=caption_text)
            elif msg_type == "video":
                context.bot.send_video(chat_id=update.message.chat_id, video=content, caption=caption_text)
            elif msg_type == "document":
                context.bot.send_document(chat_id=update.message.chat_id, document=content, caption=caption_text)
            elif msg_type == "text":
                context.bot.send_message(chat_id=update.message.chat_id, text=caption_text)
        except Exception as e:
            update.message.reply_text(f"Error sending message ID {msg_id}: {e}")


# Forward and Save Media
def forward_media(update, context):
    message = update.message
    if not is_from_me(update):
        return  # Ignore messages from others

    if message.photo:
        content = message.photo[-1].file_id
        caption = message.caption or ''
        save_message("photo", content, caption)

    elif message.video:
        content = message.video.file_id
        caption = message.caption or ''
        save_message("video", content, caption)

    elif message.document:
        content = message.document.file_id
        caption = message.caption or ''
        save_message("document", content, caption)

    elif message.text:
        content = message.text
        save_message("text", content, '')

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


# Delete Message from DB
def delete_message(msg_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE id = ?", (msg_id,))
    conn.commit()
    conn.close()

# Handle `/delete` command
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

# Fetch Message by ID
def fetch_message_by_id(msg_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, msg_type, content, caption FROM messages WHERE id = ?", (msg_id,))
    message = cursor.fetchone()
    conn.close()
    return message

# Handle `/view` command
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


# Main function
def main():
    init_db()
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("update", update_caption_command))
    dp.add_handler(CommandHandler("delete", delete_command))
    dp.add_handler(CommandHandler("view", view_command))

    dp.add_handler(MessageHandler(Filters.photo | Filters.video | Filters.document | Filters.text, forward_media))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
