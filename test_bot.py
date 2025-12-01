import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackContext
from dotenv import load_dotenv
import requests

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "5975058740:AAEE7HBv0koieZUSk9Su8wFNAWK4W2-65tI")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://mini-app-qh4y.vercel.app/")
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")

async def start_command(update: Update, context: CallbackContext):
    """Handle /start command"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text="📱 Open Post Navigator",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )],
        [InlineKeyboardButton(
            text="🔧 Admin Panel",
            url=f"{WEBAPP_URL}/admin"
        )]
    ])
    
    await update.message.reply_text(
        "👋 Добро пожаловать в Post Navigator! 🚀\n\n"
        "📚 Просматривайте посты канала по категориям\n"
        "🔧 Управляйте категориями через Админ Панель\n\n"
        "Команды:\n"
        "/start - Показать это сообщение\n"
        "/post - Отправить навигационное сообщение в канал\n"
        "/admin - Получить ссылку на админ панель\n"
        "/help - Показать помощь",
        reply_markup=keyboard
    )

async def post_command(update: Update, context: CallbackContext):
    """Handle /post command - post navigation message to channel"""
    try:
        await update.message.reply_text("📢 Отправляю навигационное сообщение в канал...")
        
        # Call FastAPI endpoint to post message
        response = requests.post(f"{FASTAPI_URL}/api/post-navigation")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                await update.message.reply_text(
                    f"✅ Навигационное сообщение отправлено в канал!\n"
                    f"ID сообщения: {result.get('message_id', 'N/A')}"
                )
            else:
                await update.message.reply_text(f"❌ Ошибка: {result.get('message', 'Неизвестная ошибка')}")
        else:
            await update.message.reply_text(f"❌ Ошибка сервера: {response.status_code}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def admin_command(update: Update, context: CallbackContext):
    """Handle /admin command"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text="🔧 Открыть Админ Панель",
            url=f"{WEBAPP_URL}/admin"
        )]
    ])
    
    await update.message.reply_text(
        "🔧 *Админ Панель*\n\n"
        "Управляйте категориями и постами:\n"
        "• Добавлять/Удалять категории\n"
        "• Добавлять/Редактировать/Удалять посты\n"
        "• Организовывать контент\n\n"
        "Нажмите кнопку ниже для доступа:\n"
        "🔑 Пароль: vvsh2024",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

async def help_command(update: Update, context: CallbackContext):
    """Handle /help command"""
    help_text = f"""
📚 *Post Navigator Bot Помощь*

🤖 *Команды:*
/start - Запустить бота и показать главное меню
/post - Отправить навигационное сообщение в канал
/admin - Открыть админ панель
/help - Показать это сообщение

📱 *Функции:*
• Просмотр постов по категориям в Mini App
• Админ панель для управления контентом
• Удобный интерфейс навигации

🔗 *Ссылки:*
• Mini App: {WEBAPP_URL}
• Admin Panel: {WEBAPP_URL}/admin

🔑 *Админ доступ:*
• Пароль: vvsh2024
• Доступен только для авторизованных пользователей

💡 *Как использовать:*
1. Нажмите /start чтобы увидеть доступные опции
2. Используйте Mini App для просмотра постов
3. Используйте Админ Панель для управления категориями
4. Используйте /post чтобы поделиться навигатором в канале
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")

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
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    print("=" * 60)
    print("🤖 Post Navigator Bot Запускается...")
    print("=" * 60)
    print("✅ Бот запущен и работает!")
    print("")
    print("📱 Доступные Команды:")
    print("   /start - Открыть главное меню")
    print("   /post - Отправить в канал")
    print("   /admin - Открыть админ панель")
    print("   /help - Показать помощь")
    print("")
    print(f"🌐 Mini App URL: {WEBAPP_URL}")
    print(f"🔧 Admin Panel: {WEBAPP_URL}/admin")
    print(f"🔑 Admin Password: vvsh2024")
    print("=" * 60)
    
    # Start polling
    application.run_polling()

if __name__ == "__main__":
    main()
