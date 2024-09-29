import sys
import logging
from datetime import datetime, timedelta
import emoji
import pytz
import jdatetime
from docs import bot_guide, bot_features
from jira_functions import create_jira_issue, create_test_issue, get_jira_issue_status, assign_issue_to_user, transition_issue_to_done
from database import (
    create_db, store_message, get_oncall_list, get_oncall_group_id, get_user_tickets, get_ticket_details, is_oncall_staff, remove_oncall_staff,
    mark_message_as_seen, update_user_state, get_user_state, get_api_token, add_oncall_staff, get_bot_owner_id, set_schedule_setting, get_schedule_setting, 
    add_oncall_history, check_date_exists, get_oncall_history_in_range, get_jira_credentials, set_jira_status, set_jira_base_url, set_jira_username,
    set_jira_password, set_jira_project_key, add_new_watcher_admin, get_watcher_list, remove_watcher_admins, is_bot_manager, set_jira_oncalls_username_in_db,
    get_user_state_message, get_oncall_user_name, is_first_time_user, add_first_time_user, get_jira_issue_key_from_message,set_oncall_group_id,
    restart_container, set_oncalls_phone_number_in_db, get_oncall_person, get_oncall_phone_number, get_last_oncall_person_for_last_month
)
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler


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
    elif query.data == 'show_bot_admins':
        show_bot_admins(query)
    elif query.data == 'add_new_oncall':
        add_oncall(query)
    elif query.data == 'add_new_bot_admin':
        add_manager(query)
    elif query.data == 'delete_oncalls':
        delete_oncalls(query , update)
    elif query.data == 'delete_manager':
        delete_manager(query, update)
    elif query.data.startswith('delete_oncall_'):
        confirm_delete(query , update)
    elif query.data.startswith('delete_manager_'):
        confirm_delete_manager(query , update)
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
    elif query.data == ('restart_bot'):
        start(update, context)
    elif query.data == ('jira_setting'):
        show_jira_setting(query)
    elif query.data.startswith('change_jira_status_to'):
        change_jira_status(query)
    elif  query.data == ('change_jira_credential'):
        change_jira_credential(query)
    elif query.data == ('change_jira_base_url'):
        set_or_change_jira_base_url(query)
    elif query.data == ('change_jira_username'):
        set_or_change_jira_username(query)
    elif query.data == ('change_jira_password'):
        set_or_change_jira_password(query)
    elif query.data == ('change_jira_project_key'):
        set_or_change_jira_project_key(query)
    elif query.data == ('jira_test_connection'):
        jira_test_connection(update, context)
    elif query.data.startswith('jira_username_'):
        set_jira_oncalls_username(query)
    elif query.data.startswith('phone_number_'):
        set_oncalls_phone_number(query)
    elif query.data == ('bot_setting'):
        bot_setting(query)
    elif query.data == ('change_oncall_group_id'):
        change_oncall_group_id(query)
    elif query.data == ('about_bot'):
        about_bot(query)
    elif query.data == ('bot_guide'):
        bot_guide(update, context)
    elif query.data == ('bot_features'):
        bot_features(update, context)
    elif query.data.startswith('transition_to_done_'):
        handle_transition(query)


