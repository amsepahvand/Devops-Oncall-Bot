import logging ,emoji ,pytz ,jdatetime
import jdatetime
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from database import create_db, store_message, add_oncall_staff, remove_oncall_staff, get_oncall_staff

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Create the database
create_db()

# Function to start the bot and prompt the user
def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("📝 Raise a Request", callback_data='raise_request')],
        [InlineKeyboardButton("⚙️ Admin Panel", callback_data='admin_panel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('👋 Welcome! Tap the button below to send a message. 😊', reply_markup=reply_markup)

# Function to handle the callback when the button is pressed
def button_handler(update: Update, context: CallbackContext) -> None:
    query: CallbackQuery = update.callback_query
    query.answer()  # Acknowledge the callback
    if query.data == 'raise_request':
        query.message.reply_text('✍️ Please write your message below!')
    elif query.data == 'admin_panel':
        if query.from_user.id == 246730472:  # Check if the user is the admin
            show_admin_panel(query.message)
        else:
            query.message.reply_text('🚫 You are not authorized to access the admin panel.')
    elif query.data == 'add_oncall':
        query.message.reply_text('✍️ Please send the username of the staff to add. Type "cancel" to go back.')
    elif query.data == 'remove_oncall':
        query.message.reply_text('✍️ Please send the user ID of the staff to remove. Type "cancel" to go back.')
    elif query.data == 'generate_schedule':
        query.message.reply_text('🔄 Generating on-call schedule...')
        generate_schedule(query.message)

def show_admin_panel(message):
    admin_keyboard = [
        [InlineKeyboardButton("➕ Add On-Call Staff", callback_data='add_oncall')],
        [InlineKeyboardButton("➖ Remove On-Call Staff", callback_data='remove_oncall')],
        [InlineKeyboardButton("📋 Generate On-Call Schedule", callback_data='generate_schedule')],
        [InlineKeyboardButton("🔙 Back", callback_data='back_to_start')]
    ]
    reply_markup = InlineKeyboardMarkup(admin_keyboard)
    message.reply_text('⚙️ Admin Panel:', reply_markup=reply_markup)

# Function to handle user messages
def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username if update.message.from_user.username else "N/A"
    message = update.message.text

    # Store the message in the SQLite database
    store_message(user_id, username, message)

    tehran_tz = pytz.timezone('Asia/Tehran')
    tehran_time = datetime.now(tehran_tz)
    
    # Get the current Persian date
    persian_now = jdatetime.datetime.fromgregorian(
        year=tehran_time.year,
        month=tehran_time.month,
        day=tehran_time.day,
        hour=tehran_time.hour,
        minute=tehran_time.minute
    ).strftime('%Y-%m-%d %H:%M')

    # Send the message to a channel (replace 'your_channel_id' with your actual channel ID)
    context.bot.send_message(chat_id='-4569098241', text=f"📩 User ID: {user_id}\n\n👤 Username: {username}\n\n🗓️ Date: {persian_now}\n\n💬 Message: {message}")

    update.message.reply_text('✅ Your message has been sent! Thank you! 🎉')

# Function to add on-call staff
adding_oncall_state = {}

# Function to add on-call staff
def add_oncall(update: Update, context: CallbackContext) -> None:
    update.callback_query.answer()
    update.callback_query.message.reply_text('✍️ Please send the username of the staff to add. Type "cancel" to go back.')
    adding_oncall_state[update.effective_chat.id] = 'awaiting_username'

# Function to handle adding on-call staff
def handle_add_oncall(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id

    if chat_id in adding_oncall_state:
        if adding_oncall_state[chat_id] == 'awaiting_username':
            if update.message.text.lower() == "cancel":
                show_admin_panel(update.message)
                del adding_oncall_state[chat_id]
                return

            # Store the username and ask for a forwarded message
            username = update.message.text
            adding_oncall_state[chat_id] = username
            update.message.reply_text(f'🔄 Please forward a message from {username} to get their user ID. Type "cancel" to go back.')
        else:
            # This means we are waiting for a forwarded message
            if update.message.forward_from:
                user_id = update.message.forward_from.id
                username = adding_oncall_state[chat_id]
                add_oncall_staff(user_id, username)
                update.message.reply_text(f'✅ {username} has been added as on-call staff with ID {user_id}!')
                del adding_oncall_state[chat_id]  # Clear the state
            else:
                update.message.reply_text('🚫 Please forward a valid message from the user.')

    user_id = update.message.from_user.id
    username = update.message.text
    add_oncall_staff(user_id, username)
    update.message.reply_text(f'✅ {username} has been added as on-call staff!')

# Function to remove on-call staff
def remove_oncall(update: Update, context: CallbackContext) -> None:
    update.callback_query.answer()
    update.callback_query.message.reply_text('✍️ Please send the user ID of the staff to remove. Type "cancel" to go back.')

# Function to handle removing on-call staff
def handle_remove_oncall(update: Update, context: CallbackContext) -> None:
    if update.message.text.lower() == "cancel":
        show_admin_panel(update.message)
        return

    staff_id = update.message.text
    remove_oncall_staff(staff_id)
    update.message.reply_text(f'✅ Staff with ID {staff_id} has been removed!')

# Function to generate on-call schedule
def generate_schedule(update: Update, context: CallbackContext) -> None:
    update.callback_query.answer()
    staff = get_oncall_staff()
    if not staff:
        update.callback_query.message.reply_text('🚫 No on-call staff available.')
        return

    schedule = []
    start_date = jdatetime.datetime.now()
    for i in range(30):
        staff_member = staff[i % len(staff)]
        persian_date = start_date + jdatetime.timedelta(days=i)
        schedule.append(f"{persian_date} - {staff_member[1]} (ID: {staff_member[0]})")

    update.callback_query.message.reply_text('\n'.join(schedule))

# Function to handle back button
def back_to_start(update: Update, context: CallbackContext) -> None:
    update.callback_query.answer()
    start(update, context)

def main():
    # Replace 'YOUR_TOKEN' with your actual bot token
    updater = Updater("7484690920:AAGySwe1UEBRLVSPkTsqFyWmkIZW_UqZn6w")  # Your API key here

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Register command and message handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_handler))  # Handle button presses
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_add_oncall)) # Handle adding on-call staff
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_remove_oncall))  # Handle removing on-call staff

    # Start the Bot
    updater.start_polling()

    # Run the bot until you send a signal to stop
    updater.idle()

if __name__ == '__main__':
    main()
