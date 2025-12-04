import os
import signal
import sys
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, InputFile
from telegram.ext import Application, CommandHandler, CallbackContext
from dotenv import load_dotenv
import requests

# ===== LOAD .ENV FILE =====
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print(f"✅ .env файл загружен из: {env_path}")
else:
    print(f"⚠️  .env файл не найден по пути: {env_path}")
    print("⚠️  Пробуем загрузить из текущей директории...")
    load_dotenv()

# ===== CONFIGURATION FROM .ENV =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://mini-app-dfv1.vercel.app")
BACKEND_URL = os.getenv("BACKEND_URL", "https://mini-app-dfv1.vercel.app")
CHANNEL_ID = os.getenv("CHANNEL_ID")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "vvsh2024")
ALLOWED_ADMIN_IDS = [int(id.strip()) for id in os.getenv("ALLOWED_ADMIN_IDS", "959805916").split(",")]

# ===== VALIDATION =====
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не установлен в .env файле!")

print("\n" + "=" * 60)
print("🤖 Telegram Bot Configuration")
print("=" * 60)
print(f"✅ Bot Token: {'*' * 20}{BOT_TOKEN[-10:]}")
print(f"✅ WebApp URL: {WEBAPP_URL}")
print(f"✅ Backend URL: {BACKEND_URL}")
print(f"✅ Channel ID: {CHANNEL_ID}")
print(f"✅ Admin IDs: {ALLOWED_ADMIN_IDS}")
print("=" * 60 + "\n")

# ===== GLOBAL APPLICATION INSTANCE =====
app = None

# ===== COMMAND HANDLERS =====

