import logging
import emoji
import pytz
import sys
import jdatetime
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from database import create_db, store_message, get_oncall_list, remove_oncall_staff, update_user_state, get_user_state, get_api_token, add_oncall_staff , get_bot_owner_id , set_schedule_setting, get_schedule_setting, add_oncall_history


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]  # Add this line
)
logger = logging.getLogger(__name__)


create_db()


def start(update: Update, context: CallbackContext):
    query = None
    user_id = get_user_id(update)
    if update.callback_query:
        query = update.callback_query
    keyboard = [
        [InlineKeyboardButton("📝 تیکت جدید", callback_data='raise_request')],
    ]
    bot_owner_id = get_bot_owner_id()
    if update.effective_user.id == int(bot_owner_id):
        keyboard.append([InlineKeyboardButton("⚙️ پنل مدیریت ربات", callback_data='admin_panel')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    if query:
        query.edit_message_text(text='👋 سلام برای ارسال درخواست روی گزینه "تیکت جدید"بزنید 😊', parse_mode="HTML", reply_markup=reply_markup)
    else:
        context.bot.send_message(chat_id=user_id, text='👋 سلام برای ارسال درخواست روی گزینه "تیکت جدید"بزنید 😊', parse_mode="HTML", reply_markup=reply_markup)

    logger.info(f"User {user_id} started the bot.")




def get_user_id(update):
    user_id = None
    if update.message:
        user_id = update.message.chat.id
    elif update.callback_query:
        user_id=update.callback_query.message.chat.id
    else:
        update.effective_user.id
    return user_id



def button_handler(update, context) :
    query = update.callback_query
    query.answer()  
    if query.data == 'raise_request':
        query.message.reply_text('✍️ Please write your message below!')
        update_user_state(query.from_user.id, 'raise_ticket')
    elif query.data == 'admin_panel':
            show_admin_panel(query)
    elif query.data == 'main_menu':
        start(update, context)
    elif query.data == 'show_oncall_list':
        show_oncall_list(query)
    elif query.data == 'add_new_oncall':
            add_oncall(query)
    elif query.data == 'delete_oncalls':
        delete_oncalls(query , update)
    elif query.data.startswith('delete_oncall_'):
        confirm_delete(query , update)
    elif query.data == 'schedule_setting':
        schedule_setting(query)
    elif query.data == 'oncall_periods':
        oncall_periods(query)
    elif query.data.startswith('every_'): 
        confirm_time_period(query)
    elif query.data == 'generate_schedule':
        generate_schedule(query)


def generate_schedule(query):
    oncall_staff = get_oncall_list()
    if not oncall_staff:
        logger.warning("No on-call staff available.")
        return

    # Step 2: Get the current date and the period setting value
    current_date = datetime.now(pytz.timezone('Asia/Tehran'))
    period_setting = get_schedule_setting()
    
    if period_setting is None:
        logger.warning("Schedule setting not found.")
        return

    # Step 3: Generate the schedule for the next 30 days
    schedule = []
    total_days = 30
    staff_count = len(oncall_staff)

    for day in range(total_days):
        # Determine which staff member to assign based on the day and period setting
        staff_index = (day // period_setting) % staff_count
        staff_member = oncall_staff[staff_index]
        name = staff_member[1]
        username = staff_member[2]

        # Calculate the date in Jalali format
        jalali_date = jdatetime.datetime.fromgregorian(
            year=current_date.year,
            month=current_date.month,
            day=current_date.day + day
        ).strftime('%Y/%m/%d')

        # Append to the schedule
        schedule.append((name, username, jalali_date))

    # Step 4: Store the generated schedule in the oncall_history table
    for name, username, date in schedule:
        add_oncall_history(name, username, date)

    logger.info("On-call schedule generated and stored in the database.")




def confirm_time_period(query):
    period_hours = query.data.split('_')[1]
    if period_hours == '24':
        set_schedule_setting(1)
    elif period_hours == '48':
        set_schedule_setting(2)
    elif period_hours == '72':
        set_schedule_setting(3)
    else:
        time_text = "N/A" 
    success_message = f"✅ تنظیمات زمانبندی برای تغییر شیفت هر {period_hours} ساعت تنظیم شد."

    buttons = [
        [InlineKeyboardButton("بازگشت به منو زمانبندی", callback_data="oncall_periods")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    query.edit_message_text(text=success_message, reply_markup=reply_markup)




def oncall_periods(query):
    current_setting = get_schedule_setting()
    if current_setting == 1:
        current_setting = "۲۴ ساعت"
    elif current_setting == 2:
        current_setting = "۴۸ ساعت"
    elif current_setting == 3:
        current_setting = "۷۲ ساعت"
    buttons = [
        [InlineKeyboardButton("هر ۲۴ ساعت", callback_data="every_24_hours")],
        [InlineKeyboardButton("هر ۴۸ ساعت", callback_data="every_48_hours")],
        [InlineKeyboardButton("هر ۷۲ ساعت", callback_data="every_72_hours")],
        [InlineKeyboardButton("بازگشت به منو قبل", callback_data="schedule_setting")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    query.edit_message_text(text=f"⚙️در حال حاضر هر شیفت پس از {current_setting} عوض می شود:", reply_markup=reply_markup)



def schedule_setting(query):
    buttons = [
        [InlineKeyboardButton("دوره های آنکالی", callback_data="oncall_periods")],
        [InlineKeyboardButton("ساخت لیست", callback_data="create_schedule")],
        [InlineKeyboardButton("بازگشت به پنل مدیریت", callback_data="admin_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    query.edit_message_text(text="⚙️ تنظیمات زمانبندی و لیست آنکالی:", reply_markup=reply_markup)














def delete_oncalls(query, update):
    user_id = get_user_id(query)
    update_user_state(user_id, 'delete_oncalls','None')
    records = get_oncall_list()
    buttons = []

    for user_id, name, username in records:
        row = [
            InlineKeyboardButton(f"{name}", callback_data=f"no_action"), 
            InlineKeyboardButton(f"@{username}",  url=f"https://t.me/{username}"),
            InlineKeyboardButton(f"{emoji.emojize('❌')}", callback_data=f"delete_oncall_{user_id}")  
        ]
        buttons.append(row)
    buttons.append([InlineKeyboardButton("منصرف شدم", callback_data="show_oncall_list")])
    reply_markup = InlineKeyboardMarkup(buttons)
    query.edit_message_text(text='لطفا فردی که میخوای حذف کنی رو انتخاب و روی ضربدر بزن کن', reply_markup=reply_markup)


def confirm_delete(query, update):
    user_id = get_user_id(update)
    state = get_user_state(user_id)
    if state == 'delete_oncalls':
        oncall_userid = query.data.split('_')[2]
        remove_oncall_staff(oncall_userid)
        buttons = []
        buttons.append([InlineKeyboardButton("بازگشت به لیست نفرات ", callback_data="show_oncall_list")])
        reply_markup = InlineKeyboardMarkup(buttons)
        query.edit_message_text(text="نفر مورد نظر با موفقیت حذف شد" , reply_markup=reply_markup)


def add_oncall(query):
    user_id = get_user_id(query)
    update_user_state(user_id, 'add_new_oncall_username', 'None')
    buttons = [
        [InlineKeyboardButton("منصرف شدم", callback_data="admin_panel")],
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    query.edit_message_text(text='لطفا یک پیام از فردی که می‌خواهید به عنوان آنکال جدید اضافه کنید،برای من فوروارد کنید.', reply_markup=reply_markup)

def handle_forwarded_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    state = get_user_state(user_id)

    if state == 'add_new_oncall_username':
        if update.message.forward_from:
            forwarded_user_id = update.message.forward_from.id
            forwarded_first_name = update.message.forward_from.first_name
            forwarded_username = update.message.forward_from.username if update.message.forward_from.username else "N/A"
            add_oncall_staff(forwarded_user_id, forwarded_first_name, forwarded_username)
            
            success_message = f'✅ ادمین جدید با نام {forwarded_first_name} و شناسه کاربری @{forwarded_username} اضافه شد!'
            buttons = [
                [InlineKeyboardButton("بازگشت به لیست نفرات", callback_data="show_oncall_list")]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            
            update.message.reply_text(success_message, reply_markup=reply_markup)
            
            update_user_state(user_id, 'normal')
        else:
            update.message.reply_text('🚫 لطفا یک پیام از کاربر مورد نظر فوروارد کنید.')




def show_oncall_list(query):
    records = get_oncall_list()
    buttons = []
    buttons.append([
        InlineKeyboardButton("Admin Name", callback_data="no_action"),
        InlineKeyboardButton("Username", callback_data="no_action"),
        InlineKeyboardButton("User ID", callback_data="no_action")
    ])

    for user_id, name, username in records:
        row = [
            InlineKeyboardButton(f"{name}", callback_data=f"staff_name_{user_id}"),
            InlineKeyboardButton(f"@{username}", url=f"https://t.me/{username}"), 
            InlineKeyboardButton(f"{user_id}", callback_data=f"staff_id_{user_id}")
        ]
        buttons.append(row)
    buttons.append([InlineKeyboardButton("اضافه کردن افراد جدید", callback_data="add_new_oncall")])
    buttons.append([InlineKeyboardButton("حذف افراد", callback_data="delete_oncalls")])
    buttons.append([InlineKeyboardButton("بازگشت به پنل مدیریت", callback_data="admin_panel")])
    reply_markup = InlineKeyboardMarkup(buttons)
    query.edit_message_text(text="لیست افراد :", reply_markup=reply_markup)



def show_admin_panel(query):
    admin_keyboard = [
        [InlineKeyboardButton("➖ مشاهده لیست نفرات", callback_data='show_oncall_list')],
        [InlineKeyboardButton("📋  تنظیمات و زمانبندی OnCall", callback_data='schedule_setting')],
        [InlineKeyboardButton("🔙 بازگشت به منو اصلی", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(admin_keyboard)
    query.edit_message_text(text='⚙️ پنل ادمین ربات ، اینجا میتونی نفرات رو ببینی یا اضافه/حذف کنی و یا اینکه لیست آنکال یک ماه آینده رو بسازی:', parse_mode="HTML", reply_markup=reply_markup)


def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username if update.message.from_user.username else "N/A"
    message = update.message.text


    state= get_user_state(user_id)

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
    elif state == 'add_new_oncall_username':
        handle_forwarded_message(update, context)
    else:
        update.message.reply_text('🚫 Please use the buttons to interact with the bot.')


def back_to_start(update: Update, context: CallbackContext) -> None:
    update.callback_query.answer()
    start(update, context)


def main():
    bot_api_token = get_api_token()

    if not bot_api_token:
        print("Error: Bot API token not found in the database.")
        return
    
    updater = Updater(bot_api_token)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(MessageHandler(Filters.forwarded, handle_forwarded_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

