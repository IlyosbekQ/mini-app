import os
import json
from typing import Dict, List
from fastapi import FastAPI, HTTPException, Depends, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from dotenv import load_dotenv
from pydantic import BaseModel
import secrets

load_dotenv()

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "5975058740:AAEE7HBv0koieZUSk9Su8wFNAWK4W2-65tI")
CHANNEL_ID = os.getenv("CHANNEL_ID", "-1002228131301")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://mini-app-qh4y.vercel.app/")

# Admin credentials
ADMIN_PASSWORD = "vvsh2024"
ALLOWED_ADMIN_IDS = [959805916]  

app = FastAPI(title="Telegram Mini App Backend")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class Post(BaseModel):
    title: str
    url: str

class AuthRequest(BaseModel):
    password: str
    user_id: int

# Load/Save categories with initial data
def load_categories():
    try:
        with open("categories.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "🎯 Ретриты и События": [
                {"title": "Расписание Ретритов", "url": "https://t.me/your_channel/1"},
                {"title": "Интервью прошедших Ретрит", "url": "https://t.me/your_channel/2"},
                {"title": "Записи прямых Эфиров", "url": "https://t.me/your_channel/3"}
            ],
            "📚 Духовные Практики": [
                {"title": "Что Такое Эго", "url": "https://t.me/your_channel/4"},
                {"title": "Смело Ошибайся", "url": "https://t.me/your_channel/5"},
                {"title": "Для Чего Я Провожу Ретриты", "url": "https://t.me/your_channel/6"},
                {"title": "Псилоцибиновый Vs Мухоморный", "url": "https://t.me/your_channel/7"},
                {"title": "Нетрипованный Трипованного", "url": "https://t.me/your_channel/8"}
            ],
            "🧘 Практики и Медитации": [
                {"title": "Буфо", "url": "https://t.me/your_channel/9"},
                {"title": "Сущности", "url": "https://t.me/your_channel/10"},
                {"title": "Церемония Камбо", "url": "https://t.me/your_channel/11"},
                {"title": "Илон Маск О Психоделиках", "url": "https://t.me/your_channel/12"}
            ],
            "💡 Личное Развитие": [
                {"title": "Научу Лутать 50к₽/мес", "url": "https://t.me/your_channel/13"},
                {"title": "Служба Заботы в Лице ВВШ", "url": "https://t.me/your_channel/14"},
                {"title": "Запись на Гипнотерапию", "url": "https://t.me/your_channel/15"},
                {"title": "Запись на Консультацию", "url": "https://t.me/your_channel/16"}
            ],
            "🌟 Важные Материалы": [
                {"title": "Отзывы", "url": "https://t.me/your_channel/17"},
                {"title": "Мой Инстаграм", "url": "https://t.me/your_channel/18"},
                {"title": "АВЕ, МАКАРОН!", "url": "https://t.me/your_channel/19"},
                {"title": "Важные Публикации", "url": "https://t.me/your_channel/20"}
            ],
            "🎮 Игры и Развлечения": [
                {"title": "Добрые Дела", "url": "https://t.me/your_channel/21"},
                {"title": "Новая Цивилизация", "url": "https://t.me/your_channel/22"},
                {"title": "Игры = Бег От Проблем", "url": "https://t.me/your_channel/23"}
            ],
            "👨 Мужское Развитие": [
                {"title": "Из Мальчика в Мужчину", "url": "https://t.me/your_channel/24"},
                {"title": "Зачем Нужны Единоборства", "url": "https://t.me/your_channel/25"},
                {"title": "Брось Пить и Курить", "url": "https://t.me/your_channel/26"},
                {"title": "Вызовы Необходимы", "url": "https://t.me/your_channel/27"}
            ],
            "📖 Книги и Знания": [
                {"title": "Золотая Коллекция Книг", "url": "https://t.me/your_channel/28"},
                {"title": "Внедри Граундинг", "url": "https://t.me/your_channel/29"},
                {"title": "Предназначение", "url": "https://t.me/your_channel/30"},
                {"title": "С Этим Миром что-то не так", "url": "https://t.me/your_channel/31"},
                {"title": "Сущности Не Плохие", "url": "https://t.me/your_channel/32"}
            ]
        }

