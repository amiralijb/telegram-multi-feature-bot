import logging
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from config import (
    LIVE_MATCHES_URL,
    PAST_MATCHES_URL,
    LEAGUE_TABLE_URL,
    UPCOMING_MATCHES_URL,
    AI_API_KEY,
    SERPAPI_KEY,
    ODDS_API_KEY
)

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
        return "❌ Yapay Zeka'dan cevap alınırken hata oluştu."

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