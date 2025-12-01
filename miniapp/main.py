# miniapp/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import json
import os

app = FastAPI()

# Serve static files (HTML, JS, CSS)
app.mount("/static", StaticFiles(directory="miniapp/static"), name="static")

# API: get categories & posts
@app.get("/api/categories")
async def get_categories():
    with open("miniapp/data/posts.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

# Root route: serve index.html
@app.get("/", response_class=HTMLResponse)
async def serve_app():
    with open("miniapp/static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())