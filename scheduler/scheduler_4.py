import logging
import sqlite3

from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, ConversationHandler
import random
import string
from pytz import timezone
from pytz import utc  # Import pytz for timezone handling
from apscheduler.events import EVENT_JOB_ADDED, EVENT_JOB_REMOVED, EVENT_JOB_EXECUTED, EVENT_JOB_ERROR


def approve_request(update, context):
    query = update.callback_query
    query.answer('Sending to scheduler...')

    # logger.info('Started approving process.')

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
        query.edit_message_text(f"Ad {req_id} has been approved. Campaign is being prepared to run.")

        logger.info(f"Req ID:{req_id} approved. Scheduling task...")

        # Schedule the task for this ad
        schedule_task(campaign_rate, user_id, message, media_id, media_type, caption)

        logger.info(f"Ad {ad_id} scheduled successfully.")
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error while approving ad for req_id {req_id}: {e}")
        query.edit_message_text("Failed to approve the ad due to a database error.")
    except Exception as e:
        logger.error(f"Unexpected error while approving ad for req_id {req_id}: {e}")
        query.edit_message_text("Failed to approve the ad due to an unexpected error.")
    finally:
        conn.close()
def init_db():
    """Initialize the database and ensure all necessary tables exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Drop tables (for testing only, remove in production)
    cursor.execute("DROP TABLE IF EXISTS user_requests")  # Only for testing
    cursor.execute("DROP TABLE IF EXISTS active_ads")  # Only for testing
    cursor.execute("DROP TABLE IF EXISTS vouchers")  # Only for testing

    # Create tables if they don't exist
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
            request_id INT NOT NULL REFERENCES user_requests(req_id),
            user_id INTEGER,
            message TEXT,
            media_id TEXT,
            media_type TEXT,
            caption TEXT,
            campaign_rate TEXT,
            status TEXT,
            job_id TEXT DEFAULT NULL
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

    logger.info(f"Database initialized and ready: {DB_NAME}")
def print_jobs():
    print("Scheduled Jobs:")
    jobs = scheduler.get_jobs()
    if jobs:
        for job in jobs:
            print(f"Job ID: {job.id}, Next Run Time: {job.next_run_time}")
    else:
        print("No jobs scheduled.")
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
def show_campaigns(update, context):
    """Display all approved campaigns with their current status and control buttons."""
    user_id = update.message.from_user.id

    # Fetch approved campaigns from the database
    active_campaigns = fetch_active_campaigns(['Running', 'Stopped'])

    if not active_campaigns:
        update.message.reply_text("There are no approved campaigns to display.")
        return

    for campaign in active_campaigns:
        ad_id, user_id, message, media_id, media_type, caption, campaign_rate, status = campaign

        # Determine button text and callback data
        button_text = "Stop Campaign" if status == 'Running' else "Start Campaign"
        toggle_button = InlineKeyboardButton(button_text, callback_data=f"toggle_{ad_id}")

        # Create and send the reply markup
        keyboard = [[toggle_button]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            f"Campaign: AD_ID={ad_id}\nTEXT: {message}\nStatus: {status}",
            reply_markup=reply_markup
        )
# Function to toggle campaign status
def toggle_campaign_status(update, context):
    """Toggle the status of a campaign and update the scheduler."""
    query = update.callback_query
    query.answer()

    ad_id = int(query.data.split("_")[1])
    user_id = query.from_user.id
    logger.info(f"User {user_id} requested status toggle for campaign AD_ID={ad_id}.")

    try:
        # Fetch the current campaign details
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status, campaign_rate, message, media_id, media_type, caption FROM active_ads WHERE ad_id = ?", (ad_id,))
            campaign = cursor.fetchone()

        if not campaign:
            query.edit_message_text("Campaign not found.")
            return

        current_status, interval, message, media_id, media_type, caption = campaign
        new_status = 'Stopped' if current_status == 'Running' else 'Running'

        # Start or stop the scheduler job
        if new_status == 'Running':
            start_scheduler_for_campaign(ad_id, interval, context, user_id, message, media_id, media_type, caption)
        else:
            stop_scheduler_for_campaign(ad_id)

        # Update the button text and message
        button_text = "Stop Campaign" if new_status == 'Running' else "Start Campaign"
        toggle_button = InlineKeyboardButton(button_text, callback_data=f"toggle_{ad_id}")
        keyboard = [[toggle_button]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        query.edit_message_text(
            text=f"Campaign AD_ID={ad_id}\nTEXT:{message}\nStatus: {new_status}",
            reply_markup=reply_markup
        )
        logger.info(f"Campaign AD_ID={ad_id} status updated to {new_status}.")
    except Exception as e:
        logger.error(f"Error toggling status for campaign AD_ID={ad_id}: {e}")
        query.edit_message_text("Failed to toggle campaign status.")
def fetch_active_campaigns(status_list):
    """Fetch campaigns with specified statuses from the database."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ad_id, user_id, message, media_id, media_type, caption, campaign_rate, status
            FROM active_ads
            WHERE status IN (?, ?)
        """, status_list)
        return cursor.fetchall()
# def fetch_campaign_status(ad_id):
#     """Fetch the current status of a campaign."""
#     with sqlite3.connect(DB_NAME) as conn:
#         cursor = conn.cursor()
#         cursor.execute("SELECT status FROM active_ads WHERE ad_id=?", (ad_id,))
#         result = cursor.fetchone()
#         return result[0] if result else None
# def update_campaign_status(ad_id, new_status):
#     """Update the status of a campaign in the database."""
#     with sqlite3.connect(DB_NAME) as conn:
#         cursor = conn.cursor()
#         cursor.execute("UPDATE active_ads SET status=? WHERE ad_id=?", (new_status, ad_id))
#         conn.commit()
def get_minutes_from_interval(interval):
    """Convert a human-readable interval string into minutes."""
    try:
        if interval.endswith('s'):  # Seconds
            return int(interval[:-1]) / 60
        elif interval.endswith('m'):  # Minutes
            return int(interval[:-1])
        elif interval.endswith('h'):  # Hours
            return int(interval[:-1]) * 60
        else:
            raise ValueError(f"Unsupported interval format: {interval}")
    except ValueError as e:
        logger.error(f"Error parsing interval '{interval}': {e}")
        return None  # Explicitly return None to signify a failure
def start_scheduler_for_campaign(ad_id, interval, context, user_id, message, media_id, media_type, caption):
    """Start a scheduler job for the campaign and store its job ID in the database."""
    job_id = f"campaign_{ad_id}"
    logger.info(f"start scheduler campign.")

    # Remove duplicate jobs if necessary
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info(f"Removed duplicate job {job_id} for campaign AD_ID={ad_id}.")

    # Schedule the new job
    scheduler.add_job(
        send_scheduled_message,
        trigger="interval",
        minutes=get_minutes_from_interval(interval),
        args=[context, user_id, message, media_id, media_type, caption],
        id=job_id
    )

    # Save the job_id in the database
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE active_ads SET status = 'Running', job_id = ? WHERE ad_id = ?", (job_id, ad_id))
        conn.commit()

    logger.info(f"Scheduler job {job_id} started successfully for campaign AD_ID={ad_id}.")
def stop_scheduler_for_campaign(ad_id):
    """Stop the scheduler job for a specific campaign."""
    job_id = f"campaign_{ad_id}"

    # Log current jobs for debugging
    active_jobs = [job.id for job in scheduler.get_jobs()]
    logger.info(f"Active jobs before removal: {active_jobs}")

    try:
        # Remove the job if it exists
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
            logger.info(f"Scheduler job {job_id} stopped for campaign AD_ID={ad_id}.")
        else:
            logger.warning(f"No active job found for campaign AD_ID={ad_id}.")

        # Update the database to reflect the stopped status
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE active_ads SET status = 'Stopped', job_id = NULL WHERE ad_id = ?", (ad_id,))
            conn.commit()
    except Exception as e:
        logger.error(f"Failed to stop scheduler job {job_id} for campaign AD_ID={ad_id}: {e}")
def get_persistent_menu():
    keyboard = [
        ["/start", "/request_to_publish"],  # A button to re-trigger the /start command
        ["/generate_voucher", "/show_requests"],  # Options for deletion and viewing posts
        ["/show_campaigns"],  # Options for deletion and viewing posts

        # ["/help"]  # Add other commands as necessary
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
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



def job_listener(event):
    if event.code == EVENT_JOB_ADDED:
        logger.info(f"Job added: {event.job_id}")
    elif event.code == EVENT_JOB_REMOVED:
        logger.info(f"Job removed: {event.job_id}")
    elif event.code == EVENT_JOB_EXECUTED:
        logger.info(f"Job executed successfully: {event.job_id}")
    elif event.code == EVENT_JOB_ERROR:
        logger.error(f"Job execution failed: {event.job_id}, {event.exception}")



def schedule_task(interval, user_id, message, media_id, media_type, caption):
    job_id = f"campaign_{user_id}_{hash(message)}"
    logger.debug(f"Scheduling message to => {CHAT_ID} every: {interval} for user {user_id}.")

    try:
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
            logger.info(f"Removed existing job with ID {job_id}.")
        scheduler.add_job(
            send_scheduled_message,
            trigger="interval",
            minutes=get_minutes_from_interval(interval),
            args=[BOT_TOKEN, user_id, message, media_id, media_type, caption],
            id=job_id,
            timezone=utc,
            misfire_grace_time=60
        )

        logger.debug(f"Registered jobs: {[job.id for job in scheduler.get_jobs()]}")

        logger.info(f"Job {job_id} scheduled successfully for user {user_id}.")
    except Exception as e:
        logger.error(f"Error scheduling task for user {user_id}: {e}")


def send_scheduled_message(bot_token, user_id, message, media_id, media_type, caption):
    logger.info(f"Sending scheduled message for User ID={user_id}.")
    bot = Bot(token=bot_token)

    # Ensure the campaign is still active
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM active_ads WHERE user_id = ? AND message = ?", (user_id, message))
        status = cursor.fetchone()

    if not status or status[0] != 'Running':
        logger.warning(f"Campaign for User ID={user_id} is not running. Message not sent.")
        return

    # Send the message
    try:
        if media_type == "photo":
            bot.send_photo(chat_id=CHAT_ID, photo=media_id, caption=caption)
        elif media_type == "video":
            bot.send_video(chat_id=CHAT_ID, video=media_id, caption=caption)
        elif media_type == "audio":
            bot.send_audio(chat_id=CHAT_ID, audio=media_id, caption=caption)
        else:
            bot.send_message(chat_id=CHAT_ID, text=message)
        logger.info(f"Message sent successfully to User ID={user_id}.")
    except Exception as e:
        logger.error(f"Failed to send message to User ID={user_id}: {e}")

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



    # Save the user request with a placeholder campaign rate and "Pending" status
    # save_user_request(user_id, message, media_id, media_type, caption, campaign_rate, "", "Pending")

    update.message.reply_text("Set your campaign rate: Every 15s, 30s, 1m.")
    keyboard = [
        [InlineKeyboardButton("Every 15s", callback_data="15s")],
        [InlineKeyboardButton("Every 30s", callback_data="30s")],
        [InlineKeyboardButton("Every 1m", callback_data="1m")]
        # [InlineKeyboardButton("Every 10m", callback_data="10m")]

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
        VALUES (?, ?, ?, ?, ?, ?, 'Running')
    """, (user_id, context.user_data['message'], context.user_data['media_id'],
          context.user_data['media_type'], context.user_data['caption'], campaign_rate))
    conn.commit()

    # Update the voucher table to reflect it was used
    cursor.execute("UPDATE vouchers SET issued_by = ? WHERE voucher_code=?", (user_id, voucher_num))
    conn.commit()

    # Close the database connection
    conn.close()

    # Start the campaign by scheduling the task
    schedule_task(campaign_rate, user_id, context.user_data['message'], context.user_data['media_id'],
                  context.user_data['media_type'], context.user_data['caption'])

    update.message.reply_text(f"Campaign has started with voucher {voucher_num}. It will run every {campaign_rate}.")
    logger.info(f"Campaign for user {user_id} has started with voucher {voucher_num} and rate {campaign_rate}.")

    return ConversationHandler.END
