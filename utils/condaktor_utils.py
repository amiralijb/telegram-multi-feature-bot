import logging
import requests
from bs4 import BeautifulSoup
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

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

def get_condaktor_menu_keyboard():
    """Generate the Condaktor menu keyboard with sports categories"""
    keyboard = [
        [InlineKeyboardButton("Canlı TV 🛜", url="https://betrewardtv.live/")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_condaktor_category_keyboard():
    """Generate the Condaktor category keyboard"""
    keyboard = [
        [InlineKeyboardButton("⚽ Futbol", callback_data="condaktor_10")],
        [InlineKeyboardButton("🏀 Basketbol", callback_data="condaktor_9")],
        [InlineKeyboardButton("🎾 Tenis", callback_data="condaktor_7")],
        [InlineKeyboardButton("🏐 Voleybol", callback_data="condaktor_8")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_live_stream_buttons():
    """Generate buttons for live streams"""
    buttons = [
        [InlineKeyboardButton("Dubai Sports 2 canlı yayın", url="https://livesoccer.live/tvtr/livetv/details/dubai-sports-2-canl%C4%B1-yay%C4%B1n-ba%C4%9Flant%C4%B1s%C4%B1/36")],
        [InlineKeyboardButton("Sharjah Sports canlı yayın", url="https://livesoccer.live/tvtr/livetv/details/sharjah-sports-canl%C4%B1-yay%C4%B1n-ba%C4%9Flant%C4%B1s%C4%B1/35")],
        [InlineKeyboardButton("Dubai Sports canlı yayın", url="https://livesoccer.live/tvtr/livetv/details/dubai-sports-canl%C4%B1-yay%C4%B1n-ba%C4%9Flant%C4%B1s%C4%B1/34")],
        [InlineKeyboardButton("Manchester United TV canlı", url="https://livesoccer.live/tvtr/livetv/details/manchester-united-tv-canl%C4%B1-yay%C4%B1n-ba%C4%9Flant%C4%B1s%C4%B1/33")],
        [InlineKeyboardButton("Persiana Sports", url="https://livesoccer.live/tvtr/livetv/details/persiana-sports-yay%C4%B1n-ba%C4%9Flant%C4%B1s%C4%B1/31")],
        [InlineKeyboardButton("Fubo Sports canlı", url="https://livesoccer.live/tvtr/livetv/details/fubo-sports-canl%C4%B1-yay%C4%B1n-ba%C4%9Flant%C4%B1s%C4%B1/29")],
        [InlineKeyboardButton("Autosport canlı", url="https://livesoccer.live/tvtr/livetv/details/autosport-canl%C4%B1-yay%C4%B1n-ba%C4%9Flant%C4%B1s%C4%B1/28")],
    ]
    return InlineKeyboardMarkup(buttons) 