async def start_command(update: Update, context: CallbackContext):
    """Handle /start command - главное меню"""
    try:
        user = update.effective_user
        user_id = user.id
        
        print(f"👤 Пользователь {user_id} ({user.first_name}) вызвал /start")
        
        # Проверяем, пришел ли пользователь из канала
        is_from_channel = False
        if context.args:
            print(f"📌 Аргументы команды: {context.args}")
            is_from_channel = context.args[0] == "channel"
        
        # Основная кнопка для всех пользователей
        keyboard = [[
            InlineKeyboardButton(
                text="📱 Открыть навигацию",
                web_app=WebAppInfo(url=f"{WEBAPP_URL}")
            )
        ]]
        
        # Добавляем кнопку админки только для админов
        if user_id in ALLOWED_ADMIN_IDS:
            keyboard.append([
                InlineKeyboardButton(
                    text="🔧 Open Admin Panel",
                    web_app=WebAppInfo(url=f"{WEBAPP_URL}/admin")
                )
            ])
        
        if is_from_channel:
            welcome_text = f"""
👋 *Добро пожаловать!*

Вы перешли из нашего канала! 🎉

📱 *Навигатор по постам* готов к использованию!

Нажмите кнопку *"Открыть навигацию"* ниже чтобы:
• 🔍 Найти нужный пост по категориям
• 📖 Читать материалы в удобном порядке
• 🎯 Быстро получить доступ ко всем ресурсам

👇 *Нажмите кнопку чтобы начать:*
"""
        else:
            welcome_text = f"""
👋 Привет, {user.first_name}!

Добро пожаловать в **Post Navigator Bot** 🚀

📚 *Что я умею:*
• Просмотр постов канала по категориям
• Удобная навигация через Mini App

👇 *Нажмите кнопку чтобы открыть навигатор:*
"""
        
        await update.message.reply_text(
            welcome_text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        print(f"✅ Ответ отправлен пользователю {user_id}")
        
    except Exception as e:
        print(f"❌ Ошибка в start_command: {e}")
        import traceback
        traceback.print_exc()

async def post_command(update: Update, context: CallbackContext):
    """Отправить пост с кнопкой в канал (только для админов) - ИСПРАВЛЕННЫЙ"""
    user_id = update.effective_user.id
    
    # Проверка прав доступа
    if user_id not in ALLOWED_ADMIN_IDS:
        await update.message.reply_text(
            "⛔ *Доступ запрещен!*\n\n"
            "Эта команда доступна только администраторам.",
            parse_mode="Markdown"
        )
        return
    
    # Проверяем, был ли это ответ на существующее сообщение с медиа
    is_reply_to_message = update.message.reply_to_message is not None
    
    # Инициализируем переменные
    photo_file = None
    message_text = None
    has_photo = False
    
    # Сценарий 1: Пользователь отправил фото с подписью (команда в подписи)
    if update.message.photo and len(update.message.photo) > 0:
        has_photo = True
        photo_file = update.message.photo[-1].file_id
        message_text = update.message.caption_html if update.message.caption_html else update.message.caption
        
        # Убираем команду /post из текста если она есть в начале
        if message_text and message_text.startswith('/post'):
            # Удаляем команду и лишние пробелы
            parts = message_text.split(' ', 1)
            message_text = parts[1] if len(parts) > 1 else ""
    
    # Сценарий 2: Пользователь ответил на сообщение с фото
    elif is_reply_to_message and update.message.reply_to_message.photo:
        has_photo = True
        reply_msg = update.message.reply_to_message
        photo_file = reply_msg.photo[-1].file_id
        
        # Текст может быть в оригинальном сообщении или в ответе
        if reply_msg.caption:
            message_text = reply_msg.caption_html if reply_msg.caption_html else reply_msg.caption
        elif update.message.text:
            # Берем текст из ответа (убираем команду)
            text_parts = update.message.text.split(' ', 1)
            message_text = text_parts[1] if len(parts) > 1 else ""
    
    # Сценарий 3: Только текст (команда с аргументами)
    elif update.message.text and context.args:
        message_text = " ".join(context.args)
    
    # Сценарий 4: Пользователь ответил на текстовое сообщение
    elif is_reply_to_message and update.message.reply_to_message.text:
        message_text = update.message.reply_to_message.text
    
    # Если ничего не найдено
    if not message_text and not has_photo:
        await update.message.reply_text(
            "📝 *Использование команды /post:*\n\n"
            "1️⃣ *Ответьте на сообщение:*\n"
            "   - Ответьте командой `/post` на фото или текст\n\n"
            "2️⃣ *Текст напрямую:*\n"
            "   - `/post Ваш текст поста`\n\n"
            "*Примеры:*\n"
            "• Ответьте `/post` на существующее сообщение\n"
            "• Напишите: `/post Текст вашего поста здесь`",
            parse_mode="Markdown"
        )
        return
    
    # Получаем username бота для ссылки
    bot_info = await context.bot.get_me()
    bot_link = f"https://t.me/{bot_info.username}?start=channel"
    
    # Кнопка для канала
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text="🚀 Открыть навигатор",
            url=bot_link
        )]
    ])
    
    try:
        # Очищаем текст от возможных проблемных символов для Markdown
        if message_text:
            # Экранируем проблемные символы для MarkdownV2
            safe_text = message_text
            # Убираем лишние пробелы в начале и конце
            safe_text = safe_text.strip()
        else:
            safe_text = ""
        
        # Формируем финальный текст поста
        if safe_text:
            post_text = f"{safe_text}\n\n👇 *Нажмите кнопку ниже чтобы открыть навигатор:*"
        else:
            post_text = "👇 *Нажмите кнопку ниже чтобы открыть навигатор:*"
        
        # Отправляем в канал
        if has_photo and photo_file:
            print(f"📸 Отправляю фото в канал {CHANNEL_ID}")
            print(f"📝 Текст: {safe_text[:100]}..." if safe_text else "📝 Без текста")
            
            # Пробуем отправить с Markdown, если будет ошибка - отправим без него
            try:
                sent_message = await context.bot.send_photo(
                    chat_id=CHANNEL_ID,
                    photo=photo_file,
                    caption=post_text,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
                print(f"✅ Фото отправлено успешно! ID сообщения: {sent_message.message_id}")
                
            except Exception as parse_error:
                print(f"⚠️ Ошибка парсинга Markdown: {parse_error}")
                # Пробуем без Markdown
                post_text_plain = f"{safe_text}\n\n👇 Нажмите кнопку ниже чтобы открыть навигатор:" if safe_text else "👇 Нажмите кнопку ниже чтобы открыть навигатор:"
                
                sent_message = await context.bot.send_photo(
                    chat_id=CHANNEL_ID,
                    photo=photo_file,
                    caption=post_text_plain,
                    reply_markup=keyboard
                )
                print(f"✅ Фото отправлено без Markdown форматирования")
        
        else:
            # Отправляем только текст
            print(f"📝 Отправляю текст в канал {CHANNEL_ID}")
            print(f"📝 Текст: {safe_text[:200]}...")
            
            try:
                sent_message = await context.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=post_text,
                    parse_mode="Markdown",
                    reply_markup=keyboard,
                    disable_web_page_preview=True
                )
                print(f"✅ Текст отправлен успешно! ID сообщения: {sent_message.message_id}")
                
            except Exception as parse_error:
                print(f"⚠️ Ошибка парсинга Markdown: {parse_error}")
                # Пробуем без Markdown
                post_text_plain = f"{safe_text}\n\n👇 Нажмите кнопку ниже чтобы открыть навигатор:" if safe_text else "👇 Нажмите кнопку ниже чтобы открыть навигатор:"
                
                sent_message = await context.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=post_text_plain,
                    reply_markup=keyboard,
                    disable_web_page_preview=True
                )
                print(f"✅ Текст отправлен без Markdown форматирования")
        
        # Отправляем подтверждение пользователю
        success_text = f"""
✅ *Пост успешно отправлен в канал!*

📊 *Детали:*
• Канал: `{CHANNEL_ID}`
• Тип: {'Фото с текстом' if has_photo else 'Текстовый пост'}
• ID сообщения: `{sent_message.message_id}`

🔗 *Ссылка для кнопки:*
`{bot_link}`

📱 *Пользователи смогут нажать кнопку "Открыть навигатор" для доступа к боту.*
"""
        
        await update.message.reply_text(
            success_text,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Критическая ошибка при отправке: {error_msg}")
        import traceback
        traceback.print_exc()
        
        error_response = f"""
❌ *Не удалось отправить пост*

*Ошибка:* `{error_msg[:100]}`

*Возможные причины:*
1. Бот не добавлен в канал как администратор
2. Неверный CHANNEL_ID в настройках
3. Проблемы с правами бота в канале
4. Слишком длинный текст или недопустимые символы

*Проверьте:*
• Бот добавлен в канал `{CHANNEL_ID}` как администратор
• CHANNEL_ID указан правильно в .env файле
"""
        
        await update.message.reply_text(
            error_response,
            parse_mode="Markdown"
        )
# Добавьте остальные обработчики команд (admin_command, status_command, help_command, etc.)
# ... [остальной код остается без изменений до main()] ...

async def admin_command(update: Update, context: CallbackContext):
    """Handle /admin command - админ-панель (только для админов)"""
    user_id = update.effective_user.id
    
    # Проверка прав доступа
    if user_id not in ALLOWED_ADMIN_IDS:
        await update.message.reply_text(
            "⛔ *Доступ запрещен!*\n\n"
            "Эта команда доступна только администраторам.",
            parse_mode="Markdown"
        )
        return
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text="🔧 Открыть Админ-панель",
            url=f"{WEBAPP_URL}/admin"
        )]
    ])
    
    admin_text = f"""
🔧 *Админ-панель*

*Управление контентом:*
• ➕ Добавление категорий
• ✏️ Редактирование категорий
• 🗑️ Удаление категорий
• 📝 Управление постами

🔑 *Данные для входа:*
• User ID: `{user_id}`
• Пароль: `{ADMIN_PASSWORD}`

⚠️ *Только для авторизованных администраторов!*
"""
    
    await update.message.reply_text(
        admin_text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )

async def status_command(update: Update, context: CallbackContext):
    """Handle /status command - статус системы"""
    await update.message.reply_text("🔍 Проверяю статус системы...")
    
    try:
        # Проверка Backend API
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            status_text = f"""
✅ *Система работает нормально*

📊 *Статистика:*
• Категорий: {data.get('categories_count', 'N/A')}
• Постов: {data.get('posts_count', 'N/A')}
• Backend: {'🟢 Онлайн' if data.get('status') == 'healthy' else '🔴 Проблемы'}
• Bot: {'🟢 Подключен' if data.get('bot_connected') else '🟡 Не подключен'}

🌐 *URLs:*
• Mini App: {WEBAPP_URL}
• API Docs: {BACKEND_URL}/docs
"""
            # Добавляем ссылку на админку только для админов
            if update.effective_user.id in ALLOWED_ADMIN_IDS:
                status_text += f"• Admin: {WEBAPP_URL}/admin\n"
                status_text += f"• Admin Password: `{ADMIN_PASSWORD}`\n"
            
            await update.message.reply_text(status_text, parse_mode="Markdown")
        else:
            await update.message.reply_text(
                f"⚠️ Backend API вернул ошибку: {response.status_code}\n"
                f"Проверьте что сервер запущен."
            )
    except requests.exceptions.RequestException as e:
        await update.message.reply_text(
            f"❌ Не удалось подключиться к Backend API\n\n"
            f"Ошибка: {str(e)}\n\n"
            f"Проверьте:\n"
            f"• Backend запущен на {BACKEND_URL}\n"
            f"• BACKEND_URL правильно настроен в .env"
        )

