# Session Summary: 2026-02-13
## Topic: Recipient Management & Workflow Improvements

---

## Overview

Major session focused on implementing enterprise-grade email recipient management, fixing LLM rate limiting issues, and improving workflow modularity.

---

## Key Decisions

### 1. Database-backed Recipient Management
**Decision:** Store email recipients in PostgreSQL instead of environment variables.

**Rationale:**
- Environment variables are not suitable for managing multiple recipients
- API-based management allows programmatic control (HR integrations, etc.)
- Supports both individual emails and distribution lists
- Audit trail with timestamps
- Enable/disable without deletion

**Implementation:**
- New `digest_recipients` table
- Full CRUD API: `POST/GET/PUT/DELETE /api/recipients`
- Toggle endpoint: `PATCH /api/recipients/{id}/toggle`
- Workflow queries recipients from DB before sending

### 2. LLM Mock Mode Toggle
**Decision:** Use hardcoded toggle in workflow code instead of environment variables.

**Rationale:**
- n8n heavily restricts env var access in expressions and code nodes
- Tried `$env.VAR`, `process.env.VAR`, `N8N_ALLOWED_EXPRESSION_ENV_VARS` - all failed
- Hardcoded toggle in Code node is reliable and easy to change

**Implementation:**
- `MOCK_MODE_ENABLED = true/false` in "Check Mock Mode" Code node
- When true: generates fake `[MOCK]` summaries without calling OpenAI
- Useful for testing workflows without burning API credits

### 3. Limit Parameter as Query Param
**Decision:** Move `limit` from request body to query parameter for summarize endpoint.

**Rationale:**
- More intuitive for simple parameters
- Easier to use in Postman/curl
- `article_ids` stays in body (can be large array)

**Implementation:**
- `POST /api/actions/summarize?limit=50`
- `limit=0` means "process all"
- Default: 10 articles
- Max: 1000 articles

---

## Problems Solved

### 1. OpenAI Rate Limits Without Completions
**Problem:** User hitting rate limits on new OpenAI account without receiving any completions.

**Cause:** New/free-tier accounts have very low RPM limits (3-20). The scrape workflow pulled multiple articles, triggering parallel summarization requests.

**Solution:** Implemented mock mode to bypass LLM during testing.

### 2. n8n Environment Variable Access Denied
**Problem:** `$env.LLM_MOCK_MODE` threw "access to env vars denied" error.

**Attempted Solutions:**
1. `N8N_BLOCK_ENV_ACCESS_IN_NODE: "false"` - didn't work
2. `N8N_ALLOWED_EXPRESSION_ENV_VARS: "LLM_MOCK_MODE"` - didn't work
3. `process.env.VAR` in Code node - "process is not defined"

**Final Solution:** Hardcoded toggle directly in workflow Code node. Not ideal but reliable.

### 3. Split Recipients Node Error
**Problem:** "A 'json' property isn't an object [item 0]" when splitting recipients.

**Cause:** Code node was in `runOnceForEachItem` mode but trying to return multiple items with `.map()`.

**Solution:** Changed to `runOnceForAllItems` mode and updated code to use `$input.first().json`.

### 4. Gmail SMTP Authentication
**Problem:** "Invalid login: 535-5.7.8 Username and Password not accepted"

**Cause:** Gmail requires App Passwords, not regular passwords.

**Solution:** 
1. Enable 2FA on Google account
2. Generate App Password at myaccount.google.com/apppasswords
3. Use 16-character password without spaces

---

## Implementation Details

### New Database Table
```sql
CREATE TABLE digest_recipients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(200),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### New API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/recipients | Add recipient |
| GET | /api/recipients | List all |
| GET | /api/recipients/{id} | Get one |
| PUT | /api/recipients/{id} | Update |
| DELETE | /api/recipients/{id} | Remove |
| PATCH | /api/recipients/{id}/toggle | Enable/disable |

### Updated Stats Response
```json
{
  "total_feeds": 3,
  "enabled_feeds": 3,
  "total_articles": 71,
  "processed_articles": 71,
  "sent_articles": 0,
  "total_recipients": 1,
  "enabled_recipients": 1
}
```

### Workflow Changes
- **send-digest.json:** Queries `digest_recipients` table, loops through enabled recipients
- **summarize-articles.json:** Added "Set Parameters" node for dynamic limit, mock mode toggle

---

## Files Changed

### New Files
- `api/routers/recipients.py` - Recipients CRUD endpoints
- `api/tests/test_recipients.py` - Contract tests
- `env.example` - Environment variable documentation

### Modified Files
- `sql/init.sql` - Added digest_recipients table
- `api/database.py` - Added recipient CRUD functions
- `api/models.py` - Added Recipient models, updated StatsResponse
- `api/main.py` - Included recipients router
- `api/routers/actions.py` - Limit as query param
- `docker-compose.yml` - Mock mode config, removed SMTP_FROM/TO
- `workflows/summarize-articles.json` - Mock mode, dynamic limit
- `workflows/send-digest.json` - DB-based recipients

---

## Commits Made

```
9a565e7 docs: update OpenAPI spec and readme notes
9ae2b5e chore(config): update docker-compose and env configuration
92ffad7 feat(api): add limit query param to summarize endpoint
7f8f113 feat(api): add recipient management for email digests
c180330 feat(workflows): split monolithic workflow into independent modules
```

---

## Known Limitations

1. **Mock Mode Toggle:** Must be changed in n8n UI or workflow JSON, not via env var
2. **n8n Env Vars:** n8n's security model heavily restricts expression access to env vars
3. **Email Sending:** Requires manual SMTP credential setup in n8n UI after first container creation

---

## Next Steps

1. Test full email digest flow with real SMTP credentials
2. Consider adding recipient categories/tags for targeted digests
3. Add unsubscribe functionality
4. Consider webhook for recipient self-registration

---

## Related Files
- `workflows/send-digest.json`
- `api/routers/recipients.py`
- `sql/init.sql`
- `env.example`
