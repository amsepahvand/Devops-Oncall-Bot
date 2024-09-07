import os
import sqlite3
import jdatetime
from datetime import datetime
import pytz

# Create a SQLite database and tables if they don't exist
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
        conn.commit()
        conn.close()

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
        minute=tehran_time.minute,
        second=tehran_time.second
    ).strftime('%Y-%m-%d %H:%M:%S')
    
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
