import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackContext
from dotenv import load_dotenv
import requests

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "5975058740:AAEE7HBv0koieZUSk9Su8wFNAWK4W2-65tI")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://nonmucous-unescheatable-ngoc.ngrok-free.dev")
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")

async def start_command(update: Update, context: CallbackContext):
    """Handle /start command"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "📱 Open Post Navigator",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )]
    ])
    
    await update.message.reply_text(
        "Welcome to Post Navigator! 🚀\n\n"
        "Click the button below to browse channel posts organized by categories.\n\n"
        "Commands:\n"
        "/start - Show this message\n"
        "/post - Post navigation message to channel\n"
        "/help - Show help",
        reply_markup=keyboard
    )

async def post_command(update: Update, context: CallbackContext):
    """Handle /post command - post navigation message to channel"""
    try:
        await update.message.reply_text("📢 Posting navigation message to channel...")
        
        # Call FastAPI endpoint to post message
        response = requests.post(f"{FASTAPI_URL}/api/post-navigation")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                await update.message.reply_text(
                    f"✅ Navigation message posted to channel!\n"
                    f"Message ID: {result.get('message_id', 'N/A')}"
                )
            else:
                await update.message.reply_text(f"❌ Error: {result.get('message', 'Unknown error')}")
        else:
            await update.message.reply_text(f"❌ Server error: {response.status_code}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def help_command(update: Update, context: CallbackContext):
    """Handle /help command - SIMPLIFIED VERSION"""
    help_text = f"""
📚 Post Navigator Bot Help

Commands:
/start - Start the bot and open navigator
/post - Post navigation message to Telegram channel
/help - Show this help message

How to use:
1. Click /start to open the post navigator
2. Browse posts by categories
3. Use /post to share navigator in channel

Admin Panel: {WEBAPP_URL}/admin
"""
    await update.message.reply_text(help_text)

async def error_handler(update: Update, context: CallbackContext):
    """Log errors"""
    print(f"Update {update} caused error {context.error}")

def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("post", post_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    print("🤖 Bot is starting...")
    print("✅ Bot is now running! Commands available:")
    print("   /start - Open navigator")
    print("   /post - Post to channel")
    print("   /help - Show help")
    
    # Start polling
    application.run_polling()

if __name__ == "__main__":
    main()