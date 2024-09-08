import os
import sqlite3
import jdatetime
from datetime import datetime
import pytz

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
                username TEXT
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_state (
                user_id INTEGER PRIMARY KEY,
                state TEXT NOT NULL,
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
    return result[0] if result else None  # Return None if no token found

def get_bot_owner_id():
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('SELECT user_id FROM bot_owner')
    result = c.fetchone()
    conn.close()
    return result[0] if result else None  # Return None if no owner ID found


# Function to store messages in the SQLite database
def store_message(user_id, username, message):
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    
    # Get the current time in Asia/Tehran timezone
    tehran_tz = pytz.timezone('Asia/Tehran')
    tehran_time = datetime.now(tehran_tz)
    
    # Get the current Persian date
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

# Function to add on-call staff
def add_oncall_staff(user_id, username):
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO oncall_staff (user_id, username) VALUES (?, ?)', (user_id, username))
    conn.commit()
    conn.close()

# Function to remove on-call staff
def remove_oncall_staff(user_id):
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('DELETE FROM oncall_staff WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

# Function to get the list of on-call staff
def get_oncall_staff():
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('SELECT user_id, username FROM oncall_staff')
    staff = c.fetchall()
    conn.close()
    return staff

# Function to update user state
def update_user_state(user_id, state, message=None):
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO user_state (user_id, state, message) VALUES (?, ?, ?)', 
              (user_id, state, message))
    conn.commit()
    conn.close()

# Function to get user state
def get_user_state(user_id):
    conn = sqlite3.connect('bot-db.db')
    c = conn.cursor()
    c.execute('SELECT state, message FROM user_state WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result if result else (None, None)  # Return (None, None) if no state found

create_db()



