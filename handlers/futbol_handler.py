import logging
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from config import TODAY_LEAGUES, LEAGUES
from utils.keyboard_utils import (
    get_futbol_dunyasi_menu_keyboard,
    get_back_keyboard,
    get_live_countries_keyboard,
    get_past_countries_keyboard,
    get_stats_menu_keyboard,
    get_league_countries_keyboard
)
from utils.api_utils import (
    get_todays_matches_by_id,
    get_livescore_from_varzesh3,
    get_past_matches_by_id,
    get_league_table_by_id,
    get_highlight_videos
)

async def show_futbol_dunyasi_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the Futbol dünyası menu"""
    context.user_data["state"] = "futbol_dunyasi"
    await update.message.reply_text("Lütfen bir seçenek seçin:", reply_markup=get_futbol_dunyasi_menu_keyboard())

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

async def show_highlight_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display football highlights"""
    context.user_data["state"] = "highlight"
    highlights = get_highlight_videos()
    if highlights:
        for title, video_url in highlights:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("İzle", url=video_url)]])
            await update.message.reply_text(f"🎥 {title}", reply_markup=kb)
    else:
        await update.message.reply_text("❌ Highlight bulunamadı.")
    await update.message.reply_text("Geri için '🔙 Geri'", reply_markup=get_back_keyboard())

async def show_past_matches_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display past matches menu"""
    context.user_data["state"] = "past"
    await update.message.reply_text("📅 Lütfen ülke seçin:", reply_markup=get_past_countries_keyboard())

async def show_live_matches_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display live matches menu"""
    context.user_data["state"] = "live"
    await update.message.reply_text("🗺️ Lütfen ülke seçin:", reply_markup=get_live_countries_keyboard())

async def show_stats_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display stats menu"""
    context.user_data["state"] = "stats"
    await update.message.reply_text("📊 İstatistikler:", reply_markup=get_stats_menu_keyboard())

async def handle_past_match_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle past match country selection"""
    text = update.message.text
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
        return True
    return False

async def handle_live_match_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle live match country selection"""
    text = update.message.text
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
        return True
    return False

async def handle_league_stats_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle league selection for stats"""
    text = update.message.text
    if text == "🗓 10 ülkenin Lig Tablosu":
        context.user_data["state"] = "league"
        await update.message.reply_text("🏆 Lütfen ülke seçin:", reply_markup=get_league_countries_keyboard())
        return True
    return False

async def handle_league_table_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle league table country selection"""
    text = update.message.text
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
        return True
    return False 