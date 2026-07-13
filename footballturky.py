import logging
import requests
import asyncio
import sqlite3
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ContextTypes
)
from google_trans_new import google_translator
import httpx
import os
import pandas as pd

# رفع مشکل proxy در httpx
from telegram.request import _httpxrequest
def patched_build_client(self):
    kwargs = self._client_kwargs.copy()
    if "proxy" in kwargs:
        kwargs.pop("proxy")
    return httpx.AsyncClient(**kwargs)
_httpxrequest.HTTPXRequest._build_client = patched_build_client

translator = google_translator()

# -------------------------------
from config import TOKEN, CHANNEL_USERNAME, ADMIN_IDS, referral_amount, AI_API_KEY, SERPAPI_KEY, ODDS_API_KEY, LIVESCORE_API_KEY, LIVESCORE_API_SECRET, LIVESCORE_COMPETITION_ID, THESPORTSDB_API_KEY

# تنظیمات از config.py بارگذاری می‌شود

# -------------------------------
# تنظیمات منوی اصلی (با تغییر: اضافه شدن ایموجی به Futbol dünyası)
admin_config = {
    "main_menu_buttons": [
        ["Canlı TV 🛜"],
        ["Futbol dünyası ⚽"],
        ["🔮 Yapay Zeka ile Futbol Maçı Tahmini", "🤖 Yapay Zeka"],
        ["Arkadaş Davet Et 🤝", "Cüzdan 💰"],
        ["🔗 Botu Paylaş"]
    ]
}

# مجموعه‌ای برای ذخیره موقت شناسه‌های کاربران (در صورت استفاده در حالت حافظه)
user_ids = set()
user_join_times = {}  # این متغیر دیگر استفاده نخواهد شد
referrals = {}

# -------------------------------
# اطلاعات لیگ‌ها و بازی‌ها
BASE_API_URL = f"https://www.thesportsdb.com/api/v1/json/{THESPORTSDB_API_KEY}/"
LIVE_MATCHES_URL = BASE_API_URL + "livescore.php"
PAST_MATCHES_URL = BASE_API_URL + "eventspastleague.php"
LEAGUE_TABLE_URL = BASE_API_URL + "lookuptable.php"
UPCOMING_MATCHES_URL = BASE_API_URL + "eventsnextleague.php"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

LEAGUES = [
    {"name": "İran", "emoji": "🇮🇷", "id": "4742", "season": "2024-2025"},
    {"name": "İngiltere", "emoji": "🇬🇧", "id": "4328", "season": "2024-2025"},
    {"name": "İspanya", "emoji": "🇪🇸", "id": "4335", "season": "2024-2025"},
    {"name": "Almanya", "emoji": "🇩🇪", "id": "4331", "season": "2024-2025"},
    {"name": "İtalya", "emoji": "🇮🇹", "id": "4332", "season": "2024-2025"},
    {"name": "Fransa", "emoji": "🇫🇷", "id": "4334", "season": "2024-2025"},
    {"name": "Hollanda", "emoji": "🇳🇱", "id": "4337", "season": "2024-2025"},
    {"name": "Portekiz", "emoji": "🇵🇹", "id": "4338", "season": "2024-2025"},
    {"name": "Türkiye", "emoji": "🇹🇷", "id": "4339", "season": "2024-2025"},
    {"name": "Amerika", "emoji": "🇺🇸", "id": "4346", "season": "2024-2025"},
    {"name": "Arjantin", "emoji": "🇦🇷", "id": "4350", "season": "2024-2025"}
]

TODAY_LEAGUES = [
    {"name": "UEFA Champions League", "id": "4480", "season": "2024-2025"},
    {"name": "Asya Şampiyonlar Ligi", "id": "4506", "season": "2024-2025"},
    {"name": "Avrupa Gemi Şampiyonları", "id": "4481", "season": "2024-2025"},
    {"name": "İngiltere Premier Ligi", "source": "varzesh3"},
    {"name": "İspanya Premier Ligi", "source": "varzesh3"}
]

# -------------------------------
# توابع مربوط به بازی‌ها
def get_live_matches_by_id(league_id):
    try:
        response = requests.get(LIVE_MATCHES_URL)
        data = response.json()
        events = data.get("events")
        if events:
            filtered = [event for event in events if event.get("idLeague") == league_id]
            return [f"{event.get('strHomeTeam', 'Bilinmiyor')} VS {event.get('strAwayTeam', 'Bilinmiyor')} - {event.get('strTime', 'Zaman bilinmiyor')} ⏳" for event in filtered]
        return []
    except Exception as e:
        logging.error(f"{league_id} lig için canlı maçlar alınırken hata: {e}")
        return []

def get_past_matches_by_id(league_id):
    try:
        params = {"id": league_id, "s": "2024-2025"}
        response = requests.get(PAST_MATCHES_URL, params=params)
        data = response.json()
        if data.get("events"):
            return [f"{m.get('strHomeTeam', 'Bilinmiyor')} {m.get('intHomeScore', '0')} - {m.get('intAwayScore', '0')} {m.get('strAwayTeam', 'Bilinmiyor')}" for m in data["events"]]
        return []
    except Exception as e:
        logging.error(f"{league_id} lig için geçmiş maçlar alınırken hata: {e}")
        return []