def change_oncall_group_id(query):
    oncall_group_id = get_oncall_group_id()
    user_id = get_user_id(query)
    update_user_state(user_id,'change_oncall_group_id')    
    keyboard = [
        [InlineKeyboardButton("منصرف شدم", callback_data='bot_setting')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(f"لطفا آیدی گروه آنکال رو وارد کنید گروه آیدی با - شروع میشود\n\n*آیدی فعلی : {oncall_group_id}*\n\nبعد از تغییر آیدی ربات ده ثانیه ریسارت میشود\n📍", reply_markup=reply_markup, parse_mode='Markdown')

def bot_setting(query):
    user_id = get_user_id(query)
    update_user_state(user_id,'None')  
    keyboard = [
        [InlineKeyboardButton("تغییر آیدی گروه آنکال 📬", callback_data='change_oncall_group_id')],
        [InlineKeyboardButton("بازگشت به منو قبلی 🔙", callback_data='admin_panel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text("بخش تنظیمات ربات 🛠", reply_markup=reply_markup, parse_mode='Markdown')

def about_bot(query):
    keyboard = [
        [InlineKeyboardButton("قابلیت های ربات 🪩", callback_data='bot_features')],
        [InlineKeyboardButton("آموزش های ربات 📚", callback_data='bot_guide')],
        [InlineKeyboardButton("بازگشت 🔙", callback_data='admin_panel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (
        "🎉 باعث افتخاره که ربات ما رو انتخاب کردین!\n\n"
        "💬 همیشه میتونید نظراتتون رو باهامون از طریق لینک زیر به اشتراک بذارید:\n"
        "🔗 [Github](https://github.com/amsepahvand/Devops-Oncall-Bot)\n\n"
        "📖 توی این قسمت میتونید قابلیت ها و نحوه استفاده از ربات رو مطالعه کنید."
    )    
    query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

def set_oncalls_phone_number(query):
    selected_user_id = query.data.split('_')[-1]
    user_id = get_user_id(query)
    update_user_state(user_id,'set_oncalls_phone_number',f'{selected_user_id}')
    query.edit_message_text('لطفا شماره همراه شخص مورد نظرتون رو با پیش شماره +98 و بدون صفر وارد کنید\n\n مثلا :+989122222222 \n و برای پاک کردن عبارت None را وارد کنید\n☎', reply_markup = None)

def set_jira_oncalls_username(query):
    selected_user_id = query.data.split('_')[-1]
    user_id = get_user_id(query)
    update_user_state(user_id,'set_jira_oncalls_username',f'{selected_user_id}')
    query.edit_message_text('لطفا یوزنیم جیرای شخص مورد نظرتون رو همونطوری که توی جیرا هست وارد کنید', reply_markup = None)

def jira_test_connection(update, context):
    status = create_test_issue()
    if status == 'ok':
        context.bot.send_message(chat_id=update.effective_chat.id,text="اتصال به جیرا با موفقیت برقرار شد ✅",parse_mode='Markdown')     
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,text="اتصال به جیرا برقرار نشد ❌\n\n لطفا مشخصات جیرا ، سطح دسترسی کاربر جیرا یا وضعیت سرویس جیرا بررسی شود",parse_mode='Markdown')

def set_or_change_jira_base_url(query):
    user_id = get_user_id(query)
    state = get_user_state(user_id)
    
    if state != "import_jira_data":
        update_user_state(user_id, 'change_jira_base_url')
    else:
        update_user_state(user_id, 'import_jira_base_url')
    query.message.reply_text('لطفا آدرس BASE URL جیرا را وارد کنید ، فرمت درست به این شکل است\n\n https://jira.example.com \n🔸')

def set_or_change_jira_username(update):
    user_id = get_user_id(update)
    state = get_user_state(user_id)
    if state != "import_jira_base_url":
        update_user_state(user_id, 'change_jira_username')
    else:
        update_user_state(user_id, 'import_jira_username')
    update.message.reply_text('لطفا نام کاربری جدید را وارد کنید توجه کنید که این نام کاربری باید بتواند به ایشو های پروژه مورد نظر دسترسی داشته یا ایشو جدید ایجاد کند')

def set_or_change_jira_password(update):
    user_id = get_user_id(update)
    state = get_user_state(user_id)
    if state != "import_jira_username":
        update_user_state(user_id, 'change_jira_password')
    else:
        update_user_state(user_id, 'import_jira_password')
    update.message.reply_text('لطفا پسورد اکانت جیرا را وارد کنید')

def set_or_change_jira_project_key(update):
    user_id = get_user_id(update)
    state = get_user_state(user_id)
    if state != "import_jira_password":
        update_user_state(user_id, 'change_jira_project_key')
    else:
        update_user_state(user_id, 'import_jira_project_key')
    update.message.reply_text('لطفا PROJECT KEY  را وارد کنید ، PROJECT KEY رو میتونید از داخل URL پروژه دربیارید ، در واقع همون کلمه قبل از شماره ایشو های پروژه جیرا است و همچنین به بزرگی و کوچکی حروف حساس است ')


def change_jira_credential(query):
    user_id = get_user_id(query)
    update_user_state(user_id, 'change_jira_credential')
    jira_base_url, username, password, send_to_jira, project_key = get_jira_credentials()
    keyboard = [
        [InlineKeyboardButton("تغییر BASE URL 🌐", callback_data='change_jira_base_url')],
        [InlineKeyboardButton("تغییر USERNAME کاربر جیرا 👤", callback_data="change_jira_username")],
        [InlineKeyboardButton("تغییر کلمه عبور فعلی 🔑", callback_data='change_jira_password')],
        [InlineKeyboardButton("تغییر PROJECT KEY 📂", callback_data="change_jira_project_key")],
        [InlineKeyboardButton("🛅 Test Connection", callback_data="jira_test_connection")],
        [InlineKeyboardButton("بازگشت به تنظیمات جیرا 🔙", callback_data="jira_setting")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(f" هرکدوم از مشخصات رو میخوای عوض کنی انتخاب کن\n BASE URL: {jira_base_url}\nUSERNAME : {username}\nPASSWORD : ░ ░ ░ ░ ░ \nPROJECT KEY : {project_key}🔸", reply_markup=reply_markup)


def change_jira_status(query):
    new_status = int(query.data.split('_')[-1])
    set_jira_status(new_status)
    keyboard = [
        [InlineKeyboardButton("بازگشت به تنظیمات جیرا 🔙", callback_data='jira_setting')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if new_status == 1:
        query.edit_message_text("وضعیت تغییر کرد: تیکت‌ها به جیرا ارسال خواهند شد ✅", reply_markup=reply_markup)
    else:
        query.edit_message_text("وضعیت تغییر کرد: تیکت‌ها به جیرا ارسال نخواهند شد ⛔", reply_markup=reply_markup)


def show_jira_setting(query):
    jira_data = get_jira_credentials()
    user_id = get_user_id(query)
    
    if jira_data:
        jira_base_url, username, password, send_to_jira, project_key = jira_data
        
        if all([jira_base_url, username, password, project_key]):
            if send_to_jira == 1:
                keyboard = [
                    [InlineKeyboardButton("تغییر وضعیت به عدم ساخت تیکت در جیرا", callback_data='change_jira_status_to_0')],
                    [InlineKeyboardButton("تغییر مشخصات جیرا 🔧", callback_data="change_jira_credential")],
                    [InlineKeyboardButton("بازگشت به منو قبلی", callback_data='admin_panel')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                query.edit_message_text("وضعیت فعلی: تیکت‌ها به جیرا ارسال می‌شوند ✅", reply_markup=reply_markup)
            else:
                keyboard = [
                    [InlineKeyboardButton("تغییر وضعیت به ساخت تیکت در جیرا", callback_data='change_jira_status_to_1')],
                    [InlineKeyboardButton("تغییر مشخصات جیرا 🔧", callback_data="change_jira_credential")],
                    [InlineKeyboardButton("بازگشت به منو قبلی 🔙", callback_data='admin_panel')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                query.edit_message_text("وضعیت فعلی: تیکت‌ها به جیرا ارسال نمی‌شوند ⛔", reply_markup=reply_markup)
        else:
            update_user_state(user_id,'import_jira_data')
            keyboard = [
                [InlineKeyboardButton("وارد کردن BASE URL 🌐", callback_data='change_jira_base_url')],
                [InlineKeyboardButton("بازگشت به منوی قبلی 🔙", callback_data='admin_panel')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text("برای استفاده از این قسمت ابتدا باید مشخصات اولیه جیرا را تکمیل کنید.", reply_markup=reply_markup)
    else:
        update_user_state(user_id,'import_jira_data')
        keyboard = [
            [InlineKeyboardButton("وارد کردن BASE URL 🌐", callback_data='change_jira_base_url')],
            [InlineKeyboardButton("بازگشت به منوی قبلی 🔙", callback_data='admin_panel')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text("برای استفاده از این قسمت ابتدا باید مشخصات اولیه جیرا را تکمیل کنید.", reply_markup=reply_markup)

def show_ticket_details(query, message_id):
    ticket = get_ticket_details(message_id)

    if ticket:
        message, persian_date, jira_issue_key = ticket
        
        details = (
            f"\n📝 پیام: {message}\n\n"
            f"📅 تاریخ: {persian_date}\n\n"
        )
        if jira_issue_key:
            details += f"🌀 شماره تیکت جیرا: {jira_issue_key}\n\n"
            status = get_jira_issue_status(jira_issue_key)
            if status != None :
                details += f"📌 وضعیت تیکت: {status}\n\n🔸"

        query.message.reply_text(details)
    else:
        query.message.reply_text("❌ تیکت پیدا نشد.")


def see_my_requests(query):
    user_id = get_user_id(query)
    tickets = get_user_tickets(user_id)
    if not tickets:
        query.message.reply_text("🔍 شما هیچ تیکتی ندارید.")
        return

    tickets = tickets[::-1]
    keyboard = []
    for ticket in tickets:
        message_id, message, _= ticket
        short_message = message[:30] + "..." if len(message) > 30 else message
        keyboard.append([InlineKeyboardButton(short_message, callback_data=f'show_ticket_{message_id}')])
    keyboard.append([InlineKeyboardButton("بازگشت به منوی اصلی", callback_data='main_menu')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text("📋 لیست تیکت‌های شما\n\n⬇ اینجا میتونی ده تیکت آخر خودت رو ببینی ⬇\n🔸", reply_markup=reply_markup)


def mark_message_as_seen_in_db(query):
    message_id = int(query.data.split("_")[-1])
    user_id = query.from_user.id 
    user_name, jira_username = get_oncall_user_name(user_id)
    mark_message_as_seen(message_id)
    keyboard = [
            [InlineKeyboardButton(f"✅توسط {user_name} مشاهده شد", callback_data="None")]
        ]
    if jira_username:
        jira_issue_key = get_jira_issue_key_from_message(message_id)
        if jira_issue_key:
            assign_issue_to_user(jira_username, jira_issue_key)
            keyboard.append([InlineKeyboardButton("انتقال به Done", callback_data=f'transition_to_done_{jira_issue_key}_by_{user_name}')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_reply_markup(reply_markup=reply_markup)


def handle_transition(query):
    issue_key = query.data.split('_')[-3]
    transition_issue_to_done(issue_key)
    first_seen = query.data.split('_')[-1]
    user_id = query.from_user.id 
    actor, jira_username = get_oncall_user_name(user_id)
    keyboard = [
            [InlineKeyboardButton(f"✅توسط {first_seen} مشاهده شد", callback_data="None")],
            [InlineKeyboardButton(f"✅توسط {actor} انجام شد", callback_data="None")]
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)
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
    
    if not oncall_history:
        buttons = [
            [InlineKeyboardButton("ساخت لیست آنکالی", callback_data="schedule_setting")]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        query.edit_message_text(text="هنوز  لیست آنکالی ساخته نشده", reply_markup=reply_markup)
        return

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
    last_oncall_person = get_last_oncall_person_for_last_month()
    oncall_persons = get_oncall_list()
    period_setting = get_schedule_setting()
    user_id = get_user_id(query)
    user_state = get_user_state(user_id)

    if not oncall_persons:
        logging.warning("No on-call persons or schedule setting found.")
        buttons = [
            [InlineKeyboardButton("مشاهده لیست آنکالی", callback_data="show_oncall_list")]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        query.edit_message_text(text="هنوز فردی به لیست آنکالی اضافه نشده", reply_markup=reply_markup)
        return

    elif period_setting is None:
        buttons = [
            [InlineKeyboardButton(" تنظیم زمانبندی آنکالی", callback_data="oncall_periods")]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        query.edit_message_text(text="هنوز زمانبندی آنکالی تعیین نشده", reply_markup=reply_markup)
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
        if day == 0 and last_oncall_person == oncall_person[2]:
            person_index = (person_index + 1) % len(oncall_persons)
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

    for user_id, name, username, jira_username in records:
        row = [
            InlineKeyboardButton(f"{name}", callback_data=f"no_action"), 
            InlineKeyboardButton(f"@{username}", url=f"https://t.me/{username}"),
            InlineKeyboardButton(f"{emoji.emojize('❌')}", callback_data=f"delete_oncall_{user_id}")  
        ]
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🔙 منصرف شدم", callback_data="show_oncall_list")])
    reply_markup = InlineKeyboardMarkup(buttons)
    query.edit_message_text(text='لطفاً فردی که می‌خواهید حذف کنید را انتخاب و روی ضربدر بزنید.', reply_markup=reply_markup)

def delete_manager(query, update):
    user_id = get_user_id(query)
    update_user_state(user_id, 'delete_manager', 'None')
    records = get_watcher_list()
    buttons = []

    for user_id, name, username in records:
        row = [
            InlineKeyboardButton(f"{name}", callback_data=f"no_action"), 
            InlineKeyboardButton(f"@{username}", url=f"https://t.me/{username}"),
            InlineKeyboardButton(f"{emoji.emojize('❌')}", callback_data=f"delete_manager_{user_id}")  
        ]
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🔙 منصرف شدم", callback_data="show_bot_admins")])
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

def confirm_delete_manager(query, update):
    user_id = get_user_id(update)
    state = get_user_state(user_id)
    if state == 'delete_manager':
        manager_userid = query.data.split('_')[2]
        remove_watcher_admins(manager_userid)
        buttons = []
        buttons.append([InlineKeyboardButton("🔙 بازگشت به لیست نفرات", callback_data="show_bot_admins")])
        reply_markup = InlineKeyboardMarkup(buttons)
        query.edit_message_text(text="✅ مدیر مورد نظر با موفقیت حذف شد.", reply_markup=reply_markup)


def add_oncall(query):
    user_id = get_user_id(query)
    update_user_state(user_id, 'add_new_oncall_username', 'None')
    buttons = [
        [InlineKeyboardButton("🔙 منصرف شدم", callback_data="admin_panel")],
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    query.edit_message_text(text='لطفاً یک پیام از فردی که می‌خواهید به عنوان آنکال جدید اضافه کنید، برای من فوروارد کنید.', reply_markup=reply_markup)

def add_manager(query):
    user_id = get_user_id(query)
    update_user_state(user_id, 'add_new_manager_username', 'None')
    buttons = [
        [InlineKeyboardButton("🔙 منصرف شدم", callback_data="admin_panel")],
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    query.edit_message_text(text='لطفاً یک پیام از فردی که می‌خواهید به عنوان مدیر ربات اضافه کنید، برای من فوروارد کنید.', reply_markup=reply_markup)



def handle_forwarded_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    state = get_user_state(user_id)

    if state == 'add_new_oncall_username':

        if update.message.forward_from:
        
            forwarded_user_id = update.message.forward_from.id
            forwarded_first_name = update.message.forward_from.first_name
            forwarded_username = update.message.forward_from.username if update.message.forward_from.username else "N/A"
            add_oncall_staff(forwarded_user_id, forwarded_first_name, forwarded_username)
            
            success_message = f'✅ فرد آنکال جدید با نام {forwarded_first_name} و شناسه کاربری @{forwarded_username} اضافه شد!'
            buttons = [
                [InlineKeyboardButton("🔙 بازگشت به لیست نفرات", callback_data="show_oncall_list")]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            
            update.message.reply_text(success_message, reply_markup=reply_markup)
            
            update_user_state(user_id, 'normal')
        else:
            update.message.reply_text('🚫 لطفاً یک پیام از کاربر مورد نظر فوروارد کنید.')
    elif state == 'add_new_manager_username':
            forwarded_user_id = update.message.forward_from.id
            forwarded_first_name = update.message.forward_from.first_name
            forwarded_username = update.message.forward_from.username if update.message.forward_from.username else "N/A"
            add_new_watcher_admin(forwarded_user_id, forwarded_first_name, forwarded_username)
            success_message = f'✅ مدیر جدید ربات با نام {forwarded_first_name} و شناسه کاربری @{forwarded_username} اضافه شد!'
            buttons = [
                [InlineKeyboardButton("🔙 بازگشت به لیست نفرات", callback_data="show_bot_admins")]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            
            update.message.reply_text(success_message, reply_markup=reply_markup)




def show_bot_admins(query):
    records = get_watcher_list()
    buttons = []
    buttons.append([
        InlineKeyboardButton("Manager Name", callback_data="no_action"),
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
    buttons.append([InlineKeyboardButton("🔶 اضافه کردن مدیر جدید ", callback_data="add_new_bot_admin")])
    buttons.append([InlineKeyboardButton("❌ حذف افراد", callback_data="delete_manager")])
    buttons.append([InlineKeyboardButton("🔙 بازگشت به منو قبلی", callback_data="show_oncall_list")])
    reply_markup = InlineKeyboardMarkup(buttons)
    query.edit_message_text(text="📋 لیست مدیران ربات:", reply_markup=reply_markup)



def show_oncall_list(query):
    records = get_oncall_list()
    buttons = []
    buttons.append([
        InlineKeyboardButton("Oncall Name", callback_data="no_action"),
        InlineKeyboardButton("Username", callback_data="no_action"),
        InlineKeyboardButton("Jira Username", callback_data="no_action"),
        InlineKeyboardButton("Phone", callback_data="no_action")

    ])

    for user_id, name, username, jira_username, phone_number in records:
        row = [
            InlineKeyboardButton(f"{name}", callback_data=f"staff_name_{user_id}"),
            InlineKeyboardButton(f"@{username}", url=f"https://t.me/{username}"),
            InlineKeyboardButton(f"{jira_username}", callback_data=f"jira_username_{user_id}"),
            InlineKeyboardButton(f"{phone_number}", callback_data=f"phone_number_{user_id}")
        ]
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🔷 اضافه کردن افراد جدید ", callback_data="add_new_oncall")])
    buttons.append([InlineKeyboardButton("❌ حذف افراد", callback_data="delete_oncalls")])
    buttons.append([InlineKeyboardButton("👥 مشاهده مدیران ربات ", callback_data="show_bot_admins")])
    buttons.append([InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_panel")])
    reply_markup = InlineKeyboardMarkup(buttons)
    query.edit_message_text(text="📋 لیست افراد آنکال \n میتونید برای اتواساین تیکت های جیرا روی username جیرا هر نفر کلیک کنید و بصورت دستی واردش کنید:\n📍", reply_markup=reply_markup)


def show_admin_panel(query):
    admin_keyboard = [
        [InlineKeyboardButton("👥 مشاهده لیست نفرات", callback_data='show_oncall_list')],
        [InlineKeyboardButton("📋 تنظیمات و زمانبندی OnCall", callback_data='schedule_setting')],
        [InlineKeyboardButton("🌀 تنظیمات ارسال تیکت به جیرا", callback_data='jira_setting')],
        [InlineKeyboardButton("🛠 تنظیمات ربات", callback_data='bot_setting')],
        [InlineKeyboardButton("🤖 درباره ربات", callback_data='about_bot')],
        [InlineKeyboardButton("🔙 بازگشت به منو اصلی", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(admin_keyboard)
    query.edit_message_text(text='⚙️ پنل ادمین ربات، اینجا می‌توانید نفرات را ببینید یا اضافه/حذف کنید و یا اینکه لیست آنکال یک ماه آینده را بسازید:', parse_mode="HTML", reply_markup=reply_markup)


def construct_reply_text(oncall_name, mention, jira_issue_key, oncall_phone_number):
    tehran_tz = pytz.timezone('Asia/Tehran')
    current_time = datetime.now(tehran_tz)
    current_hour = current_time.hour

    if current_hour >= 18 or current_hour < 8:
        base_text = f'✅ تیکت شما با موفقیت ثبت شد و [{oncall_name}](https://t.me/{mention}) مسئول رسیدگی به آن می‌باشد.\n'
        
        if jira_issue_key:
            base_text += f'\n 🔰 شماره تیکت : {jira_issue_key}\n👨‍💻 همکاران ما در سریع‌ترین زمان ممکن با شما ارتباط برقرار می‌کنند\n🔸'
        else:
            base_text += '👨‍💻 همکاران ما در سریع‌ترین زمان ممکن با شما ارتباط برقرار می‌کنند \n🔸'
        
        if oncall_phone_number != 'None' and oncall_phone_number != 'none':
            base_text += f'\n 📞 شماره تماس اضطراری : {oncall_phone_number}\n🚨'
    else:
        base_text = "تیکت شما با موفقیت ثبت شد \n"
        if jira_issue_key:
            base_text += f'\n 🔰 شماره تیکت : {jira_issue_key}\n👨‍💻 همکاران ما در سریع‌ترین زمان ممکن با شما ارتباط برقرار می‌کنند\n🔸'
        else:
            base_text += '👨‍💻 همکاران ما در سریع‌ترین زمان ممکن با شما ارتباط برقرار می‌کنند \n🔸'

    return base_text


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

        oncall_staff = get_oncall_person()
        if oncall_staff:
            oncall_name, oncall_username = oncall_staff[0]
            oncall_phone_number = get_oncall_phone_number(oncall_username)
            mention = f"{oncall_username}"

            jira_data = get_jira_credentials()
            send_to_jira = jira_data[3] if jira_data else 1

            jira_issue_key = None
            if send_to_jira == 1:
                summary = update.message.text[:40] 
                message = f"{update.message.text}\n\nRequester Telegram ID : {username}"
                jira_issue_key = create_jira_issue(summary, message)
                message = update.message.text


            message_id = store_message(user_id, username, message, status='None', jira_issue_key=jira_issue_key)

            keyboard = [[InlineKeyboardButton(" به من اساین کن ⏱", callback_data=f"message_has_been_seen_{message_id}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            tehran_tz = pytz.timezone('Asia/Tehran')
            current_time = datetime.now(tehran_tz)
            current_hour = current_time.hour

            if current_hour >= 18 or current_hour < 8:
            
                if jira_issue_key != None:
                    jira_base_url, _, _, _, _ = get_jira_credentials()
                    jira_issue_link = f"{jira_base_url}/browse/{jira_issue_key}"
                    context.bot.send_message(chat_id=str(oncall_group_id),text=f"📩 تیکت جدید\n\n👤 کاربر: @{username}\n\n🗓️ تاریخ: {persian_now}\n\n💬 شرح پیام: \n{message} \n\nلینک جیرا: {jira_issue_link if jira_issue_link else 'N/A'}\n\n🔔 جهت اطلاع  \n\nنفر آنکال : @{mention}\n🔸",reply_markup=reply_markup)

                else:
                    context.bot.send_message(chat_id=str(oncall_group_id), text=f"📩 تیکت جدید\n\n👤 کاربر: @{username}\n\n🗓️ تاریخ: {persian_now}\n\n💬 شرح پیام: \n{message} \n\n🔔 جهت اطلاع  \n\nنفر آنکال : {mention}\n🔸", reply_markup=reply_markup)
            else:
                if jira_issue_key != None:
                    jira_base_url, _, _, _, _ = get_jira_credentials()
                    jira_issue_link = f"{jira_base_url}/browse/{jira_issue_key}"
                    context.bot.send_message(chat_id=str(oncall_group_id),text=f"📩 تیکت جدید\n\n👤 کاربر: @{username}\n\n🗓️ تاریخ: {persian_now}\n\n💬 شرح پیام: \n{message} \n\nلینک جیرا: {jira_issue_link if jira_issue_link else 'N/A'}\n🔸",reply_markup=reply_markup)

                else:
                    context.bot.send_message(chat_id=str(oncall_group_id), text=f"📩 تیکت جدید\n\n👤 کاربر: @{username}\n\n🗓️ تاریخ: {persian_now}\n\n💬 شرح پیام: \n{message} \n🔸", reply_markup=reply_markup)

            restart_keyboard = [
                [InlineKeyboardButton("🔄 شروع مجدد", callback_data="restart_bot")]
            ]
            restart_reply_markup = InlineKeyboardMarkup(restart_keyboard)
            reply_text = construct_reply_text(oncall_name, mention, jira_issue_key, oncall_phone_number)
            update.message.reply_text(reply_text, reply_markup=restart_reply_markup, parse_mode='Markdown')

        else:
            context.bot.send_message(chat_id=str(oncall_group_id), text=f"تنظیمات ربات اعم از نفرات آنکال یا زمانبندی آنکال به درستی اعمال نشده ، فراموش نکنید بعد از وارد کردن این موارد باید یک لیست هم بسازید", reply_markup=None)
            restart_keyboard = [
                [InlineKeyboardButton("🔄 شروع مجدد", callback_data="restart_bot")]]
            restart_reply_markup = InlineKeyboardMarkup(restart_keyboard)
            update.message.reply_text('در حال حاضر ربات آماده به کار نیست لطفا با پشتیبانی تماس بگیرید',reply_markup=restart_reply_markup)
    elif state == 'change_jira_base_url':
        set_jira_base_url(message)
        keyboard = [
            [InlineKeyboardButton("بازگشت به منو مقداردهی جیرا", callback_data="change_jira_credential")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(f'New Base URL : {message}',reply_markup=reply_markup)
    elif state == 'change_jira_username':
        set_jira_username(message)
        keyboard = [
            [InlineKeyboardButton("بازگشت به منو مقداردهی جیرا", callback_data="change_jira_credential")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(f'New USERNAME : {message}',reply_markup=reply_markup)
    elif state == 'change_jira_password':
        set_jira_password(message)
        keyboard = [
            [InlineKeyboardButton("بازگشت به منو مقداردهی جیرا", callback_data="change_jira_credential")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(f'Your Password Was Changed',reply_markup=reply_markup)
    elif state == 'change_jira_project_key':
        set_jira_project_key(message)
        keyboard = [
            [InlineKeyboardButton("بازگشت به منو مقداردهی جیرا", callback_data="change_jira_credential")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(f'New Project Key : {message}',reply_markup=reply_markup)

    elif state == 'import_jira_base_url':
        set_jira_base_url(message)
        update.message.reply_text(f'Base URL  :  {message}',reply_markup=None)
        set_or_change_jira_username(update)
    elif state == 'import_jira_username':
        set_jira_username(message)
        update.message.reply_text(f'Username  :  {message}',reply_markup=None)
        set_or_change_jira_password(update)
    elif state == 'import_jira_password':
        set_jira_password(message)
        update.message.reply_text(f'Password  : ░ ░ ░ ░ ░ ',reply_markup=None)
        set_or_change_jira_project_key(update)
    elif state == 'import_jira_project_key':
        set_jira_project_key(message)
        update.message.reply_text(f'Project Key  :  {message}',reply_markup=None)

        connection_status = create_test_issue()
        if connection_status == 'error':
            keyboard = [
                [InlineKeyboardButton("بازگشت به منو مشخصات جیرا", callback_data="change_jira_credential")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text('ارتباط با جیرا برقرار نشد لطفا مشخصات را بررسی کنید  و یا از کارکرد جیرا با این مشخصات اطمینان حاصل کنید',reply_markup=reply_markup)
        else:
            set_jira_status(1)
            keyboard = [
                [InlineKeyboardButton("بازگشت به منو مشخصات جیرا", callback_data="change_jira_credential")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text('مشخصات جیرا با موفقیت ثبت و وضعیت ارسال بطور خودکار فعال شد',reply_markup=reply_markup)
    elif state == 'set_jira_oncalls_username':
        selected_user_id = get_user_state_message(user_id)
        set_jira_oncalls_username_in_db(selected_user_id, message)
        keyboard = [
            [InlineKeyboardButton("بازگشت به لیست آنکال", callback_data="show_oncall_list")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('یوزنیم جیرا با موفقیت برای کاربر ثبت شد',reply_markup=reply_markup)
    elif state == 'set_oncalls_phone_number':
        selected_user_id = get_user_state_message(user_id)
        set_oncalls_phone_number_in_db(selected_user_id, message)
        keyboard = [
            [InlineKeyboardButton("بازگشت به لیست آنکال", callback_data="show_oncall_list")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('شماره تماس با موفقیت برای کاربر ثبت شد',reply_markup=reply_markup)

    elif state == 'change_oncall_group_id':
        set_oncall_group_id(message)
        keyboard = [
            [InlineKeyboardButton("بازگشت به تنظیمات", callback_data="bot_setting")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('آیدی گروه با موفقیت ثبت شد لطفا برای ریستارت سرویس چند لحظه صبر کنید',reply_markup=reply_markup)
        restart_container('devops_oncall_bot')



def back_to_start(update: Update, context: CallbackContext) -> None:
    update.callback_query.answer()
    start(update, context)

def start(update: Update, context: CallbackContext):
    query = None
    user_id = get_user_id(update)
    username = update.effective_user.username
    name = update.effective_user.first_name

    if is_first_time_user(user_id):
        add_first_time_user(user_id, username, name)
        oncall_group_id = get_oncall_group_id()
        if oncall_group_id:
            context.bot.send_message(chat_id=oncall_group_id,text=(f"👤 کاربر: {name}\n🆔 آیدی: {user_id}\n📱 نام کاربری: @{username}\n🎉 کاربر برای اولین بار ربات را استارت زد!"))
    if update.callback_query:
        query = update.callback_query

    keyboard = [
        [InlineKeyboardButton("📝 تیکت جدید", callback_data='raise_request')],
        [InlineKeyboardButton("📜 لیست تیکت‌های من", callback_data='my_requests')],
    ]

    bot_owner_id = get_bot_owner_id()
    if update.effective_user.id == int(bot_owner_id) or int(is_oncall_staff(user_id)) or int(is_bot_manager(user_id)):
        keyboard.append([InlineKeyboardButton("⚙️ پنل مدیریت ربات", callback_data='admin_panel')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    if query:
        query.edit_message_text(text='👋 سلام! برای ارسال درخواست، لطفاً روی گزینه "تیکت جدید" کلیک کنید. 😊', parse_mode="HTML", reply_markup=reply_markup)
    else:
        context.bot.send_message(chat_id=user_id, text='👋 سلام! برای ارسال درخواست، لطفاً روی گزینه "تیکت جدید" کلیک کنید. 😊', parse_mode="HTML", reply_markup=reply_markup)


def oncall(update: Update , context: CallbackContext):
    oncall_staff = get_oncall_person()
    if oncall_staff:
        oncall_name, oncall_username = oncall_staff[0]
        oncall_person = f"{oncall_username}"
    
    if oncall_person:
        name, username =oncall_name, oncall_username
        message = f"👨‍💻 آنکال امروز :  {name}\n\n👤 نام کاربری : @{username} \n\n توجه کنید فرد آنکال فقط در ساعات ۶ بعد از ظهر تا ۸ صبح و ایام تعطیل فعالیت دارد.\n\n🔸 "
    else:
        message = f"❌ فرد آنکال برای امروز مشخص نشده است."
    update.message.reply_text(message)



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
    updater.dispatcher.add_handler(CommandHandler('oncall', oncall))


    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
