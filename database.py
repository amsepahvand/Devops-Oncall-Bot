import os
import sqlite3
import jdatetime
from datetime import datetime
import pytz
import logging

def create_db():
    if not os.path.exists('bot-db.db'):
        conn = sqlite3.connect('bot-db.db')
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_message (
                user_id INTEGER,
                username TEXT,
                message TEXT,
                persian_date TEXT
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS oncall_staff (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                username TEXT
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
                date TEXT
            )
        ''')
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

def store_message(user_id, username, message):
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
    
    c.execute('INSERT INTO user_message (user_id, username, message, persian_date) VALUES (?, ?, ?, ?)', 
              (user_id, username, message, persian_date))
    conn.commit()
    conn.close()

def add_oncall_staff(user_id, name, username):
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO oncall_staff (user_id, name, username) VALUES (?, ?, ?)', (user_id, name, username))
    conn.commit()
    conn.close()

def get_oncall_list():
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('SELECT user_id, name, username FROM oncall_staff')
    staff = c.fetchall()
    conn.close()
    return staff

def remove_oncall_staff(user_id):
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('DELETE FROM oncall_staff WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

# Function to update user state
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

def set_schedule_setting(setting_value):
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('UPDATE schedule_setting SET setting_value = ? WHERE setting_value IS NOT NULL ', (setting_value,))
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
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('INSERT INTO oncall_history (name, username, date) VALUES (?, ?, ?)', (name, username, date))
    conn.commit()
    conn.close()

def get_oncall_history():
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('SELECT name, username, date FROM oncall_history')
    history = c.fetchall()
    conn.close()
    return history

create_db()


#        logging.info(f"{oncall_userid} - 22222222222222222222222222222222222") 
