from telegram import Bot
import schedule
import time

# Your Telegram Bot Token
BOT_TOKEN = "7887654568:AAE38OGqlb46abFe9Jflq5DMT3X3Vcd30Xo"
CHAT_ID = "-1001885191160"  # Replace with the chat ID where the bot should send the message
MESSAGE = "This is your scheduled message!"  # The predefined message

# Initialize the bot
bot = Bot(token=BOT_TOKEN)

# Function to send a message
def send_message():
    try:
        bot.send_message(chat_id=CHAT_ID, text=MESSAGE)
        print(f"Message sent: {MESSAGE}")
    except Exception as e:
        print(f"Error sending message: {e}")

# Schedule the messages
# schedule.every().day.at("09:00").do(send_message)  # Example: 9:00 AM
# schedule.every().day.at("14:00").do(send_message)  # Example: 2:00 PM
schedule.every().minute.do(send_message)  # Example: 2:00 PM



# Keep the script running
print("Telegram bot scheduler is running. Press Ctrl+C to stop.")
try:
    while True:
        schedule.run_pending()
        time.sleep(1)
except KeyboardInterrupt:
    print("\nScheduler stopped.")
