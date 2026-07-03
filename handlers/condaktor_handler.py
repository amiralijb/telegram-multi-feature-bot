import logging
import asyncio
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from utils.condaktor_utils import (
    get_condaktor_links_by_cat,
    get_condaktor_menu_keyboard,
    get_condaktor_category_keyboard,
    get_live_stream_buttons
)
from utils.keyboard_utils import get_back_keyboard
from utils.supabase_utils import get_channels_from_supabase, get_channel_by_id
from config import SUPABASE_URL, SUPABASE_KEY

async def get_condaktor_from_database():
    """
    Fetch condaktor information from the database instead of web scraping
    Returns a list of information text
    """
    try:
        # Get all channels from database
        channels = get_channels_from_supabase()
        
        if not channels or len(channels) == 0:
            logging.warning("No channels found in database, returning default info")
            return get_default_condaktor_info()
        
        # Create info list
        info = []
        
        # Add title
        info.append("🌐 <b>TV Rehberi</b>")
        
        # Group channels by category
        categories = {}
        for channel in channels:
            category = channel.get("category", "Genel")
            if category not in categories:
                categories[category] = []
            categories[category].append(channel)
        
        # Add channels by category
        for category, category_channels in categories.items():
            info.append(f"\n<b>📡 {category}:</b>")
            for channel in category_channels[:5]:  # Limit to 5 channels per category
                name = channel.get("name", "İsimsiz")
                info.append(f"📺 {name}")
        
        # Add extra info
        info.append("\n<b>ℹ️ Bilgi:</b>")
        info.append("✅ Tüm kanallar ücretsiz olarak sunulmuştur.")
        info.append("🔄 Yayın donması durumunda sayfayı yenileyiniz.")
        info.append("📱 Mobil cihazda, tam ekran modunu kullanabilirsiniz.")
        
        return info
        
    except Exception as e:
        logging.error(f"Error fetching Condaktor info from database: {e}")
        return get_default_condaktor_info()

def get_default_condaktor_info():
    """Return default Condaktor info when database fails"""
    return [
        "🌐 <b>TV Rehberi</b>",
        "\n<b>📡 Spor Kanalları:</b>",
        "📺 BeIN Sports 1",
        "📺 BeIN Sports 2",
        "📺 BeIN Sports 3",
        "📺 TRT Spor",
        "📺 S Sport",
        "\n<b>📡 Genel Kanallar:</b>",
        "📺 TRT 1",
        "📺 TRT 2",
        "📺 Fox TV",
        "\n<b>ℹ️ Bilgi:</b>",
        "✅ Tüm kanallar ücretsiz olarak sunulmuştur.",
        "🔄 Yayın donması durumunda sayfayı yenileyiniz.",
        "📱 Mobil cihazda, tam ekran modunu kullanabilirsiniz."
    ]

async def get_todays_matches_from_database():
    """Get today's matches information from database"""
    try:
        # Get sports channels with category "Football" or "Soccer"
        channels = get_channels_from_supabase()
        football_channels = [ch for ch in channels if ch.get("category", "").lower() in ["football", "soccer", "futbol"]]
        
        if not football_channels or len(football_channels) == 0:
            return None
        
        # Format the information - don't show channel IDs
        matches_info = "<b>📅 BUGÜNKÜ MAÇLAR</b>\n\n"
        
        # Get today's date for comparison
        import datetime
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        today_matches = []
        
        # Filter channels to only include today's matches if possible
        for channel in football_channels:
            match_date = channel.get("match_date", None) or channel.get("date", None)
            if match_date and match_date >= today:
                today_matches.append(channel)
        
        # If we don't have specific today's matches, use all football channels
        if not today_matches:
            today_matches = football_channels
        
        for i, channel in enumerate(today_matches[:5]):  # Limit to first 5 channels
            name = channel.get("name", "İsimsiz")
            description = channel.get("description", "Açıklama Yok")
            time = channel.get("time", "")
            
            # Show time if available, otherwise just display name and description
            if time:
                matches_info += f"• <b>{time}</b> - {description}\n\n"
            else:
                matches_info += f"• <b>{name}</b>: {description}\n\n"
            
        return matches_info
    except Exception as e:
        logging.error(f"Error fetching today's matches from database: {e}")
        return None

