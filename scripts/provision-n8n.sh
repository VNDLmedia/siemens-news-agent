#!/bin/sh
# =====================================================
# n8n Provisioning Script
# Automatically imports workflows and credentials
# on first container startup
# =====================================================

set -e

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
sleep 5

# Step 1: Import workflows
echo ""
echo "[1/4] Importing workflows..."
n8n import:workflow --separate --input=/workflows/
echo "Workflows imported!"

# Step 2: Generate credentials from environment
echo ""
echo "[2/4] Generating credentials from environment..."
mkdir -p /tmp/creds

# Postgres credential (always created)
cat > /tmp/creds/postgres.json << EOF
{
  "id": "news-agent-postgres",
  "name": "News Agent DB",
  "type": "postgres",
  "data": {
    "host": "postgres",
    "port": 5432,
    "database": "${CRED_POSTGRES_DB:-news_agent}",
    "user": "${CRED_POSTGRES_USER:-n8n}",
    "password": "${CRED_POSTGRES_PASSWORD:-n8n_password}",
    "ssl": "disable"
  }
}
EOF
echo "Generated: Postgres credential"

# OpenAI credential (only if API key provided)
if [ -n "$OPENAI_API_KEY" ]; then
    cat > /tmp/creds/openai.json << EOF
{
  "id": "news-agent-openai",
  "name": "OpenAI API",
  "type": "openAiApi",
  "data": {
    "apiKey": "${OPENAI_API_KEY}"
  }
}
EOF
    echo "Generated: OpenAI credential"
else
    echo "Skipped: OpenAI credential (OPENAI_API_KEY not set)"
fi

# SMTP credential (only if host provided)
if [ -n "$SMTP_HOST" ]; then
    cat > /tmp/creds/smtp.json << EOF
{
  "id": "news-agent-smtp",
  "name": "Email SMTP",
  "type": "smtp",
  "data": {
    "host": "${SMTP_HOST}",
    "port": ${SMTP_PORT:-587},
    "user": "${SMTP_USER}",
    "password": "${SMTP_PASSWORD}",
    "secure": false
  }
}
EOF
    echo "Generated: SMTP credential"
else
    echo "Skipped: SMTP credential (SMTP_HOST not set)"
fi

# Telegram credential (only if access token provided)
if [ -n "$TELEGRAM_ACCESS_TOKEN" ]; then
    cat > /tmp/creds/telegram.json << EOF
{
  "id": "news-agent-telegram",
  "name": "Telegram Bot",
  "type": "telegramApi",
  "data": {
    "accessToken": "${TELEGRAM_ACCESS_TOKEN}"
  }
}
EOF
    echo "Generated: Telegram credential"
else
    echo "Skipped: Telegram credential (TELEGRAM_ACCESS_TOKEN not set)"
fi

# Step 3: Import credentials
echo ""
echo "[3/4] Importing credentials..."
n8n import:credentials --separate --input=/tmp/creds/

# Secure cleanup
rm -rf /tmp/creds
echo "Credentials imported and temp files cleaned!"

# Step 4: Activate workflows
echo ""
echo "[4/4] Activating workflows..."
for wfid in $(n8n list:workflow 2>/dev/null | cut -d'|' -f1); do
    echo "Activating workflow: $wfid"
    n8n update:workflow --id="$wfid" --active=true 2>/dev/null || true
done

# Mark as provisioned
touch "$PROVISION_MARKER"

echo ""
echo "========================================"
echo "Provisioning complete!"
echo "========================================"

# Start n8n
exec n8n start
