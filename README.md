# 🤖 Telegram AI Sports Bot

A Telegram bot for AI chat, football scores, live TV links, referrals, wallet tracking, and admin controls.

## Features
- AI chat assistant
- Football module: live scores, fixtures, standings, and highlights
- Live sports TV menus
- User referrals and wallet tracking
- Admin panel and broadcast tools
- SQLite storage
- Supabase-backed channel lists

## Requirements
- Python 3.10+
- A Telegram bot token
- Optional: OpenAI, SerpAPI, Odds API, Supabase, and TheSportsDB credentials

## Setup

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
```

Fill in `.env` with your own values, especially:

- `BOT_TOKEN`
- `CHANNEL_USERNAME`
- `ADMIN_IDS`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SUPABASE_SERVICE_KEY`
- `OPENAI_API_KEY`
- `SERPAPI_KEY`
- `ODDS_API_KEY`
- `THESPORTSDB_API_KEY`

## Run

```bash
python main.py
```

## Notes
- `footballturky.py` is kept for compatibility with the original project layout.
- If Supabase is not configured, the bot falls back to sample channel data where possible.
