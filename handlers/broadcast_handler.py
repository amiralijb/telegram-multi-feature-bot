import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from config import ADMIN_IDS
from database import get_all_users

async def init_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initialize the broadcast menu for admins"""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🚫 Bu bölüme erişim izniniz yok.")
        return
    
    keyboard = [
        [InlineKeyboardButton("Metin Gönder", callback_data="broadcast_text")],
        [InlineKeyboardButton("Fotoğraf Gönder", callback_data="broadcast_photo")],
        [InlineKeyboardButton("Dosya Gönder", callback_data="broadcast_document")],
        [InlineKeyboardButton("Video Gönder", callback_data="broadcast_video")],
        [InlineKeyboardButton("Ses Gönder", callback_data="broadcast_audio")],
        [InlineKeyboardButton("Geri", callback_data="broadcast_cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📢 *Toplu Mesaj Gönderimi*\n\n"
        "Bu bölümden tüm kullanıcılara mesaj, fotoğraf, dosya, video veya ses dosyası gönderebilirsiniz.\n"
        "Lütfen göndermek istediğiniz içerik türünü seçin:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle broadcast option selection callback"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await query.edit_message_text("🚫 Bu bölüme erişim izniniz yok.")
        return
    
    callback_data = query.data
    
    if callback_data == "broadcast_text":
        context.user_data["broadcast_type"] = "text"
        await query.edit_message_text(
            "✏️ Lütfen tüm kullanıcılara göndermek istediğiniz metni yazın:"
        )
    
    elif callback_data == "broadcast_photo":
        context.user_data["broadcast_type"] = "photo"
        await query.edit_message_text(
            "🖼️ Lütfen tüm kullanıcılara göndermek istediğiniz fotoğrafı açıklama (isteğe bağlı) ile birlikte gönderin:"
        )
    
    elif callback_data == "broadcast_document":
        context.user_data["broadcast_type"] = "document"
        await query.edit_message_text(
            "📎 Lütfen tüm kullanıcılara göndermek istediğiniz dosyayı açıklama (isteğe bağlı) ile birlikte gönderin:"
        )
    
    elif callback_data == "broadcast_video":
        context.user_data["broadcast_type"] = "video"
        await query.edit_message_text(
            "🎬 Lütfen tüm kullanıcılara göndermek istediğiniz videoyu açıklama (isteğe bağlı) ile birlikte gönderin:"
        )
    
    elif callback_data == "broadcast_audio":
        context.user_data["broadcast_type"] = "audio"
        await query.edit_message_text(
            "🎵 Lütfen tüm kullanıcılara göndermek istediğiniz ses dosyasını açıklama (isteğe bağlı) ile birlikte gönderin:"
        )
    
    elif callback_data == "broadcast_confirm":
        # Start the broadcast process
        await execute_broadcast(update, context)
    
    elif callback_data == "broadcast_cancel":
        # Clear broadcast data and go back
        context.user_data.pop("broadcast_type", None)
        context.user_data.pop("broadcast_content", None)
        context.user_data.pop("broadcast_caption", None)
        await query.edit_message_text("🔙 Toplu mesaj gönderimi iptal edildi.")

async def handle_broadcast_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the input for broadcast messages"""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return False
    
    broadcast_type = context.user_data.get("broadcast_type")
    if not broadcast_type:
        return False
    
    # Get the content based on the message type
    if broadcast_type == "text" and update.message.text:
        context.user_data["broadcast_content"] = update.message.text
        context.user_data["broadcast_caption"] = None
    
    elif broadcast_type == "photo" and update.message.photo:
        context.user_data["broadcast_content"] = update.message.photo[-1].file_id
        context.user_data["broadcast_caption"] = update.message.caption
    
    elif broadcast_type == "document" and update.message.document:
        context.user_data["broadcast_content"] = update.message.document.file_id
        context.user_data["broadcast_caption"] = update.message.caption
    
    elif broadcast_type == "video" and update.message.video:
        context.user_data["broadcast_content"] = update.message.video.file_id
        context.user_data["broadcast_caption"] = update.message.caption
    
    elif broadcast_type == "audio" and (update.message.audio or update.message.voice):
        if update.message.audio:
            context.user_data["broadcast_content"] = update.message.audio.file_id
        else:
            context.user_data["broadcast_content"] = update.message.voice.file_id
        context.user_data["broadcast_caption"] = update.message.caption
    
    else:
        await update.message.reply_text(
            f"❌ Gönderilen içerik türü istenen türle ({broadcast_type}) eşleşmiyor.\n"
            "Lütfen doğru içeriği tekrar gönderin veya /cancel komutu ile işlemi iptal edin."
        )
        return True
    
    # Show preview and confirmation buttons
    keyboard = [
        [InlineKeyboardButton("✅ Tüm Kullanıcılara Gönder", callback_data="broadcast_confirm")],
        [InlineKeyboardButton("❌ İptal", callback_data="broadcast_cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send preview message based on content type
    if broadcast_type == "text":
        message_content = context.user_data["broadcast_content"]
        
        await update.message.reply_text(
            f"📝 *Mesaj Önizlemesi*:\n\n"
            f"{message_content}\n\n"
            "Bu mesajı tüm kullanıcılara göndermek istediğinizden emin misiniz?",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    elif broadcast_type == "photo":
        file_id = context.user_data["broadcast_content"]
        caption = context.user_data["broadcast_caption"] or ""
        
        await update.message.reply_photo(
            photo=file_id,
            caption=f"📝 *Mesaj Önizlemesi*\nAçıklama: {caption}\n\nBu fotoğrafı tüm kullanıcılara göndermek istediğinizden emin misiniz?",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    elif broadcast_type == "document":
        file_id = context.user_data["broadcast_content"]
        caption = context.user_data["broadcast_caption"] or ""
        
        await update.message.reply_document(
            document=file_id,
            caption=f"📝 *Mesaj Önizlemesi*\nAçıklama: {caption}\n\nBu dosyayı tüm kullanıcılara göndermek istediğinizden emin misiniz?",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    elif broadcast_type == "video":
        file_id = context.user_data["broadcast_content"]
        caption = context.user_data["broadcast_caption"] or ""
        
        await update.message.reply_video(
            video=file_id,
            caption=f"📝 *Mesaj Önizlemesi*\nAçıklama: {caption}\n\nBu videoyu tüm kullanıcılara göndermek istediğinizden emin misiniz?",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    elif broadcast_type == "audio":
        file_id = context.user_data["broadcast_content"]
        caption = context.user_data["broadcast_caption"] or ""
        
        await update.message.reply_audio(
            audio=file_id,
            caption=f"📝 *Mesaj Önizlemesi*\nAçıklama: {caption}\n\nBu ses dosyasını tüm kullanıcılara göndermek istediğinizden emin misiniz?",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    return True

async def execute_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute the broadcast to all users"""
    query = update.callback_query
    
    broadcast_type = context.user_data.get("broadcast_type")
    broadcast_content = context.user_data.get("broadcast_content")
    broadcast_caption = context.user_data.get("broadcast_caption")
    
    if not broadcast_type or not broadcast_content:
        await query.edit_message_text("❌ Toplu mesaj bilgileri eksik. Lütfen tekrar deneyin.")
        context.user_data.pop("broadcast_type", None)
        context.user_data.pop("broadcast_content", None)
        context.user_data.pop("broadcast_caption", None)
        return
    
    # Get all users
    await query.edit_message_text("⏳ Kullanıcı listesi alınıyor...")
    users = get_all_users()
    total_users = len(users)
    
    if total_users == 0:
        await query.edit_message_text("❌ Veritabanında hiçbir kullanıcı bulunamadı!")
        return
    
    # Start broadcasting
    await query.edit_message_text(f"⏳ {total_users} kullanıcıya mesaj gönderiliyor...")
    
    success_count = 0
    failed_count = 0
    
    # Create a progress status message
    status_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"🔄 Gönderim durumu: 0/{total_users} (%0)"
    )
    
    for i, user in enumerate(users, 1):
        try:
            telegram_id = user[0]
            
            # Update status message every 5 users or for the last user
            if i % 5 == 0 or i == total_users:
                progress = (i / total_users) * 100
                await status_message.edit_text(
                    f"🔄 Gönderim durumu: {i}/{total_users} (%{progress:.1f})"
                )
            
            # Send the appropriate message type
            if broadcast_type == "text":
                await context.bot.send_message(
                    chat_id=telegram_id,
                    text=broadcast_content,
                    parse_mode="Markdown"
                )
            elif broadcast_type == "photo":
                await context.bot.send_photo(
                    chat_id=telegram_id,
                    photo=broadcast_content,
                    caption=broadcast_caption,
                    parse_mode="Markdown"
                )
            elif broadcast_type == "document":
                await context.bot.send_document(
                    chat_id=telegram_id,
                    document=broadcast_content,
                    caption=broadcast_caption,
                    parse_mode="Markdown"
                )
            elif broadcast_type == "video":
                await context.bot.send_video(
                    chat_id=telegram_id,
                    video=broadcast_content,
                    caption=broadcast_caption,
                    parse_mode="Markdown"
                )
            elif broadcast_type == "audio":
                await context.bot.send_audio(
                    chat_id=telegram_id,
                    audio=broadcast_content,
                    caption=broadcast_caption,
                    parse_mode="Markdown"
                )
            
            success_count += 1
        
        except Exception as e:
            logging.error(f"Error sending broadcast to user {telegram_id}: {e}")
            failed_count += 1
    
    # Show final report
    await status_message.edit_text(
        f"✅ Toplu mesaj gönderimi tamamlandı!\n\n"
        f"📊 Sonuç raporu:\n"
        f"👥 Toplam kullanıcı: {total_users}\n"
        f"✓ Başarılı gönderim: {success_count}\n"
        f"✗ Başarısız gönderim: {failed_count}\n"
    )
    
    # Clean up
    context.user_data.pop("broadcast_type", None)
    context.user_data.pop("broadcast_content", None)
    context.user_data.pop("broadcast_caption", None)

async def cancel_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the current broadcast operation"""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🚫 Bu bölüme erişim izniniz yok.")
        return
    
    if "broadcast_type" in context.user_data:
        context.user_data.pop("broadcast_type", None)
        context.user_data.pop("broadcast_content", None)
        context.user_data.pop("broadcast_caption", None)
        await update.message.reply_text("❌ Toplu mesaj gönderimi iptal edildi.")
    else:
        await update.message.reply_text("❓ Devam eden bir toplu mesaj gönderimi bulunmuyor.") 