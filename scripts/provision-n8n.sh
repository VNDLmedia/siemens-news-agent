#!/bin/sh
# =====================================================
# n8n Provisioning Script
# Automatically imports workflows and credentials
# on first container startup
# =====================================================

# Don't use set -e - we want n8n to start even if provisioning has issues
PROVISION_MARKER="/home/node/.n8n/.provisioned"

# Check if already provisioned
if [ -f "$PROVISION_MARKER" ]; then
    echo "Already provisioned - skipping"
    exec n8n start
fi

echo "========================================"
echo "First startup - provisioning n8n..."
echo "========================================"

# Wait for database to be ready
echo "Waiting for database..."
sleep 10

# =====================================================
# Step 1: Generate credentials from environment
# =====================================================
echo ""
echo "[1/5] Generating credentials from environment..."
mkdir -p /tmp/creds

# Postgres credential (always created)
cat > /tmp/creds/postgres.json << 'EOFPG'
{
  "id": "news-agent-postgres",
  "name": "News Agent DB",
  "type": "postgres",
  "data": {
    "host": "postgres",
    "port": 5432,
    "database": "PLACEHOLDER_DB",
    "user": "PLACEHOLDER_USER",
    "password": "PLACEHOLDER_PASS",
    "ssl": "disable"
  }
}
EOFPG
# Replace placeholders with actual values
sed -i "s/PLACEHOLDER_DB/${CRED_POSTGRES_DB:-news_agent}/g" /tmp/creds/postgres.json
sed -i "s/PLACEHOLDER_USER/${CRED_POSTGRES_USER:-n8n}/g" /tmp/creds/postgres.json
sed -i "s/PLACEHOLDER_PASS/${CRED_POSTGRES_PASSWORD:-n8n_password}/g" /tmp/creds/postgres.json
echo "  + Postgres credential"

# OpenAI credential (only if API key provided)
if [ -n "$OPENAI_API_KEY" ]; then
    cat > /tmp/creds/openai.json << 'EOFAI'
{
  "id": "news-agent-openai",
  "name": "OpenAI API",
  "type": "openAiApi",
  "data": {
    "apiKey": "PLACEHOLDER_KEY"
  }
}
EOFAI
    sed -i "s/PLACEHOLDER_KEY/${OPENAI_API_KEY}/g" /tmp/creds/openai.json
    echo "  + OpenAI credential"
else
    echo "  - OpenAI credential (OPENAI_API_KEY not set)"
fi

# SMTP credential (only if host provided)
if [ -n "$SMTP_HOST" ]; then
    cat > /tmp/creds/smtp.json << 'EOFSMTP'
{
  "id": "news-agent-smtp",
  "name": "Email SMTP",
  "type": "smtp",
  "data": {
    "host": "PLACEHOLDER_HOST",
    "port": 587,
    "user": "PLACEHOLDER_USER",
    "password": "PLACEHOLDER_PASS",
    "secure": false
  }
}
EOFSMTP
    sed -i "s/PLACEHOLDER_HOST/${SMTP_HOST}/g" /tmp/creds/smtp.json
    sed -i "s/587/${SMTP_PORT:-587}/g" /tmp/creds/smtp.json
    sed -i "s/PLACEHOLDER_USER/${SMTP_USER}/g" /tmp/creds/smtp.json
    sed -i "s/PLACEHOLDER_PASS/${SMTP_PASSWORD}/g" /tmp/creds/smtp.json
    echo "  + SMTP credential"
else
    echo "  - SMTP credential (SMTP_HOST not set)"
fi

# Telegram credential (only if access token provided)
if [ -n "$TELEGRAM_ACCESS_TOKEN" ]; then
    cat > /tmp/creds/telegram.json << 'EOFTG'
{
  "id": "news-agent-telegram",
  "name": "Telegram Bot",
  "type": "telegramApi",
  "data": {
    "accessToken": "PLACEHOLDER_TOKEN"
  }
}
EOFTG
    sed -i "s/PLACEHOLDER_TOKEN/${TELEGRAM_ACCESS_TOKEN}/g" /tmp/creds/telegram.json
    echo "  + Telegram credential"
else
    echo "  - Telegram credential (TELEGRAM_ACCESS_TOKEN not set)"
fi

# =====================================================
# Step 2: Import credentials (must happen before workflows)
# =====================================================
echo ""
echo "[2/5] Importing credentials..."
if n8n import:credentials --separate --input=/tmp/creds/ 2>&1; then
    echo "Credentials imported!"
else
    echo "WARNING: Credential import had issues (continuing anyway)"
fi
rm -rf /tmp/creds

# =====================================================
# Step 3: Prepare workflows with correct credential IDs
# =====================================================
echo ""
echo "[3/5] Preparing workflows with credential mapping..."
mkdir -p /tmp/workflows

# Copy all workflow files
if cp /workflows/*.json /tmp/workflows/ 2>/dev/null; then
    echo "Copied workflow files"
else
    echo "WARNING: No workflow files found or copy failed"
fi

# Rewrite credential references in all workflow files
# Uses simple patterns compatible with busybox sed
for wf in /tmp/workflows/*.json; do
    [ -f "$wf" ] || continue
    
    filename=$(basename "$wf")
    echo "  Processing: $filename"
    
    # Create temp file for sed operations
    # OpenAI credentials -> news-agent-openai
    sed 's/"openAiApi": {[^}]*"id": "[^"]*"/"openAiApi": { "id": "news-agent-openai"/g' "$wf" > "$wf.tmp" && mv "$wf.tmp" "$wf"
    
    # Postgres credentials -> news-agent-postgres  
    sed 's/"postgres": {[^}]*"id": "[^"]*"/"postgres": { "id": "news-agent-postgres"/g' "$wf" > "$wf.tmp" && mv "$wf.tmp" "$wf"
    
    # SMTP credentials -> news-agent-smtp
    sed 's/"smtp": {[^}]*"id": "[^"]*"/"smtp": { "id": "news-agent-smtp"/g' "$wf" > "$wf.tmp" && mv "$wf.tmp" "$wf"
    
    # Telegram credentials -> news-agent-telegram
    sed 's/"telegramApi": {[^}]*"id": "[^"]*"/"telegramApi": { "id": "news-agent-telegram"/g' "$wf" > "$wf.tmp" && mv "$wf.tmp" "$wf"
done

echo "Credential mappings applied!"

# =====================================================
# Step 4: Import workflows
# =====================================================
echo ""
echo "[4/5] Importing workflows..."
if n8n import:workflow --separate --input=/tmp/workflows/ 2>&1; then
    echo "Workflows imported!"
else
    echo "WARNING: Workflow import had issues (continuing anyway)"
fi
rm -rf /tmp/workflows

# =====================================================
# Step 5: Activate workflows (best effort)
# =====================================================
echo ""
echo "[5/5] Activating workflows..."
# Give n8n a moment to register workflows
sleep 2
workflow_list=$(n8n list:workflow 2>/dev/null || echo "")
if [ -n "$workflow_list" ]; then
    echo "$workflow_list" | while read -r line; do
        wfid=$(echo "$line" | cut -d'|' -f1 | tr -d ' ')
        if [ -n "$wfid" ] && [ "$wfid" != "ID" ]; then
            echo "  Activating: $wfid"
            n8n update:workflow --id="$wfid" --active=true 2>/dev/null || true
        fi
    done
else
    echo "  No workflows to activate (or list command failed)"
fi

# Mark as provisioned
touch "$PROVISION_MARKER"

echo ""
echo "========================================"
echo "Provisioning complete! Starting n8n..."
echo "========================================"

# Start n8n - this is critical, must always run
exec n8n start
