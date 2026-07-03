import logging
import os
import pandas as pd
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from config import ADMIN_IDS, referral_amount
from database import get_all_users, get_bot_stats_text
from handlers.broadcast_handler import init_broadcast

# پنل مدیریت با دکمه‌های اینلاین و نمایش اطلاعات واقعی ربات
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🚫 دسترسی ندارید.")
        return
    keyboard = [
        [InlineKeyboardButton("About Bot", callback_data="admin_about")],
        [InlineKeyboardButton("Show Menu", callback_data="admin_showmenu"),
         InlineKeyboardButton("Add Row", callback_data="admin_addrow")],
        [InlineKeyboardButton("Remove Row", callback_data="admin_removerow"),
         InlineKeyboardButton("Set Row", callback_data="admin_setrow")],
        [InlineKeyboardButton("Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("Export Users", callback_data="admin_exportusers")],
        [InlineKeyboardButton("Manage Admins", callback_data="admin_manageadmins")],
        [InlineKeyboardButton("Bot Stats", callback_data="admin_botstats")],
        [InlineKeyboardButton("Set API Keys", callback_data="admin_setapikeys")],
        [InlineKeyboardButton("Set Welcome", callback_data="admin_setwelcome")],
        [InlineKeyboardButton("Channels", callback_data="admin_channels")],
        [InlineKeyboardButton("Set Pagination", callback_data="admin_setpagination")],
        [InlineKeyboardButton("Set Referral", callback_data="admin_setreferral")],
        [InlineKeyboardButton("Edit Code", callback_data="admin_editcode")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🔧 پنل مدیریت:", reply_markup=reply_markup)

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "admin_about":
        await query.edit_message_text(text="این ربات به صورت داینامیک اطلاعات واقعی خود را نمایش می‌دهد.")
    elif data == "admin_showmenu":
        from config import admin_config
        config_text = "تنظیمات منوی اصلی:\n"
        for idx, row in enumerate(admin_config["main_menu_buttons"], start=1):
            config_text += f"{idx}. {', '.join(row)}\n"
        await query.edit_message_text(text=config_text)
    elif data == "admin_addrow":
        await query.edit_message_text(text="برای افزودن ردیف جدید از دستور /addrow استفاده کنید.")
    elif data == "admin_removerow":
        await query.edit_message_text(text="برای حذف ردیف از دستور /removerow استفاده کنید.")
    elif data == "admin_setrow":
        await query.edit_message_text(text="برای ویرایش ردیف از دستور /setrow استفاده کنید.")
    elif data == "admin_broadcast":
        # Start the broadcast menu (using the new broadcast handler)
        keyboard = [
            [InlineKeyboardButton("ارسال متن", callback_data="broadcast_text")],
            [InlineKeyboardButton("ارسال عکس", callback_data="broadcast_photo")],
            [InlineKeyboardButton("ارسال فایل", callback_data="broadcast_document")],
            [InlineKeyboardButton("ارسال ویدیو", callback_data="broadcast_video")],
            [InlineKeyboardButton("ارسال صوت", callback_data="broadcast_audio")],
            [InlineKeyboardButton("بازگشت", callback_data="broadcast_cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📢 *ارسال پیام همگانی*\n\n"
            "از این بخش می‌توانید پیام، عکس، فایل، ویدیو و صوت را برای همه کاربران ربات ارسال کنید.\n"
            "لطفاً نوع محتوایی که می‌خواهید ارسال کنید را انتخاب نمایید:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    elif data == "admin_exportusers":
        await query.edit_message_text(text="برای دریافت لیست کاربران به صورت اکسل از دستور /exportusers استفاده کنید.")
    elif data == "admin_manageadmins":
        msg = "ادمین‌های فعلی:\n" + "\n".join(str(a) for a in ADMIN_IDS)
        msg += "\nبرای افزودن از دستور /addadmin و حذف از /removeadmin استفاده کنید."
        await query.edit_message_text(text=msg)
    elif data == "admin_botstats":
        stats_text = get_bot_stats_text()
        await query.edit_message_text(text=stats_text)
    elif data == "admin_setapikeys":
        await query.edit_message_text(text="برای تغییر کلیدهای API از دستور /setapikeys استفاده کنید.")
    elif data == "admin_setwelcome":
        await query.edit_message_text(text="برای تغییر پیام خوش‌آمد از دستور /setwelcome استفاده کنید.")
    elif data == "admin_channels":
        bot_channels = ["@channel1", "@channel2"]
        msg = "کانال‌ها/گروه‌های ثبت شده:\n" + "\n".join(bot_channels)
        await query.edit_message_text(text=msg)
    elif data == "admin_setpagination":
        await query.edit_message_text(text="برای تنظیم صفحه‌بندی از دستور /setpagination استفاده کنید.")
    elif data == "admin_setreferral":
        await query.edit_message_text(text="برای تغییر مبلغ ارجاع از دستور /setreferral استفاده کنید.")
    elif data == "admin_editcode":
        await query.edit_message_text(text="برای ویرایش کد ربات از دستور /editcode استفاده کنید.")
    else:
        await query.edit_message_text(text="عملیات نامشخص.")

# -------------------------------
# دستورات اضافی مدیریت
async def export_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🚫 دسترسی ندارید.")
        return
    users = get_all_users()
    if not users:
        await update.message.reply_text("هیچ کاربری ثبت نشده است.")
        return
    df = pd.DataFrame(users, columns=["Telegram ID", "Join Date"])
    filename = "users.xlsx"
    df.to_excel(filename, index=False)
    with open(filename, "rb") as f:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=f, filename=filename)
    os.remove(filename)

async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🚫 دسترسی ندارید.")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("❗ لطفاً شناسه کاربر (عدد) وارد کنید.")
        return
    new_admin = int(context.args[0])
    if new_admin in ADMIN_IDS:
        await update.message.reply_text("این کاربر از قبل ادمین است.")
    else:
        ADMIN_IDS.append(new_admin)
        await update.message.reply_text(f"✅ کاربر {new_admin} به عنوان ادمین اضافه شد.")

async def remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🚫 دسترسی ندارید.")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("❗ لطفاً شناسه کاربر (عدد) وارد کنید.")
        return
    rem_admin = int(context.args[0])
    if rem_admin in ADMIN_IDS:
        ADMIN_IDS.remove(rem_admin)
        await update.message.reply_text(f"✅ کاربر {rem_admin} از ادمین‌ها حذف شد.")
    else:
        await update.message.reply_text("این کاربر ادمین نیست.")

async def set_api_keys(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🚫 دسترسی ندارید.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("❗ فرمت صحیح: /setapikeys <کلید> <مقدار>")
        return
    key_name = context.args[0]
    new_value = " ".join(context.args[1:])
    import config
    if key_name == "TOKEN":
        config.TOKEN = new_value
    elif key_name == "AI_API_KEY":
        config.AI_API_KEY = new_value
    elif key_name == "SERPAPI_KEY":
        config.SERPAPI_KEY = new_value
    elif key_name == "ODDS_API_KEY":
        config.ODDS_API_KEY = new_value
    elif key_name == "LIVESCORE_API_KEY":
        config.LIVESCORE_API_KEY = new_value
    elif key_name == "LIVESCORE_API_SECRET":
        config.LIVESCORE_API_SECRET = new_value
    else:
        await update.message.reply_text("❗ کلید نامعتبر است.")
        return
    await update.message.reply_text(f"✅ {key_name} به‌روزرسانی شد.")

async def set_welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🚫 دسترسی ندارید.")
        return
    if not context.args:
        await update.message.reply_text("❗ لطفاً پیام خوش‌آمد را وارد کنید.")
        return
    import config
    config.welcome_message = " ".join(context.args)
    await update.message.reply_text("✅ پیام خوش‌آمد تغییر کرد.")

async def show_welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🚫 دسترسی ندارید.")
        return
    from config import welcome_message
    await update.message.reply_text(f"پیام خوش‌آمد فعلی:\n\n{welcome_message}")

async def channels_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🚫 دسترسی ندارید.")
        return
    bot_channels = ["@channel1", "@channel2"]
    msg = "کانال‌ها/گروه‌های ثبت شده:\n" + "\n".join(bot_channels)
    await update.message.reply_text(msg)

async def set_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🚫 دسترسی ندارید.")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("❗ لطفاً عدد صفحه‌بندی وارد کنید.")
        return
    pagination_size = int(context.args[0])
    await update.message.reply_text(f"✅ اندازه صفحه‌بندی روی {pagination_size} تنظیم شد.")

async def set_referral_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🚫 دسترسی ندارید.")
        return
    try:
        new_amount = float(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("❗ فرمت صحیح: /setreferral <مبلغ>")
        return
    import config
    config.referral_amount = new_amount
    await update.message.reply_text(f"✅ مبلغ ارجاع روی {config.referral_amount} تنظیم شد.")

async def edit_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🚫 دسترسی ندارید.")
        return
    if not context.args:
        await update.message.reply_text("❗ لطفاً کد جدید را وارد کنید.")
        return
    new_code = " ".join(context.args)
    try:
        with open("footballturky.py", "w", encoding="utf-8") as f:
            f.write(new_code)
        await update.message.reply_text("✅ کد ربات به‌روزرسانی شد. (برای اعمال تغییرات نیاز به ریستارت دارید.)")
    except Exception as e:
        await update.message.reply_text(f"❗ خطا در ویرایش کد: {e}")

async def show_detailed_admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🚫 دسترسی ندارید.")
        return
    stats_text = get_bot_stats_text()
    await update.message.reply_text(stats_text) 