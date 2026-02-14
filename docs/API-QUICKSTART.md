# 🚀 News AI Agent API - Quick Start Guide

**Get your FastAPI running in 5 minutes with automatic OpenAPI documentation!**

---

## ⚡ Super Quick Start (Docker)

```bash
# 1. Start everything (API + n8n + PostgreSQL)
cd n8n
docker-compose up -d

# 2. Wait 30 seconds for services to start

# 3. Open your browser
```

**🎉 You're done! Access:**

- **📖 API Documentation (Swagger UI):** http://localhost:3000/docs
- **📘 Alternative Docs (ReDoc):** http://localhost:3000/redoc
- **🔧 n8n Dashboard:** http://localhost:5678
- **💓 API Health Check:** http://localhost:3000/api/health

---

## 🧪 Test the API

### 1. Check Health (No Auth Required)

```bash
curl http://localhost:3000/api/health
```

### 2. List Feeds (Requires API Key)

```bash
curl -H "X-API-Key: dev-api-key-change-in-production" \
     http://localhost:3000/api/feeds
```

### 3. Add a New Feed

```bash
curl -X POST http://localhost:3000/api/feeds \
  -H "X-API-Key: dev-api-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "FAZ",
    "url": "https://www.faz.net/rss/aktuell/",
    "language": "de",
    "category": "general"
  }'
```

### 4. Trigger RSS Scraping

```bash
curl -X POST http://localhost:3000/api/workflows/scrape \
  -H "X-API-Key: dev-api-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### 5. View Articles

```bash
curl -H "X-API-Key: dev-api-key-change-in-production" \
     "http://localhost:3000/api/articles?limit=10"
```

---

## 🎨 Interactive API Exploration

**Open:** http://localhost:3000/docs

You get:
- ✅ **Try it now** buttons for every endpoint
- ✅ **Automatic request/response examples**
- ✅ **Built-in authentication** (click "Authorize", enter API key)
- ✅ **Full schema documentation**
- ✅ **Zero configuration needed!**

**This is the fastest way to understand and test the API!**

---

## 📚 API Endpoints Overview

### Feed Management
- `POST /api/feeds` - Add RSS feed
- `GET /api/feeds` - List all feeds
- `PUT /api/feeds/{id}` - Update feed
- `DELETE /api/feeds/{id}` - Remove feed
- `PATCH /api/feeds/{id}/toggle` - Enable/disable feed

### Article Management
- `GET /api/articles` - List articles (with filters)
- `GET /api/articles/{id}` - Get specific article
- `DELETE /api/articles/{id}` - Delete article

### Workflows
- `POST /api/workflows/scrape` - Fetch new articles
- `POST /api/workflows/summarize` - AI summarization
- `POST /api/workflows/send-digest` - Send email

### System
- `GET /api/health` - Health check
- `GET /api/stats` - System statistics

---

## 🔑 Authentication

**Development API Key:** `dev-api-key-change-in-production`

Include in header:
```
X-API-Key: dev-api-key-change-in-production
```

⚠️ **Change this in production!** Edit `n8n/.env`:
```bash
API_KEY=your-secure-production-key
```

---

## 📂 Project Structure

```
AI-news-agent/
├── api/                    # 🆕 FastAPI Application
│   ├── main.py            # API entry point
│   ├── models.py          # Pydantic models (validation)
│   ├── database.py        # Database queries
│   ├── routers/           # Endpoint logic
│   ├── Dockerfile         # Container definition
│   └── README.md          # Detailed API docs
│
├── n8n/                    # n8n Workflows
│   ├── docker-compose.yml # 🔄 Updated with API service
│   ├── sql/init.sql       # 🔄 Updated with rss_sources table
│   └── workflows/         # Automation workflows
│
├── docs/
│   ├── API-GUIDE.md       # 🆕 Complete API reference
│   └── session-summaries/ # Development notes
│
└── API-QUICKSTART.md      # 🆕 This file
```

---

## 🐍 Python Integration Example

```python
import requests

API_KEY = "dev-api-key-change-in-production"
BASE_URL = "http://localhost:3000/api"
headers = {"X-API-Key": API_KEY}

# Add a feed
response = requests.post(
    f"{BASE_URL}/feeds",
    headers=headers,
    json={
        "name": "Zeit Online",
        "url": "https://www.zeit.de/index",
        "language": "de"
    }
)
print(f"Feed created: {response.json()['name']}")

# Get unprocessed articles
response = requests.get(
    f"{BASE_URL}/articles",
    headers=headers,
    params={"processed": False, "limit": 10}
)
articles = response.json()
print(f"Found {len(articles)} unprocessed articles")

# Trigger scraping
response = requests.post(
    f"{BASE_URL}/actions/scrape",
    headers=headers,
    json={}
)
print(response.json()["message"])
```

---

## 🔧 Configuration

### Environment Variables

Located in `n8n/.env` (create from `n8n/env.example`):

```bash
# Database
POSTGRES_USER=n8n
POSTGRES_PASSWORD=n8n_password
POSTGRES_DB=news_agent

# API Security
API_KEY=dev-api-key-change-in-production
SECRET_KEY=change-this-to-random-32-chars

# n8n
N8N_USER=admin
N8N_PASSWORD=admin123
```

---

## 🛠️ Troubleshooting

### API won't start

```bash
# Check logs
docker logs news-agent-api

# Restart API only
docker-compose restart api
```

### Can't connect to database

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Test database connection
docker exec -it news-agent-postgres psql -U n8n -d news_agent
```

### 401 Unauthorized errors

```bash
# Verify you're including the header
curl -v -H "X-API-Key: dev-api-key-change-in-production" \
     http://localhost:3000/api/feeds

# Check API key in .env matches what you're sending
```

---

## 📖 Learn More

- **Detailed API Docs:** `api/README.md`
- **Integration Guide:** `docs/API-GUIDE.md`
- **Interactive Docs:** http://localhost:3000/docs
- **Session Notes:** `docs/session-summaries/`

---

## 🎯 What You Built

✅ **Enterprise-grade FastAPI** with automatic OpenAPI docs  
✅ **Full CRUD operations** for feeds and articles  
✅ **Workflow triggers** (scrape, summarize, send)  
✅ **Type-safe models** with Pydantic validation  
✅ **API key authentication**  
✅ **Health monitoring** endpoints  
✅ **Database-driven** feed management  
✅ **Docker containerized** deployment  
✅ **Production-ready** architecture  

---

## 🚀 Next Steps

1. ✅ **Explore the docs:** http://localhost:3000/docs
2. ✅ **Test with Swagger UI** (click "Try it out")
3. ✅ **Add more RSS feeds** via API
4. ✅ **Build your integration** (Python, Node.js, etc.)
5. ✅ **Deploy to production** (change API keys!)

---

## 🎉 Congratulations!

You now have a **production-ready REST API** for your News AI Agent with:
- **Automatic documentation** (Swagger + ReDoc)
- **Type safety** (Pydantic models)
- **Fast performance** (async Python)
- **Easy integration** (REST standard)

**The API makes your entire news aggregation system programmable!**

Visit http://localhost:3000/docs and start exploring! 🚀
