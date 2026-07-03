from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from config import admin_config, LEAGUES

def group_buttons(buttons, group_size=2):
    return [buttons[i:i+group_size] for i in range(0, len(buttons), group_size)]

def get_main_menu_keyboard():
    buttons = [btn for row in admin_config["main_menu_buttons"] for btn in row]
    rows = group_buttons(buttons, 2)
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

# تابع ساخت کیبورد برای منوی زیر "Futbol dünyası"
def get_futbol_dunyasi_menu_keyboard():
    buttons = [
        ["Futbol Highlightleri 🎥"],
        ["Puan Durumu ve İstatistikler 🗓"],
        ["Geçmiş Maç Sonuçları ⚽"],
        ["Gelecek Maçlar 📡"],
        ["Bugünün Önemli Maçları ⚽"],
        ["🔙 Geri"]
    ]
    rows = [row for row in buttons]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

def get_live_countries_keyboard():
    buttons = [f"🏆 {league['emoji']} {league['name']}" for league in LEAGUES] + ["🔙 Geri"]
    rows = group_buttons(buttons, 2)
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

def get_past_countries_keyboard():
    buttons = [f"🏆 {league['emoji']} {league['name']}" for league in LEAGUES] + ["🔙 Geri"]
    rows = group_buttons(buttons, 2)
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

def get_stats_menu_keyboard():
    buttons = ["🗓 10 ülkenin Lig Tablosu", "🔙 Geri"]
    rows = group_buttons(buttons, 2)
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

def get_league_countries_keyboard():
    buttons = [f"🏆 {league['emoji']} {league['name']}" for league in LEAGUES] + ["🔙 Geri"]
    rows = group_buttons(buttons, 2)
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

def get_back_keyboard():
    return ReplyKeyboardMarkup([["🔙 Geri"]], resize_keyboard=True) 