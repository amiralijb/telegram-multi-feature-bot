import logging
from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_IDS
from utils.keyboard_utils import get_main_menu_keyboard, get_back_keyboard
from database import get_all_users
from handlers.start_handler import ensure_subscription
from handlers.broadcast_handler import handle_broadcast_input
from handlers.futbol_handler import (
    show_futbol_dunyasi_menu,
    show_todays_matches,
    show_highlight_menu,
    show_past_matches_menu,
    show_live_matches_menu,
    show_stats_menu,
    handle_past_match_selection,
    handle_live_match_selection,
    handle_league_stats_selection,
    handle_league_table_selection
)
from handlers.wallet_handler import (
    show_invite_menu,
    show_wallet_menu,
    handle_share_bot
)
from handlers.ai_handler import (
    start_ai_chat,
    handle_ai_message,
    start_prediction,
    handle_prediction_request
)
from handlers.condaktor_handler import (
    show_condaktor_menu,
    show_live_stream_menu,
    show_canli_tv_menu
)
from handlers.sport_tv_handler import (
    show_sport_tv_menu,
    handle_sport_tv_text
)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Central message handler for all user text messages"""
    if not await ensure_subscription(update, context):
        return

    # Check if this is a broadcast message from an admin
    if update.effective_user.id in ADMIN_IDS:
        # Try to handle as a broadcast input
        is_broadcast = await handle_broadcast_input(update, context)
        if is_broadcast:
            return

    text = update.message.text
    state = context.user_data.get("state", "main")

    # Main menu state
    if state == "main":
        if text == "Bugünün Önemli Maçları ⚽":
            context.user_data["state"] = "today_matches"
            await show_todays_matches(update, context)
        elif text == "Gelecek Maçlar 📡":
            await show_live_matches_menu(update, context)
        elif text == "Geçmiş Maç Sonuçları ⚽":
            await show_past_matches_menu(update, context)
        elif text == "Puan Durumu ve İstatistikler 🗓":
            await show_stats_menu(update, context)
        elif text == "Canlı TV 🛜":
            context.user_data["state"] = "canli_tv"
            await show_canli_tv_menu(update, context)
        elif text == "Sport TV 📺":
            await show_sport_tv_menu(update, context)
        elif text == "Futbol dünyası ⚽":
            await show_futbol_dunyasi_menu(update, context)
        elif text == "tv 🤖":
            await show_live_stream_menu(update, context)
        elif text == "🔗 Botu Paylaş":
            await handle_share_bot(update, context)
        elif text == "🤖 Yapay Zeka":
            await start_ai_chat(update, context)
        elif text == "🔮 Yapay Zeka ile Futbol Maçı Tahmini":
            await start_prediction(update, context)
        elif text == "Arkadaş Davet Et 🤝":
            await show_invite_menu(update, context)
        elif text == "Cüzdan 💰":
            await show_wallet_menu(update, context)
        else:
            await update.message.reply_text("⏳ Lütfen geçerli bir seçenek seçin.", reply_markup=get_main_menu_keyboard())
    
    # Sport TV state
    elif state == "sport_tv" or state == "sport_tv_category":
        await handle_sport_tv_text(update, context)
    
    # Today matches state
    elif state == "today_matches":
        if text == "🔙 Geri":
            context.user_data["state"] = "main"
            await update.message.reply_text("🏠 Ana menüye dönülüyor:", reply_markup=get_main_menu_keyboard())
        else:
            await update.message.reply_text("⏪ '🔙 Geri' tuşunu kullanın.", reply_markup=get_back_keyboard())
    
    # Live matches state
    elif state == "live":
        if text == "🔙 Geri":
            context.user_data["state"] = "main"
            await update.message.reply_text("🏠 Ana menüye dönülüyor:", reply_markup=get_main_menu_keyboard())
        else:
            handled = await handle_live_match_selection(update, context)
            if not handled:
                await update.message.reply_text("⏳ Lütfen geçerli bir seçenek seçin.")
    
    # Live match detail state
    elif state == "live_detail":
        if text == "🔙 Geri":
            context.user_data["state"] = "live"
            await update.message.reply_text("📡 Maçlar menüsüne dönülüyor:")
            await show_live_matches_menu(update, context)
        else:
            await update.message.reply_text("⏪ '🔙 Geri' tuşunu kullanın.", reply_markup=get_back_keyboard())
    
    # Past matches state
    elif state == "past":
        if text == "🔙 Geri":
            context.user_data["state"] = "main"
            await update.message.reply_text("🏠 Ana menüye dönülüyor:", reply_markup=get_main_menu_keyboard())
        else:
            handled = await handle_past_match_selection(update, context)
            if not handled:
                await update.message.reply_text("⏳ Lütfen geçerli bir seçenek seçin.")
    
    # Past match detail state
    elif state == "past_detail":
        if text == "🔙 Geri":
            context.user_data["state"] = "past"
            await update.message.reply_text("📅 Geçmiş maç menüsüne dönülüyor:")
            await show_past_matches_menu(update, context)
        else:
            await update.message.reply_text("⏪ '🔙 Geri' tuşunu kullanın.", reply_markup=get_back_keyboard())
    
    # Stats state
    elif state == "stats":
        if text == "🔙 Geri":
            context.user_data["state"] = "main"
            await update.message.reply_text("🏠 Ana menüye dönülüyor:", reply_markup=get_main_menu_keyboard())
        else:
            handled = await handle_league_stats_selection(update, context)
            if not handled:
                await update.message.reply_text("⏳ Lütfen geçerli bir seçenek seçin.")
    
    # League state
    elif state == "league":
        if text == "🔙 Geri":
            context.user_data["state"] = "stats"
            await update.message.reply_text("📊 İstatistik menüsüne dönülüyor:")
            await show_stats_menu(update, context)
        else:
            handled = await handle_league_table_selection(update, context)
            if not handled:
                await update.message.reply_text("⏳ Lütfen geçerli bir seçenek seçin.")
    
    # League detail state
    elif state == "league_detail":
        if text == "🔙 Geri":
            context.user_data["state"] = "league"
            await update.message.reply_text("🏆 Lig menüsüne dönülüyor:")
            from utils.keyboard_utils import get_league_countries_keyboard
            await update.message.reply_text("🏆 Lütfen ülke seçin:", reply_markup=get_league_countries_keyboard())
        else:
            await update.message.reply_text("⏪ '🔙 Geri' tuşunu kullanın.", reply_markup=get_back_keyboard())
    
    # Live stream state
    elif state == "live_stream":
        if text == "🔙 Geri":
            context.user_data["state"] = "main"
            await update.message.reply_text("🏠 Ana menüye dönülüyor:", reply_markup=get_main_menu_keyboard())
        else:
            await update.message.reply_text("⏪ '🔙 Geri' tuşunu kullanın.", reply_markup=get_back_keyboard())
    
    # Condaktor state
    elif state == "condaktor":
        if text == "🔙 Geri":
            context.user_data["state"] = "main"
            await update.message.reply_text("🏠 Ana menüye dönülüyor:", reply_markup=get_main_menu_keyboard())
        else:
            await update.message.reply_text("⏪ '🔙 Geri' tuşunu kullanın.", reply_markup=get_back_keyboard())
    
    # Highlight state
    elif state == "highlight":
        if text == "🔙 Geri":
            context.user_data["state"] = "main"
            await update.message.reply_text("🏠 Ana menüye dönülüyor:", reply_markup=get_main_menu_keyboard())
        else:
            await update.message.reply_text("⏪ '🔙 Geri' tuşunu kullanın.", reply_markup=get_back_keyboard())
    
    # AI state
    elif state == "ai":
        await handle_ai_message(update, context)
    
    # Prediction state
    elif state == "prediction":
        await handle_prediction_request(update, context)
    
    # Invite state
    elif state == "invite":
        if text == "🔙 Geri":
            context.user_data["state"] = "main"
            await update.message.reply_text("🏠 Ana menüye dönülüyor:", reply_markup=get_main_menu_keyboard())
        else:
            await update.message.reply_text("⏪ '🔙 Geri' tuşunu kullanın.", reply_markup=get_back_keyboard())
    
    # Wallet state
    elif state == "wallet":
        if text == "🔙 Geri":
            context.user_data["state"] = "main"
            await update.message.reply_text("🏠 Ana menüye dönülüyor:", reply_markup=get_main_menu_keyboard())
        else:
            await update.message.reply_text("⏪ '🔙 Geri' tuşunu.", reply_markup=get_back_keyboard())
    
    # Futbol dunyasi state
    elif state == "futbol_dunyasi":
        if text == "🔙 Geri":
            context.user_data["state"] = "main"
            await update.message.reply_text("🏠 Ana menüye dönülüyor:", reply_markup=get_main_menu_keyboard())
        elif text == "Futbol Highlightleri 🎥":
            await show_highlight_menu(update, context)
        elif text == "Puan Durumu ve İstatistikler 🗓":
            await show_stats_menu(update, context)
        elif text == "Geçmiş Maç Sonuçları ⚽":
            await show_past_matches_menu(update, context)
        elif text == "Gelecek Maçlar 📡":
            await show_live_matches_menu(update, context)
        elif text == "Bugünün Önemli Maçları ⚽":
            context.user_data["state"] = "today_matches"
            await show_todays_matches(update, context)
        else:
            await update.message.reply_text("⏳ Lütfen geçerli bir seçenek seçin.", reply_markup=get_futbol_dunyasi_menu_keyboard())
    
    # Canli TV state
    elif state == "canli_tv":
        if text == "🔙 Geri":
            context.user_data["state"] = "main"
            await update.message.reply_text("🏠 Ana menüye dönülüyor:", reply_markup=get_main_menu_keyboard())
        else:
            await update.message.reply_text("⏪ '🔙 Geri' tuşunu kullanın.", reply_markup=get_back_keyboard())
    
    else:
        await update.message.reply_text("⏳ Lütfen bekleyin...", reply_markup=get_main_menu_keyboard()) 