async def get_live_channels_from_database():
    """Get current live channels information from database"""
    try:
        # Get all channels
        channels = get_channels_from_supabase()
        
        if not channels or len(channels) == 0:
            return None
            
        # Import datetime for filtering
        import datetime
        current_time = datetime.datetime.now()
        current_hour = current_time.hour
        current_date = current_time.strftime("%Y-%m-%d")
        
        # Filter channels to show only current/upcoming ones
        current_channels = []
        for channel in channels:
            # Check if there's a date field
            channel_date = channel.get("date", None) or channel.get("match_date", None)
            
            # Check if there's a time field
            channel_time = channel.get("time", "")
            channel_hour = -1
            if channel_time and ":" in channel_time:
                try:
                    channel_hour = int(channel_time.split(":")[0])
                except (ValueError, IndexError):
                    pass
            
            # Include channel if:
            # 1. It's for today or future and
            # 2. It doesn't have time info OR the time is current/upcoming (-1 hour buffer)
            if (not channel_date or channel_date >= current_date) and \
               (channel_hour == -1 or channel_hour >= current_hour - 1):
                current_channels.append(channel)
        
        # If we don't have specifically filtered channels, use all channels
        if not current_channels:
            current_channels = channels
            
        # Process channel information - don't show channel IDs
        channels_info = "<b>📺 CANLI KANALLAR</b>\n\n"
        
        for i, channel in enumerate(current_channels[:5]):  # Limit to first 5 channels
            name = channel.get("name", "İsimsiz")
            description = channel.get("description", "Açıklama Yok")
            time = channel.get("time", "")
            
            # Show time if available
            if time:
                channels_info += f"• <b>{time}</b> - <b>{name}</b>: {description}\n\n"
            else:
                channels_info += f"• <b>{name}</b>: {description}\n\n"
        
        return channels_info
    except Exception as e:
        logging.error(f"Error fetching live channels from database: {e}")
        return None

