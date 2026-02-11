# News AI Agent API 🚀

**Enterprise-grade REST API for news aggregation and AI summarization with automatic OpenAPI documentation.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql)](https://www.postgresql.org/)

---

## 🌟 Features

- ✅ **Automatic API Documentation** - Interactive Swagger UI + ReDoc
- ✅ **Full REST API** - CRUD operations for feeds and articles
- ✅ **Workflow Triggers** - Start scraping, summarization, and digests
- ✅ **Type Safety** - Pydantic models with runtime validation
- ✅ **Authentication** - API key-based security
- ✅ **Health Checks** - Built-in monitoring endpoints
- ✅ **Docker Ready** - Containerized deployment
- ✅ **Production Grade** - Async, performant, scalable

---

## 📚 Quick Links

Once running, access:

- **📖 Interactive API Docs (Swagger UI):** http://localhost:3000/docs
- **📘 Alternative Docs (ReDoc):** http://localhost:3000/redoc
- **🔧 OpenAPI Schema:** http://localhost:3000/openapi.json
- **💓 Health Check:** http://localhost:3000/api/health

---

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# From project root
cd n8n
docker-compose up -d

# API will be available at http://localhost:3000
# Docs at http://localhost:3000/docs
```

### Option 2: Local Development

```bash
cd api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your configuration

# Run development server
uvicorn main:app --reload --port 3000

# Or use Python directly
python main.py
```

---

## 📖 API Documentation

### Authentication

All endpoints (except `/health`) require API key authentication:

```bash
# Include in header
X-API-Key: your-api-key
```

**Default API Key (development):** `dev-api-key-change-in-production`

⚠️ **IMPORTANT:** Change the API key in production!

### Base URL

```
http://localhost:3000/api
```

### Available Endpoints

#### 🗂️ Feed Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/feeds` | Create new RSS feed |
| `GET` | `/api/feeds` | List all feeds |
| `GET` | `/api/feeds/{id}` | Get specific feed |
| `PUT` | `/api/feeds/{id}` | Update feed |
| `DELETE` | `/api/feeds/{id}` | Delete feed |
| `PATCH` | `/api/feeds/{id}/toggle` | Enable/disable feed |

#### 📰 Article Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/articles` | List articles (with filters) |
| `GET` | `/api/articles/{id}` | Get specific article |
| `DELETE` | `/api/articles/{id}` | Delete article |

#### ⚡ Workflow Actions

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/actions/scrape` | Trigger RSS scraping |
| `POST` | `/api/actions/summarize` | Trigger AI summarization |
| `POST` | `/api/actions/send-digest` | Send email digest |
| `POST` | `/api/articles/{id}/summarize` | Summarize single article |

#### 🔧 System

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check (no auth) |
| `GET` | `/api/stats` | System statistics |

---

## 💡 Example Usage

### Create a New Feed

```bash
curl -X POST "http://localhost:3000/api/feeds" \
  -H "X-API-Key: dev-api-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "FAZ",
    "url": "https://www.faz.net/rss/aktuell/",
    "language": "de",
    "category": "general",
    "enabled": true
  }'
```

**Response:**
```json
{
  "id": "uuid-here",
  "name": "FAZ",
  "url": "https://www.faz.net/rss/aktuell/",
  "language": "de",
  "category": "general",
  "enabled": true,
  "article_count": 0,
  "last_fetched": null,
  "created_at": "2026-02-11T..."
}
```

### List All Feeds

```bash
curl "http://localhost:3000/api/feeds?enabled_only=true" \
  -H "X-API-Key: dev-api-key-change-in-production"
```

### Get Unprocessed Articles

```bash
curl "http://localhost:3000/api/articles?processed=false&limit=20" \
  -H "X-API-Key: dev-api-key-change-in-production"
```

### Trigger Scraping

```bash
curl -X POST "http://localhost:3000/api/actions/scrape" \
  -H "X-API-Key: dev-api-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Trigger Summarization

```bash
curl -X POST "http://localhost:3000/api/actions/summarize" \
  -H "X-API-Key: dev-api-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "limit": 10
  }'
```

### Check System Stats

```bash
curl "http://localhost:3000/api/stats" \
  -H "X-API-Key: dev-api-key-change-in-production"
```

**Response:**
```json
{
  "total_feeds": 3,
  "active_feeds": 3,
  "total_articles": 156,
  "processed_articles": 120,
  "unsent_articles": 15,
  "last_scrape": "2026-02-11T10:30:00Z",
  "last_summarization": "2026-02-11T10:35:00Z"
}
```

---

## 🐍 Python Client Example

