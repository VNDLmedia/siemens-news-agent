# News AI Agent

## Quick Start

1. Create .env file

```bash
cp env.example .env
```

2. Edit .env with your credentials

3. Start containers

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

### Importing to Postman

1. Open Postman
2. Import → File → Select `openapi.yaml`
3. Create environment with variable `API_KEY` = your key
4. In collection, add pre-request script or set header manually:
   ```
   X-API-Key: {{API_KEY}}
   ```

Alternatively, use built-in API Key auth in collection settings.
