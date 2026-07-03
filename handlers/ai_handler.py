import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes

from utils.api_utils import get_ai_continuous_answer, get_prediction
from utils.keyboard_utils import get_back_keyboard

async def handle_ai_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle AI message requests"""
    text = update.message.text
    if text == "🔙 Geri":
        context.user_data["state"] = "main"
        context.user_data["ai_history"] = []
        from utils.keyboard_utils import get_main_menu_keyboard
        await update.message.reply_text("🏠 Ana menüye dönülüyor:", reply_markup=get_main_menu_keyboard())
    else:
        context.user_data["ai_history"].append({"role": "user", "content": text})
        await update.message.reply_text("⏳ İşleniyor...")
        try:
            answer = await asyncio.to_thread(get_ai_continuous_answer, context.user_data["ai_history"])
            context.user_data["ai_history"].append({"role": "assistant", "content": answer})
            await update.message.reply_text(answer, reply_markup=get_back_keyboard())
        except Exception as e:
            logging.error(f"AI processing error: {e}")
            await update.message.reply_text("❌ Yanıt alınırken bir hata oluştu.", reply_markup=get_back_keyboard())

async def start_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start an AI chat session"""
    context.user_data["state"] = "ai"
    if "ai_history" not in context.user_data or not context.user_data["ai_history"]:
        context.user_data["ai_history"] = [
            {"role": "system", "content": "Sen GPT-4o mini asistanısın. Sorulara cevap ver."}
        ]
    await update.message.reply_text("🤖 Sorunu yazın (çıkmak için '🔙 Geri'):", reply_markup=get_back_keyboard())

async def handle_prediction_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle football match prediction requests"""
    text = update.message.text
    if text == "🔙 Geri":
        context.user_data["state"] = "main"
        from utils.keyboard_utils import get_main_menu_keyboard
        await update.message.reply_text("🏠 Ana menüye dönülüyor:", reply_markup=get_main_menu_keyboard())
    else:
        await update.message.reply_text("⏳ Tahmin işleniyor...")
        try:
            prediction = await asyncio.to_thread(get_prediction, text)
            prediction_message = f"🔮 Tahmin sonucu:\n\n{prediction}"
            await update.message.reply_text(prediction_message, reply_markup=get_back_keyboard())
        except Exception as e:
            logging.error(f"Prediction error: {e}")
            await update.message.reply_text("❌ Tahmin yapılırken bir hata oluştu.", reply_markup=get_back_keyboard())

async def start_prediction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start a prediction request"""
    context.user_data["state"] = "prediction"
    await update.message.reply_text("🔮 Takım/maç girin:", reply_markup=get_back_keyboard()) 