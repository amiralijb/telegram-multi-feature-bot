from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from config import referral_amount
from database import get_referral_count
from utils.keyboard_utils import get_back_keyboard

async def show_invite_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the invite menu with referral link"""
    user_id = update.effective_user.id
    invite_count = get_referral_count(user_id)
    referral_link = f"https://t.me/{context.bot.username}?start={user_id}"
    message = f"🤝 Arkadaş Davet Et\n\nReferans kodunuz: {referral_link}\nDavet: {invite_count}\nKazancınız: {invite_count * referral_amount:.2f}TL"
    share_button = InlineKeyboardButton("🔗 Daveti Paylaş", url=referral_link)
    reply_markup = InlineKeyboardMarkup([[share_button]])
    await update.message.reply_text(message, reply_markup=reply_markup)
    await update.message.reply_text("Geri için '🔙 Geri'", reply_markup=get_back_keyboard())

async def show_wallet_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the wallet menu with current earnings"""
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
    """Handle wallet menu callbacks"""
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "withdraw":
         await query.edit_message_text("💸 Çekme özelliği yakında aktif olacak.")
    elif data == "back_to_main":
         context.user_data["state"] = "main"
         await query.edit_message_text("🏠 Ana menüye dönülüyor.")
         from utils.keyboard_utils import get_main_menu_keyboard
         await context.bot.send_message(chat_id=update.effective_chat.id, text="🏠 Ana Menü:", reply_markup=get_main_menu_keyboard())

async def handle_share_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the bot share command"""
    share_button = InlineKeyboardButton("🔗 Paylaş", switch_inline_query="")
    reply_markup = InlineKeyboardMarkup([[share_button]])
    await update.message.reply_text("Botu paylaşmak için:", reply_markup=reply_markup) 