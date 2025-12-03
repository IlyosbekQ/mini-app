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

BOT_TOKEN = os.getenv("BOT_TOKEN", "5975058740:AAEE7HBv0koieZUSk9Su8wFNAWK4W2-65tI")
CHANNEL_ID = os.getenv("CHANNEL_ID", "deleted_me")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://nonmucuous-unescheatable-ngoc.ngrok-free.dev")

# Admin credentials
ADMIN_PASSWORD = "vvsh2024"
ALLOWED_ADMIN_IDS = [5975058740]

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

# Load/Save categories
def load_categories():
    try:
        with open("categories.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
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

def save_categories(data):
    with open("categories.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

CATEGORIES_DATA = load_categories()
bot = Bot(token=BOT_TOKEN)

def verify_admin(password: str, user_id: int):
    return password == ADMIN_PASSWORD and user_id in ALLOWED_ADMIN_IDS

# API Endpoints
@app.post("/api/admin/auth")
async def admin_auth(auth: AuthRequest):
    if verify_admin(auth.password, auth.user_id):
        return {"status": "success", "message": "Authenticated"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/api/categories")
async def get_categories():
    return CATEGORIES_DATA

@app.post("/api/categories/add")
async def add_category(category: str, password: str, user_id: int):
    if not verify_admin(password, user_id):
        raise HTTPException(status_code=401, detail="Unauthorized")
    if category in CATEGORIES_DATA:
        raise HTTPException(status_code=400, detail="Category already exists")
    CATEGORIES_DATA[category] = []
    save_categories(CATEGORIES_DATA)
    return {"status": "success", "category": category}

@app.delete("/api/categories/{category}")
async def delete_category(category: str, password: str, user_id: int):
    if not verify_admin(password, user_id):
        raise HTTPException(status_code=401, detail="Unauthorized")
    if category not in CATEGORIES_DATA:
        raise HTTPException(status_code=404, detail="Category not found")
    del CATEGORIES_DATA[category]
    save_categories(CATEGORIES_DATA)
    return {"status": "success"}

@app.post("/api/categories/{category}/posts")
async def add_post(category: str, post: Post, password: str, user_id: int):
    if not verify_admin(password, user_id):
        raise HTTPException(status_code=401, detail="Unauthorized")
    if category not in CATEGORIES_DATA:
        raise HTTPException(status_code=404, detail="Category not found")
    CATEGORIES_DATA[category].append(post.dict())
    save_categories(CATEGORIES_DATA)
    return {"status": "success", "post": post}

@app.put("/api/categories/{category}/posts/{post_index}")
async def update_post(category: str, post_index: int, post: Post, password: str, user_id: int):
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
    if not verify_admin(password, user_id):
        raise HTTPException(status_code=401, detail="Unauthorized")
    if category not in CATEGORIES_DATA:
        raise HTTPException(status_code=404, detail="Category not found")
    if post_index >= len(CATEGORIES_DATA[category]):
        raise HTTPException(status_code=404, detail="Post not found")
    CATEGORIES_DATA[category].pop(post_index)
    save_categories(CATEGORIES_DATA)
    return {"status": "success"}

@app.put("/api/categories/{old_name}/rename")
async def rename_category(old_name: str, new_name: str, password: str, user_id: int):
    if not verify_admin(password, user_id):
        raise HTTPException(status_code=401, detail="Unauthorized")
    if old_name not in CATEGORIES_DATA:
        raise HTTPException(status_code=404, detail="Category not found")
    if new_name in CATEGORIES_DATA:
        raise HTTPException(status_code=400, detail="New name already exists")
    CATEGORIES_DATA[new_name] = CATEGORIES_DATA.pop(old_name)
    save_categories(CATEGORIES_DATA)
    return {"status": "success"}

@app.get("/", response_class=HTMLResponse)
async def serve_miniapp():
    with open("miniapp.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/admin", response_class=HTMLResponse)
async def serve_admin():
    with open("admin.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

if __name__ == "__main__":
    import uvicorn
    print("🚀 FastAPI Server starting...")
    print(f"📱 Mini App: http://localhost:8000")
    print(f"🔧 Admin Panel: http://localhost:8000/admin")
    uvicorn.run(app, host="0.0.0.0", port=8000)