def save_categories(data):
    with open("categories.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

CATEGORIES_DATA = load_categories()

# Initialize bot
bot = Bot(token=BOT_TOKEN)

# Admin authentication
def verify_admin(password: str, user_id: int):
    return password == ADMIN_PASSWORD and user_id in ALLOWED_ADMIN_IDS

# API Endpoints
@app.post("/api/admin/auth")
async def admin_auth(auth: AuthRequest):
    """Authenticate admin"""
    if verify_admin(auth.password, auth.user_id):
        return {"status": "success", "message": "Authenticated"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/api/categories")
async def get_categories():
    """Returns all categories and their posts"""
    return CATEGORIES_DATA

@app.post("/api/categories/add")
async def add_category(category: str, password: str, user_id: int):
    """Add a new category"""
    if not verify_admin(password, user_id):
        raise HTTPException(status_code=401, detail="Unauthorized")
    if category in CATEGORIES_DATA:
        raise HTTPException(status_code=400, detail="Category already exists")
    CATEGORIES_DATA[category] = []
    save_categories(CATEGORIES_DATA)
    return {"status": "success", "category": category}

@app.delete("/api/categories/{category}")
async def delete_category(category: str, password: str, user_id: int):
    """Delete a category"""
    if not verify_admin(password, user_id):
        raise HTTPException(status_code=401, detail="Unauthorized")
    if category not in CATEGORIES_DATA:
        raise HTTPException(status_code=404, detail="Category not found")
    del CATEGORIES_DATA[category]
    save_categories(CATEGORIES_DATA)
    return {"status": "success"}

@app.put("/api/categories/{old_name}/rename")
async def rename_category(old_name: str, new_name: str, password: str, user_id: int):
    """Rename a category"""
    if not verify_admin(password, user_id):
        raise HTTPException(status_code=401, detail="Unauthorized")
    if old_name not in CATEGORIES_DATA:
        raise HTTPException(status_code=404, detail="Category not found")
    if new_name in CATEGORIES_DATA:
        raise HTTPException(status_code=400, detail="New name already exists")
    CATEGORIES_DATA[new_name] = CATEGORIES_DATA.pop(old_name)
    save_categories(CATEGORIES_DATA)
    return {"status": "success"}

@app.post("/api/categories/{category}/posts")
async def add_post(category: str, post: Post, password: str, user_id: int):
    """Add a post to a category"""
    if not verify_admin(password, user_id):
        raise HTTPException(status_code=401, detail="Unauthorized")
    if category not in CATEGORIES_DATA:
        raise HTTPException(status_code=404, detail="Category not found")
    CATEGORIES_DATA[category].append(post.dict())
    save_categories(CATEGORIES_DATA)
    return {"status": "success", "post": post}

@app.put("/api/categories/{category}/posts/{post_index}")
async def update_post(category: str, post_index: int, post: Post, password: str, user_id: int):
    """Update a post"""
    if not verify_admin(password, user_id):
        raise HTTPException(status_code=401, detail="Unauthorized")
    if category not in CATEGORIES_DATA:
        raise HTTPException(status_code=404, detail="Category not found")
    if post_index >= len(CATEGORIES_DATA[category]):
        raise HTTPException(status_code=404, detail="Post not found")
    CATEGORIES_DATA[category][post_index] = post.dict()
    save_categories(CATEGORIES_DATA)
    return {"status": "success"}

@app.delete("/api/categories/{category}/posts/{post_index}")
async def delete_post(category: str, post_index: int, password: str, user_id: int):
    """Delete a post"""
    if not verify_admin(password, user_id):
        raise HTTPException(status_code=401, detail="Unauthorized")
    if category not in CATEGORIES_DATA:
        raise HTTPException(status_code=404, detail="Category not found")
    if post_index >= len(CATEGORIES_DATA[category]):
        raise HTTPException(status_code=404, detail="Post not found")
    CATEGORIES_DATA[category].pop(post_index)
    save_categories(CATEGORIES_DATA)
    return {"status": "success"}

@app.post("/api/post-navigation")
async def trigger_navigation_post():
    """Post navigation message to channel"""
    try:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                text="📱 Open Post Navigator",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )]
        ])
        
        message_text = (
            "📚 *Welcome to Post Navigator!*\n\n"
            "Browse all channel posts organized by categories.\n"
            "Tap the button below to get started! 👇"
        )
        
        message = await bot.send_message(
            chat_id=CHANNEL_ID,
            text=message_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
        return {
            "status": "success",
            "message_id": message.message_id
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
# Continuation of app.py - add this after the previous code

@app.get("/", response_class=HTMLResponse)
async def serve_miniapp():
    """Serve the Mini App HTML"""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Post Navigator</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 500px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }
        .header h1 { font-size: 24px; margin-bottom: 5px; }
        .header p { opacity: 0.9; font-size: 14px; }
        .content { padding: 20px; }
        .category-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-bottom: 20px;
        }
        .category-btn {
            padding: 15px 20px;
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            background: white;
            cursor: pointer;
            transition: all 0.3s;
            text-align: left;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .category-btn:hover { border-color: #667eea; background: #f5f7ff; }
        .category-btn.active {
            border-color: #667eea;
            background: #f5f7ff;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
        }
        .category-name { font-weight: 600; color: #333; font-size: 15px; }
        .category-count { font-size: 12px; color: #888; }
        .posts-section { display: none; margin-top: 20px; }
        .posts-section.visible { display: block; }
        .section-title {
            font-size: 14px;
            font-weight: 600;
            color: #666;
            margin-bottom: 10px;
        }
        .post-list {
            background: #f8f9fa;
            border-radius: 12px;
            overflow: hidden;
        }
        .post-item {
            padding: 15px;
            border-bottom: 1px solid #e0e0e0;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.2s;
        }
        .post-item:last-child { border-bottom: none; }
        .post-item:hover { background: #e9ecef; }
        .post-title { font-weight: 500; color: #333; font-size: 14px; }
        .post-arrow { color: #667eea; }
        .info-box {
            background: #f0f4ff;
            border: 1px solid #d0dcff;
            border-radius: 12px;
            padding: 15px;
            text-align: center;
            color: #667eea;
            font-size: 14px;
        }
        .loading { text-align: center; padding: 40px 20px; }
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 Post Navigator</h1>
            <p>Browse channel posts by category</p>
        </div>
        <div class="content">
            <div id="loading" class="loading">
                <div class="spinner"></div>
                <p>Loading categories...</p>
            </div>
            <div id="app" style="display: none;">
                <div class="category-list" id="categoryList"></div>
                <div id="postsSection" class="posts-section">
                    <div class="section-title">Посты:</div>
                    <div class="post-list" id="postList"></div>
                </div>
                <div id="infoBox" class="info-box">
                    👆 Выберите категорию для просмотра постов
                </div>
            </div>
        </div>
    </div>
    <script>
        let tg = window.Telegram.WebApp;
        let categories = {};
        let selectedCategory = null;
        
        tg.ready();
        tg.expand();
        
        async function loadCategories() {
            try {
                const response = await fetch('/api/categories');
                categories = await response.json();
                renderCategories();
                document.getElementById('loading').style.display = 'none';
                document.getElementById('app').style.display = 'block';
            } catch (error) {
                console.error('Error loading categories:', error);
                alert('Failed to load categories');
            }
        }
        
        function renderCategories() {
            const list = document.getElementById('categoryList');
            list.innerHTML = '';
            
            Object.keys(categories).forEach(category => {
                const btn = document.createElement('button');
                btn.className = 'category-btn';
                btn.innerHTML = `
                    <div class="category-name">${category}</div>
                    <div class="category-count">${categories[category].length} постов</div>
                `;
                btn.onclick = () => selectCategory(category, btn);
                list.appendChild(btn);
            });
        }
        
        function selectCategory(category, btnElement) {
            selectedCategory = category;
            document.querySelectorAll('.category-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            btnElement.classList.add('active');
            renderPosts(category);
            document.getElementById('postsSection').classList.add('visible');
            document.getElementById('infoBox').style.display = 'none';
        }
        
        function renderPosts(category) {
            const postList = document.getElementById('postList');
            postList.innerHTML = '';
            
            categories[category].forEach(post => {
                const item = document.createElement('div');
                item.className = 'post-item';
                item.innerHTML = `
                    <div class="post-title">${post.title}</div>
                    <div class="post-arrow">→</div>
                `;
                item.onclick = () => openPost(post);
                postList.appendChild(item);
            });
        }
        
        function openPost(post) {
            tg.openTelegramLink(post.url);
            setTimeout(() => {
                tg.close();
            }, 100);
        }
        
        loadCategories();
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

@app.get("/admin", response_class=HTMLResponse)
async def serve_admin():
    """Serve Admin Panel with Authentication"""
    admin_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Panel - Post Navigator</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            min-height: 100vh;
            padding: 20px;
        }
        .login-container {
            max-width: 400px;
            margin: 100px auto;
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .login-title {
            font-size: 24px;
            font-weight: 600;
            text-align: center;
            margin-bottom: 30px;
            color: #333;
        }
        .input-group {
            margin-bottom: 20px;
        }
        .input-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: #555;
        }
        .input-group input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
        }
        .input-group input:focus {
            outline: none;
            border-color: #667eea;
        }
        .btn {
            width: 100%;
            padding: 12px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.3s;
            font-size: 14px;
        }
        .btn-primary {
            background: #667eea;
            color: white;
        }
        .btn-primary:hover { background: #5568d3; }
        .alert {
            padding: 12px 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: none;
        }
        .alert.error {
            background: #fed7d7;
            color: #742a2a;
            border: 1px solid #fc8181;
        }
        .alert.active { display: block; }
        .container { display: none; max-width: 1200px; margin: 0 auto; }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        }
        .header h1 { font-size: 28px; margin-bottom: 5px; }
        .section {
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        }
        .section-title {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 20px;
            color: #333;
        }
        .btn-success { background: #48bb78; color: white; }
        .btn-success:hover { background: #38a169; }
        .btn-danger { background: #f56565; color: white; }
        .btn-danger:hover { background: #e53e3e; }
        .btn-secondary { background: #718096; color: white; }
        .btn-secondary:hover { background: #4a5568; }
        .categories-list { display: grid; gap: 15px; }
        .category-card {
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            padding: 20px;
            background: #f9fafb;
        }
        .category-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .category-name {
            font-size: 18px;
            font-weight: 600;
            color: #333;
        }
        .category-actions { display: flex; gap: 10px; }
        .posts-list { margin-top: 15px; }
        .post-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px;
            background: white;
            border-radius: 8px;
            margin-bottom: 8px;
            border: 1px solid #e0e0e0;
        }
        .post-info { flex: 1; }
        .post-title {
            font-weight: 500;
            color: #333;
            margin-bottom: 3px;
        }
        .post-url {
            font-size: 12px;
            color: #888;
        }
        .post-actions { display: flex; gap: 8px; }
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }
        .modal.active { display: flex; }
        .modal-content {
            background: white;
            padding: 30px;
            border-radius: 15px;
            max-width: 500px;
            width: 90%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        .modal-title {
            font-size: 22px;
            font-weight: 600;
            margin-bottom: 20px;
            color: #333;
        }
        .modal-actions {
            display: flex;
            gap: 10px;
            margin-top: 20px;
            justify-content: flex-end;
        }
    </style>
</head>
<body>
    <div class="login-container" id="loginContainer">
        <div class="login-title">🔐 Admin Login</div>
        <div id="loginAlert" class="alert"></div>
        <div class="input-group">
            <label>Password</label>
            <input type="password" id="passwordInput" placeholder="Enter admin password">
        </div>
        <button class="btn btn-primary" onclick="login()">Login</button>
    </div>

    <div class="container" id="adminPanel">
        <div class="header">
            <h1>🔧 Admin Panel</h1>
            <p>Manage categories and posts</p>
        </div>
        <div id="alert" class="alert"></div>
        <div class="section">
            <div class="section-title">➕ Add New Category</div>
            <div class="input-group">
                <label>Category Name</label>
                <input type="text" id="newCategoryInput" placeholder="e.g., 🎯 New Category">
            </div>
            <button class="btn btn-primary" onclick="addCategory()">Add Category</button>
        </div>
        <div class="section">
            <div class="section-title">📚 Manage Categories & Posts</div>
            <div id="categoriesList" class="categories-list"></div>
        </div>
    </div>

    <div id="postModal" class="modal">
        <div class="modal-content">
            <div class="modal-title" id="modalTitle">Add Post</div>
            <div class="input-group">
                <label>Post Title</label>
                <input type="text" id="postTitle" placeholder="e.g., Важный пост">
            </div>
            <div class="input-group">
                <label>Post URL</label>
                <input type="text" id="postUrl" placeholder="https://t.me/channel/123">
            </div>
            <div class="modal-actions">
                <button class="btn btn-secondary" onclick="closePostModal()">Cancel</button>
                <button class="btn btn-success" onclick="savePost()">Save Post</button>
            </div>
        </div>
    </div>

    <script>
        let tg = window.Telegram.WebApp;
        let categories = {};
        let currentCategory = null;
        let currentPostIndex = null;
        let adminPassword = null;
        let userId = null;

        tg.ready();
        tg.expand();

        userId = tg.initDataUnsafe?.user?.id;

        async function login() {
            const password = document.getElementById('passwordInput').value;
            if (!password) {
                showLoginAlert('Please enter password');
                return;
            }
            if (!userId) {
                showLoginAlert('Please open from Telegram');
                return;
            }

            try {
                const response = await fetch('/api/admin/auth', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ password, user_id: userId })
                });

                if (response.ok) {
                    adminPassword = password;
                    document.getElementById('loginContainer').style.display = 'none';
                    document.getElementById('adminPanel').style.display = 'block';
                    await loadCategories();
                } else {
                    showLoginAlert('Invalid credentials');
                }
            } catch (error) {
                showLoginAlert('Login failed');
            }
        }

        function showLoginAlert(message) {
            const alert = document.getElementById('loginAlert');
            alert.textContent = message;
            alert.className = 'alert error active';
            setTimeout(() => alert.classList.remove('active'), 3000);
        }

        async function loadCategories() {
            try {
                const response = await fetch('/api/categories');
                categories = await response.json();
                renderCategories();
            } catch (error) {
                showAlert('Failed to load categories', 'error');
            }
        }

        function renderCategories() {
            const list = document.getElementById('categoriesList');
            list.innerHTML = '';

            Object.keys(categories).forEach(category => {
                const card = document.createElement('div');
                card.className = 'category-card';
                card.innerHTML = `
                    <div class="category-header">
                        <div class="category-name">${category}</div>
                        <div class="category-actions">
                            <button class="btn btn-primary" onclick="openAddPostModal('${category.replace(/'/g, "\\'")}')">Add Post</button>
                            <button class="btn btn-danger" onclick="deleteCategory('${category.replace(/'/g, "\\'")}')">Delete</button>
                        </div>
                    </div>
                    <div class="posts-list" id="posts-${btoa(category)}"></div>
                `;
                list.appendChild(card);
                renderPosts(category);
            });
        }

        function renderPosts(category) {
            const postsList = document.getElementById(`posts-${btoa(category)}`);
            postsList.innerHTML = '';

            categories[category].forEach((post, index) => {
                const item = document.createElement('div');
                item.className = 'post-item';
                item.innerHTML = `
                    <div class="post-info">
                        <div class="post-title">${post.title}</div>
                        <div class="post-url">${post.url}</div>
                    </div>
                    <div class="post-actions">
                        <button class="btn btn-secondary" onclick='editPost(${JSON.stringify(category)}, ${index})'>Edit</button>
                        <button class="btn btn-danger" onclick='deletePost(${JSON.stringify(category)}, ${index})'>Delete</button>
                    </div>
                `;
                postsList.appendChild(item);
            });
        }

        async function addCategory() {
            const name = document.getElementById('newCategoryInput').value.trim();
            if (!name) return showAlert('Please enter a category name', 'error');

            try {
                const response = await fetch(`/api/categories/add?category=${encodeURIComponent(name)}&password=${adminPassword}&user_id=${userId}`, {
                    method: 'POST'
                });
                if (response.ok) {
                    showAlert('Category added!', 'success');
                    document.getElementById('newCategoryInput').value = '';
                    await loadCategories();
                } else {
                    showAlert('Failed to add category', 'error');
                }
            } catch (error) {
                showAlert('Error adding category', 'error');
            }
        }

        async function deleteCategory(category) {
            if (!confirm(`Delete "${category}"?`)) return;
            try {
                const response = await fetch(`/api/categories/${encodeURIComponent(category)}?password=${adminPassword}&user_id=${userId}`, {
                    method: 'DELETE'
                });
                if (response.ok) {
                    showAlert('Category deleted!', 'success');
                    await loadCategories();
                } else {
                    showAlert('Failed to delete category', 'error');
                }
            } catch (error) {
                showAlert('Error deleting category', 'error');
            }
        }

        function openAddPostModal(category) {
            currentCategory = category;
            currentPostIndex = null;
            document.getElementById('modalTitle').textContent = 'Add Post';
            document.getElementById('postTitle').value = '';
            document.getElementById('postUrl').value = '';
            document.getElementById('postModal').classList.add('active');
        }

        function editPost(category, index) {
            currentCategory = category;
            currentPostIndex = index;
            const post = categories[category][index];
            document.getElementById('modalTitle').textContent = 'Edit Post';
            document.getElementById('postTitle').value = post.title;
            document.getElementById('postUrl').value = post.url;
            document.getElementById('postModal').classList.add('active');
        }

        function closePostModal() {
            document.getElementById('postModal').classList.remove('active');
        }

        async function savePost() {
            const title = document.getElementById('postTitle').value.trim();
            const url = document.getElementById('postUrl').value.trim();
            if (!title || !url) return showAlert('Fill all fields', 'error');

            const post = { title, url };
            try {
                let response;
                if (currentPostIndex === null) {
                    response = await fetch(`/api/categories/${encodeURIComponent(currentCategory)}/posts?password=${adminPassword}&user_id=${userId}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(post)
                    });
                } else {
                    response = await fetch(`/api/categories/${encodeURIComponent(currentCategory)}/posts/${currentPostIndex}?password=${adminPassword}&user_id=${userId}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(post)
                    });
                }

                if (response.ok) {
                    showAlert('Post saved!', 'success');
                    closePostModal();
                    await loadCategories();
                } else {
                    showAlert('Failed to save post', 'error');
                }
            } catch (error) {
                showAlert('Error saving post', 'error');
            }
        }

        async function deletePost(category, index) {
            if (!confirm('Delete this post?')) return;
            try {
                const response = await fetch(`/api/categories/${encodeURIComponent(category)}/posts/${index}?password=${adminPassword}&user_id=${userId}`, {
                    method: 'DELETE'
                });
                if (response.ok) {
                    showAlert('Post deleted!', 'success');
                    await loadCategories();
                } else {
                    showAlert('Failed to delete post', 'error');
                }
            } catch (error) {
                showAlert('Error deleting post', 'error');
            }
        }

        function showAlert(message, type) {
            const alert = document.getElementById('alert');
            alert.textContent = message;
            alert.className = `alert ${type} active`;
            setTimeout(() => alert.classList.remove('active'), 3000);
        }
    </script>
</body>
</html>
    """
    return HTMLResponse(content=admin_html)

if __name__ == "__main__":
    import uvicorn
    print("🚀 FastAPI Server starting...")
    print(f"📱 Mini App: http://localhost:8000")
    print(f"🔧 Admin Panel: http://localhost:8000/admin")
    print(f"📚 API Docs: http://localhost:8000/docs")
    print(f"🔑 Admin Password: {ADMIN_PASSWORD}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
