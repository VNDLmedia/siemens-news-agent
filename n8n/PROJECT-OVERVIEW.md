# News AI Agent - Project Overview

## 📦 Was wurde gebaut?

Ein vollautomatischer News-Aggregator mit KI-Zusammenfassungen, der:
- RSS Feeds abruft und parsed
- Artikel dedupliziert
- Mit OpenAI zusammenfasst
- Täglich per Email versendet

## 📂 Projektstruktur

```
n8n/
├── docker-compose.yml          # Docker Setup (n8n + PostgreSQL)
├── env.example                 # Environment Variables Template
├── .gitignore                  # Git ignore für sensitive Daten
├── README.md                   # Ausführliche Setup-Anleitung
├── PROJECT-OVERVIEW.md         # Diese Datei
├── start.ps1                   # Windows Quick-Start Script
├── start.sh                    # Linux/Mac Quick-Start Script
│
├── sql/
│   └── init.sql                # Datenbank Schema & Initialisierung
│
└── workflows/
    ├── 01-rss-ingestion.json   # RSS Feed Abruf (alle 15 Min)
    ├── 02-summarization.json   # OpenAI Summarization (alle 5 Min)
    └── 03-email-digest.json    # Email Versand (täglich 8 Uhr)
```

## 🔄 System-Architektur

### Datenfluss

```
RSS Feeds (TechCrunch, Hacker News)
         ↓
    [Workflow 01: RSS Ingestion]
         ↓ (Deduplizierung)
    [PostgreSQL Database]
         ↓ (unprocessed = true)
    [Workflow 02: Summarization]
         ↓ (OpenAI GPT-4o-mini)
    [PostgreSQL Database]
         ↓ (processed = true, sent = false)
    [Workflow 03: Email Digest]
         ↓ (HTML Email)
    📧 Dein Postfach
```

### Komponenten

1. **n8n** (Port 5678)
   - Workflow-Engine
   - Web-Interface für Management
   - Führt alle 3 Workflows aus

2. **PostgreSQL** (Port 5432)
   - Speichert Artikel
   - Tracking: processed/sent Status
   - Deduplication via unique URL

3. **OpenAI API**
   - GPT-4o-mini für Summaries
   - 2 Formate: Kurz (150 chars) + Lang (Paragraph)

4. **SMTP Email**
   - Versendet HTML-formatierte Digests
   - Konfigurierbar (Gmail, Outlook, etc.)

## 🎯 Implementierte Features (aus requirements.pdf)

### ✅ Implementiert (MVP - Phase 1)

| # | Feature | Status |
|---|---------|--------|
| 1 | RSS-Feed Import | ✅ TechCrunch + Hacker News |
| 6 | Quellen-Verwaltung | ✅ In Workflow editierbar |
| 7 | Abruf-Intervall | ✅ 15 Minuten |
| 8 | Deduplizierung | ✅ Via URL-Check |
| 16 | Kurz-Summary | ✅ 2-3 Sätze |
| 17 | Ausführliche Summary | ✅ Paragraph |
| 23 | Multi-LLM Support | ✅ OpenAI (erweiterbar) |
| 27 | E-Mail Newsletter | ✅ HTML Format |
| 38 | Zeitplanung | ✅ Cron-basiert |
| 44 | n8n Workflows | ✅ 3 Workflows |
| 45 | Self-Hosted Option | ✅ Docker Compose |
| 47 | Datenbank | ✅ PostgreSQL |
| 48 | Logging & Monitoring | ✅ n8n built-in |

**13 von 83 Features implementiert (16%)**

### 🔜 Nächste Phase (Phase 2)

- Feature 9-10: Keyword-Filter
- Feature 11: Entity Recognition
- Feature 13: Sentiment-Analyse
- Feature 28-35: Weitere Output-Kanäle (Slack, Teams, Discord)
- Feature 49-56: Updater Input-Kanäle

### ❌ Außerhalb MVP-Scope

- Feature 42: Learning Loop (ML Training)
- Feature 75: Dynamic Workflow Updates
- Web Dashboard (Feature 43, 55)

## 🚀 Quick Start

### Windows
```powershell
cd n8n
.\start.ps1
```

### Linux/Mac
```bash
cd n8n
chmod +x start.sh
./start.sh
```

### Manuell
```bash
cd n8n
cp env.example .env
# Edit .env mit deinen Credentials
docker-compose up -d
# Öffne http://localhost:5678
```

## ⚙️ Konfiguration

### Erforderliche Credentials

1. **OpenAI API Key**
   - Hole dir einen Key: https://platform.openai.com/api-keys
   - Setze in `.env`: `OPENAI_API_KEY=sk-...`

