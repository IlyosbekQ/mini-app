# app.py
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import json
import os

app = FastAPI()

# Optional: mount static if you have CSS/JS — but for simplicity, we inline HTML
# For now, we'll serve everything from memory (no separate static/ folder needed)

# Serve categories API
@app.get("/api/categories")
async def get_categories():
    # Load posts.json from same directory
    with open("data/posts.json", "r", encoding="utf-8") as f:
        return json.load(f)

# Serve Mini App (single-page HTML + JS)
@app.get("/", response_class=HTMLResponse)
async def serve_miniapp():
    # Inline HTML + JS (no external files needed → simpler for Vercel)
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
      <title>Channel Navigator</title>
      <style>
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 20px; background: #f5f5f9; }
        select, button { width: 100%; padding: 12px; margin: 8px 0; border-radius: 8px; border: 1px solid #ddd; }
        #posts { margin-top: 16px; }
        .post-btn { background: #0088cc; color: white; margin: 4px 0; border: none; }
        .hidden { display: none; }
      </style>
    </head>
    <body>
      <h2>📚 Channel Posts</h2>
      <select id="categorySelect" onchange="loadPosts()">
        <option value="">Select Category</option>
      </select>
      <div id="posts"></div>

      <script src="https://telegram.org/js/telegram-web-app.js"></script>
      <script>
        Telegram.WebApp.ready();

        async function loadCategories() {
          const res = await fetch('/api/categories');
          const data = await res.json();
          const select = document.getElementById('categorySelect');
          Object.keys(data).forEach(cat => {
            const opt = document.createElement('option');
            opt.value = cat;
            opt.textContent = cat;
            select.appendChild(opt);
          });
        }

        function loadPosts() {
          const cat = document.getElementById('categorySelect').value;
          if (!cat) return;
          
          fetch('/api/categories')
            .then(r => r.json())
            .then(data => {
              const posts = data[cat] || [];
              const div = document.getElementById('posts');
              div.innerHTML = '<h3>Posts:</h3>';
              
              posts.forEach(p => {
                const btn = document.createElement('button');
                btn.className = 'post-btn';
                btn.textContent = p.title;
                btn.onclick = () => {
                  const url = p.url.trim();
                  Telegram.WebApp.close();
                  if (Telegram.WebApp.openLink) {
                    Telegram.WebApp.openLink(url, { try_instant_view: true });
                  } else {
                    window.location.href = url;
                  }
                };
                div.appendChild(btn);
              });
            });
        }

        loadCategories();
      </script>
    </body>
    </html>
    """
    return HTMLResponse(html)