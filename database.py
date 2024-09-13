import os
import sys
import sqlite3
import jdatetime
from datetime import datetime
import pytz
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def create_db():
    if not os.path.exists('bot-db.db'):
        conn = sqlite3.connect('bot-db.db')
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_messages (
                message_id AUTOINCREMENT PRIMARY KEY,
                user_id INTEGER,
                username TEXT,
                message TEXT,
                persian_date TEXT,
                status  TEXT
                created_date DATE,
                seen_date DATE ,
                assignie TEXT ,
                jira_issue_key TEXT DEFAULT None
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS jira_ticketing_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                jira_base_url TEXT,
                username TEXT,
                password TEXT ,
                send_to_jira INTEGER DEFAULT 0,
                project_key TEXT
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS oncall_staff (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                username TEXT,
                jira_username TXT DEFAULT None
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_state (
                user_id INTEGER PRIMARY KEY,
                state TEXT,
                message TEXT
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS bot_owner (
                user_id TEXT PRIMARY KEY
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS oncall_group (
                group_id INTEGER PRIMARY KEY
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS bot_api_token (
                token TEXT
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS schedule_setting (
                setting_value INTEGER DEFAULT 1
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS oncall_history (
                name TEXT,
                username TEXT,
                date TEXT UNIQUE
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS watcher_admins (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                username TEXT
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS first_time_users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                name TEXT,
                start_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

def get_oncall_user_name(user_id):
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('SELECT name , jira_username FROM oncall_staff WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result if result else (None, None)

def get_jira_issue_key_from_message(message_id):
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('SELECT jira_issue_key FROM user_messages WHERE message_id = ?', (message_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None 

def set_jira_oncalls_username_in_db(user_id, jira_username):
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('UPDATE oncall_staff SET jira_username = ? WHERE user_id = ?', (jira_username, user_id))
    conn.commit()
    conn.close()

def set_api_token(token):
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO bot_api_token (token) VALUES (?)', (token,))
    conn.commit()
    conn.close()

def get_api_token():
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('SELECT token FROM bot_api_token')
    result = c.fetchone()
    conn.close()
    return result[0] if result else None 

def get_bot_owner_id():
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('SELECT user_id FROM bot_owner WHERE user_id IS NOT NULL AND user_id != ""')
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def get_oncall_group_id():
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('SELECT group_id FROM oncall_group')
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def add_oncall_staff(user_id, name, username):
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO oncall_staff (user_id, name, username) VALUES (?, ?, ?)', (user_id, name, username))
    conn.commit()
    conn.close()

def add_new_watcher_admin(user_id, name, username):
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO watcher_admins (user_id, name, username) VALUES (?, ?, ?)', (user_id, name, username))
    conn.commit()
    conn.close()

def get_watcher_list():
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('SELECT user_id, name, username FROM watcher_admins')
    watcher_admins = c.fetchall()
    conn.close()
    return watcher_admins 

def get_oncall_list():
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('SELECT user_id, name, username, jira_username FROM oncall_staff')
    staff = c.fetchall()
    conn.close()
    return staff

def remove_watcher_admins(user_id):
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('DELETE FROM watcher_admins WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def remove_oncall_staff(user_id):
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('DELETE FROM oncall_staff WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def update_user_state(user_id, state, message=None):
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO user_state (user_id, state, message) VALUES (?, ?, ?)', 
              (user_id, state, message))
    conn.commit()
    conn.close()

def get_user_state(user_id):
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('SELECT state, message FROM user_state WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else (None, None)

def get_user_state_message(user_id):
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('SELECT state, message FROM user_state WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result[1] if result else (None, None) 

def set_schedule_setting(setting_value):
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM schedule_setting')
    row_count = c.fetchone()[0]
    
    if row_count == 0:
        c.execute('INSERT INTO schedule_setting (setting_value) VALUES (?)', (setting_value,))
    else:
        c.execute('UPDATE schedule_setting SET setting_value = ? WHERE setting_value IS NOT NULL', (setting_value,))
    
    conn.commit()
    conn.close()

def get_schedule_setting():
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('SELECT setting_value FROM schedule_setting')
    result = c.fetchone()
    conn.close()
    return result[0] if result else None  

def add_oncall_history(name, username, date):
    reindex_oncall_history()
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()

    c.execute('''
        UPDATE oncall_history 
        SET name = ?, username = ? 
        WHERE date = ?
    ''', (name, username, date))
    if c.rowcount == 0:
        c.execute('INSERT INTO oncall_history (name, username, date) VALUES (?, ?, ?)', (name, username, date))
    
    conn.commit()
    conn.close()

def get_oncall_history_in_range(start_date, end_date):
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('''
        SELECT name, username, date 
        FROM oncall_history 
        WHERE date BETWEEN ? AND ?
        ORDER BY date
    ''', (start_date, end_date))
    
    history = c.fetchall()
    conn.close()
    return history

def check_date_exists(date):
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM oncall_history WHERE date = ?', (date,))
    exists = c.fetchone()[0] > 0
    conn.close()
    return exists

def reindex_oncall_history():
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS new_oncall_history (
            name TEXT,
            username TEXT,
            date TEXT UNIQUE
        )
    ''')

    c.execute('''
        INSERT INTO new_oncall_history (name, username, date)
        SELECT name, username, date FROM oncall_history
        ORDER BY date
    ''')

    c.execute('DROP TABLE oncall_history')
    c.execute('ALTER TABLE new_oncall_history RENAME TO oncall_history')
    
    conn.commit()
    conn.close()


def mark_message_as_seen(message_id):
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    
    seen_date = datetime.now(pytz.timezone('Asia/Tehran')).strftime('%Y-%m-%d %H:%M:%S')
    c.execute('UPDATE user_messages SET seen_date = ? WHERE message_id = ?', (seen_date, message_id))
    
    if c.rowcount == 0:
        logging.warning(f"No message found with message_id: {message_id}")
    
    conn.commit()
    conn.close()


def store_message(user_id, username, message, assignie=None, status='not reported', jira_issue_key=None):
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    
    tehran_tz = pytz.timezone('Asia/Tehran')
    tehran_time = datetime.now(tehran_tz)
    
    persian_date = jdatetime.datetime.fromgregorian(
        year=tehran_time.year,
        month=tehran_time.month,
        day=tehran_time.day,
        hour=tehran_time.hour,
        minute=tehran_time.minute
    ).strftime('%Y-%m-%d %H:%M')
    
    created_date = tehran_time.strftime('%Y-%m-%d %H:%M:%S')

    c.execute('INSERT INTO user_messages (user_id, username, message, persian_date, created_date, assignie, status, jira_issue_key) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', 
              (user_id, username, message, persian_date, created_date, assignie, status, jira_issue_key))

    message_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return message_id

def is_oncall_staff(user_id):
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM oncall_staff WHERE user_id = ?', (user_id,))
    exists = c.fetchone()[0] > 0
    conn.close()
    return exists

def is_bot_manager(user_id):
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM watcher_admins WHERE user_id = ?', (user_id,))
    exists = c.fetchone()[0] > 0
    conn.close()
    return exists

def get_user_tickets(user_id):
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('SELECT message_id, message, persian_date, assignie FROM user_messages WHERE user_id = ? ORDER BY created_date DESC LIMIT 10', (user_id,))
    tickets = c.fetchall()
    conn.close()
    return tickets

def get_ticket_details(message_id):
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('SELECT message, persian_date, assignie, jira_issue_key  FROM user_messages WHERE message_id = ?', (message_id,))
    ticket = c.fetchone()
    conn.close()
    return ticket

def get_jira_credentials():
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('SELECT jira_base_url, username, password, send_to_jira, project_key FROM jira_ticketing_data')
    result = c.fetchone()
    conn.close()
    return result if result else None

def set_jira_status(status):
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('UPDATE jira_ticketing_data SET send_to_jira = ? WHERE send_to_jira IS NOT NULL', (int(status),))
    conn.commit()
    conn.close()

def set_jira_base_url(base_url):
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM jira_ticketing_data')
    count = c.fetchone()[0]
    
    if count > 0:
        c.execute('UPDATE jira_ticketing_data SET jira_base_url = ? WHERE id IS NOT NULL', (base_url,))
    else:
        c.execute('INSERT INTO jira_ticketing_data (jira_base_url) VALUES (?)', (base_url,))
    
    conn.commit()
    conn.close()

def set_jira_username(username):
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM jira_ticketing_data')
    count = c.fetchone()[0]
    
    if count > 0:
        c.execute('UPDATE jira_ticketing_data SET username = ? WHERE id IS NOT NULL', (username,))
    else:
        raise Exception("No row exists in jira_ticketing_data to update.")
    
    conn.commit()
    conn.close()

def set_jira_password(password):
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM jira_ticketing_data')
    count = c.fetchone()[0]
    
    if count > 0:
        c.execute('UPDATE jira_ticketing_data SET password = ? WHERE id IS NOT NULL', (password,))
    else:
        raise Exception("No row exists in jira_ticketing_data to update.")
    
    conn.commit()
    conn.close()

def set_jira_project_key(project_key):
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM jira_ticketing_data')
    count = c.fetchone()[0]
    
    if count > 0:
        c.execute('UPDATE jira_ticketing_data SET project_key = ? WHERE id IS NOT NULL', (project_key,))
    else:
        raise Exception("No row exists in jira_ticketing_data to update.")
    
    conn.commit()
    conn.close()

def is_first_time_user(user_id):
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM first_time_users WHERE user_id = ?', (user_id,))
    is_first_time = c.fetchone()[0] == 0
    conn.close()
    return is_first_time

def add_first_time_user(user_id, username, name):
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('INSERT INTO first_time_users (user_id, username, name) VALUES (?, ?, ?)', (user_id, username, name))
    conn.commit()
    conn.close()

create_db()






#    logger.info(f"Test issue created successfully: {result}")