2. **Email SMTP**
   - Gmail: App-Passwort erstellen
   - Setze in `.env`: SMTP_HOST, SMTP_USER, SMTP_PASSWORD

3. **n8n Credentials**
   - Nach Start: http://localhost:5678
   - Settings → Credentials
   - Erstelle: PostgreSQL, OpenAI, SMTP accounts

## 📊 Datenbank Schema

```sql
articles (
  id UUID PRIMARY KEY,
  url TEXT UNIQUE,              -- Für Deduplizierung
  title TEXT,
  content TEXT,
  source TEXT,
  published_at TIMESTAMP,
  fetched_at TIMESTAMP,
  summary_short TEXT,           -- OpenAI kurz
  summary_long TEXT,            -- OpenAI lang
  processed BOOLEAN,            -- Hat Summary?
  sent BOOLEAN,                 -- In Email gesendet?
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)
```

## 🧪 Testing-Strategie

1. **Datenbank-Test**: Prüfe init.sql wurde ausgeführt
2. **RSS-Test**: Manuell Workflow 01 ausführen
3. **OpenAI-Test**: Manuell Workflow 02 ausführen
4. **Email-Test**: Manuell Workflow 03 ausführen
5. **Automatik-Test**: 24h laufen lassen, prüfe tägliche Email

Siehe `README.md` für detaillierte Test-Anleitungen.

## 🔧 Maintenance

### Logs prüfen
```bash
docker-compose logs -f n8n
docker-compose logs -f postgres
```

### Datenbank Cleanup
```sql
-- Alte Artikel löschen (älter als 30 Tage)
DELETE FROM articles WHERE fetched_at < NOW() - INTERVAL '30 days';

-- Alle Artikel zurücksetzen (für Testing)
UPDATE articles SET sent = FALSE, processed = FALSE;
```

### Backup
```bash
# Datenbank Backup
docker exec news-agent-postgres pg_dump -U n8n news_agent > backup.sql

# Workflows exportieren (in n8n UI)
Workflows → ... → Export
```

## 📈 Kosten-Schätzung

**OpenAI (GPT-4o-mini):**
- Input: ~$0.15 / 1M Tokens
- Output: ~$0.60 / 1M Tokens

**Beispiel:**
- 100 Artikel/Tag
- ~500 Tokens pro Artikel (Input + Output)
- = 50.000 Tokens/Tag = 1.5M Tokens/Monat
- **≈ $0.50 - $1.00 / Monat**

**Hosting:**
- Self-Hosted (Docker): Kostenlos
- Server: ~$5-10/Monat (VPS)

**Total: ~$5-12 / Monat**

## 🛡️ Sicherheit

### Implementiert:
- ✅ Environment Variables für Secrets
- ✅ .gitignore für .env
- ✅ n8n Basic Auth
- ✅ PostgreSQL Passwort-Schutz

### TODO (Production):
- [ ] HTTPS/TLS für n8n
- [ ] Firewall-Regeln
- [ ] PostgreSQL SSL
- [ ] Rate Limiting
- [ ] Backup-Strategie

## 📞 Support & Troubleshooting

Siehe `README.md` → Troubleshooting Section

Häufige Probleme:
- PostgreSQL Connection → Prüfe Container Status
- OpenAI Errors → Prüfe API Key & Balance
- Email nicht gesendet → SMTP Credentials prüfen
- Workflows nicht automatisch → Aktivieren nicht vergessen!

## 🎓 Lessons Learned

### Was funktioniert gut in n8n:
✅ RSS Feed Parsing
✅ Database Operations
✅ LLM Integration
✅ Email Sending
✅ Scheduling

### Was schwierig ist:
⚠️ Complex State Management
⚠️ Dynamic Workflow Updates
⚠️ Advanced NLP (besser: externe Service)
⚠️ UI Building (n8n ist kein Frontend-Tool)

### Empfehlungen:
- **Für MVP:** n8n ist perfekt! 🎯
- **Für Scale:** Überlege Hybrid (n8n + Python API)
- **Für UI:** Separates Frontend (React + n8n Webhooks)

## 🗺️ Roadmap

### Phase 1 (✅ Completed)
- [x] Docker Setup
- [x] RSS Ingestion
- [x] OpenAI Summarization
- [x] Email Digest
- [x] PostgreSQL Storage

### Phase 2 (Next Steps)
- [ ] Keyword Filtering
- [ ] Slack Integration
- [ ] More RSS Sources
- [ ] Sentiment Analysis
- [ ] Web Dashboard (React)

### Phase 3 (Future)
- [ ] Updater Function
- [ ] Multi-LLM Fallback
- [ ] Twitter/X Integration
- [ ] Analytics Dashboard

---

**Status:** 🟢 Production Ready (MVP)
**Maintainer:** Klaus
**Last Updated:** 2026-02-09
