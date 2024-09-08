import logging
import emoji
import pytz
import jdatetime
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from database import create_db, store_message, add_oncall_staff, remove_oncall_staff, get_oncall_staff, update_user_state, get_user_state, get_api_token ,get_bot_owner_id


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s', level=logging.INFO)


create_db()


def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("📝 تیکت جدید", callback_data='raise_request')],
    ]
    bot_owner_id = get_bot_owner_id()
    if update.effective_user.id == bot_owner_id:
    
        keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data='admin_panel')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('👋 سلام برای ارسال درخواست روی گزینه "تیکت جدید"بزنید 😊', reply_markup=reply_markup)

def button_handler(update: Update, context: CallbackContext) -> None:
    query: CallbackQuery = update.callback_query
    query.answer()  
    if query.data == 'raise_request':
        query.message.reply_text('✍️ Please write your message below!')
        update_user_state(query.from_user.id, 'raise_ticket')
    elif query.data == 'admin_panel':
        if query.from_user.id == 246730472:
            show_admin_panel(query.message)
        else:
            query.message.reply_text('🚫 You are not authorized to access the admin panel.')
    elif query.data == 'main_menu':
        start(update, context)

def show_admin_panel(message):
    admin_keyboard = [
        [InlineKeyboardButton("➕ Add On-Call Staff", callback_data='add_oncall')],
        [InlineKeyboardButton("➖ Remove On-Call Staff", callback_data='remove_oncall')],
        [InlineKeyboardButton("📋 Generate On-Call Schedule", callback_data='generate_schedule')],
        [InlineKeyboardButton("🔙 Back", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(admin_keyboard)
    message.reply_text('⚙️ Admin Panel:', reply_markup=reply_markup)

def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username if update.message.from_user.username else "N/A"
    message = update.message.text


    state, _ = get_user_state(user_id)

    if state == 'raise_ticket':
        store_message(user_id, username, message)
        
        tehran_tz = pytz.timezone('Asia/Tehran')
        tehran_time = datetime.now(tehran_tz)
        
        persian_now = jdatetime.datetime.fromgregorian(
            year=tehran_time.year,
            month=tehran_time.month,
            day=tehran_time.day,
            hour=tehran_time.hour,
            minute=tehran_time.minute
        ).strftime('%Y-%m-%d %H:%M')

        context.bot.send_message(chat_id='-4569098241', text=f"📩 User ID: {user_id}\n\n👤 Username: {username}\n\n🗓️ Date: {persian_now}\n\n💬 Message: {message}")

        update.message.reply_text('✅ Your message has been sent! Thank you! 🎉')

        update_user_state(user_id, 'normal') 
    else:
        update.message.reply_text('🚫 Please use the buttons to interact with the bot.')

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
    bot_api_token = get_api_token()

    # Check if the token and owner ID are retrieved
    if not bot_api_token:
        print("Error: Bot API token not found in the database.")
        return
    
    updater = Updater(bot_api_token)  # Your API key here

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Register command and message handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_handler))  # Handle button presses
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_add_oncall))  # Handle adding on-call staff
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_remove_oncall))  # Handle removing on-call staff

    # Start the Bot
    updater.start_polling()

    # Run the bot until you send a signal to stop
    updater.idle()

if __name__ == '__main__':
    main()
