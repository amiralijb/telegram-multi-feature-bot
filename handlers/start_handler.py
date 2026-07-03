import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from config import CHANNEL_USERNAME, welcome_message
from utils.keyboard_utils import get_main_menu_keyboard
from database import add_user, add_referral

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

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_subscription(update, context):
        return

    from config import user_ids
    user_ids.add(update.effective_chat.id)
    add_user(update.effective_user.id)

    args = update.message.text.split()
    if len(args) > 1:
        try:
            referrer_id = int(args[1])
            if referrer_id != update.effective_user.id:
                add_referral(referrer_id, update.effective_user.id)
                await context.bot.send_message(chat_id=referrer_id, text="🎉 A user has been referred using your code!")
        except Exception as e:
            logging.error(f"Invalid referral code: {e}")

    await update.message.reply_text(welcome_message, reply_markup=get_main_menu_keyboard()) 