async def get_match_schedule_from_supabase():
    """
    Fetch match schedule directly from Supabase conductors table
    Returns formatted match schedule information
    """
    try:
        import datetime
        
        # Get current date for filtering
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        logging.info(f"Current date for filtering: {current_date}")
        
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        
        # Log the URL being used for debugging
        logging.info(f"Fetching from Supabase URL: {SUPABASE_URL}/rest/v1/conductors")
        
        # Fetch match schedule from conductors table - try to filter by date if available
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/conductors?select=*",
            headers=headers
        )
        
        # Log response status for debugging
        logging.info(f"Supabase response status: {response.status_code}")
        
        if response.status_code != 200:
            logging.error(f"Error response from Supabase: {response.text}")
            return await fetch_schedule_from_website()
        
        all_matches = response.json()
        logging.info(f"Retrieved {len(all_matches)} total matches from conductors table")
        
        # Filter matches by date if date field exists
        matches = []
        for match in all_matches:
            # Check if there's a date field to filter by
            match_date = match.get("date", None) or match.get("match_date", None)
            
            # If no date field or date is current/future, include the match
            if not match_date or match_date >= current_date:
                matches.append(match)
        
        logging.info(f"After date filtering: {len(matches)} current/upcoming matches")
        
        if not matches or len(matches) == 0:
            logging.warning("No current match schedule found in conductors table, fetching from website")
            return await fetch_schedule_from_website()
            
        # Format the information from conductors table
        schedule_info = "<b>📺 BUGÜNKÜ MAÇ PROGRAMI</b>\n\n"
        
        # Log the first match for debugging structure
        if matches:
            logging.info(f"Sample match data: {matches[0]}")
        
        for match in matches:
            # Get time with fallbacks
            time = None
            for field in ["time", "saat", "zaman"]:
                if field in match and match[field]:
                    time = match[field]
                    break
            
            # Get title with fallbacks
            title = None
            for field in ["title", "match", "mac", "description"]:
                if field in match and match[field]:
                    title = match[field]
                    break
            
            # Only add if we have the minimum information
            if time and title:
                # Don't show channel_id, only display time and title
                schedule_info += f"<b>{time}</b>\n{title}\n\n"
            
        return schedule_info
    except Exception as e:
        logging.error(f"Error fetching match schedule from Supabase conductors table: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return await fetch_schedule_from_website()

async def fetch_schedule_from_website():
    """Fetch schedule information directly from BetReward TV website"""
    try:
        url = "https://betrewardtv.live/"
        logging.info(f"Fetching schedule from website: {url}")
        
        response = requests.get(url, timeout=15)  # Add timeout
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        logging.info("Successfully parsed website HTML")
        
        # Extract match schedule information
        schedule_info = "<b>📺 BUGÜNKÜ MAÇ PROGRAMI</b>\n\n"
        
        # Try multiple selectors to find program data
        selectors = [
            '.program-item',
            '.text-sm.font-medium.text-white.break-words.mb-3',
            '.text-sm',
            '.text-white',
            '.match-item',
            '.kondüktör-item',
            'div.grid div',
            'div.mt-2 div'
        ]
        
        program_elements = []
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                logging.info(f"Found {len(elements)} elements with selector: {selector}")
                program_elements = elements
                break
        
        if program_elements:
            for element in program_elements[:15]:  # Limit to 15 items
                text = element.get_text().strip()
                if text and len(text) > 5:  # Make sure it's a proper text item
                    # Try multiple formats for match data
                    if '|' in text:
                        # Extract only time and match info, don't include channel ID
                        parts = text.split('|')
                        time = parts[0].strip()
                        match_info = parts[1].strip()
                        
                        # Remove any channel references if they exist
                        if 'channel' in match_info.lower() or 'kanal' in match_info.lower():
                            match_info = match_info.split(':', 1)[-1].strip()
                        
                        schedule_info += f"<b>{time}</b>\n{match_info}\n\n"
                    elif ':' in text and len(text) < 100:
                        # Try to parse time:match format
                        time_parts = text.split(':', 1)
                        if len(time_parts) >= 2:
                            hour = time_parts[0].strip()
                            rest = time_parts[1].strip()
                            
                            # Check if hour is numeric
                            if hour.isdigit() and len(hour) <= 2:
                                # Look for the first word break after the minutes
                                minutes_end = rest.find(' ')
                                if minutes_end > 0:
                                    minutes = rest[:minutes_end].strip()
                                    if minutes.isdigit() and len(minutes) <= 2:
                                        match_info = rest[minutes_end:].strip()
                                        # Don't include channel ID
                                        schedule_info += f"<b>{hour}:{minutes}</b>\n{match_info}\n\n"
                                        continue
                            
                        # If we couldn't parse it cleanly, just add the text
                        schedule_info += f"{text}\n\n"
                    else:
                        schedule_info += f"{text}\n\n"
        else:
            logging.warning("No program elements found on the website")
            schedule_info += "Programa bilgisi bulunamadı. Supabase üzerinden 'conductors' tablosunu kontrol ediniz.\n"
        
        return schedule_info
    except Exception as e:
        logging.error(f"Error fetching schedule from website: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return "<b>📺 BUGÜNKÜ MAÇ PROGRAMI</b>\n\nProgram bilgisi geçici olarak kullanılamıyor."

async def show_condaktor_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the Condaktor menu with information from database"""
    context.user_data["state"] = "condaktor"
    
    # Send loading message
    loading_message = await update.message.reply_text("⏳ Canlı TV bilgileri yükleniyor, lütfen bekleyin...")
    
    # Fetch match schedule directly from Supabase
    match_schedule = await get_match_schedule_from_supabase()
    
    # Get channels from database
    channels = get_channels_from_supabase()
    
    # Create keyboard with channel buttons
    buttons = []
    
    # Add channels from database if available (limit to 5)
    if channels and len(channels) > 0:
        for channel in channels[:5]:
            channel_id = channel.get("id")
            name = channel.get("name", "İsimsiz")
            stream_url = channel.get("stream_url", "")
            
            if stream_url:
                buttons.append([InlineKeyboardButton(f"📺 {name}", web_app={"url": stream_url})])
    else:
        # Fallback buttons if no channels in database
        buttons = [
            [InlineKeyboardButton("🔴 Canlı TV İzle", web_app={"url": "https://betrewardtv.live/"})],
            [InlineKeyboardButton("🔄 Alternatif Link", web_app={"url": "https://betrewardtv.live/"})]
        ]
    
    reply_markup = InlineKeyboardMarkup(buttons)
    
    # Delete loading message
    try:
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=loading_message.message_id
        )
    except Exception as e:
        logging.error(f"Error deleting loading message: {e}")
    
    # Send match schedule if available
    if match_schedule:
        await update.message.reply_text(
            match_schedule,
            parse_mode=ParseMode.HTML
        )
    else:
        # Fallback to database info if match schedule not available
        info_list = await get_condaktor_from_database()
        info_message = "\n".join(info_list)
        
        await update.message.reply_text(
            info_message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    
    # Send web app button (same as in show_canli_yayin_menu)
    web_app_button = InlineKeyboardMarkup([
        [InlineKeyboardButton("📺 CANLI YAYIN İZLE", web_app={"url": "https://betrewardtv.live/"})]
    ])
    
    await update.message.reply_text(
        "BetReward TV'yi açmak için aşağıdaki butona tıklayın:",
        reply_markup=web_app_button
    )
    
    # Send back button
    await update.message.reply_text(
        "Geri dönmek için '🔙 Geri' tuşuna basınız.",
        reply_markup=get_back_keyboard()
    )

async def condaktor_category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Condaktor category selection"""
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "condaktor_back":
        keyboard = get_condaktor_category_keyboard()
        await query.edit_message_text("Lütfen bir kategori seçin:", reply_markup=keyboard)
        return

    cat_id = data.split("_")[1]
    links = await asyncio.to_thread(get_condaktor_links_by_cat, cat_id)
    if links:
        buttons = [
            [InlineKeyboardButton(f"{description}", url=link)]
            for title, description, link in links
        ]
        buttons.append([InlineKeyboardButton("🔙 Geri", callback_data="condaktor_back")])
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_text("Mevcut linkler:", reply_markup=reply_markup)
    else:
        buttons = [[InlineKeyboardButton("🔙 Geri", callback_data="condaktor_back")]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_text("❌ Bilgiler bulunamadı.", reply_markup=reply_markup)

async def show_live_stream_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the live stream menu with separate columns from Supabase conductors table"""
    # Show loading message
    if not isinstance(update, CallbackQuery):
        loading_message = await update.message.reply_text("⏳ Bilgiler yükleniyor, lütfen bekleyin...")
    
    try:
        # Create header message
        message = "📺 <b>Canlı TV Menüsü</b>\n\n"
        
        # Get match data from Supabase
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        
        # Fetch from conductors table
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/conductors?select=*&limit=5",
            headers=headers
        )
        
        if response.status_code == 200:
            matches = response.json()
            
            # Display each match with separate columns
            if matches:
                for i, match in enumerate(matches[:5]):  # Limit to 5 matches
                    message += f"<b>🏆 Maç #{i+1}:</b>\n"
                    
                    # Display each column separately
                    for column, value in match.items():
                        if value and column != "id" and column != "created_at":
                            # Format each column appropriately
                            if column == "time":
                                message += f"⏰ <b>Saat:</b> {value}\n"
                            elif column == "title" or column == "match":
                                message += f"🏆 <b>Maç:</b> {value}\n"
                            elif column == "channel" or column == "kanal":
                                message += f"📺 <b>Kanal:</b> {value}\n"
                            elif column == "date" or column == "tarih":
                                message += f"📅 <b>Tarih:</b> {value}\n"
                            else:
                                message += f"📌 <b>{column.capitalize()}:</b> {value}\n"
                    
                    # Add a button for this match
                    message += f"<a href='https://betrewardtv.live/'>📺 Bu maçı izlemek için tıklayın</a>\n\n"
            else:
                message += "Maç bilgisi bulunamadı.\n\n"
        
        # Create buttons for BetReward TV
        keyboard = [
            [InlineKeyboardButton("📺 BetReward TV'de İzle", web_app={"url": "https://betrewardtv.live/"})],
            [InlineKeyboardButton("📊 Canlı Skorlar", web_app={"url": "https://betrewardtv.live/#skorlar"})],
            [InlineKeyboardButton("🔙 Geri", callback_data="back_to_main")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Delete loading message if it exists
        if not isinstance(update, CallbackQuery) and 'loading_message' in locals():
            try:
                await context.bot.delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=loading_message.message_id
                )
            except Exception as e:
                logging.error(f"Error deleting loading message: {e}")
        
        # Send the message
        if isinstance(update, CallbackQuery):
            await update.message.edit_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
    except Exception as e:
        logging.error(f"Error in show_live_stream_menu: {e}")
        import traceback
        logging.error(traceback.format_exc())
        
        # Create fallback message
        message = "📺 <b>Canlı TV Menüsü</b>\n\n"
        message += "Bilgiler yüklenirken bir hata oluştu. Lütfen daha sonra tekrar deneyin.\n\n"
        
        keyboard = [
            [InlineKeyboardButton("📺 BetReward TV'de İzle", web_app={"url": "https://betrewardtv.live/"})],
            [InlineKeyboardButton("🔙 Geri", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if isinstance(update, CallbackQuery):
            await update.message.edit_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )

async def show_canli_yayin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show a simple web app button that opens BetReward TV directly
    """
    context.user_data["state"] = "canli_yayin"
    
    # Create a single button that opens the website as a web app
    button = InlineKeyboardMarkup([
        [InlineKeyboardButton("📺 CANLI YAYIN İZLE", web_app={"url": "https://betrewardtv.live/"})]
    ])
    
    # Send the button
    await update.message.reply_text(
        "BetReward TV'yi açmak için aşağıdaki butona tıklayın:",
        reply_markup=button
    )
    
    # Send back button
    await update.message.reply_text(
        "Geri dönmek için '🔙 Geri' tuşuna basınız.",
        reply_markup=get_back_keyboard()
    )

async def handle_konduktor_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle kondüktör button callback showing each column separately"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "show_konduktor":
        # Show loading message
        await query.edit_message_text("⏳ Kondüktör bilgileri yükleniyor...", parse_mode="HTML")
        
        try:
            # Get match data directly from Supabase
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json"
            }
            
            # Fetch from conductors table
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/conductors?select=*&limit=10",
                headers=headers
            )
            
            # Update header message
            await query.edit_message_text(
                "📺 <b>BUGÜNKÜ MAÇ PROGRAMI</b>\n\n",
                parse_mode="HTML"
            )
            
            if response.status_code == 200:
                matches = response.json()
                
                # Fields to exclude from display
                excluded_fields = ['id', 'created_at', 'updated_at', 'channel_id', 'duration', 'channel_id']
                
                if matches:
                    # Display each match as separate message
                    for i, match in enumerate(matches[:10]):  # Limit to 10 matches
                        # Prepare match message
                        match_message = f"<b>🏆 Maç #{i+1}:</b>\n"
                        
                        # Convert time to Turkish format if needed
                        time_value = None
                        for time_field in ["time", "saat", "zaman"]:
                            if time_field in match and match[time_field]:
                                time_value = match[time_field]
                                # Convert time to Turkish format if in HH:MM format
                                if ":" in time_value:
                                    try:
                                        hour, minute = time_value.split(":")
                                        time_value = f"{hour}.{minute}"
                                    except:
                                        pass
                                break
                        
                        # Add time information first with Turkish formatting
                        if time_value:
                            match_message += f"⏰ <b>Saat:</b> {time_value}\n"
                        
                        # Display each column separately - only show relevant fields in Turkish
                        for column, value in match.items():
                            if value and column.lower() not in excluded_fields and column.lower() not in ["time", "saat", "zaman"]:
                                # Format each column appropriately in Turkish
                                if column.lower() == "title" or column.lower() == "match" or column.lower() == "mac":
                                    match_message += f"🏆 <b>Maç:</b> {value}\n"
                                elif column.lower() == "channel" or column.lower() == "kanal":
                                    match_message += f"📺 <b>Kanal:</b> {value}\n"
                                elif column.lower() == "date" or column.lower() == "tarih":
                                    match_message += f"📅 <b>Tarih:</b> {value}\n"
                                elif column.lower() == "league" or column.lower() == "lig":
                                    match_message += f"🏆 <b>Lig:</b> {value}\n"
                                elif column.lower() == "stadium" or column.lower() == "stadyum":
                                    match_message += f"🏟️ <b>Stadyum:</b> {value}\n"
                                elif column.lower() == "score" or column.lower() == "skor":
                                    match_message += f"⚽ <b>Skor:</b> {value}\n"
                                elif column.lower() == "status" or column.lower() == "durum":
                                    match_message += f"📊 <b>Durum:</b> {value}\n"
                        
                        # Add watch button
                        keyboard = [[InlineKeyboardButton("📺 İzle", web_app={"url": "https://betrewardtv.live/"})]]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        
                        # Send each match as separate message
                        await query.message.reply_text(
                            text=match_message,
                            reply_markup=reply_markup,
                            parse_mode="HTML"
                        )
                else:
                    await query.message.reply_text(
                        "Maç bilgisi bulunamadı.",
                        parse_mode="HTML"
                    )
            
            # Send back button as separate message
            await query.message.reply_text(
                "Geri dönmek için:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 GERİ DÖN", callback_data="back_to_canli_yayin")]
                ])
            )
            
        except Exception as e:
            logging.error(f"Error in handle_konduktor_callback: {e}")
            import traceback
            logging.error(traceback.format_exc())
            
            # Fallback message and buttons
            await query.edit_message_text(
                "❌ Kondüktör bilgileri alınırken bir hata oluştu.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📺 BetReward TV'de İzle", web_app={"url": "https://betrewardtv.live/"})],
                    [InlineKeyboardButton("🔙 GERİ DÖN", callback_data="back_to_canli_yayin")]
                ]),
                parse_mode="HTML"
            )
    
    elif query.data == "back_to_canli_yayin":
        # Go back to main live stream menu with fresh data
        await show_live_stream_menu(update, context)

