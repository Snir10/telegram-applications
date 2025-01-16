from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, ConversationHandler
import sqlite3
import schedule
import time
import threading

# Telegram Bot Token
BOT_TOKEN = "7887654568:AAE38OGqlb46abFe9Jflq5DMT3X3Vcd30Xo"

# Database setup
DB_NAME = "scheduler_bot.db"

# Connect to the database
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_data (
            user_id INTEGER PRIMARY KEY,
            message TEXT
        )
    """)
    conn.commit()
    conn.close()

# Save user message to the database
def save_user_data(user_id, message):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("REPLACE INTO user_data (user_id, message) VALUES (?, ?)", (user_id, message))
    conn.commit()
    conn.close()

# Get user message from the database
def get_user_data(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT message FROM user_data WHERE user_id = ?", (user_id,))
    data = cursor.fetchone()
    conn.close()
    return data[0] if data else None

# Telegram Bot setup
updater = Updater(BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Conversation states
WAITING_FOR_TEXT = 1

# Start command handler
def start(update, context):
    update.message.reply_text("Welcome! Please send me a text that you'd like scheduled.")
    return WAITING_FOR_TEXT

# Handle user text input
def handle_text_input(update, context):
    user_id = update.message.from_user.id
    user_message = update.message.text

    # Save the user input to the database
    save_user_data(user_id, user_message)

    # Send a message with scheduling options
    keyboard = [
        [InlineKeyboardButton("Every 15s", callback_data="15s")],
        [InlineKeyboardButton("Every 30s", callback_data="30s")],
        [InlineKeyboardButton("Every 1m", callback_data="1m")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Choose your scheduling option:", reply_markup=reply_markup)

    return ConversationHandler.END

# Scheduler function
def schedule_task(interval, user_id, context):
    def send_scheduled_message():
        user_message = get_user_data(user_id)
        if user_message:
            context.bot.send_message(
                chat_id=user_id,
                text=f"Scheduled message: {user_message}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("View Post", url="https://example.com/post")]
                ])
            )
    if interval == "15s":
        schedule.every(15).seconds.do(send_scheduled_message)
    elif interval == "30s":
        schedule.every(30).seconds.do(send_scheduled_message)
    elif interval == "1m":
        schedule.every(1).minutes.do(send_scheduled_message)

# Handle button callbacks
def button_callback(update, context):
    query = update.callback_query
    query.answer()
    interval = query.data  # Get the selected interval (e.g., "15s", "30s", or "1m")
    user_id = query.from_user.id

    # Set up the scheduler
    schedule_task(interval, user_id, context)

    # Send confirmation message
    query.edit_message_text(f"Scheduler started! Sending messages every {interval}.")

# Run scheduled tasks in a separate thread
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Add command and handlers
dispatcher.add_handler(ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        WAITING_FOR_TEXT: [MessageHandler(Filters.text & ~Filters.command, handle_text_input)]
    },
    fallbacks=[]
))
dispatcher.add_handler(CallbackQueryHandler(button_callback))

# Initialize the database
init_db()

# Start the scheduler thread
threading.Thread(target=run_scheduler, daemon=True).start()

# Start the bot
print("Bot is running...")
updater.start_polling()
updater.idle()
