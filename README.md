# AI News agent

Automated news aggregation and distribution system built on n8n workflows. Ingests articles from RSS feeds, stores them in PostgreSQL, and publishes summaries to configured output channels (email, LinkedIn, X).

## Quick Start

1. Create .env file

```bash
cp env.example .env
```

2. Edit .env with your credentials

3. Start container

```bash
docker compose up -d
```

Visit `http://localhost:5678` to create n8n admin account (required on first startup).

## Environment Variables

**Required:**
- `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` - Database credentials
- `API_KEY` - FastAPI authentication key
- `SECRET_KEY` - 32+ character secret for JWT
- `OPENAI_API_KEY` - OpenAI or compatible API key ([get one](https://platform.openai.com/api-keys))

**Optional:**
- `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` - SMTP server for email digests
  - Gmail requires App Password (not regular password): [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
- `TIMEZONE` - Default: `Europe/Berlin`

Recipients are managed via API (`POST /api/recipients`), not environment variables.

## n8n Admin Setup

n8n 2.x requires manual owner account creation. Visit `http://localhost:5678` on first startup and create your account. This cannot be automated via environment variables.

## Telegram Bot (Local Development)

The Telegram Agent workflow requires Telegram servers to send webhook requests to your n8n instance. For local development, you must expose n8n via a public tunnel.

**Using ngrok:**

```bash
# Install and authenticate (free account required)
ngrok http 5678

# Copy the forwarding URL (e.g., https://abc123.ngrok-free.app)
```

**Using localtunnel (no signup):**

```bash
npx localtunnel --port 5678
```

After obtaining your public URL:

1. Add to `.env`:
   ```
   WEBHOOK_URL=https://your-tunnel-url.ngrok-free.app
   ```

2. Restart containers:
   ```bash
   docker compose down && docker compose up -d
   ```

3. In n8n, toggle the Telegram Agent workflow inactive then active to re-register the webhook.

> **Note:** Tunnel URLs change on restart. For persistent webhooks, deploy to a server with a static public IP or use a paid tunnel plan with reserved domains.

## LLM Mock Mode

To test workflows without burning OpenAI credits:

1. Open n8n UI (`http://localhost:5678`)
2. Edit workflow: "Summarize Articles"
3. Find node: "Check Mock Mode"
4. Change `MOCK_MODE_ENABLED = false` to `true`
5. Save workflow

When enabled, generates `[MOCK]` summaries instead of calling OpenAI.

## Managing Email Recipients

Recipients are stored in database and managed via API:

```bash
# Add recipient
curl -X POST http://localhost:3000/api/recipients \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "name": "John Doe"}'

# List recipients
curl http://localhost:3000/api/recipients \
  -H "X-API-Key: your_api_key"

# Disable recipient (without deletion)
curl -X PATCH http://localhost:3000/api/recipients/{id}/toggle \
  -H "X-API-Key: your_api_key"
```

Distribution lists are supported - add multiple recipients, all enabled recipients receive digests.

## Initial RSS Feeds

`sql/init.sql` includes 50+ curated feeds across categories:

- German: Tagesschau, Spiegel, FAZ, SZ, Handelsblatt, Heise
- English: BBC, CNN, Reuters, TechCrunch, Ars Technica, Hacker News

Feeds are inserted on first database initialization. Categories: general, business, tech, politics, science.

## Running Tests

API tests run inside Docker against the live database:

```bash
# Run all tests
docker compose exec api python -m pytest tests/ -v

# Run specific test file
docker compose exec api python -m pytest tests/test_articles.py -v

# Run with coverage
docker compose exec api python -m pytest tests/ -v --cov=. --cov-report=term-missing
```

Tests use unique identifiers and clean up after themselves, so they're safe to run against a development database.

## API Documentation

**Interactive Swagger UI:**  
`http://localhost:3000/docs`

**ReDoc:**  
`http://localhost:3000/redoc`

**OpenAPI Spec:**  
`http://localhost:3000/openapi.yaml`

### Regenerating OpenAPI Spec

```bash
./scripts/update-openapi.sh
```

Script fetches latest spec from running API and updates `openapi.yaml`.

### Using the OpenAPI Spec

The `openapi.yaml` file follows the [OpenAPI 3.0 Specification](https://spec.openapis.org/oas/v3.0.3), an industry standard for describing REST APIs. Most HTTP clients and API testing tools can import it directly:

| Tool | Import Method |
|------|---------------|
| **Postman** | Import → File → Select `openapi.yaml` |
| **Insomnia** | Create → Import from File |
| **Bruno** | Collection → Import Collection → OpenAPI |
| **Hoppscotch** | Import → OpenAPI |
| **Thunder Client** (VS Code) | Collections → Import → OpenAPI |
| **HTTPie Desktop** | Import → OpenAPI |
| **Swagger UI** | Already served at `/docs` when API is running |

#### Postman Setup

1. Import `openapi.yaml` as described above
2. Create environment with variable `API_KEY` = your key
3. In collection, add pre-request script or set header manually:
   ```
   X-API-Key: {{API_KEY}}
   ```

Alternatively, use built-in API Key auth in collection settings.

> **Note:** OpenAPI is widely adopted—if your preferred tool isn't listed, check its docs for "OpenAPI" or "Swagger" import. The terms are often used interchangeably (Swagger was renamed to OpenAPI in 2016).