async def show_canli_tv_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the Canlı TV 🛜 menu with separate columns from Supabase conductors table"""
    # Show loading message
    if not isinstance(update, CallbackQuery):
        loading_message = await update.message.reply_text("⏳ Bilgiler yükleniyor, lütfen bekleyin...")
    
    try:
        # Get match data from Supabase
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        
        # Fetch from conductors table
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/conductors?select=*&limit=5",
            headers=headers
        )
        
        # Delete loading message if it exists
        if not isinstance(update, CallbackQuery) and 'loading_message' in locals():
            try:
                await context.bot.delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=loading_message.message_id
                )
            except Exception as e:
                logging.error(f"Error deleting loading message: {e}")
        
        # Send header message
        if isinstance(update, CallbackQuery):
            await update.message.edit_text(
                text="📺 <b>Canlı TV 🛜 Menüsü</b>\n\n",
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                text="📺 <b>Canlı TV 🛜 Menüsü</b>\n\n",
                parse_mode="HTML"
            )
        
        if response.status_code == 200:
            matches = response.json()
            
            # Fields to exclude from display
            excluded_fields = ['id', 'created_at', 'updated_at', 'channel_id', 'duration', 'channel_id']
            
            # Display each match as separate message
            if matches:
                for i, match in enumerate(matches[:5]):  # Limit to 5 matches
                    # Prepare match message
                    match_message = f"<b>🏆 Maç #{i+1}:</b>\n"
                    
                    # Convert time to Turkish format if needed
                    time_value = None
                    for time_field in ["time", "saat", "zaman"]:
                        if time_field in match and match[time_field]:
                            time_value = match[time_field]
                            # Convert time to Turkish format if in HH:MM format
                            if ":" in time_value:
                                try:
                                    hour, minute = time_value.split(":")
                                    time_value = f"{hour}.{minute}"
                                except:
                                    pass
                            break
                    
                    # Add time information first with Turkish formatting
                    if time_value:
                        match_message += f"⏰ <b>Saat:</b> {time_value}\n"
                    
                    # Display each column separately - only show relevant fields in Turkish
                    for column, value in match.items():
                        if value and column.lower() not in excluded_fields and column.lower() not in ["time", "saat", "zaman"]:
                            # Format each column appropriately in Turkish
                            if column.lower() == "title" or column.lower() == "match" or column.lower() == "mac":
                                match_message += f"🏆 <b>Maç:</b> {value}\n"
                            elif column.lower() == "channel" or column.lower() == "kanal":
                                match_message += f"📺 <b>Kanal:</b> {value}\n"
                            elif column.lower() == "date" or column.lower() == "tarih":
                                match_message += f"📅 <b>Tarih:</b> {value}\n"
                            elif column.lower() == "league" or column.lower() == "lig":
                                match_message += f"🏆 <b>Lig:</b> {value}\n"
                            elif column.lower() == "stadium" or column.lower() == "stadyum":
                                match_message += f"🏟️ <b>Stadyum:</b> {value}\n"
                            elif column.lower() == "score" or column.lower() == "skor":
                                match_message += f"⚽ <b>Skor:</b> {value}\n"
                            elif column.lower() == "status" or column.lower() == "durum":
                                match_message += f"📊 <b>Durum:</b> {value}\n"
                    
                    # Add a link for this match
                    match_message += f"<a href='https://betrewardtv.live/'>📺 Bu maçı izlemek için tıklayın</a>"
                    
                    # Add button to watch on BetReward TV
                    keyboard = [[InlineKeyboardButton("📺 İzle", web_app={"url": "https://betrewardtv.live/"})]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    # Send each match as separate message
                    if isinstance(update, CallbackQuery):
                        await update.effective_message.reply_text(
                            text=match_message,
                            reply_markup=reply_markup,
                            parse_mode="HTML"
                        )
                    else:
                        await update.message.reply_text(
                            text=match_message,
                            reply_markup=reply_markup,
                            parse_mode="HTML"
                        )
            else:
                # If no matches found
                if isinstance(update, CallbackQuery):
                    await update.effective_message.reply_text(
                        "Maç bilgisi bulunamadı.\n\n",
                        parse_mode="HTML"
                    )
                else:
                    await update.message.reply_text(
                        "Maç bilgisi bulunamadı.\n\n",
                        parse_mode="HTML"
                    )
        
        # Create back button in a separate message
        keyboard = [[InlineKeyboardButton("🔙 Geri", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if isinstance(update, CallbackQuery):
            await update.effective_message.reply_text(
                text="Ana menüye dönmek için:",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                text="Ana menüye dönmek için:",
                reply_markup=reply_markup
            )
            
    except Exception as e:
        logging.error(f"Error in show_canli_tv_menu: {e}")
        import traceback
        logging.error(traceback.format_exc())
        
        # Create fallback message
        message = "📺 <b>Canlı TV 🛜 Menüsü</b>\n\n"
        message += "Bilgiler yüklenirken bir hata oluştu. Lütfen daha sonra tekrar deneyin.\n\n"
        
        keyboard = [
            [InlineKeyboardButton("📺 BetReward TV'de İzle", web_app={"url": "https://betrewardtv.live/"})],
            [InlineKeyboardButton("🔙 Geri", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if isinstance(update, CallbackQuery):
            await update.message.edit_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode="HTML"
            ) 