```python
import requests

API_BASE = "http://localhost:3000/api"
API_KEY = "dev-api-key-change-in-production"

class NewsAgentClient:
    def __init__(self, base_url=API_BASE, api_key=API_KEY):
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key}
    
    def create_feed(self, name, url, language="de", category=None):
        """Add a new RSS feed"""
        response = requests.post(
            f"{self.base_url}/feeds",
            headers=self.headers,
            json={
                "name": name,
                "url": url,
                "language": language,
                "category": category,
                "enabled": True
            }
        )
        return response.json()
    
    def get_articles(self, processed=None, sent=None, limit=50):
        """Get articles with optional filters"""
        params = {"limit": limit}
        if processed is not None:
            params["processed"] = processed
        if sent is not None:
            params["sent"] = sent
        
        response = requests.get(
            f"{self.base_url}/articles",
            headers=self.headers,
            params=params
        )
        return response.json()
    
    def trigger_scrape(self):
        """Trigger RSS feed scraping"""
        response = requests.post(
            f"{self.base_url}/actions/scrape",
            headers=self.headers,
            json={}
        )
        return response.json()
    
    def get_stats(self):
        """Get system statistics"""
        response = requests.get(
            f"{self.base_url}/stats",
            headers=self.headers
        )
        return response.json()

# Usage
client = NewsAgentClient()

# Add a feed
feed = client.create_feed("Zeit Online", "https://www.zeit.de/index")
print(f"Created feed: {feed['name']}")

# Get unprocessed articles
articles = client.get_articles(processed=False)
print(f"Found {len(articles)} unprocessed articles")

# Trigger scraping
result = client.trigger_scrape()
print(result["message"])

# Check stats
stats = client.get_stats()
print(f"Total articles: {stats['total_articles']}")
```

---

## 📂 Project Structure

```
api/
├── main.py                 # FastAPI application entry point
├── config.py               # Configuration management
├── models.py               # Pydantic models (validation)
├── database.py             # Database queries and connection
├── security.py             # Authentication middleware
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker container definition
├── .env.example            # Environment variables template
├── routers/
│   ├── __init__.py
│   ├── feeds.py           # Feed management endpoints
│   ├── articles.py        # Article management endpoints
│   ├── actions.py         # Workflow trigger endpoints
│   └── system.py          # Health and stats endpoints
└── README.md              # This file
```

---

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/news_agent

# n8n Integration
N8N_WEBHOOK_BASE_URL=http://localhost:5678/webhook

# Security (CHANGE IN PRODUCTION!)
API_KEY=your-secure-api-key
SECRET_KEY=your-secret-key-min-32-chars

# API Settings
HOST=0.0.0.0
PORT=3000
DEBUG=true
```

### Security Best Practices

1. **Change default API key** before deployment
2. **Use strong SECRET_KEY** (32+ random characters)
3. **Enable HTTPS** in production
4. **Restrict CORS origins** to trusted domains
5. **Use environment variables** for secrets (never commit)
6. **Implement rate limiting** for production
7. **Regular security updates** (dependencies)

---

## 🏗️ Development

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Code Style

```bash
# Format code
black .

# Lint
flake8

# Type checking
mypy .
```

### Hot Reload Development

```bash
# Uvicorn watches for file changes
uvicorn main:app --reload --port 3000
```

---

## 🐳 Production Deployment

### Docker Production Build

```bash
# Build production image
docker build -t news-agent-api:latest .

# Run with Gunicorn (production server)
docker run -d \
  -p 3000:3000 \
  --env-file .env \
  --name news-agent-api \
  news-agent-api:latest \
  gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:3000
```

### Environment-Specific Configs

```bash
# Development
DEBUG=true
uvicorn main:app --reload

# Production
DEBUG=false
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

---

## 📊 Monitoring

### Health Check Endpoint

```bash
curl http://localhost:3000/api/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "n8n": "reachable",
  "timestamp": "2026-02-11T10:00:00Z"
}
```

### Metrics (Future)

- Prometheus metrics at `/metrics`
- Request latency tracking
- Error rate monitoring
- Database connection pool stats

---

## 🔍 Troubleshooting

### API won't start

```bash
# Check if port 3000 is already in use
lsof -i :3000  # Mac/Linux
netstat -ano | findstr :3000  # Windows

# Check database connection
psql -h localhost -U n8n -d news_agent

# Check logs
docker logs news-agent-api
```

### Database connection errors

```bash
# Verify DATABASE_URL format
postgresql://username:password@host:port/database

# Test connection
python -c "import asyncpg; asyncpg.connect('your-database-url')"
```

### n8n webhook errors

```bash
# Verify n8n is running
curl http://localhost:5678/healthz

# Check N8N_WEBHOOK_BASE_URL is correct
echo $N8N_WEBHOOK_BASE_URL
```

### Authentication failing

```bash
# Verify API key in header
curl -v -H "X-API-Key: your-key" http://localhost:3000/api/feeds

# Check .env file has correct API_KEY
```

---

## 🚦 API Status Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | OK | Successful GET/PUT/PATCH |
| 201 | Created | Successful POST |
| 400 | Bad Request | Invalid input data |
| 401 | Unauthorized | Missing API key |
| 403 | Forbidden | Invalid API key |
| 404 | Not Found | Resource doesn't exist |
| 500 | Internal Error | Server error |
| 503 | Service Unavailable | n8n unreachable |

---

## 📝 License

Part of the News AI Agent project. For internal/enterprise use.

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'feat: add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📞 Support

- **Documentation:** Visit `/docs` for interactive API documentation
- **Issues:** Report bugs via GitHub issues
- **Questions:** Check session summaries in `/docs/session-summaries/`

---

**Built with ❤️ using FastAPI**

🔗 **Next Steps:**
1. Visit http://localhost:3000/docs to see the automatic documentation
2. Test the API endpoints with the interactive Swagger UI
3. Integrate the API into your applications
4. Build custom clients and workflows

**Enjoy your automated news aggregation! 🎉**
