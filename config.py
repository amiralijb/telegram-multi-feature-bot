import os

# Bot Configuration
TOKEN = "TOKEN"  
CHANNEL_USERNAME = "@CHANNEL_USERNAME"  
ADMIN_IDS = [5224242242454]  

# Referral Configuration
referral_amount = 3  

# API Keys
AI_API_KEY = os.getenv("OPENAI_API_KEY")
SERPAPI_KEY = "SERPAPI_KEY"
ODDS_API_KEY = "ODDS_API_KEY"

LIVESCORE_API_KEY = "LIVESCORE_API_KEY"
LIVESCORE_API_SECRET = "LIVESCORE_API_SECRET"
LIVESCORE_COMPETITION_ID = "LIVESCORE_COMPETITION_ID"

# Supabase Configuration
SUPABASE_URL = "SUPABASE_URL"
SUPABASE_KEY = "SUPABASE_KEY"
# Alternative service role key if needed
SUPABASE_SERVICE_KEY = "SUPABASE_SERVICE_KEY"

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

# API URLs
BASE_API_URL = "SUPABASE_SERVICE_KEY"
LIVE_MATCHES_URL = BASE_API_URL + "livescore.php"
PAST_MATCHES_URL = BASE_API_URL + "eventspastleague.php"
LEAGUE_TABLE_URL = BASE_API_URL + "lookuptable.php"
UPCOMING_MATCHES_URL = BASE_API_URL + "eventsnextleague.php"

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
welcome_message = "🌟 Bot'a hoş geldiniz!" 