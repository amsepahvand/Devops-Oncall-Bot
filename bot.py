import sys
import logging
from datetime import datetime, timedelta

import emoji
import pytz
import jdatetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from database import (
    create_db, store_message, get_oncall_list, get_oncall_group_id, get_user_tickets, get_ticket_details, is_oncall_staff, remove_oncall_staff,
    mark_message_as_seen, update_user_state, get_user_state, get_api_token, add_oncall_staff, get_bot_owner_id, set_schedule_setting, get_schedule_setting, 
    add_oncall_history, check_date_exists, get_oncall_history_in_range
)


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


create_db()
oncall_group_id = get_oncall_group_id()

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
    user_id = get_user_id(query)
    if query.data == 'raise_request':
        query.message.reply_text('✍️ لطفا متن پیام خودتون رو بنویسید و همینجا ارسال کنید')
        update_user_state(query.from_user.id, 'raise_ticket')
    elif query.data == 'admin_panel':
        update_user_state(user_id, 'admin_panel')
        show_admin_panel(query)
    elif query.data == 'main_menu':
        update_user_state(user_id, 'main_menu')
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
        generate_schedule_list_start_date(query)
    elif query.data.startswith('start_schedule_'):
        generate_oncall_schedule(query , context)
    elif query.data.startswith('rewrite_list'):
        update_user_state(user_id, 'approve_overwrite')
        generate_oncall_schedule(query , context)
    elif query.data == ('send_schedule_list_to_group'):
        send_schedule_list_to_group(query, context)
    elif query.data.startswith('message_has_been_seen_'):
        mark_message_as_seen_in_db(query)
    elif query.data == ('my_requests'):
        see_my_requests(query)
    elif query.data.startswith('show_ticket_'):
        message_id = int(query.data.split('_')[2])
        show_ticket_details(query, message_id)
    


def show_ticket_details(query, message_id):
    ticket = get_ticket_details(message_id)

    if ticket:
        message, persian_date, assignie = ticket
        details = (
            f"\n📝 پیام: {message}\n\n"
            f"📅 تاریخ: {persian_date}\n\n"
            f"👤 واگذار شده به: {assignie}\n\n"
        )
        query.message.reply_text(details)
    else:
        query.message.reply_text("❌ تیکت پیدا نشد.")


def see_my_requests(query):
    user_id = get_user_id(query)
    tickets = get_user_tickets(user_id)

    if not tickets:
        query.message.reply_text("🔍 شما هیچ تیکتی ندارید.")
        return

    keyboard = []
    for ticket in tickets:
        message_id, message, _, _= ticket
        # Show the first 30 characters of the message
        short_message = message[:30] + "..." if len(message) > 30 else message
        keyboard.append([InlineKeyboardButton(short_message, callback_data=f'show_ticket_{message_id}')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.reply_text("📋 لیست تیکت‌های شما:", reply_markup=reply_markup)


def mark_message_as_seen_in_db(query):
    message_id = int(query.data.split("_")[-1])
    mark_message_as_seen(message_id)
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("✅ مشاهده شد", callback_data="None")]])
    
    query.edit_message_reply_markup(reply_markup=reply_markup)


