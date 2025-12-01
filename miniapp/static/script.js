// Wait for Telegram WebApp to initialize
Telegram.WebApp.ready();

// Load categories
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

// Load posts for selected category
function loadPosts() {
  const category = document.getElementById('categorySelect').value;
  if (!category) return;

  fetch('/api/categories')
    .then(res => res.json())
    .then(data => {
      const posts = data[category] || [];
      const container = document.getElementById('posts');
      container.innerHTML = '<h3>Posts:</h3>';
      
      posts.forEach(post => {
        const btn = document.createElement('button');
        btn.className = 'post-btn';
        btn.textContent = post.title;
        btn.onclick = () => openPost(post.url);
        container.appendChild(btn);
      });
    });
}

// Handle post selection
function openPost(url) {
  // Ensure URL is clean (no trailing spaces)
  const cleanUrl = url.trim();

  // Close WebApp first (best practice)
  Telegram.WebApp.close();

  // Telegram auto-redirects after close IF you call `window.location.href`
  // But better: use `Telegram.WebApp.openLink()` (more reliable)
  if (Telegram.WebApp.openLink) {
    Telegram.WebApp.openLink(cleanUrl, { try_instant_view: true });
  } else {
    // Fallback
    window.location.href = cleanUrl;
  }
}

// Initialize
loadCategories();