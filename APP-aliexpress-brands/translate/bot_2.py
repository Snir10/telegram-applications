from telegram.ext import MessageHandler, Filters, Updater

def handle_message(update, context):
    message = update.message

    # Check if it's a forwarded message
    if message.forward_date:
        original_text = message.text or "No text content"
        source = (
            f"Forwarded from @{message.forward_from_chat.username}"
            if message.forward_from_chat and message.forward_from_chat.username
            else "Forwarded from an unknown source"
        )

        # Manipulate text
        manipulated_text = f"Modified: {original_text}\n\n---\nSource: {source}"
        update.message.reply_text(manipulated_text)
    else:
        # Handle normal messages
        update.message.reply_text(f"Received: {message.text}")

# Set up the updater and dispatcher
updater = Updater("7887654568:AAE38OGqlb46abFe9Jflq5DMT3X3Vcd30Xo", use_context=True)
dispatcher = updater.dispatcher

# Add a handler for all messages
dispatcher.add_handler(MessageHandler(Filters.all, handle_message))

# Start the bot
updater.start_polling()
updater.idle()
