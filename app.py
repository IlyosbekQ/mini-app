import os
import json
from typing import Dict, List
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles  # <-- Добавьте эту строку
from telegram import Bot
from pydantic import BaseModel
from dotenv import load_dotenv
import time

# ===== LOAD .ENV FILE =====
# Ищем .env файл в корневой папке проекта
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print(f"✅ .env файл загружен из: {env_path}")
else:
    print(f"⚠️  .env файл не найден по пути: {env_path}")
    print("⚠️  Пробуем загрузить из текущей директории...")
    load_dotenv()

# ===== CONFIGURATION FROM ENVIRONMENT =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
WEBAPP_URL = os.getenv("WEBAPP_URL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
ALLOWED_ADMIN_IDS_STR = os.getenv("ALLOWED_ADMIN_IDS", "959805916")

# Parse admin IDs from comma-separated string
ALLOWED_ADMIN_IDS = [int(id.strip()) for id in ALLOWED_ADMIN_IDS_STR.split(",")]

# Security settings
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
LOCKOUT_TIME = int(os.getenv("LOCKOUT_TIME", "300"))  # 5 minutes

# ===== VALIDATION =====
print("\n" + "=" * 60)
print("🔍 ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ")
print("=" * 60)

if not BOT_TOKEN:
    print("❌ BOT_TOKEN не установлен!")
    print("   Установите в .env: BOT_TOKEN=ваш_токен")
    raise ValueError("BOT_TOKEN не установлен в переменных окружения!")
else:
    print(f"✅ BOT_TOKEN: {'*' * 20}{BOT_TOKEN[-10:]}")

if not ADMIN_PASSWORD:
    print("❌ ADMIN_PASSWORD не установлен!")
    print("   Установите в .env: ADMIN_PASSWORD=ваш_пароль")
    raise ValueError("ADMIN_PASSWORD не установлен в переменных окружения!")
else:
    print(f"✅ ADMIN_PASSWORD: {'*' * len(ADMIN_PASSWORD)}")

print(f"✅ WEBAPP_URL: {WEBAPP_URL or 'не установлен'}")
print(f"✅ CHANNEL_ID: {CHANNEL_ID or 'не установлен'}")
print(f"✅ ALLOWED_ADMIN_IDS: {ALLOWED_ADMIN_IDS}")
print("=" * 60 + "\n")

# ===== FASTAPI APP =====
app = FastAPI(
    title="Telegram Mini App Backend",
    version="2.0",
    description="Backend для навигации по постам Telegram канала"
)

# CORS middleware
# dev: allow anything; production: restrict
allow_origins = ["*"] if os.getenv("ENV", "dev") == "dev" else [WEBAPP_URL]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== ПОДКЛЮЧЕНИЕ СТАТИЧЕСКИХ ФАЙЛОВ =====
# Определяем путь к папке static относительно текущего файла
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"

# Проверяем существование папки static
if not STATIC_DIR.exists():
    print(f"⚠️  Папка static не найдена по пути: {STATIC_DIR}")
    print(f"📁 Текущая директория: {BASE_DIR}")
    print(f"📁 Создаю папку static...")
    STATIC_DIR.mkdir(exist_ok=True)

# Подключаем статические файлы
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ===== DATA MODELS =====
class Post(BaseModel):
    title: str
    url: str

class AuthRequest(BaseModel):
    password: str
    user_id: int

# ===== DATA STORAGE =====
# Путь к файлу данных - исправлен
DATA_FILE = BASE_DIR / "data" / "categories.json"

def load_categories() -> Dict:
    """Загрузить категории из файла"""
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️  Файл categories.json не найден, создаю дефолтные данные...")
        default_data = {
            "🎯 Ретриты и События": [
                {"title": "НОВИЧКУ", "url": "https://t.me/your_channel/1"},
                {"title": "ЗАКРЫТЫЙ КАНАЛ", "url": "https://t.me/your_channel/2"},
                {"title": "Расписание Ретритов", "url": "https://t.me/your_channel/3"}
            ],
            "📚 Духовные Практики": [
                {"title": "Что Такое Эго", "url": "https://t.me/your_channel/6"},
                {"title": "Смело Ошибайся", "url": "https://t.me/your_channel/7"}
            ],
            "💼 Услуги и Запись": [
                {"title": "Служба Заботы", "url": "https://t.me/your_channel/16"},
                {"title": "Запись на Гипнотерапию", "url": "https://t.me/your_channel/17"}
            ]
        }
        save_categories(default_data)
        return default_data

def save_categories(data: Dict):
    """Сохранить категории в файл"""
    # Создаем папку data если её нет
    # ensure parent directory exists
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Загружаем данные при старте
CATEGORIES_DATA = load_categories()

# ===== SECURITY =====
# Защита от брутфорса
failed_login_attempts = {}

def verify_admin(password: str, user_id: int) -> bool:
    """Проверка админских прав с защитой от брутфорса"""
    # Проверка блокировки
    if user_id in failed_login_attempts:
        attempts, last_attempt = failed_login_attempts[user_id]
        if attempts >= MAX_LOGIN_ATTEMPTS:
            time_passed = time.time() - last_attempt
            if time_passed < LOCKOUT_TIME:
                remaining = int(LOCKOUT_TIME - time_passed)
                print(f"🚫 User {user_id} заблокирован. Осталось: {remaining}с")
                return False
            else:
                # Сброс после истечения времени блокировки
                del failed_login_attempts[user_id]
                print(f"🔓 Блокировка user {user_id} снята")
    
    # Проверка пароля и ID
    is_valid = password == ADMIN_PASSWORD and user_id in ALLOWED_ADMIN_IDS
    
    if not is_valid:
        # Увеличение счетчика неудачных попыток
        if user_id in failed_login_attempts:
            attempts, _ = failed_login_attempts[user_id]
            failed_login_attempts[user_id] = (attempts + 1, time.time())
            print(f"⚠️  Неудачная попытка входа #{attempts + 1} для user {user_id}")
        else:
            failed_login_attempts[user_id] = (1, time.time())
            print(f"⚠️  Первая неудачная попытка входа для user {user_id}")
    else:
        # Сброс счетчика при успешной аутентификации
        if user_id in failed_login_attempts:
            del failed_login_attempts[user_id]
        print(f"✅ Успешная аутентификация user {user_id}")
    
    return is_valid

# ===== TELEGRAM BOT =====
try:
    bot = Bot(token=BOT_TOKEN)
    print("✅ Telegram Bot инициализирован")
except Exception as e:
    print(f"⚠️  Ошибка инициализации бота: {e}")
    bot = None

# ===== API ENDPOINTS =====

@app.get("/")
async def root():
    """Главная страница с информацией об API"""
    return {
        "app": "Telegram Mini App Backend",
        "version": "2.0",
        "status": "running",
        "endpoints": {
            "miniapp": "/miniapp",
            "admin": "/admin",
            "api_docs": "/docs",
            "categories": "/api/categories",
            "admin_api": "/api/admin/*",
            "static_files": "/static/{filename}"
        }
    }

@app.get("/miniapp", response_class=HTMLResponse)
async def serve_miniapp():
    """Главный интерфейс Mini App"""
    try:
        html_path = STATIC_DIR / "miniapp.html"
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        # Создаем дефолтный miniapp.html если его нет
        default_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Telegram Mini App</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body>
            <h1>Mini App работает!</h1>
            <p>Создайте файл miniapp.html в папке static</p>
        </body>
        </html>
        """
        return HTMLResponse(content=default_html)

@app.get("/admin", response_class=HTMLResponse)
async def serve_admin():
    """Админ-панель"""
    try:
        html_path = STATIC_DIR / "admin.html"
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        # Создаем дефолтный admin.html если его нет
        default_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin Panel</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body>
            <h1>Admin Panel работает!</h1>
            <p>Создайте файл admin.html в папке static</p>
        </body>
        </html>
        """
        return HTMLResponse(content=default_html)

# ===== ADMIN AUTHENTICATION =====

@app.post("/api/admin/auth")
async def admin_auth(auth: AuthRequest):
    """Аутентификация администратора"""
    if verify_admin(auth.password, auth.user_id):
        return {"status": "success", "message": "Authenticated"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

# ===== CATEGORIES API =====

@app.get("/api/categories")
async def get_categories():
    """Получить все категории"""
    return CATEGORIES_DATA

@app.post("/api/categories/add")
async def add_category(category: str, password: str, user_id: int):
    """Добавить новую категорию"""
    if not verify_admin(password, user_id):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if category in CATEGORIES_DATA:
        raise HTTPException(status_code=400, detail="Category already exists")
    
    CATEGORIES_DATA[category] = []
    save_categories(CATEGORIES_DATA)
    
    print(f"➕ Категория добавлена: {category}")
    return {"status": "success", "category": category}

@app.delete("/api/categories/{category}")
async def delete_category(category: str, password: str, user_id: int):
    """Удалить категорию"""
    if not verify_admin(password, user_id):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if category not in CATEGORIES_DATA:
        raise HTTPException(status_code=404, detail="Category not found")
    
    del CATEGORIES_DATA[category]
    save_categories(CATEGORIES_DATA)
    
    print(f"🗑️  Категория удалена: {category}")
    return {"status": "success"}

@app.put("/api/categories/{old_name}/rename")
async def rename_category(old_name: str, new_name: str, password: str, user_id: int):
    """Переименовать категорию"""
    if not verify_admin(password, user_id):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if old_name not in CATEGORIES_DATA:
        raise HTTPException(status_code=404, detail="Category not found")
    
    if new_name in CATEGORIES_DATA:
        raise HTTPException(status_code=400, detail="New name already exists")
    
    CATEGORIES_DATA[new_name] = CATEGORIES_DATA.pop(old_name)
    save_categories(CATEGORIES_DATA)
    
    print(f"✏️  Категория переименована: {old_name} → {new_name}")
    return {"status": "success"}

# ===== POSTS API =====

@app.post("/api/categories/{category}/posts")
async def add_post(category: str, post: Post, password: str, user_id: int):
    """Добавить пост в категорию"""
    if not verify_admin(password, user_id):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if category not in CATEGORIES_DATA:
        raise HTTPException(status_code=404, detail="Category not found")
    
    CATEGORIES_DATA[category].append(post.dict())
    save_categories(CATEGORIES_DATA)
    
    print(f"➕ Пост добавлен в '{category}': {post.title}")
    return {"status": "success", "post": post}

@app.put("/api/categories/{category}/posts/{post_index}")
async def update_post(category: str, post_index: int, post: Post, password: str, user_id: int):
    """Обновить пост"""
    if not verify_admin(password, user_id):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if category not in CATEGORIES_DATA:
        raise HTTPException(status_code=404, detail="Category not found")
    
    if post_index >= len(CATEGORIES_DATA[category]):
        raise HTTPException(status_code=404, detail="Post not found")
    
    CATEGORIES_DATA[category][post_index] = post.dict()
    save_categories(CATEGORIES_DATA)
    
    print(f"✏️  Пост обновлён в '{category}': {post.title}")
    return {"status": "success"}

@app.delete("/api/categories/{category}/posts/{post_index}")
async def delete_post(category: str, post_index: int, password: str, user_id: int):
    """Удалить пост"""
    if not verify_admin(password, user_id):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if category not in CATEGORIES_DATA:
        raise HTTPException(status_code=404, detail="Category not found")
    
    if post_index >= len(CATEGORIES_DATA[category]):
        raise HTTPException(status_code=404, detail="Post not found")
    
    deleted_post = CATEGORIES_DATA[category].pop(post_index)
    save_categories(CATEGORIES_DATA)
    
    print(f"🗑️  Пост удалён из '{category}': {deleted_post['title']}")
    return {"status": "success"}

# ===== HEALTH CHECK =====

@app.get("/api/health")
async def health_check():
    """Проверка работоспособности API"""
    return {
        "status": "healthy",
        "categories_count": len(CATEGORIES_DATA),
        "posts_count": sum(len(posts) for posts in CATEGORIES_DATA.values()),
        "bot_connected": bot is not None,
        "static_dir_exists": STATIC_DIR.exists(),
        "data_file_exists": DATA_FILE.exists()
    }

# ===== LOCAL DEVELOPMENT =====

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "=" * 60)
    print("🚀 FastAPI Server starting...")
    print("=" * 60)
    print(f"📄 Имя файла: {Path(__file__).name}")
    print(f"📁 Базовая директория: {BASE_DIR}")
    print(f"📁 Папка static: {STATIC_DIR}")
    print(f"📁 Папка static существует: {STATIC_DIR.exists()}")
    print(f"📁 Файлы в static: {list(STATIC_DIR.glob('*')) if STATIC_DIR.exists() else 'папка не существует'}")
    print(f"📁 Файл данных: {DATA_FILE}")
    print(f"📁 Файл данных существует: {DATA_FILE.exists()}")
    print(f"📱 Mini App: http://localhost:8000/miniapp")
    print(f"🔧 Admin Panel: http://localhost:8000/admin")
    print(f"📚 API Docs: http://localhost:8000/docs")
    print(f"🔑 Admin Password: {ADMIN_PASSWORD}")
    print("=" * 60 + "\n")
    

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
