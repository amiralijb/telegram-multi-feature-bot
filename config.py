import os

def _env(name: str, default: str = "") -> str:
    value = os.getenv(name)
    return value if value is not None and value != "" else default

def _env_int_list(name: str, default=None):
    raw = os.getenv(name, "")
    if not raw:
        return list(default or [])
    values = []
    for item in raw.replace(";", ",").split(","):
        item = item.strip()
        if not item:
            continue
        try:
            values.append(int(item))
        except ValueError:
            continue
    return values or list(default or [])

def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name, "")
    try:
        return float(raw) if raw else default
    except ValueError:
        return default

# Bot Configuration
TOKEN = _env("BOT_TOKEN", _env("TOKEN", "TOKEN"))
CHANNEL_USERNAME = _env("CHANNEL_USERNAME", "@CHANNEL_USERNAME")
ADMIN_IDS = _env_int_list("ADMIN_IDS", default=[])

# Referral Configuration
referral_amount = _env_float("REFERRAL_REWARD", 3.0)

# API Keys
AI_API_KEY = _env("OPENAI_API_KEY")
SERPAPI_KEY = _env("SERPAPI_KEY")
ODDS_API_KEY = _env("ODDS_API_KEY")

LIVESCORE_API_KEY = _env("LIVESCORE_API_KEY")
LIVESCORE_API_SECRET = _env("LIVESCORE_API_SECRET")
LIVESCORE_COMPETITION_ID = _env("LIVESCORE_COMPETITION_ID")

# TheSportsDB / football data endpoints
THESPORTSDB_API_KEY = _env("THESPORTSDB_API_KEY", "1")
BASE_API_URL = f"https://www.thesportsdb.com/api/v1/json/{THESPORTSDB_API_KEY}/"
LIVE_MATCHES_URL = BASE_API_URL + "livescore.php"
PAST_MATCHES_URL = BASE_API_URL + "eventspastleague.php"
LEAGUE_TABLE_URL = BASE_API_URL + "lookuptable.php"
UPCOMING_MATCHES_URL = BASE_API_URL + "eventsnextleague.php"

# Supabase Configuration
SUPABASE_URL = _env("SUPABASE_URL")
SUPABASE_KEY = _env("SUPABASE_KEY")
SUPABASE_SERVICE_KEY = _env("SUPABASE_SERVICE_KEY")

# Menu Configuration
admin_config = {
    "main_menu_buttons": [
        ["Canlı TV 🛜", "Sport TV 📺"],
        ["Futbol dünyası ⚽"],
        ["🔮 Yapay Zeka ile Futbol Maçı Tahmini", "🤖 Yapay Zeka"],
        ["Arkadaş Davet Et 🤝", "Cüzdan 💰"],
        ["🔗 Botu Paylaş"]
    ]
}

# Storage for user IDs
user_ids = set()
user_join_times = {}
referrals = {}

# League Information
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

# Default welcome message
welcome_message = _env("WELCOME_MESSAGE", "🌟 Bot'a hoş geldiniz!")
