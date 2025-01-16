import logging
import sqlite3
import schedule
import time
from threading import Thread
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, ConversationHandler
import random
import string


# Constants
BOT_TOKEN = "7887654568:AAE38OGqlb46abFe9Jflq5DMT3X3Vcd30Xo"
CHAT_ID = "-1001885191160"  # Real channel/chat ID
ADMIN_USER_ID = 516389439
# Database setup
DB_NAME = "bot_ads.db"

# Initialize logging
logging.basicConfig(
    format='%(asctime)s | %(levelname)s | %(message)s',
    level=logging.INFO)
logger = logging.getLogger()



# Admin approval logic
# import sqlite3

def approve_request(update, context):
    query = update.callback_query
    query.answer('Sending to scheduler...')

    logger.info('Started approving process.')

    req_id = int(query.data.split("_")[1])  # Extract the req_id from callback data
    user_id = query.from_user.id

    # Ensure only admins can approve ads
    if user_id != ADMIN_USER_ID:
        query.edit_message_text("You are not authorized to approve ads.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        # Check if the request exists and is pending approval
        cursor.execute("""
            SELECT user_id, message, media_id, media_type, caption, campaign_rate 
            FROM user_requests 
            WHERE req_id = ? AND approval_status = 'Pending'
        """, (req_id,))
        ad_data = cursor.fetchone()

        if not ad_data:
            query.edit_message_text("Request not found or already processed.")
            return

        # Unpack the ad data
        user_id, message, media_id, media_type, caption, campaign_rate = ad_data

        # Generate a new ad_id (or let the DB handle it if auto-incremented)
        cursor.execute("""
            INSERT INTO active_ads (request_id, user_id, message, media_id, media_type, caption, campaign_rate, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (req_id, user_id, message, media_id, media_type, caption, campaign_rate, 'Running'))

        # Get the auto-generated ad_id
        ad_id = cursor.lastrowid  # SQLite's method for the last inserted row

        # Update the request's approval status
        cursor.execute("""
            UPDATE user_requests 
            SET approval_status = 'Approved' 
            WHERE req_id = ?
        """, (req_id,))
        conn.commit()

        # Notify the user about the approval
        query.edit_message_text(f"Ad {ad_id} has been approved. Campaign is being prepared to run.")

        logger.info(f"Ad {ad_id} approved. Scheduling task...")

        # Schedule the task for this ad
        schedule_task(campaign_rate, context, user_id, message, media_id, media_type, caption)

        logger.info(f"Ad {ad_id} scheduled successfully.")
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error while approving ad for req_id {req_id}: {e}")
        query.edit_message_text("Failed to approve the ad due to a database error.")
    except Exception as e:
        logger.error(f"Unexpected error while approving ad for req_id {req_id}: {e}")
        query.edit_message_text("Failed to approve the ad due to an unexpected error.")
    finally:
        conn.close()
# Initialize Database
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Drop the table if it exists (for testing purposes)
    cursor.execute("DROP TABLE IF EXISTS user_requests")

    # Recreate the user_requests table with the required columns
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_requests (
            req_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT,
            media_id TEXT,
            media_type TEXT,
            caption TEXT,
            campaign_rate TEXT,
            voucher_num TEXT,
            approval_status TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS active_ads (
            ad_id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INT NOT NULL REFERENCES user_requests(request_id),
            user_id INTEGER,
            message TEXT,
            media_id TEXT,
            media_type TEXT,
            caption TEXT,
            campaign_rate TEXT,
            status TEXT
            
            
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vouchers (
            voucher_code TEXT PRIMARY KEY,
            issued_by INTEGER
        )
    """)

    conn.commit()
    conn.close()
# New function to get running campaigns from the database
def get_running_campaigns():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT ad_id, user_id, message, media_id, media_type, caption, campaign_rate FROM active_ads WHERE status='running'")
    active_campaigns = cursor.fetchall()
    conn.close()
    return active_campaigns
# Command to show running campaigns
def check_column_exists():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(active_ads);")
    columns = cursor.fetchall()
    conn.close()
    return any(column[1] == 'status' for column in columns)
# def add_status_column():
#     if not check_column_exists():
#         conn = sqlite3.connect(DB_NAME)
#         cursor = conn.cursor()
#         cursor.execute("ALTER TABLE active_ads ADD COLUMN status TEXT DEFAULT 'stopped'")
#         conn.commit()
#         conn.close()
#     else:
#         logger.info("The 'status' column already exists.")
def show_running_campaign(update, context):
    user_id = update.message.from_user.id
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Make sure you're checking for 'running' status
    cursor.execute(
        "SELECT ad_id, user_id, message, media_id, media_type, caption, campaign_rate, status FROM active_ads WHERE status='running'")
    active_campaigns = cursor.fetchall()
    conn.close()

    if not active_campaigns:
        update.message.reply_text("There are no running campaigns.")
        return

    for campaign in active_campaigns:
        ad_id, user_id, message, media_id, media_type, caption, campaign_rate, status = campaign
        toggle_button = InlineKeyboardButton("Stop Campaign" if status == 'running' else "Start Campaign",
                                             callback_data=f"toggle_{ad_id}")
        keyboard = [[toggle_button]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(f"Campaign: {message}\nStatus: {status}", reply_markup=reply_markup)
# Call the function to add the 'status' column if it doesn't exist yet

#TODO: implement it on a active campaigns
def toggle_campaign_status(update, context):
    query = update.callback_query
    query.answer()

    ad_id = int(query.data.split("_")[1])  # Extract ad_id from callback data

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        # Get current status
        cursor.execute("SELECT status FROM active_ads WHERE ad_id=?", (ad_id,))
        result = cursor.fetchone()

        if result:
            current_status = result[0]
            new_status = 'stopped' if current_status == 'running' else 'running'

            # Update the campaign status
            cursor.execute("UPDATE active_ads SET status=? WHERE ad_id=?", (new_status, ad_id))
            conn.commit()

            query.edit_message_text(f"Campaign {ad_id} status changed to: {new_status.capitalize()}.")
            logger.info(f"Campaign {ad_id} status changed to {new_status}.")
        else:
            query.edit_message_text("Campaign not found.")
    except Exception as e:
        logger.error(f"Error toggling campaign status for ad {ad_id}: {e}")
        query.edit_message_text("Failed to toggle campaign status.")
    finally:
        conn.close()
# Callback function for button press
#TODO: implement it on a active campaigns
def toggle_campaign(update, context):
    query = update.callback_query
    query.answer()
    action_data = query.data.split("_")
    action = action_data[0]
    ad_id = int(action_data[1])

    # Handle toggling the campaign status in the database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if action == "stop":
        cursor.execute("UPDATE active_ads SET status='stopped' WHERE ad_id=?", (ad_id,))
        query.edit_message_text(f"Campaign {ad_id} has been stopped.")
        logger.info(f"Campaign {ad_id} stopped.")
    elif action == "toggle":
        cursor.execute("SELECT status FROM active_ads WHERE ad_id=?", (ad_id,))
        current_status = cursor.fetchone()[0]
        new_status = 'running' if current_status == 'stopped' else 'stopped'
        cursor.execute("UPDATE active_ads SET status=? WHERE ad_id=?", (new_status, ad_id))
        query.edit_message_text(f"Campaign {ad_id} is now {new_status}.")
        logger.info(f"Campaign {ad_id} toggled to {new_status}.")

    conn.commit()
    conn.close()


def get_persistent_menu():
    keyboard = [
        ["/request_to_publish"],  # A button to re-trigger the /start command
        ["/show_requests"],  # Options for deletion and viewing posts
        ["/show_running_campaign"],  # Options for deletion and viewing posts
        ["/generate_voucher"],  # A button to re-trigger the /start command

        # ["/help"]  # Add other commands as necessary
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
# Initialize with a starting ad_id value
# HARDCODED_AD_ID = 1000

# Initialize with a starting ad_id value
def save_user_request(user_id, message, media_id, media_type, caption, campaign_rate, voucher_num, approval_status="Pending"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        # Insert into user_requests table, omitting req_id
        cursor.execute("""
            INSERT INTO user_requests (user_id, message, media_id, media_type, caption, campaign_rate, voucher_num, approval_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, message, media_id, media_type, caption, campaign_rate, voucher_num, approval_status))

        # Retrieve the auto-generated req_id
        req_id = cursor.lastrowid
        logger.info(f"New request ID: {req_id}")

        conn.commit()
        logger.info(f"User request saved successfully with req_id {req_id}.")
    except sqlite3.IntegrityError as e:
        logger.error(f"Failed to save user request: {e}")
    finally:
        conn.close()

#DB functions
# Send scheduled media + caption
def send_scheduled_message(context, user_id, message, media_id, media_type, caption):
    logger.info(f"Sending scheduled message to user {user_id}: {message} with media {media_type}")
    if media_type == "photo":
        context.bot.send_photo(chat_id=CHAT_ID, photo=media_id, caption=caption)
    elif media_type == "video":
        context.bot.send_video(chat_id=CHAT_ID, video=media_id, caption=caption)
    elif media_type == "audio":
        context.bot.send_audio(chat_id=CHAT_ID, audio=media_id, caption=caption)
    else:
        context.bot.send_message(chat_id=CHAT_ID, text=message)
# Scheduler function
def schedule_task(interval, context, user_id, message, media_id, media_type, caption):
    logger.info(f"Scheduling message every {interval} for user {user_id}.")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        # Update the ad status to 'running'
        cursor.execute("""
            UPDATE active_ads
            SET status = 'running'
            WHERE user_id = ? AND message = ? AND media_id = ?
        """, (user_id, message, media_id))
        conn.commit()

        # Define the job
        def scheduled_job():
            send_scheduled_message(context, user_id, message, media_id, media_type, caption)

        # Schedule the job
        if interval == "15s":
            schedule.every(15).seconds.do(scheduled_job)
        elif interval == "30s":
            schedule.every(30).seconds.do(scheduled_job)
        elif interval == "1m":
            schedule.every(1).minute.do(scheduled_job)

    except Exception as e:
        logger.error(f"Error scheduling task: {e}")
    finally:
        conn.close()
# Run scheduled tasks in a separate thread
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)
# Telegram Bot setup
updater = Updater(BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher
# Conversation states
WAITING_FOR_MESSAGE = 1
WAITING_FOR_VOUCHER = 2
def start(update, context):
    logger.info(f"User {update.message.from_user.id} started the conversation.")
    update.message.reply_text("Here is your post history. Use the buttons below each post to manage your posts:",
                              reply_markup=get_persistent_menu())
    update.message.reply_text("Welcome! Please send a /request_to_publish to get started.")
    return ConversationHandler.END
def request_to_publish(update, context):
    user_id = update.message.from_user.id
    logger.info(f"User {user_id} is requesting to publish an ad.")
    update.message.reply_text(
        "Please upload or forward your media and text message. The message will be sent to the pre-selected channel.")
    return WAITING_FOR_MESSAGE
def handle_uploaded_message(update, context):
    user_id = update.message.from_user.id
    message = update.message.text
    caption = update.message.caption if update.message.caption else "No caption provided."
    media_type = None
    media_id = None

    # Handle different media types
    if update.message.photo:
        media_type = "photo"
        media_id = update.message.photo[-1].file_id  # Get the highest resolution photo
    elif update.message.video:
        media_type = "video"
        media_id = update.message.video.file_id
    elif update.message.audio:
        media_type = "audio"
        media_id = update.message.audio.file_id

    logger.info(f"User {user_id} uploaded media: {media_type}, caption: {caption}")

    # Store the media and message in context.user_data for later use in button callback
    context.user_data['message'] = message
    context.user_data['media_id'] = media_id
    context.user_data['media_type'] = media_type
    context.user_data['caption'] = caption

    # Default campaign rate
    campaign_rate = "15s"  # This will be updated once the user selects it


    # Save the user request with a placeholder campaign rate and "Pending" status
    save_user_request(user_id, message, media_id, media_type, caption, campaign_rate, "", "Pending")

    update.message.reply_text("Set your campaign rate: Every 15s, 30s, 1m.")
    keyboard = [
        [InlineKeyboardButton("Every 15s", callback_data="15s")],
        [InlineKeyboardButton("Every 30s", callback_data="30s")],
        [InlineKeyboardButton("Every 1m", callback_data="1m")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Choose your campaign rate:", reply_markup=reply_markup)
    return WAITING_FOR_VOUCHER
def handle_voucher_number(update, context):
    user_id = update.message.from_user.id
    voucher_num = update.message.text
    campaign_rate = context.user_data.get('campaign_rate')

    # Validate voucher number (you can implement any logic here)
    logger.info(f"User {user_id} entered voucher number: {voucher_num}")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Check if the voucher number exists
    cursor.execute("SELECT * FROM vouchers WHERE voucher_code=?", (voucher_num,))
    voucher = cursor.fetchone()

    if not voucher:
        # Voucher doesn't exist
        update.message.reply_text("Invalid voucher number. Please enter a valid voucher.")
        conn.close()
        return

    # Voucher is valid, proceed to store the ad as 'running'
    cursor.execute(""" 
        INSERT INTO active_ads (user_id, message, media_id, media_type, caption, campaign_rate, status)
        VALUES (?, ?, ?, ?, ?, ?, 'running')
    """, (user_id, context.user_data['message'], context.user_data['media_id'],
          context.user_data['media_type'], context.user_data['caption'], campaign_rate))
    conn.commit()

    # Update the voucher table to reflect it was used
    cursor.execute("UPDATE vouchers SET issued_by = ? WHERE voucher_code=?", (user_id, voucher_num))
    conn.commit()

    # Close the database connection
    conn.close()

    # Start the campaign by scheduling the task
    schedule_task(campaign_rate, context, user_id, context.user_data['message'], context.user_data['media_id'],
                  context.user_data['media_type'], context.user_data['caption'])

    update.message.reply_text(f"Campaign has started with voucher {voucher_num}. It will run every {campaign_rate}.")
    logger.info(f"Campaign for user {user_id} has started with voucher {voucher_num} and rate {campaign_rate}.")

    return ConversationHandler.END
# Function to generate a random voucher code
def generate_voucher_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
# Command handler to generate a voucher
def generate_voucher(update, context):
    user_id = update.message.from_user.id

    # Generate a new voucher code
    voucher_code = generate_voucher_code()

    # Store the voucher in the database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO vouchers (voucher_code, issued_by)
        VALUES (?, ?)
    """, (voucher_code, user_id))
    conn.commit()
    conn.close()

    # Notify the user with the generated voucher code
    update.message.reply_text(f"Your voucher code is: {voucher_code}\nUse it to activate a campaign.")
    logger.info(f"Voucher {voucher_code} generated for user {user_id}.")
def button_callback(update, context):
    query = update.callback_query
    query.answer()
    campaign_rate = query.data  # Selected campaign rate (15s, 30s, or 1m)
    user_id = query.from_user.id

    logger.info(f"User {user_id} selected campaign rate: {campaign_rate}")

    # Update user campaign rate in database
    context.user_data['campaign_rate'] = campaign_rate
    save_user_request(user_id, context.user_data['message'], context.user_data['media_id'],
                      context.user_data['media_type'], context.user_data['caption'], campaign_rate,
                      context.user_data.get('voucher_num'), "Pending")

    # Start the scheduler for sending the message
    # schedule_task(campaign_rate, context, user_id, context.user_data['message'], context.user_data['media_id'],
    #               context.user_data['media_type'], context.user_data['caption'])

    query.edit_message_text(f"Your ad has been submitted for approval. Campaign rate: {campaign_rate}.")
    logger.info(f"Ad submitted for user {user_id} with campaign rate: {campaign_rate}.")

    return ConversationHandler.END
def add_ad_id_column():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Check if the column exists before attempting to add it
    try:
        cursor.execute("ALTER TABLE user_requests ADD COLUMN ad_id INTEGER")
    except sqlite3.OperationalError:
        # Column already exists
        pass

    conn.commit()
    conn.close()
# add_ad_id_column()


# Define the function to handle the /show_requests command
# Admin views pending requests
def show_requests(update, context):
    user_id = update.message.from_user.id

    # Verify admin privileges
    if user_id != ADMIN_USER_ID:
        update.message.reply_text("You are not authorized to view the requests.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        # Fetch pending requests
        cursor.execute("""
            SELECT req_id, user_id, message, media_id, media_type, caption, campaign_rate 
            FROM user_requests 
            WHERE approval_status = 'Pending'
        """)
        pending_requests = cursor.fetchall()

        if not pending_requests:
            update.message.reply_text("No pending requests found.")
            logger.info("No pending requests found in the database.")
            return

        # Display each pending request
        for request in pending_requests:
            ad_id, user_id, message, media_id, media_type, caption, campaign_rate = request
            logger.info(f"Fetched pending ad: ID={ad_id}, User={user_id}, Rate={campaign_rate}")

            # Display ad preview and approval options
            if media_type == "photo":
                update.message.reply_photo(
                    photo=media_id,
                    caption=f"Ad preview: {message}\nRate: {campaign_rate}\nAd ID: {ad_id}"
                )
            elif media_type == "video":
                update.message.reply_video(
                    video=media_id,
                    caption=f"Ad preview: {message}\nRate: {campaign_rate}\nAd ID: {ad_id}"
                )
            elif media_type == "audio":
                update.message.reply_audio(
                    audio=media_id,
                    caption=f"Ad preview: {message}\nRate: {campaign_rate}\nAd ID: {ad_id}"
                )
            else:
                update.message.reply_text(f"Ad preview: {message}\nRate: {campaign_rate}\nAd ID: {ad_id}")

            # Inline buttons for approve/decline
            keyboard = [
                [InlineKeyboardButton("Approve", callback_data=f"approve_{ad_id}")],
                [InlineKeyboardButton("Decline", callback_data=f"decline_{ad_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text("Choose an action:", reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"Error fetching pending requests: {e}")
        update.message.reply_text("Failed to fetch pending requests due to a database error.")
    finally:
        conn.close()
# Add handlers for user flow
dispatcher.add_handler(CommandHandler("start", start))
# Add handler for /show_requests
show_requests_handler = CommandHandler('show_requests', show_requests)
# Add new command to dispatcher
dispatcher.add_handler(CommandHandler("show_running_campaign", show_running_campaign))
# dispatcher.add_handler(CallbackQueryHandler(toggle_campaign, pattern=r"^(stop|toggle)_(\d+)$"))
dispatcher.add_handler(CallbackQueryHandler(toggle_campaign_status, pattern=r"^toggle_\d+$"))
# Add the generate_voucher command handler to the dispatcher
dispatcher.add_handler(show_requests_handler)
dispatcher.add_handler(CommandHandler("generate_voucher", generate_voucher))
approve_button_handler = CallbackQueryHandler(approve_request, pattern=r"^approve_\d+$")
dispatcher.add_handler(approve_button_handler)
dispatcher.add_handler(ConversationHandler(
    entry_points=[CommandHandler("request_to_publish", request_to_publish)],
    states={
        WAITING_FOR_MESSAGE: [
            MessageHandler(Filters.text | Filters.photo | Filters.video | Filters.audio & ~Filters.command,
                           handle_uploaded_message)],
        WAITING_FOR_VOUCHER: [MessageHandler(Filters.text & ~Filters.command, handle_voucher_number)],
    },
    fallbacks=[CallbackQueryHandler(button_callback)],
))
# Run the scheduler thread
Thread(target=run_scheduler, daemon=True).start()
init_db()
# add_status_column()
# add_ad_id_column()
# Run the bot
logger.info("Starting the bot.")
updater.start_polling()
updater.idle()