def get_league_table_by_id(league_id, season="2024-2025"):
    try:
        params = {"l": league_id, "s": season}
        response = requests.get(LEAGUE_TABLE_URL, params=params)
        data = response.json()
        if data.get("table"):
            return [f"{team.get('intRank', '?')}. {team.get('strTeam', 'Bilinmiyor')} - Oynanan: {team.get('intPlayed', '?')} | Puan: {team.get('intPoints', '?')}" for team in data["table"]]
        return []
    except Exception as e:
        logging.error(f"{league_id} lig için puan durumu alınırken hata: {e}")
        return []

def get_todays_matches_by_id(league_id):
    try:
        params = {"id": league_id}
        response = requests.get(UPCOMING_MATCHES_URL, params=params)
        data = response.json()
        events = data.get("events")
        if events:
            now = datetime.now()
            upcoming = []
            for event in events:
                date_str = event.get("dateEvent")
                if date_str:
                    event_date = datetime.strptime(date_str, "%Y-%m-%d")
                    if 0 <= (event_date - now).days <= 3:
                        match_text = f"{event.get('strHomeTeam', 'Bilinmiyor')} VS {event.get('strAwayTeam', 'Bilinmiyor')}"
                        if event.get("strTime"):
                            match_text += f" - Başlangıç: {event.get('strTime')}"
                        match_text += f" - Tarih: {event_date.strftime('%Y-%m-%d')}"
                        upcoming.append(match_text)
            return upcoming
        return []
    except Exception as e:
        logging.error(f"{league_id} lig için gelecek maçlar alınırken hata: {e}")
        return []

def get_livescore_from_varzesh3(league_name=None):
    url = "https://www.varzesh3.com/livescore"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        matches = []
        match_divs = soup.find_all("div", class_="livescore-match")
        for div in match_divs:
            league_tag = div.find("div", class_="league-name")
            card_league = league_tag.get_text(strip=True) if league_tag else ""
            if league_name and league_name not in card_league:
                continue
            home_team_tag = div.find("span", class_="home-team")
            away_team_tag = div.find("span", class_="away-team")
            time_tag = div.find("span", class_="match-time")
            home_team = home_team_tag.get_text(strip=True) if home_team_tag else "Bilinmiyor"
            away_team = away_team_tag.get_text(strip=True) if away_team_tag else "Bilinmiyor"
            match_time = time_tag.get_text(strip=True) if time_tag else "Zaman bilinmiyor"
            match_str = f"{home_team} VS {away_team} - {match_time}"
            matches.append(match_str)
        return matches
    except Exception as e:
        logging.error(f"Varzesh3'ten canlı skor alınırken hata: {e}")
        return []

def get_highlight_videos():
    try:
        params = {"id": "4328", "s": "2024-2025"}
        response = requests.get(PAST_MATCHES_URL, params=params)
        data = response.json()
        if data.get("events"):
            highlights = []
            for event in data["events"]:
                video_url = event.get("strVideo") or event.get("strYoutube")
                if video_url:
                    title = event.get("strEvent") or "Başlıksız"
                    highlights.append((title, video_url))
                if len(highlights) >= 5:
                    break
            return highlights
        return []
    except Exception as e:
        logging.error(f"Highlightler alınırken hata: {e}")
        return []

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

# -------------------------------
# توابع مربوط به منوی Canlı TV (Condaktor)
async def show_condaktor_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Canlı TV 🛜", url="https://betrewardtv.live/")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Lütfen aşağıdan seçim yapın:", reply_markup=reply_markup)

