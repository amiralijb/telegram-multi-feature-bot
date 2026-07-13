import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from utils.supabase_utils import (
    get_channels_from_supabase, 
    get_channel_by_id
)
from utils.keyboard_utils import get_back_keyboard, get_main_menu_keyboard

async def show_sport_tv_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all Sport TV channels directly without grouping"""
    context.user_data["state"] = "sport_tv"
    
    # Show loading message
    loading_message = await update.message.reply_text("⏳ Kanallar yükleniyor, lütfen bekleyin...")
    
    # Get all channels from Supabase
    channels = get_channels_from_supabase()
    
    # Delete loading message
    try:
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=loading_message.message_id
        )
    except Exception as e:
        logging.error(f"Error deleting loading message: {e}")
    
    if channels:
        # Create inline keyboard for channels
        buttons = []
        
        # Prioritize Turkish names and sort channels alphabetically
        def get_channel_name(channel):
            return (channel.get("name_tr", "") or 
                   channel.get("name_en", "") or 
                   channel.get("name_fa", "") or 
                   "Bilinmiyor")
        
        sorted_channels = sorted(channels, key=lambda x: get_channel_name(x))
        
        for channel in sorted_channels:
            # Get appropriate channel name based on available fields with Turkish priority
            channel_name = get_channel_name(channel)
            channel_id = channel.get("id")
            
            # Add category indicator if available
            category = channel.get("category", "")
            if category:
                if category.lower() == "sports" or category.lower() == "sport":
                    emoji = "⚽ "
                elif category.lower() == "news":
                    emoji = "📰 "
                elif category.lower() == "kids" or category.lower() == "children":
                    emoji = "👶 "
                elif category.lower() == "movies" or category.lower() == "film":
                    emoji = "🎬 "
                elif category.lower() == "documentary" or category.lower() == "belgesel":
                    emoji = "🌍 "
                elif category.lower() == "music" or category.lower() == "müzik":
                    emoji = "🎵 "
                else:
                    emoji = "📡 "
            else:
                emoji = "📡 "
            
            # Only add button if channel has a name
            if channel_name.strip():
                buttons.append([InlineKeyboardButton(f"{emoji}{channel_name}", callback_data=f"sport_tv_{channel_id}")])
        
        # Add back button
        buttons.append([InlineKeyboardButton("🔙 Ana Menü", callback_data="sport_tv_back_to_main")])
        
        reply_markup = InlineKeyboardMarkup(buttons)
        
        if update.message:
            await update.message.reply_text(
                "📺 <b>TV Kanalları</b>\n\n" +
                "Aşağıdaki listeden izlemek istediğiniz kanalı seçebilirsiniz.",
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        else:
            await update.callback_query.edit_message_text(
                "📺 <b>TV Kanalları</b>\n\n" +
                "Aşağıdaki listeden izlemek istediğiniz kanalı seçebilirsiniz.",
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
    else:
        # Create a fallback button to go back
        buttons = [[InlineKeyboardButton("🔙 Ana Menü", callback_data="sport_tv_back_to_main")]]
        reply_markup = InlineKeyboardMarkup(buttons)
        
        if update.message:
            await update.message.reply_text(
                "❌ Kanal bulunamadı veya bir hata oluştu.\n\n" +
                "Lütfen daha sonra tekrar deneyin.",
                reply_markup=reply_markup
            )
        else:
            await update.callback_query.edit_message_text(
                "❌ Kanal bulunamadı veya bir hata oluştu.\n\n" +
                "Lütfen daha sonra tekrar deneyin.",
                reply_markup=reply_markup
            )

async def handle_channel_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle channel selection callback"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "sport_tv_back_to_main":
        # Go back to main menu
        context.user_data["state"] = "main"
        await query.edit_message_text("🏠 Ana menüye dönülüyor...")
        return
    
    # Handle channel selection
    if data.startswith("sport_tv_"):
        channel_id = data.replace("sport_tv_", "")
        
        # Show loading message
        await query.edit_message_text("⏳ Kanal bilgileri yükleniyor...")
        
        channel = get_channel_by_id(channel_id)
        
        if channel:
            # Get appropriate channel name based on available fields
            channel_name = channel.get("name_tr", "") or channel.get("name_en", "") or channel.get("name_fa", "") or "Bilinmiyor"
            channel_desc = channel.get("description", "")
            
            # Create buttons for going back and watching on BetReward TV
            buttons = [
                [InlineKeyboardButton("📺 BetReward TV'de İzle", url="https://betrewardtv.live/")],
                [InlineKeyboardButton("🔙 Kanallara Dön", callback_data="sport_tv_back_to_channels")]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            
            # Send channel info with Turkish formatting
            message = f"📡 <b>{channel_name}</b>\n\n"
            
            if channel_desc:
                message += f"ℹ️ <i>{channel_desc}</i>\n\n"
            
            # Show alternate names if available
            alt_names = []
            tr_name = channel.get("name_tr", "")
            en_name = channel.get("name_en", "")
            fa_name = channel.get("name_fa", "")
            
            if tr_name and tr_name != channel_name:
                alt_names.append(f"🇹🇷 {tr_name}")
            if en_name and en_name != channel_name:
                alt_names.append(f"🇬🇧 {en_name}")
            
            if alt_names:
                message += "📋 <b>Diğer İsimler:</b>\n"
                message += "\n".join(alt_names) + "\n\n"
            
            await query.edit_message_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        else:
            await query.edit_message_text(
                text="❌ Kanal bilgisi bulunamadı.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Geri", callback_data="sport_tv_back_to_channels")]])
            )
    elif data == "sport_tv_back_to_channels":
        # Go back to all channels
        await show_sport_tv_menu(update, context)

async def handle_sport_tv_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages in sport_tv state"""
    text = update.message.text
    
    if text == "🔙 Geri":
        # Go back to main menu
        context.user_data["state"] = "main"
        from utils.keyboard_utils import get_main_menu_keyboard
        await update.message.reply_text("🏠 Ana menüye dönülüyor...", reply_markup=get_main_menu_keyboard())
    elif text == "Sport TV 📺":
        # Show all channels directly
        await show_sport_tv_menu(update, context)
    else:
        # Show help message
        await update.message.reply_text(
            "⚠️ Lütfen bir kanal seçin veya '🔙 Geri' tuşuna basarak ana menüye dönün.", 
            reply_markup=get_back_keyboard()
        ) 