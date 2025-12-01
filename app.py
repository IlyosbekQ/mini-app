import os
import json
from typing import Dict, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from dotenv import load_dotenv

load_dotenv()

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "5975058740:AAEE7HBv0koieZUSk9Su8wFNAWK4W2-65tI")
CHANNEL_ID = os.getenv("CHANNEL_ID", "-1002228131301")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://nonmucous-unescheatable-ngoc.ngrok-free.dev")

app = FastAPI(title="Telegram Mini App Backend")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Categories data
CATEGORIES_DATA = {
    "Math": [
        {"title": "Limits Lesson", "url": "https://t.me/deleted_me/18"},
        {"title": "Integrals", "url": "https://t.me/deleted_me/17"},
        {"title": "Derivatives", "url": "https://t.me/deleted_me/16"}
    ],
    "Physics": [
        {"title": "Kinematics", "url": "https://t.me/deleted_me/15"},
        {"title": "Dynamics", "url": "https://t.me/deleted_me/14"}
    ],
    "Chemistry": [
        {"title": "Organic Chemistry", "url": "https://t.me/deleted_me/13"}
    ]
}

# Initialize bot
bot = Bot(token=BOT_TOKEN)

@app.get("/api/categories")
async def get_categories():
    """Returns all categories and their posts"""
    return CATEGORIES_DATA

@app.post("/api/categories")
async def update_categories(data: Dict[str, List[Dict[str, str]]]):
    """Update categories data"""
    global CATEGORIES_DATA
    CATEGORIES_DATA = data
    with open("categories.json", "w") as f:
        json.dump(CATEGORIES_DATA, f, indent=2)
    return {"status": "success"}

async def post_navigation_message():
    """Posts navigation message to channel"""
    try:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "📱 Open Post Navigator",
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

@app.post("/api/post-navigation")
async def trigger_navigation_post():
    """Endpoint to post navigation message"""
    result = await post_navigation_message()
    return result

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
        .category-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin-bottom: 20px;
        }
        .category-btn {
            padding: 20px;
            border: 2px solid #e0e0e0;
            border-radius: 15px;
            background: white;
            cursor: pointer;
            transition: all 0.3s;
            text-align: center;
        }
        .category-btn:hover { border-color: #667eea; background: #f5f7ff; }
        .category-btn.active {
            border-color: #667eea;
            background: #f5f7ff;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
        }
        .category-icon { font-size: 32px; margin-bottom: 8px; }
        .category-name { font-weight: 600; color: #333; }
        .category-count { font-size: 12px; color: #888; margin-top: 4px; }
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
        .post-title { font-weight: 500; color: #333; }
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
                <div class="category-grid" id="categoryGrid"></div>
                <div id="postsSection" class="posts-section">
                    <div class="section-title">Select a post:</div>
                    <div class="post-list" id="postList"></div>
                </div>
                <div id="infoBox" class="info-box">
                    👆 Select a category above to view posts
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
        
        const categoryIcons = {
            'Math': '📐',
            'Physics': '⚛️',
            'Chemistry': '🧪'
        };
        
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
            const grid = document.getElementById('categoryGrid');
            grid.innerHTML = '';
            
            Object.keys(categories).forEach(category => {
                const btn = document.createElement('button');
                btn.className = 'category-btn';
                btn.innerHTML = `
                    <div class="category-icon">${categoryIcons[category] || '📁'}</div>
                    <div class="category-name">${category}</div>
                    <div class="category-count">${categories[category].length} posts</div>
                `;
                btn.onclick = () => selectCategory(category, btn);
                grid.appendChild(btn);
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

if __name__ == "__main__":
    import uvicorn
    print("🚀 FastAPI Server starting...")
    print(f"📱 Open: http://localhost:8000")
    print(f"📚 API Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)