async def help_command(update: Update, context: CallbackContext):
    """Handle /help command - подробная помощь"""
    user_id = update.effective_user.id
    
    help_text = f"""
📚 *Post Navigator Bot - Помощь*

🤖 *Команды бота:*

/start - Главное меню
/miniapp - Открыть навигатор постов
/status - Проверить статус системы
/help - Показать это сообщение

📱 *Как пользоваться:*

1. Нажмите кнопку "Открыть навигацию"
2. Выберите нужную категорию
3. Кликните на пост чтобы открыть его в Telegram

🌐 *Ссылки:*
• Навигатор: {WEBAPP_URL}
"""
    
    # Добавляем админские команды только для админов
    if user_id in ALLOWED_ADMIN_IDS:
        help_text += f"""
        
🔧 *Админ-команды:*
/admin - Админ-панель
/post - Отправить пост в канал (текст или фото)
• Admin Panel: {WEBAPP_URL}/admin
• Пароль: `{ADMIN_PASSWORD}`
"""
    
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def error_handler(update: Update, context: CallbackContext):
    """Log and handle errors"""
    print(f"❌ Update {update} вызвал ошибку: {context.error}")
    import traceback
    traceback.print_exc()
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ Произошла ошибка при обработке команды.\n"
            "Попробуйте ещё раз или используйте /help для справки."
        )

# ===== MAIN FUNCTION (СИНХРОННЫЙ ВАРИАНТ) =====

def main():
    """Основная функция запуска - синхронная версия"""
    global app
    
    print("🚀 Инициализация бота...")
    
    # Создаём приложение
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики команд
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("post", post_command))
    app.add_handler(CommandHandler("help", help_command))
    
    # Добавляем обработчик ошибок
    app.add_error_handler(error_handler)
    
    # Запускаем приложение
    print("\n" + "=" * 60)
    print("🤖 Post Navigator Bot Запущен!")
    print("=" * 60)
    
    # Запускаем polling в фоновом режиме
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"\n\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
