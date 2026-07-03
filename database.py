import sqlite3
import logging
from datetime import datetime

# توابع مدیریت دیتابیس
def connect_db():
    return sqlite3.connect('users.db')

def create_table():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        telegram_id INTEGER UNIQUE, 
                        referral_code TEXT, 
                        join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS referrals (
                        referrer_id INTEGER, 
                        referred_id INTEGER)''')
    conn.commit()
    conn.close()

def add_user(telegram_id, referral_code=None):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (telegram_id, referral_code) VALUES (?, ?)", 
                   (telegram_id, referral_code))
    conn.commit()
    conn.close()

def get_total_users():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    conn.close()
    return total_users

def get_all_users():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_id, join_date FROM users")
    users = cursor.fetchall()
    conn.close()
    return users

def get_all_referrals():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT referrer_id, COUNT(*) FROM referrals GROUP BY referrer_id")
    referrals_data = cursor.fetchall()
    conn.close()
    return referrals_data

def get_referral_count(user_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM referrals WHERE referrer_id = ?", (user_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_creation_date():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT MIN(join_date) FROM users")
    result = cursor.fetchone()[0]
    conn.close()
    if result:
        return result.split()[0]
    return "نامشخص"

def get_bot_stats_text():
    from config import ADMIN_IDS, admin_config
    
    creation_date = get_creation_date()
    total_users = get_total_users()
    active_users = total_users
    deleted_users = 0
    admin_count = len(ADMIN_IDS)
    button_count = sum(len(row) for row in admin_config["main_menu_buttons"])
    message_count = 5
    referral_count = sum(1 for _ in get_all_referrals())
    referral_message = f"▪️تعداد ارجاعات: {referral_count}"

    stats = (
        f"▪️تاریخ ایجاد: {creation_date}\n\n"
        f"▪️کاربران:\n"
        f"▫️فعال: {active_users}\n"
        f"▫️حذف شده: {deleted_users}\n"
        f"▪️تعداد ادمین‌ها: {admin_count}\n\n"
        f"▪️ساختار ربات:\n"
        f"▫️دکمه‌ها: {button_count} / 200\n"
        f"▫️پیام‌ها: {message_count} / 400\n"
        f"▫️تعداد ارجاعات: {referral_count}\n"
    )
    return stats

def add_referral(referrer_id, referred_id):
    """Add a new referral to the database"""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO referrals (referrer_id, referred_id) VALUES (?, ?)", 
                  (referrer_id, referred_id))
    conn.commit()
    conn.close() 