def generate_voucher_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
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
            logger.info(f"Fetched pending requests ad: ID={ad_id}, User={user_id}, Rate={campaign_rate}")

            # Display ad preview and approval options
            if media_type == "photo":
                update.message.reply_photo(
                    photo=media_id,
                    caption=f"Advertisment ID preview: {ad_id}\n TEXT: {message}\nRate:{campaign_rate}"
                )
            elif media_type == "video":
                update.message.reply_video(
                    video=media_id,
                    caption=f"Advertisment ID preview: {ad_id}\nTEXT: {message}\nRate:{campaign_rate}"
                )
            elif media_type == "audio":
                update.message.reply_audio(
                    audio=media_id,
                    caption=f"Advertisment ID preview: {ad_id}\nTEXT: {message}\nRate:{campaign_rate}"
                )
            else:
                update.message.reply_text(f"Advertisment ID preview: {ad_id}\nTEXT: {message}\nRate:{campaign_rate}")

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


# Constants
BOT_TOKEN = "7887654568:AAE38OGqlb46abFe9Jflq5DMT3X3Vcd30Xo"
CHAT_ID = "-1001885191160"  # Real channel/chat ID
ADMIN_USER_ID = 516389439
# Database setup
DB_NAME = "bot_ads.db"

utc_tz = timezone('utc')

