# News AI Agent - MVP Setup Guide

Automatisierter News-Aggregator mit KI-Zusammenfassungen und täglichem Email-Digest.

## 🎯 Features

- **RSS Feed Ingestion**: Automatisches Abrufen von News aus mehreren RSS-Feeds (alle 15 Minuten)
- **Deduplizierung**: Intelligente Erkennung und Filterung doppelter Artikel
- **KI-Zusammenfassungen**: Automatische Generierung von Kurz- und Langzusammenfassungen via OpenAI
- **Täglicher Digest**: Schön formatierte HTML-Email mit allen neuen Artikeln (täglich um 8:00 Uhr)
- **Persistente Speicherung**: PostgreSQL-Datenbank für Article-Historie

## 📋 Voraussetzungen

- Docker & Docker Compose installiert
- OpenAI API Key ([hier erhalten](https://platform.openai.com/api-keys))
- SMTP Email-Account (z.B. Gmail mit App-Passwort)

## 🚀 Installation & Setup

### 1. Environment Variables einrichten

Kopiere die `env.example` Datei und benenne sie in `.env` um:

```bash
cp env.example .env
```

Bearbeite die `.env` Datei und füge deine Credentials ein:

```bash
# PostgreSQL (kannst du so lassen für lokales Testing)
POSTGRES_USER=n8n
POSTGRES_PASSWORD=dein_sicheres_passwort
POSTGRES_DB=news_agent

# n8n Web-Interface Zugang
N8N_USER=admin
N8N_PASSWORD=dein_n8n_passwort

# OpenAI API Key (ERFORDERLICH!)
OPENAI_API_KEY=sk-dein-openai-key-hier

# Email SMTP (ERFORDERLICH für Email-Digest)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=deine-email@gmail.com
SMTP_PASSWORD=dein-app-passwort
SMTP_FROM=News Agent <deine-email@gmail.com>

# Empfänger Email
RECIPIENT_EMAIL=deine-email@gmail.com

# FastAPI Configuration
API_KEY=dev-api-key-change-in-production
SECRET_KEY=dev-secret-key-32-chars-minimum
```

**Wichtig für Gmail:**
- Aktiviere 2-Faktor-Authentifizierung
- Erstelle ein [App-Passwort](https://myaccount.google.com/apppasswords) (nicht dein normales Passwort!)

### 2. Container starten

```bash
docker-compose up -d
```

Die Container starten jetzt:
- **FastAPI**: http://localhost:3000 (API + Docs)
- **n8n**: http://localhost:5678
- **PostgreSQL**: localhost:5432

Prüfe den Status:
```bash
docker-compose ps
```

Logs ansehen:
```bash
docker-compose logs -f n8n
docker-compose logs -f postgres
```

### 3. n8n Dashboard öffnen & Owner Account erstellen

Öffne deinen Browser und gehe zu: **http://localhost:5678**

Beim ersten Start:
1. Erstelle deinen **Owner Account** (Email, Name, Passwort)
2. Die Workflows werden **automatisch importiert** ✨

### 4. Credentials einrichten

n8n benötigt Credentials für externe Services. Gehe zu **Settings → Credentials** und erstelle:

#### PostgreSQL Credentials
- Name: `PostgreSQL account`
- Host: `postgres`
- Database: `news_agent` (oder dein `POSTGRES_DB`)
- User: `n8n` (oder dein `POSTGRES_USER`)
- Password: dein `POSTGRES_PASSWORD`
- Port: `5432`

#### OpenAI Credentials
- Name: `OpenAI account`
- API Key: dein `OPENAI_API_KEY`

#### SMTP Credentials
- Name: `SMTP account`
- Host: `smtp.gmail.com` (oder dein `SMTP_HOST`)
- Port: `587`
- User: dein `SMTP_USER`
- Password: dein `SMTP_PASSWORD`
- Secure: `false` (für STARTTLS)

### 5. Workflows aktivieren

Der Hauptworkflow wurde **automatisch importiert** beim ersten Start! 🎉

Gehe zu **Workflows** und du siehst:
- **AI-news-agent** - Hauptworkflow (RSS Feed, Summarization, Email)

**Aktiviere den Workflow:**
1. Öffne den Workflow
2. Klicke auf den **"Active"** Toggle oben rechts (muss grün sein)
3. Prüfe, ob alle Nodes korrekt verbunden sind

**Wichtig:** Stelle sicher, dass der Workflow die richtigen Credentials verwendet (siehe Node-Settings).

**Hinweis:** Die REST API läuft jetzt als separater FastAPI-Service (nicht mehr als n8n Workflow).

## 🧪 Testing

### Test 1: Datenbank-Verbindung prüfen

```bash
docker exec -it news-agent-postgres psql -U n8n -d news_agent -c "SELECT * FROM articles;"
```

Du solltest mindestens einen Test-Artikel sehen.

### Test 2: RSS Ingestion manuell ausführen

1. Öffne Workflow **"01 - RSS Feed Ingestion"**
2. Klicke auf **"Execute Workflow"** (Play-Button oben rechts)
3. Warte 10-20 Sekunden
4. Du solltest grüne Checkmarks sehen und eine Meldung wie "Successfully ingested X new articles"

Prüfe die Datenbank:
```bash
docker exec -it news-agent-postgres psql -U n8n -d news_agent -c "SELECT title, source, processed FROM articles ORDER BY fetched_at DESC LIMIT 5;"
```

### Test 3: Summarization manuell ausführen

1. Öffne Workflow **"02 - Article Summarization"**
2. Klicke auf **"Execute Workflow"**
3. Warte (kann 20-60 Sekunden dauern, abhängig von der Anzahl der Artikel)
4. Prüfe Ergebnis: "Processed X articles (Y successful)"

Prüfe die Summaries in der Datenbank:
```bash
docker exec -it news-agent-postgres psql -U n8n -d news_agent -c "SELECT title, summary_short FROM articles WHERE processed = TRUE LIMIT 3;"
```

### Test 4: Email Digest manuell senden

1. Öffne Workflow **"03 - Daily Email Digest"**
2. Klicke auf **"Execute Workflow"**
3. Prüfe dein Email-Postfach!
4. Du solltest eine schön formatierte HTML-Email erhalten

## 📊 Workflow-Übersicht

```
┌─────────────────────────────────────────────────────────────┐
│                    AUTOMATISCHER ABLAUF                     │
└─────────────────────────────────────────────────────────────┘

   ⏰ Alle 15 Minuten
        │
        ▼
   ┌─────────────────┐
   │ RSS Ingestion   │  → Holt neue Artikel
   │ (Workflow 01)   │  → Prüft Duplikate
   └────────┬────────┘  → Speichert in DB
            │
            ▼
   ┌─────────────────┐
   │   PostgreSQL    │  → Artikel unprocessed
   │   (Database)    │
   └────────┬────────┘
            │
   ⏰ Alle 5 Minuten │
            │
            ▼
   ┌─────────────────┐
   │ Summarization   │  → Holt 10 unprocessed
   │ (Workflow 02)   │  → OpenAI erstellt Summaries
   └────────┬────────┘  → Markiert als processed
            │
            ▼
   ┌─────────────────┐
   │   PostgreSQL    │  → Artikel processed
   │   (Database)    │     aber unsent
   └────────┬────────┘
            │
   ⏰ Täglich 8:00   │
            │
            ▼
   ┌─────────────────┐
   │  Email Digest   │  → Sammelt alle unsent
   │ (Workflow 03)   │  → Generiert HTML
   └────────┬────────┘  → Sendet Email
            │           → Markiert als sent
            ▼
       📧 Dein Postfach
```

## 🔧 Konfiguration anpassen

### Weitere RSS Feeds hinzufügen

1. Öffne Workflow **"01 - RSS Feed Ingestion"**
2. Klicke auf das **"+"** Icon nach dem Schedule Trigger
3. Füge einen neuen **"RSS Feed Read"** Node hinzu
4. Gib die Feed-URL ein
5. Verbinde ihn mit dem **"Merge Feeds"** Node
6. Speichern!

**Beliebte News RSS Feeds:**
- TechCrunch: `https://feeds.feedburner.com/TechCrunch/`
- Hacker News: `https://hnrss.org/frontpage`
- Heise: `https://www.heise.de/rss/heise-atom.xml`
- Tagesschau: `https://www.tagesschau.de/xml/rss2/`
- The Verge: `https://www.theverge.com/rss/index.xml`

### Zeitplan ändern

**RSS Ingestion:**
- Standard: Alle 15 Minuten
- Ändern: Öffne Workflow → Schedule Trigger Node → "Rule" anpassen

**Summarization:**
- Standard: Alle 5 Minuten
- Ändern: Öffne Workflow → Schedule Trigger Node → "Rule" anpassen

**Email Digest:**
- Standard: Täglich um 8:00 Uhr
- Ändern: Öffne Workflow → Schedule Trigger Node → Cron Expression anpassen
- Beispiele:
  - `0 8 * * *` = Täglich 8:00
  - `0 18 * * *` = Täglich 18:00
  - `0 8 * * 1-5` = Werktags 8:00

### OpenAI Modell ändern

Im Workflow **"02 - Article Summarization"**:
- Öffne den **"OpenAI Summarize"** Node
- Model: `gpt-4o-mini` (günstig, schnell) oder `gpt-4o` (bessere Qualität, teurer)
- Temperature: `0.3` (konsistenter) bis `0.7` (kreativer)

## 🛑 Container stoppen/neustarten

```bash
# Stoppen
docker-compose down

# Neustarten
docker-compose up -d

# Neu bauen (bei Änderungen)
docker-compose down
docker-compose up -d --build

# Alles löschen (inkl. Daten!)
docker-compose down -v
```

## 🐛 Troubleshooting

### Problem: "Cannot connect to PostgreSQL"
```bash
# Prüfe ob Container läuft
docker-compose ps

# Prüfe Logs
docker-compose logs postgres

# Neustart
docker-compose restart postgres
```

### Problem: "OpenAI API Error"
- Prüfe ob API Key korrekt ist
- Prüfe OpenAI Account Balance: https://platform.openai.com/usage
- Teste mit curl:
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Problem: "Email wird nicht gesendet"
- Prüfe SMTP Credentials in n8n
- Für Gmail: Verwende **App-Passwort**, nicht normales Passwort
- Teste SMTP manuell:
```bash
docker exec -it news-agent-n8n sh
# Im Container:
telnet smtp.gmail.com 587
```

### Problem: "Workflows werden nicht automatisch ausgeführt"
- Prüfe ob Workflows **aktiviert** sind (Toggle oben rechts)
- Schedule Trigger muss grün sein
- Prüfe n8n Logs: `docker-compose logs n8n`

### Problem: "Zu viele Duplikate"
Die Deduplizierung basiert auf der **URL**. Wenn verschiedene Feeds leicht unterschiedliche URLs haben (z.B. mit Tracking-Parametern), werden sie als unterschiedlich erkannt.

**Lösung:** Erweitere die Deduplizierungs-Logik im Workflow 01.

## 🌐 REST API

Der News AI Agent bietet eine **production-ready REST API** mit FastAPI, um programmatisch mit dem System zu interagieren!

### Quick Start

1. **API startet automatisch!** ✨
   - Starte Container: `docker compose up -d`
   - API läuft auf: http://localhost:3000
   - **Automatische Dokumentation**: http://localhost:3000/docs

2. **API Docs ansehen:**
   - **Swagger UI**: http://localhost:3000/docs (interaktiv, "Try it out" Buttons)
   - **ReDoc**: http://localhost:3000/redoc (alternative Dokumentation)
   - **OpenAPI JSON**: http://localhost:3000/openapi.json (für Postman/Insomnia)
   - **OpenAPI YAML**: http://localhost:3000/openapi.yaml (für Postman/Insomnia)

3. **Authentifizierung:**
   - Die meisten Endpoints benötigen einen API Key im Header: `X-API-Key`
   - Standard Dev Key: `dev-api-key-change-in-production` (in `.env` ändern!)
   - `/api/health` ist öffentlich (keine Auth nötig)

### API Endpoints

#### Feed Management
| Method | Endpoint | Beschreibung | Auth |
|--------|----------|-------------|------|
| POST | `/api/feeds` | RSS Feed erstellen | ✅ |
| GET | `/api/feeds` | Alle Feeds auflisten | ✅ |
| GET | `/api/feeds/{id}` | Feed abrufen | ✅ |
| PUT | `/api/feeds/{id}` | Feed aktualisieren | ✅ |
| DELETE | `/api/feeds/{id}` | Feed löschen | ✅ |
| PATCH | `/api/feeds/{id}/toggle` | Feed aktivieren/deaktivieren | ✅ |

#### Article Management
| Method | Endpoint | Beschreibung | Auth |
|--------|----------|-------------|------|
| GET | `/api/articles` | Artikel auflisten (Filter: source, processed, sent, limit, offset) | ✅ |
| GET | `/api/articles/{id}` | Artikel abrufen | ✅ |
| DELETE | `/api/articles/{id}` | Artikel löschen | ✅ |

#### Workflow Actions
| Method | Endpoint | Beschreibung | Auth |
|--------|----------|-------------|------|
| POST | `/api/actions/scrape` | RSS Scraping triggern | ✅ |
| POST | `/api/actions/summarize` | AI Summarization triggern | ✅ |
| POST | `/api/actions/send-digest` | Email Digest senden | ✅ |

#### System
| Method | Endpoint | Beschreibung | Auth |
|--------|----------|-------------|------|
| GET | `/api/health` | Health Check | ❌ |
| GET | `/api/stats` | System-Statistiken | ✅ |

**Base URL:** `http://localhost:3000`

### Beispiele

```bash
# Health Check (keine Auth)
curl http://localhost:3000/api/health

# Feeds auflisten
curl -H "X-API-Key: dev-api-key-change-in-production" \
  http://localhost:3000/api/feeds

# Neuen Feed erstellen
curl -X POST \
  -H "X-API-Key: dev-api-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{"name":"TechCrunch","url":"https://feeds.feedburner.com/TechCrunch/","language":"en","category":"tech"}' \
  http://localhost:3000/api/feeds

# Unverarbeitete Artikel abrufen
curl -H "X-API-Key: dev-api-key-change-in-production" \
  "http://localhost:3000/api/articles?processed=false&limit=10"

# RSS Scraping triggern
curl -X POST \
  -H "X-API-Key: dev-api-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{}' \
  http://localhost:3000/api/actions/scrape

# Statistiken abrufen
curl -H "X-API-Key: dev-api-key-change-in-production" \
  http://localhost:3000/api/stats
```

### Postman/Insomnia Import

Die OpenAPI-Spezifikation kann in **JSON** oder **YAML** Format direkt importiert werden:

```bash
# Option 1: OpenAPI YAML herunterladen (empfohlen)
curl http://localhost:3000/openapi.yaml > openapi.yaml

# Option 2: OpenAPI JSON herunterladen
curl http://localhost:3000/openapi.json > openapi.json

# In Postman/Insomnia importieren
# File → Import → openapi.yaml (oder openapi.json)
```

**Tipp:** Die OpenAPI-Spec wird **automatisch generiert** von FastAPI. Änderungen am Code sind sofort in der Spec sichtbar!

### Python Beispiel

```python
import requests

BASE_URL = "http://localhost:3000"
API_KEY = "dev-api-key-change-in-production"

headers = {"X-API-Key": API_KEY}

# Feeds abrufen
feeds = requests.get(f"{BASE_URL}/api/feeds", headers=headers).json()

# Neuen Feed erstellen
new_feed = requests.post(
    f"{BASE_URL}/api/feeds",
    headers=headers,
    json={
        "name": "Hacker News",
        "url": "https://hnrss.org/frontpage",
        "language": "en",
        "category": "tech"
    }
).json()

# Scraping triggern
requests.post(f"{BASE_URL}/api/actions/scrape", headers=headers)
```

## 📈 Nächste Schritte (Phase 2)

- [ ] Keyword-Filtering hinzufügen
- [ ] Mehrere Output-Kanäle (Slack, Teams)
- [ ] Web-Dashboard für Artikel-Verwaltung
- [ ] Sentiment-Analyse
- [ ] Updater-Funktion (Quellen per Chat hinzufügen)
- [ ] Redis für Caching und Rate Limiting

## 📝 Lizenz

Dieses Projekt ist ein MVP für persönliche/interne Nutzung.

---

**Viel Erfolg! 🚀**

Bei Fragen: Prüfe die Logs und die [n8n Dokumentation](https://docs.n8n.io/).