async def condaktor_category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "condaktor_back":
        keyboard = [
            [InlineKeyboardButton("⚽ Futbol", callback_data="condaktor_10")],
            [InlineKeyboardButton("🏀 Basketbol", callback_data="condaktor_9")],
            [InlineKeyboardButton("🎾 Tenis", callback_data="condaktor_7")],
            [InlineKeyboardButton("🏐 Voleybol", callback_data="condaktor_8")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Lütfen bir kategori seçin:", reply_markup=reply_markup)
        return

    cat_id = data.split("_")[1]
    links = await asyncio.to_thread(get_condaktor_links_by_cat, cat_id)
    if links:
        buttons = [
            [InlineKeyboardButton(f"{description}", url=link)]
            for title, description, link in links
        ]
        buttons.append([InlineKeyboardButton("🔙 Geri", callback_data="condaktor_back")])
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_text("Mevcut linkler:", reply_markup=reply_markup)
    else:
        buttons = [[InlineKeyboardButton("🔙 Geri", callback_data="condaktor_back")]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_text("❌ Bilgiler bulunamadı.", reply_markup=reply_markup)

def get_condaktor_links_by_cat(cat_id):
    url = f"https://livesoccer.live/tvtr/livetv?cat_id={cat_id}"
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            if "/tvtr/livetv/details/" in a["href"]:
                title = a.get_text(strip=True)
                if not title:
                    title = a.get("title", "")
                link_url = a["href"]
                description = a.get("title", "")
                if not link_url.startswith("http"):
                    link_url = "https://livesoccer.live" + link_url
                if title and link_url:
                    links.append((title, description, link_url))
        unique_links = []
        seen = set()
        for title, description, link in links:
            if link not in seen:
                unique_links.append((title, description, link))
                seen.add(link)
        return unique_links
    except Exception as e:
        logging.error(f"Error fetching condaktor links for cat {cat_id}: {e}")
        return []

def get_google_search_results(query: str) -> str:
    url = "https://serpapi.com/search"
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERPAPI_KEY,
        "hl": "tr"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        results = []
        organic_results = data.get("organic_results", [])
        for result in organic_results:
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            if title:
                results.append(f"{title}\n{snippet}")
            if len(results) >= 3:
                break
        if results:
            return "\n\n".join(results)
        else:
            return "Sonuç bulunamadı."
    except Exception as e:
        logging.error(f"SerpAPI aramasında hata: {e}")
        return "Sonuç bulunamadı."

def get_ai_continuous_answer(history: list) -> str:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AI_API_KEY}"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": history
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        answer = result["choices"][0]["message"]["content"]
        return answer
    except Exception as e:
        logging.error(f"Yapay Zeka API çağrısında hata: {e}")
        return "❌ Yapay Zeka’dan cevap alınırken hata oluştu."

def get_football_match_odds(query: str) -> str:
    url = "https://api.the-odds-api.com/v3/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "sport": "soccer_epl",
        "region": "uk",
        "mkt": "h2h"
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if data.get("success") != 1:
            return None
        events = data.get("data", [])
        for event in events:
            home = event.get("home_team", "").lower()
            away = event.get("away_team", "").lower()
            if query.lower() in home or query.lower() in away:
                odds_summary = f"Maç: {event.get('home_team')} vs {event.get('away_team')}\n"
                bookmakers = event.get("bookmakers", [])
                for bookmaker in bookmakers:
                    for market in bookmaker.get("markets", []):
                        for outcome in market.get("outcomes", []):
                            odds_summary += f"{outcome.get('name')}: {outcome.get('price')}\n"
                return odds_summary
        return None
    except Exception as e:
        logging.error(f"Oran verileri alınırken hata: {e}")
        return None

def get_prediction(query: str) -> str:
    odds_info = get_football_match_odds(query)
    if odds_info is None:
        odds_info = "Bu maç için oran bilgisi bulunamadı."
    google_results = get_google_search_results(query)
    prompt = f"Bilgiler ışığında:\n\nŞans bilgisi:\n{odds_info}\n\nGoogle arama sonuçları:\n{google_results}\n\nLütfen bu futbol maçının sonucunu ve tahminini belirtin. Soru: {query}\n\nCevap:"
    history = [
        {"role": "system", "content": "Sen, maç oranları ve Google arama sonuçlarına göre futbol maçları tahmini yapan bir yapay Zeka asistanısın."},
        {"role": "user", "content": prompt}
    ]
    prediction = get_ai_continuous_answer(history)
    return prediction

# -------------------------------
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

# -------------------------------
# تابع بررسی عضویت در کانال (اجباری کردن عضویت)
async def ensure_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    invite_link = "https://t.me/+9mlEPlmOqZUzNDgx"
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        is_member = member.status in ["member", "administrator", "creator", "restricted"]
    except Exception as e:
        logging.error(f"Kullanıcı {user_id} üyeliği kontrol edilirken hata: {e}")
        is_member = False
    if not is_member:
        join_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Kanal'a Üye Ol", url=invite_link)]])
        await update.message.reply_text("🚨 Lütfen kanala üye olun ve tekrar /start komutunu gönderin.", reply_markup=join_keyboard)
        return False
    else:
        return True

# -------------------------------
# توابع مربوط به دستورات /start و پیام‌های کاربری
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_subscription(update, context):
        return

    user_ids.add(update.effective_chat.id)
    add_user(update.effective_user.id)

    args = update.message.text.split()
    if len(args) > 1:
        try:
            referrer_id = int(args[1])
            if referrer_id != update.effective_user.id:
                conn = connect_db()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO referrals (referrer_id, referred_id) VALUES (?, ?)", (referrer_id, update.effective_user.id))
                conn.commit()
                conn.close()
                await context.bot.send_message(chat_id=referrer_id, text="🎉 A user has been referred using your code!")
        except Exception as e:
            logging.error(f"Invalid referral code: {e}")

    welcome_message = "🌟 Bot'a hoş geldiniz!"
    await update.message.reply_text(welcome_message, reply_markup=get_main_menu_keyboard())

async def show_todays_matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_lines = []
    for league in TODAY_LEAGUES:
        if league.get("source") == "varzesh3":
            matches = get_livescore_from_varzesh3(league["name"])
        else:
            matches = get_todays_matches_by_id(league["id"])
        if matches:
            message_lines.append(f"📡 {league['name']} için gelecek 3 günün maçları:\n" + "\n".join(matches))
        else:
            message_lines.append(f"❌ {league['name']} için maç bulunamadı.")
    full_message = "\n\n".join(message_lines)
    await update.message.reply_text(full_message, reply_markup=get_back_keyboard())

async def show_condaktor_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["state"] = "condaktor"
    await show_condaktor_menu(update, context)

async def show_live_stream_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [InlineKeyboardButton("Dubai Sports 2 canlı yayın", url="https://livesoccer.live/tvtr/livetv/details/dubai-sports-2-canl%C4%B1-yay%C4%B1n-ba%C4%9Flant%C4%B1s%C4%B1/36")],
        [InlineKeyboardButton("Sharjah Sports canlı yayın", url="https://livesoccer.live/tvtr/livetv/details/sharjah-sports-canl%C4%B1-yay%C4%B1n-ba%C4%9Flant%C4%B1s%C4%B1/35")],
        [InlineKeyboardButton("Dubai Sports canlı yayın", url="https://livesoccer.live/tvtr/livetv/details/dubai-sports-canl%C4%B1-yay%C4%B1n-ba%C4%9Flant%C4%B1s%C4%B1/34")],
        [InlineKeyboardButton("Manchester United TV canlı", url="https://livesoccer.live/tvtr/livetv/details/manchester-united-tv-canl%C4%B1-yay%C4%B1n-ba%C4%9Flant%C4%B1s%C4%B1/33")],
        [InlineKeyboardButton("Persiana Sports", url="https://livesoccer.live/tvtr/livetv/details/persiana-sports-yay%C4%B1n-ba%C4%9Flant%C4%B1s%C4%B1/31")],
        [InlineKeyboardButton("Fubo Sports canlı", url="https://livesoccer.live/tvtr/livetv/details/fubo-sports-canl%C4%B1-yay%C4%B1n-ba%C4%9Flant%C4%B1s%C4%B1/29")],
        [InlineKeyboardButton("Autosport canlı", url="https://livesoccer.live/tvtr/livetv/details/autosport-canl%C4%B1-yay%C4%B1n-ba%C4%9Flant%C4%B1s%C4%B1/28")],
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("Lütfen aşağıdan seçim yapın:", reply_markup=reply_markup)
    await update.message.reply_text("Geri için '🔙 Geri'", reply_markup=get_back_keyboard())

async def show_invite_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    invite_count = get_referral_count(user_id)
    referral_link = f"https://t.me/{context.bot.username}?start={user_id}"
    message = f"🤝 Arkadaş Davet Et\n\nReferans kodunuz: {referral_link}\nDavet: {invite_count}\nKazancınız: {invite_count * referral_amount:.2f}TL"
    share_button = InlineKeyboardButton("🔗 Daveti Paylaş", url=referral_link)
    reply_markup = InlineKeyboardMarkup([[share_button]])
    await update.message.reply_text(message, reply_markup=reply_markup)
    await update.message.reply_text("Geri için '🔙 Geri'", reply_markup=get_back_keyboard())

async def show_wallet_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    invite_count = get_referral_count(user_id)
    earnings = invite_count * referral_amount
    message = f"💰 Cüzdan\n\nKazancınız: {earnings:.2f}TL\nDavet: {invite_count}"
    wallet_buttons = [
         [InlineKeyboardButton("💸 Çekme", callback_data="withdraw")],
         [InlineKeyboardButton("🔙 Geri", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(wallet_buttons)
    await update.message.reply_text(message, reply_markup=reply_markup)

async def handle_wallet_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "withdraw":
         await query.edit_message_text("💸 Çekme özelliği yakında aktif olacak.")
    elif data == "back_to_main":
         context.user_data["state"] = "main"
         await query.edit_message_text("🏠 Ana menüye dönülüyor.")
         await context.bot.send_message(chat_id=update.effective_chat.id, text="🏠 Ana Menü:", reply_markup=get_main_menu_keyboard())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_subscription(update, context):
        return

    # بخش ارسال پیام همگانی (broadcast)
    if update.effective_user.id in ADMIN_IDS and context.user_data.get("broadcast"):
        if update.message.text:
            broadcast_message = update.message.text
            media_type = "text"
        elif update.message.photo:
            # استفاده از شناسه فایل عکس برای ارسال مجدد
            broadcast_message = update.message.photo[-1].file_id
            media_type = "photo"
        else:
            await update.message.reply_text("❗ فقط پیام متنی و عکس برای ارسال همگانی مجاز است.")
            return

        sent_count = 0
        users = get_all_users()
        for user in users:
            telegram_id = user[0]
            try:
                if media_type == "text":
                    await context.bot.send_message(chat_id=telegram_id, text=broadcast_message)
                elif media_type == "photo":
                    await context.bot.send_photo(chat_id=telegram_id, photo=broadcast_message)
                sent_count += 1
            except Exception as e:
                logging.error(f"Error while sending message to {telegram_id}: {e}")

        await update.message.reply_text(f"✅ {sent_count} کاربر پیام دریافت کردند.")
        context.user_data["broadcast"] = False
        return

    text = update.message.text
    state = context.user_data.get("state", "main")
    if state == "main":
        if text == "Bugünün Önemli Maçları ⚽":
            context.user_data["state"] = "today_matches"
            await show_todays_matches(update, context)
        elif text == "Gelecek Maçlar 📡":
            context.user_data["state"] = "live"
            await update.message.reply_text("🗺️ Lütfen ülke seçin:", reply_markup=get_live_countries_keyboard())
        elif text == "Geçmiş Maç Sonuçları ⚽":
            context.user_data["state"] = "past"
            await update.message.reply_text("📅 Lütfen ülke seçin:", reply_markup=get_past_countries_keyboard())
        elif text == "Puan Durumu ve İstatistikler 🗓":
            context.user_data["state"] = "stats"
            await update.message.reply_text("📊 İstatistikler:", reply_markup=get_stats_menu_keyboard())
        elif text == "Canlı TV 🛜":
            context.user_data["state"] = "condaktor"
            await show_condaktor_menu_handler(update, context)
        elif text == "Futbol dünyası ⚽":
            context.user_data["state"] = "futbol_dunyasi"
            await update.message.reply_text("Lütfen bir seçenek seçin:", reply_markup=get_futbol_dunyasi_menu_keyboard())
        elif text == "tv 🤖":
            context.user_data["state"] = "live_stream"
            await show_live_stream_buttons(update, context)
        elif text == "🔗 Botu Paylaş":
            share_button = InlineKeyboardButton("🔗 Paylaş", switch_inline_query="")
            reply_markup = InlineKeyboardMarkup([[share_button]])
            await update.message.reply_text("Botu paylaşmak için:", reply_markup=reply_markup)
        elif text == "🤖 Yapay Zeka":
            context.user_data["state"] = "ai"
            if "ai_history" not in context.user_data or not context.user_data["ai_history"]:
                context.user_data["ai_history"] = [
                    {"role": "system", "content": "Sen GPT-4o mini asistanısın. Sorulara cevap ver."}
                ]
            await update.message.reply_text("🤖 Sorunu yazın (çıkmak için '🔙 Geri'):", reply_markup=get_back_keyboard())
        elif text == "🔮 Yapay Zeka ile Futbol Maçı Tahmini":
            context.user_data["state"] = "prediction"
            await update.message.reply_text("🔮 Takım/maç girin:", reply_markup=get_back_keyboard())
        elif text == "Arkadaş Davet Et 🤝":
            context.user_data["state"] = "invite"
            await show_invite_menu(update, context)
        elif text == "Cüzdan 💰":
            context.user_data["state"] = "wallet"
            await show_wallet_menu(update, context)
        else:
            await update.message.reply_text("⏳ Lütfen geçerli bir seçenek seçin.", reply_markup=get_main_menu_keyboard())
    elif state == "today_matches":
        if text == "🔙 Geri":
            context.user_data["state"] = "main"
            await update.message.reply_text("🏠 Ana menüye dönülüyor:", reply_markup=get_main_menu_keyboard())
        else:
            await update.message.reply_text("⏪ '🔙 Geri' tuşunu kullanın.", reply_markup=get_back_keyboard())
    elif state == "live":
        if text == "🔙 Geri":
            context.user_data["state"] = "main"
            await update.message.reply_text("🏠 Ana menüye dönülüyor:", reply_markup=get_main_menu_keyboard())
        else:
            matched_league = None
            for league in LEAGUES:
                if league["name"] in text:
                    matched_league = league
                    break
            if matched_league:
                context.user_data["selected_league"] = matched_league
                context.user_data["state"] = "live_detail"
                matches = get_todays_matches_by_id(matched_league["id"])
                if matches:
                    match_text = f"📡 {matched_league['name']} maçları:\n" + "\n".join(matches)
                else:
                    match_text = f"❌ {matched_league['name']} maç bulunamadı."
                await update.message.reply_text(match_text, reply_markup=get_back_keyboard())
            else:
                await update.message.reply_text("⏳ Lütfen geçerli bir seçenek seçin.", reply_markup=get_live_countries_keyboard())
    elif state == "live_detail":
        if text == "🔙 Geri":
            context.user_data["state"] = "live"
            await update.message.reply_text("📡 Maçlar menüsüne dönülüyor:", reply_markup=get_live_countries_keyboard())
        else:
            await update.message.reply_text("⏪ '🔙 Geri' tuşunu kullanın.", reply_markup=get_back_keyboard())
    elif state == "past":
        if text == "🔙 Geri":
            context.user_data["state"] = "main"
            await update.message.reply_text("🏠 Ana menüye dönülüyor:", reply_markup=get_main_menu_keyboard())
        else:
            matched_league = None
            for league in LEAGUES:
                if league["name"] in text:
                    matched_league = league
                    break
            if matched_league:
                context.user_data["selected_league"] = matched_league
                context.user_data["state"] = "past_detail"
                matches = get_past_matches_by_id(matched_league["id"])
                if matches:
                    joiner = "\n\n" if matched_league["name"] == "Türkiye" else "\n"
                    match_text = f"📅 {matched_league['name']} geçmiş maçları:\n" + joiner.join(matches)
                else:
                    match_text = f"❌ {matched_league['name']} maç sonucu bulunamadı."
                await update.message.reply_text(match_text, reply_markup=get_back_keyboard())
            else:
                await update.message.reply_text("⏳ Lütfen geçerli bir seçenek seçin.", reply_markup=get_past_countries_keyboard())
    elif state == "past_detail":
        if text == "🔙 Geri":
            context.user_data["state"] = "past"
            await update.message.reply_text("📅 Geçmiş maç menüsüne dönülüyor:", reply_markup=get_past_countries_keyboard())
        else:
            await update.message.reply_text("⏪ '🔙 Geri' tuşunu kullanın.", reply_markup=get_back_keyboard())
    elif state == "stats":
        if text == "🗓 10 ülkenin Lig Tablosu":
            context.user_data["state"] = "league"
            await update.message.reply_text("🏆 Lütfen ülke seçin:", reply_markup=get_league_countries_keyboard())
        elif text == "🔙 Geri":
            context.user_data["state"] = "main"
            await update.message.reply_text("🏠 Ana menüye dönülüyor:", reply_markup=get_main_menu_keyboard())
        else:
            await update.message.reply_text("⏳ Lütfen geçerli bir seçenek seçin.", reply_markup=get_stats_menu_keyboard())
    elif state == "league":
        if text == "🔙 Geri":
            context.user_data["state"] = "stats"
            await update.message.reply_text("📊 İstatistik menüsüne dönülüyor:", reply_markup=get_stats_menu_keyboard())
        else:
            matched_league = None
            for league in LEAGUES:
                if league["name"] in text:
                    matched_league = league
                    break
            if matched_league:
                context.user_data["selected_league"] = matched_league
                context.user_data["state"] = "league_detail"
                standings = get_league_table_by_id(matched_league["id"], season=matched_league.get("season", "2024-2025"))
                if standings:
                    standings_text = f"🏆 {matched_league['name']} lig tablosu:\n\n" + "\n".join(standings)
                else:
                    standings_text = "❌ Lig tablosu bilgisi yok."
                await update.message.reply_text(standings_text, reply_markup=get_back_keyboard())
            else:
                await update.message.reply_text("⏳ Lütfen geçerli bir seçenek seçin.", reply_markup=get_league_countries_keyboard())
    elif state == "league_detail":
        if text == "🔙 Geri":
            context.user_data["state"] = "league"
            await update.message.reply_text("🏆 Lig menüsüne dönülüyor:", reply_markup=get_league_countries_keyboard())
        else:
            await update.message.reply_text("⏪ '🔙 Geri' tuşunu kullanın.", reply_markup=get_back_keyboard())
    elif state == "live_stream":
        if text == "🔙 Geri":
            context.user_data["state"] = "main"
            await update.message.reply_text("🏠 Ana menüye dönülüyor:", reply_markup=get_main_menu_keyboard())
        else:
            await update.message.reply_text("⏪ '🔙 Geri' tuşunu kullanın.", reply_markup=get_back_keyboard())
    elif state == "condaktor":
        if text == "🔙 Geri":
            context.user_data["state"] = "main"
            await update.message.reply_text("🏠 Ana menüye dönülüyor:", reply_markup=get_main_menu_keyboard())
        else:
            await update.message.reply_text("⏪ '🔙 Geri' tuşunu kullanın.", reply_markup=get_back_keyboard())
    elif state == "highlight":
        if text == "🔙 Geri":
            context.user_data["state"] = "main"
            await update.message.reply_text("🏠 Ana menüye dönülüyor:", reply_markup=get_main_menu_keyboard())
        else:
            await update.message.reply_text("⏪ '🔙 Geri' tuşunu kullanın.", reply_markup=get_back_keyboard())
    elif state == "ai":
        if text == "🔙 Geri":
            context.user_data["state"] = "main"
            context.user_data["ai_history"] = []
            await update.message.reply_text("🏠 Ana menüye dönülüyor:", reply_markup=get_main_menu_keyboard())
        else:
            context.user_data["ai_history"].append({"role": "user", "content": text})
            await update.message.reply_text("⏳ İşleniyor...")
            answer = await asyncio.to_thread(get_ai_continuous_answer, context.user_data["ai_history"])
            context.user_data["ai_history"].append({"role": "assistant", "content": answer})
            await update.message.reply_text(answer, reply_markup=get_back_keyboard())
    elif state == "prediction":
        if text == "🔙 Geri":
            context.user_data["state"] = "main"
            await update.message.reply_text("🏠 Ana menüye dönülüyor:", reply_markup=get_main_menu_keyboard())
        else:
            await update.message.reply_text("⏳ Tahmin işleniyor...")
            prediction = await asyncio.to_thread(get_prediction, text)
            prediction_message = f"🔮 Tahmin sonucu:\n\n{prediction}"
            await update.message.reply_text(prediction_message, reply_markup=get_back_keyboard())
    elif state == "invite":
        if text == "🔙 Geri":
            context.user_data["state"] = "main"
            await update.message.reply_text("🏠 Ana menüye dönülüyor:", reply_markup=get_main_menu_keyboard())
        else:
            await update.message.reply_text("⏪ '🔙 Geri' tuşunu kullanın.", reply_markup=get_back_keyboard())
    elif state == "wallet":
        if text == "🔙 Geri":
            context.user_data["state"] = "main"
            await update.message.reply_text("🏠 Ana menüye dönülüyor:", reply_markup=get_main_menu_keyboard())
        else:
            await update.message.reply_text("⏪ '🔙 Geri' tuşunu.", reply_markup=get_back_keyboard())
    elif state == "futbol_dunyasi":
        if text == "🔙 Geri":
            context.user_data["state"] = "main"
            await update.message.reply_text("🏠 Ana menüye dönülüyor:", reply_markup=get_main_menu_keyboard())
        elif text == "Futbol Highlightleri 🎥":
            context.user_data["state"] = "highlight"
            highlights = get_highlight_videos()
            if highlights:
                for title, video_url in highlights:
                    kb = InlineKeyboardMarkup([[InlineKeyboardButton("İzle", url=video_url)]])
                    await update.message.reply_text(f"🎥 {title}", reply_markup=kb)
            else:
                await update.message.reply_text("❌ Highlight bulunamadı.")
            await update.message.reply_text("Geri için '🔙 Geri'", reply_markup=get_back_keyboard())
        elif text == "Puan Durumu ve İstatistikler 🗓":
            context.user_data["state"] = "stats"
            await update.message.reply_text("📊 İstatistikler:", reply_markup=get_stats_menu_keyboard())
        elif text == "Geçmiş Maç Sonuçları ⚽":
            context.user_data["state"] = "past"
            await update.message.reply_text("📅 Lütfen ülke seçin:", reply_markup=get_past_countries_keyboard())
        elif text == "Gelecek Maçlar 📡":
            context.user_data["state"] = "live"
            await update.message.reply_text("🗺️ Lütfen ülke seçin:", reply_markup=get_live_countries_keyboard())
        elif text == "Bugünün Önemli Maçları ⚽":
            context.user_data["state"] = "today_matches"
            await show_todays_matches(update, context)
        else:
            await update.message.reply_text("⏳ Lütfen geçerli bir seçenek seçin.", reply_markup=get_futbol_dunyasi_menu_keyboard())
    else:
        await update.message.reply_text("⏳ Lütfen bekleyin...", reply_markup=get_main_menu_keyboard())

# -------------------------------
# پنل مدیریت با دکمه‌های اینلاین و نمایش اطلاعات واقعی ربات
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🚫 دسترسی ندارید.")
        return
    keyboard = [
        [InlineKeyboardButton("About Bot", callback_data="admin_about")],
        [InlineKeyboardButton("Show Menu", callback_data="admin_showmenu"),
         InlineKeyboardButton("Add Row", callback_data="admin_addrow")],
        [InlineKeyboardButton("Remove Row", callback_data="admin_removerow"),
         InlineKeyboardButton("Set Row", callback_data="admin_setrow")],
        [InlineKeyboardButton("Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("Export Users", callback_data="admin_exportusers")],
        [InlineKeyboardButton("Manage Admins", callback_data="admin_manageadmins")],
        [InlineKeyboardButton("Bot Stats", callback_data="admin_botstats")],
        [InlineKeyboardButton("Set API Keys", callback_data="admin_setapikeys")],
        [InlineKeyboardButton("Set Welcome", callback_data="admin_setwelcome")],
        [InlineKeyboardButton("Channels", callback_data="admin_channels")],
        [InlineKeyboardButton("Set Pagination", callback_data="admin_setpagination")],
        [InlineKeyboardButton("Set Referral", callback_data="admin_setreferral")],
        [InlineKeyboardButton("Edit Code", callback_data="admin_editcode")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🔧 پنل مدیریت:", reply_markup=reply_markup)

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "admin_about":
        await query.edit_message_text(text="این ربات به صورت داینامیک اطلاعات واقعی خود را نمایش می‌دهد.")
    elif data == "admin_showmenu":
        config_text = "تنظیمات منوی اصلی:\n"
        for idx, row in enumerate(admin_config["main_menu_buttons"], start=1):
            config_text += f"{idx}. {', '.join(row)}\n"
        await query.edit_message_text(text=config_text)
    elif data == "admin_addrow":
        await query.edit_message_text(text="برای افزودن ردیف جدید از دستور /addrow استفاده کنید.")
    elif data == "admin_removerow":
        await query.edit_message_text(text="برای حذف ردیف از دستور /removerow استفاده کنید.")
    elif data == "admin_setrow":
        await query.edit_message_text(text="برای ویرایش ردیف از دستور /setrow استفاده کنید.")
    elif data == "admin_broadcast":
        context.user_data["broadcast"] = True
        await query.edit_message_text(text="پیام سراسری (متن یا عکس) را وارد کنید:")
    elif data == "admin_exportusers":
        await query.edit_message_text(text="برای دریافت لیست کاربران به صورت اکسل از دستور /exportusers استفاده کنید.")
    elif data == "admin_manageadmins":
        msg = "ادمین‌های فعلی:\n" + "\n".join(str(a) for a in ADMIN_IDS)
        msg += "\nبرای افزودن از دستور /addadmin و حذف از /removeadmin استفاده کنید."
        await query.edit_message_text(text=msg)
    elif data == "admin_botstats":
        stats_text = get_bot_stats_text()
        await query.edit_message_text(text=stats_text)
    elif data == "admin_setapikeys":
        await query.edit_message_text(text="برای تغییر کلیدهای API از دستور /setapikeys استفاده کنید.")
    elif data == "admin_setwelcome":
        await query.edit_message_text(text="برای تغییر پیام خوش‌آمد از دستور /setwelcome استفاده کنید.")
    elif data == "admin_channels":
        bot_channels = ["@channel1", "@channel2"]
        msg = "کانال‌ها/گروه‌های ثبت شده:\n" + "\n".join(bot_channels)
        await query.edit_message_text(text=msg)
    elif data == "admin_setpagination":
        await query.edit_message_text(text="برای تنظیم صفحه‌بندی از دستور /setpagination استفاده کنید.")
    elif data == "admin_setreferral":
        await query.edit_message_text(text="برای تغییر مبلغ ارجاع از دستور /setreferral استفاده کنید.")
    elif data == "admin_editcode":
        await query.edit_message_text(text="برای ویرایش کد ربات از دستور /editcode استفاده کنید.")
    else:
        await query.edit_message_text(text="عملیات نامشخص.")

# -------------------------------
# دستورات اضافی مدیریت
async def export_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🚫 دسترسی ندارید.")
        return
    users = get_all_users()
    if not users:
        await update.message.reply_text("هیچ کاربری ثبت نشده است.")
        return
    df = pd.DataFrame(users, columns=["Telegram ID", "Join Date"])
    filename = "users.xlsx"
    df.to_excel(filename, index=False)
    with open(filename, "rb") as f:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=f, filename=filename)
    os.remove(filename)

async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🚫 دسترسی ندارید.")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("❗ لطفاً شناسه کاربر (عدد) وارد کنید.")
        return
    new_admin = int(context.args[0])
    if new_admin in ADMIN_IDS:
        await update.message.reply_text("این کاربر از قبل ادمین است.")
    else:
        ADMIN_IDS.append(new_admin)
        await update.message.reply_text(f"✅ کاربر {new_admin} به عنوان ادمین اضافه شد.")

async def remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🚫 دسترسی ندارید.")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("❗ لطفاً شناسه کاربر (عدد) وارد کنید.")
        return
    rem_admin = int(context.args[0])
    if rem_admin in ADMIN_IDS:
        ADMIN_IDS.remove(rem_admin)
        await update.message.reply_text(f"✅ کاربر {rem_admin} از ادمین‌ها حذف شد.")
    else:
        await update.message.reply_text("این کاربر ادمین نیست.")

async def set_api_keys(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🚫 دسترسی ندارید.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("❗ فرمت صحیح: /setapikeys <کلید> <مقدار>")
        return
    key_name = context.args[0]
    new_value = " ".join(context.args[1:])
    global TOKEN, AI_API_KEY, SERPAPI_KEY, ODDS_API_KEY, LIVESCORE_API_KEY, LIVESCORE_API_SECRET
    if key_name == "TOKEN":
        TOKEN = new_value
    elif key_name == "AI_API_KEY":
        AI_API_KEY = new_value
    elif key_name == "SERPAPI_KEY":
        SERPAPI_KEY = new_value
    elif key_name == "ODDS_API_KEY":
        ODDS_API_KEY = new_value
    elif key_name == "LIVESCORE_API_KEY":
        LIVESCORE_API_KEY = new_value
    elif key_name == "LIVESCORE_API_SECRET":
        LIVESCORE_API_SECRET = new_value
    else:
        await update.message.reply_text("❗ کلید نامعتبر است.")
        return
    await update.message.reply_text(f"✅ {key_name} به‌روزرسانی شد.")

async def set_welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🚫 دسترسی ندارید.")
        return
    if not context.args:
        await update.message.reply_text("❗ لطفاً پیام خوش‌آمد را وارد کنید.")
        return
    global welcome_message
    welcome_message = " ".join(context.args)
    await update.message.reply_text("✅ پیام خوش‌آمد تغییر کرد.")

async def show_welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🚫 دسترسی ندارید.")
        return
    await update.message.reply_text(f"پیام خوش‌آمد فعلی:\n\n{welcome_message}")

async def channels_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🚫 دسترسی ندارید.")
        return
    bot_channels = ["@channel1", "@channel2"]
    msg = "کانال‌ها/گروه‌های ثبت شده:\n" + "\n".join(bot_channels)
    await update.message.reply_text(msg)

async def set_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🚫 دسترسی ندارید.")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("❗ لطفاً عدد صفحه‌بندی وارد کنید.")
        return
    global pagination_size
    pagination_size = int(context.args[0])
    await update.message.reply_text(f"✅ اندازه صفحه‌بندی روی {pagination_size} تنظیم شد.")

async def set_referral_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🚫 دسترسی ندارید.")
        return
    try:
        new_amount = float(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("❗ فرمت صحیح: /setreferral <مبلغ>")
        return
    global referral_amount
    referral_amount = new_amount
    await update.message.reply_text(f"✅ مبلغ ارجاع روی {referral_amount} تنظیم شد.")

async def edit_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🚫 دسترسی ندارید.")
        return
    if not context.args:
        await update.message.reply_text("❗ لطفاً کد جدید را وارد کنید.")
        return
    new_code = " ".join(context.args)
    try:
        with open("footballturky.py", "w", encoding="utf-8") as f:
            f.write(new_code)
        await update.message.reply_text("✅ کد ربات به‌روزرسانی شد. (برای اعمال تغییرات نیاز به ریستارت دارید.)")
    except Exception as e:
        await update.message.reply_text(f"❗ خطا در ویرایش کد: {e}")

async def show_detailed_admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🚫 دسترسی ندارید.")
        return
    stats_text = get_bot_stats_text()
    await update.message.reply_text(stats_text)

# -------------------------------
# تابع اصلی
def main():
    create_table()
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^admin_"))
    app.add_handler(CommandHandler("exportusers", export_users))
    app.add_handler(CommandHandler("manageadmins", channels_list))
    app.add_handler(CommandHandler("addadmin", add_admin))
    app.add_handler(CommandHandler("removeadmin", remove_admin))
    app.add_handler(CommandHandler("botstats", show_detailed_admin_stats))
    app.add_handler(CommandHandler("setapikeys", set_api_keys))
    app.add_handler(CommandHandler("setwelcome", set_welcome_message))
    app.add_handler(CommandHandler("showwelcome", show_welcome_message))
    app.add_handler(CommandHandler("channels", channels_list))
    app.add_handler(CommandHandler("setpagination", set_pagination))
    app.add_handler(CommandHandler("setreferral", set_referral_amount))
    app.add_handler(CommandHandler("editcode", edit_code))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_wallet_callback, pattern="^(withdraw|back_to_main)$"))
    app.add_handler(CallbackQueryHandler(condaktor_category_handler, pattern="^condaktor_|^main_menu$"))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