# Initialize logging
logging.basicConfig(
    format='%(asctime)s | %(levelname)s | %(message)s',
    level=logging.INFO
)

updater = Updater(BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher
# Conversation states
WAITING_FOR_MESSAGE = 1
WAITING_FOR_VOUCHER = 2

logger = logging.getLogger(__name__)  # Get the logger instance
# logging.getLogger('apscheduler').setLevel(logging.INFO)
# logging.getLogger('apscheduler.jobstores').setLevel(logging.INFO)


# jobstores = {
#     'default': RedisJobStore(host='localhost', port=6379, db=0)
# }

jobstores = {'default': MemoryJobStore()}


scheduler = BackgroundScheduler(tz=utc_tz, jobstores=jobstores)
scheduler.start()
scheduler.print_jobs()
# scheduler.add_listener(job_listener, EVENT_JOB_ADDED | EVENT_JOB_REMOVED | EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

# Add handlers for user flow
dispatcher.add_handler(CommandHandler("start", start)) #handler for /start
show_requests_handler = CommandHandler('show_requests', show_requests) #handler for /show_requests
dispatcher.add_handler(CommandHandler("show_campaigns", show_campaigns))
dispatcher.add_handler(CommandHandler("generate_voucher", generate_voucher))


approve_button_handler = CallbackQueryHandler(approve_request, pattern=r"^approve_\d+$")
dispatcher.add_handler(CallbackQueryHandler(toggle_campaign_status, pattern=r"^toggle_\d+$"))

dispatcher.add_handler(show_requests_handler)
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

init_db()
# logger.info(f"Jobs at startup: {[job.id for job in scheduler.get_jobs()]}")

# Run the bot
logger.info("Starting the bot.")
updater.start_polling()
updater.idle()