def send_schedule_list_to_group(query, context):
    tehran_tz = pytz.timezone('Asia/Tehran')
    start_date = datetime.now(tehran_tz)
    end_date = start_date + timedelta(days=30)

    jalali_start_date = jdatetime.datetime.fromgregorian(
        year=start_date.year,
        month=start_date.month,
        day=start_date.day
    ).strftime('%Y/%m/%d')

    jalali_end_date = jdatetime.datetime.fromgregorian(
        year=end_date.year,
        month=end_date.month,
        day=end_date.day
    ).strftime('%Y/%m/%d')

    oncall_history = get_oncall_history_in_range(jalali_start_date, jalali_end_date)
    
    if not oncall_history:  # Check if the on-call history is empty
        buttons = [
            [InlineKeyboardButton("ساخت لیست آنکالی", callback_data="schedule_setting")]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        query.edit_message_text(text="هنوز  لیست آنکالی ساخته نشده نشده", reply_markup=reply_markup)
        return  # Exit the function if the list is empty

    oncall_count = {}
    schedule_message = ""
    
    for name, username, date in oncall_history:
        if date not in oncall_count:
            oncall_count[date] = []
        oncall_count[date].append((name, username))
    
    line_number = 1
    for date, persons in oncall_count.items():
        names_str = ", ".join([name for name, _ in persons])
        schedule_message += f"{line_number}. {date}: {names_str}\n"
        line_number += 1  
    
    unique_usernames = set()
    for persons in oncall_count.values():
        unique_usernames.update([username for _, username in persons])
    
    unique_usernames_str = "\n".join([f"@{username}" for username in unique_usernames])
    
    jalali_start_date_display = jalali_start_date
    jalali_end_date_display = jalali_end_date 
    
    final_message = f"📅 لیست آنکالی برای بازه {jalali_start_date_display} تا {jalali_end_date_display}:\n\n{schedule_message}\n\n" \
                    f"🔹 جهت اطلاع:\n{unique_usernames_str}"
    
    context.bot.send_message(chat_id=str(oncall_group_id), text=final_message, reply_markup=None)
    buttons = [
        [InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    query.edit_message_text(text="✅ لیست به گروه آنکال ارسال شد.", reply_markup=reply_markup)

def alert_user_about_exist_list(query, date):
    start_schedule_date = query.data.split('_')[2]
    buttons = [
        [InlineKeyboardButton("🔄 بازنویسی کن", callback_data=f"rewrite_list_{start_schedule_date}")],
        [InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    query.edit_message_text(text=f"❗ برای تاریخ‌های مورد نظر رکوردهایی در دیتابیس موجود است. آیا بازنویسی شود؟", reply_markup=reply_markup)



def alert_user_about_exist_list(query, date):
    start_schedule_date = query.data.split('_')[2]
    buttons = [
        [InlineKeyboardButton("🔄 بازنویسی کن", callback_data=f"rewrite_list_{start_schedule_date}")],
        [InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    query.edit_message_text(text=f"❗ برای تاریخ‌های مورد نظر رکوردهایی در دیتابیس موجود است. آیا بازنویسی شود؟", reply_markup=reply_markup)


def generate_oncall_schedule(query , context):

    start_date = query.data.split('_')[2]

    oncall_persons = get_oncall_list()
    period_setting = get_schedule_setting()
    user_id = get_user_id(query)
    user_state = get_user_state(user_id)

    if not oncall_persons or period_setting is None:
        logging.warning("No on-call persons or schedule setting found.")
        buttons = [
            [InlineKeyboardButton("مشاهده لیست آنکالی", callback_data="show_oncall_list")]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        query.edit_message_text(text="هنوز فردی به لیست آنکالی اضافه نشده", reply_markup=reply_markup)

        
        return

    tehran_tz = pytz.timezone('Asia/Tehran')
    if start_date == 'today':
        current_date = datetime.now(tehran_tz)
    else:
        current_date = datetime.now(tehran_tz) + timedelta(days=1)  

    existing_dates = []

    
    for day in range(30):
        future_date = current_date + timedelta(days=day)
        jalali_date = jdatetime.datetime.fromgregorian(
            year=future_date.year,
            month=future_date.month,
            day=future_date.day
        ).strftime('%Y/%m/%d')

        if check_date_exists(jalali_date):
            existing_dates.append(jalali_date)
     
    if user_state != 'approve_overwrite':
        if existing_dates:
            alert_user_about_exist_list(query, existing_dates)
            return
        else:
            pass
        for day in range(30):
            future_date = current_date + timedelta(days=day)
            jalali_date = jdatetime.datetime.fromgregorian(
                year=future_date.year,
                month=future_date.month,
                day=future_date.day
            ).strftime('%Y/%m/%d')
            person_index = (day // period_setting) % len(oncall_persons)
            oncall_person = oncall_persons[person_index]
            
            add_oncall_history(oncall_person[1], oncall_person[2], jalali_date)
            user_id = get_user_id(query)
            update_user_state(user_id, 'None')

        buttons = [
            [InlineKeyboardButton("📤 ارسال لیست به گروه آنکال", callback_data="send_schedule_list_to_group")],
            [InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_panel")]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)

        query.edit_message_text(text="✅ برنامه آنکالی با موفقیت ایجاد شد.", reply_markup=reply_markup)


def generate_schedule_list_start_date(query):
    buttons = [
        [InlineKeyboardButton("📅 تاریخ شروع لیست از امروز", callback_data="start_schedule_today")],
        [InlineKeyboardButton("📅 تاریخ شروع لیست از فردا", callback_data="start_schedule_tomorrow")],
        [InlineKeyboardButton("بازگشت به منو قبلی", callback_data="schedule_setting")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    query.edit_message_text(text="لطفاً انتخاب کنید:", reply_markup=reply_markup)


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
        [InlineKeyboardButton("🔙 بازگشت به منو زمانبندی", callback_data="oncall_periods")]
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
        [InlineKeyboardButton("🔙 بازگشت به منو قبل", callback_data="schedule_setting")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    query.edit_message_text(text=f"⚙️ در حال حاضر هر شیفت پس از {current_setting} عوض می‌شود:", reply_markup=reply_markup)


def schedule_setting(query):
    buttons = [
        [InlineKeyboardButton("📅 دوره‌های آنکالی", callback_data="oncall_periods")],
        [InlineKeyboardButton("📝 ساخت لیست جدید", callback_data="generate_schedule")],
        [InlineKeyboardButton("📤 ارسال لیست فعلی به گروه آنکال", callback_data="send_schedule_list_to_group")],
        [InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    query.edit_message_text(text="⚙️ تنظیمات زمانبندی و لیست آنکالی:", reply_markup=reply_markup)


def delete_oncalls(query, update):
    user_id = get_user_id(query)
    update_user_state(user_id, 'delete_oncalls', 'None')
    records = get_oncall_list()
    buttons = []

    for user_id, name, username in records:
        row = [
            InlineKeyboardButton(f"{name}", callback_data=f"no_action"), 
            InlineKeyboardButton(f"@{username}", url=f"https://t.me/{username}"),
            InlineKeyboardButton(f"{emoji.emojize('❌')}", callback_data=f"delete_oncall_{user_id}")  
        ]
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🔙 منصرف شدم", callback_data="show_oncall_list")])
    reply_markup = InlineKeyboardMarkup(buttons)
    query.edit_message_text(text='لطفاً فردی که می‌خواهید حذف کنید را انتخاب و روی ضربدر بزنید.', reply_markup=reply_markup)


def confirm_delete(query, update):
    user_id = get_user_id(update)
    state = get_user_state(user_id)
    if state == 'delete_oncalls':
        oncall_userid = query.data.split('_')[2]
        remove_oncall_staff(oncall_userid)
        buttons = []
        buttons.append([InlineKeyboardButton("🔙 بازگشت به لیست نفرات", callback_data="show_oncall_list")])
        reply_markup = InlineKeyboardMarkup(buttons)
        query.edit_message_text(text="✅ نفر مورد نظر با موفقیت حذف شد.", reply_markup=reply_markup)


def add_oncall(query):
    user_id = get_user_id(query)
    update_user_state(user_id, 'add_new_oncall_username', 'None')
    buttons = [
        [InlineKeyboardButton("🔙 منصرف شدم", callback_data="admin_panel")],
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    query.edit_message_text(text='لطفاً یک پیام از فردی که می‌خواهید به عنوان آنکال جدید اضافه کنید، برای من فوروارد کنید.', reply_markup=reply_markup)

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
                [InlineKeyboardButton("🔙 بازگشت به لیست نفرات", callback_data="show_oncall_list")]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            
            update.message.reply_text(success_message, reply_markup=reply_markup)
            
            update_user_state(user_id, 'normal')
        else:
            update.message.reply_text('🚫 لطفاً یک پیام از کاربر مورد نظر فوروارد کنید.')


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
    buttons.append([InlineKeyboardButton("➕ اضافه کردن افراد جدید", callback_data="add_new_oncall")])
    buttons.append([InlineKeyboardButton("❌ حذف افراد", callback_data="delete_oncalls")])
    buttons.append([InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_panel")])
    reply_markup = InlineKeyboardMarkup(buttons)
    query.edit_message_text(text="📋 لیست افراد:", reply_markup=reply_markup)


def show_admin_panel(query):
    admin_keyboard = [
        [InlineKeyboardButton("➖ مشاهده لیست نفرات", callback_data='show_oncall_list')],
        [InlineKeyboardButton("📋 تنظیمات و زمانبندی OnCall", callback_data='schedule_setting')],
        [InlineKeyboardButton("🔙 بازگشت به منو اصلی", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(admin_keyboard)
    query.edit_message_text(text='⚙️ پنل ادمین ربات، اینجا می‌توانید نفرات را ببینید یا اضافه/حذف کنید و یا اینکه لیست آنکال یک ماه آینده را بسازید:', parse_mode="HTML", reply_markup=reply_markup)


def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username if update.message.from_user.username else "N/A"
    message = update.message.text

    state = get_user_state(user_id)

    if state == 'raise_ticket':
        tehran_tz = pytz.timezone('Asia/Tehran')
        tehran_time = datetime.now(tehran_tz)
        
        persian_now = jdatetime.datetime.fromgregorian(
            year=tehran_time.year,
            month=tehran_time.month,
            day=tehran_time.day,
            hour=tehran_time.hour,
            minute=tehran_time.minute
        ).strftime('%Y-%m-%d %H:%M')

        oncall_staff = get_oncall_list()
        if oncall_staff:
            oncall_user_id, oncall_name, oncall_username = oncall_staff[0]
            mention = f"@{oncall_username}"

            message_id = store_message(user_id, username, message, assignie=oncall_username, status='not reported')
            keyboard = [[InlineKeyboardButton("👁️ مشاهده نشده ⏱", callback_data=f"message_has_been_seen_{message_id}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            context.bot.send_message(chat_id=str(oncall_group_id), text=f"📩 تیکت جدید\n\n👤 کاربر: {username}\n\n🗓️ تاریخ: {persian_now}\n\n💬 شرح پیام: \n{message} \n\n🔔 جهت اطلاع  \n\n{mention}", reply_markup=reply_markup)

            update.message.reply_text(f'✅ تیکت شما با موفقیت ثبت شد و {mention} مسئول رسیدگی به آن می‌باشد.\nدر سریع‌ترین زمان ممکن با شما ارتباط برقرار می‌کنند 🎉')


def back_to_start(update: Update, context: CallbackContext) -> None:
    update.callback_query.answer()
    start(update, context)


def start(update: Update, context: CallbackContext):
    query = None
    user_id = get_user_id(update)
    if update.callback_query:
        query = update.callback_query

    keyboard = [
        [InlineKeyboardButton("📝 تیکت جدید", callback_data='raise_request')],
        [InlineKeyboardButton("📜 لیست تیکت‌های من", callback_data='my_requests')],
    ]

    bot_owner_id = get_bot_owner_id()
    if update.effective_user.id == int(bot_owner_id) or int(is_oncall_staff(user_id)):
        keyboard.append([InlineKeyboardButton("⚙️ پنل مدیریت ربات", callback_data='admin_panel')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    if query:
        query.edit_message_text(text='👋 سلام! برای ارسال درخواست، لطفاً روی گزینه "تیکت جدید" کلیک کنید. 😊', parse_mode="HTML", reply_markup=reply_markup)
    else:
        context.bot.send_message(chat_id=user_id, text='👋 سلام! برای ارسال درخواست، لطفاً روی گزینه "تیکت جدید" کلیک کنید. 😊', parse_mode="HTML", reply_markup=reply_markup)

    logger.info(f"User {user_id} started the bot.")


def main():
    bot_api_token = get_api_token()

    if not bot_api_token:
        print("Error: Bot API token not found in the database.")
        return
    
    updater = Updater(bot_api_token)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.forwarded, handle_forwarded_message))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))


    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
