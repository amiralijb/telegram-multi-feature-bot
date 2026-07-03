import logging
import httpx
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler
)
from telegram.request import _httpxrequest
from google_trans_new import google_translator

# Fix for httpx proxy handling
def patched_build_client(self):
    kwargs = self._client_kwargs.copy()
    # Remove both 'proxy' and 'proxies' if they exist
    if "proxy" in kwargs:
        kwargs.pop("proxy")
    if "proxies" in kwargs:
        kwargs.pop("proxies")
    return httpx.AsyncClient(**kwargs)
_httpxrequest.HTTPXRequest._build_client = patched_build_client

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Initialize translator
translator = google_translator()

# Import our modules
from config import TOKEN
from database import create_table
from handlers.start_handler import start
from handlers.admin_handler import (
    admin_panel, 
    admin_callback_handler,
    export_users,
    add_admin,
    remove_admin,
    set_api_keys,
    set_welcome_message,
    show_welcome_message,
    channels_list,
    set_pagination,
    set_referral_amount,
    edit_code,
    show_detailed_admin_stats
)
from handlers.broadcast_handler import (
    init_broadcast,
    handle_broadcast_callback,
    cancel_broadcast
)
from handlers.message_handler import handle_message
from handlers.wallet_handler import handle_wallet_callback
from handlers.condaktor_handler import condaktor_category_handler
from handlers.sport_tv_handler import handle_channel_selection

def main():
    """Initialize and run the bot"""
    # Create database tables if they don't exist
    create_table()
    
    # Initialize the application with our token
    app = Application.builder().token(TOKEN).build()
    
    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("broadcast", init_broadcast))
    app.add_handler(CommandHandler("cancel", cancel_broadcast))
    app.add_handler(CommandHandler("exportusers", export_users))
    app.add_handler(CommandHandler("manageadmins", channels_list))
    app.add_handler(CommandHandler("addadmin", add_admin))
    app.add_handler(CommandHandler("removeadmin", remove_admin))
    app.add_handler(CommandHandler("botstats", show_detailed_admin_stats))
    app.add_handler(CommandHandler("setapikeys", set_api_keys))
    app.add_handler(CommandHandler("setwelcome", set_welcome_message))
    app.add_handler(CommandHandler("showwelcome", show_welcome_message))
    app.add_handler(CommandHandler("channels", channels_list))
    app.add_handler(CommandHandler("setpagination", set_pagination))
    app.add_handler(CommandHandler("setreferral", set_referral_amount))
    app.add_handler(CommandHandler("editcode", edit_code))
    
    # Add message and callback handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_wallet_callback, pattern="^(withdraw|back_to_main)$"))
    app.add_handler(CallbackQueryHandler(condaktor_category_handler, pattern="^condaktor_|^main_menu$"))
    app.add_handler(CallbackQueryHandler(handle_channel_selection, pattern="^sport_tv_"))
    app.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^admin_"))
    app.add_handler(CallbackQueryHandler(handle_broadcast_callback, pattern="^broadcast_"))
    
    # Print a message to indicate that the bot is running
    print("🤖 Bot is running...")
    
    # Start the bot
    app.run_polling()

if __name__ == "__main__":
    main() 