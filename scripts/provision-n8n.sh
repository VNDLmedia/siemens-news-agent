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

# =====================================================
# Step 1: Generate credentials from environment
# =====================================================
echo ""
echo "[1/5] Generating credentials from environment..."
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
echo "  ✓ Postgres credential"

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
    echo "  ✓ OpenAI credential"
else
    echo "  ⊘ OpenAI credential (OPENAI_API_KEY not set)"
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
    echo "  ✓ SMTP credential"
else
    echo "  ⊘ SMTP credential (SMTP_HOST not set)"
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
    echo "  ✓ Telegram credential"
else
    echo "  ⊘ Telegram credential (TELEGRAM_ACCESS_TOKEN not set)"
fi

# =====================================================
# Step 2: Import credentials (must happen before workflows)
# =====================================================
echo ""
echo "[2/5] Importing credentials..."
n8n import:credentials --separate --input=/tmp/creds/
rm -rf /tmp/creds
echo "Credentials imported!"

# =====================================================
# Step 3: Prepare workflows with correct credential IDs
# =====================================================
echo ""
echo "[3/5] Preparing workflows with credential mapping..."
mkdir -p /tmp/workflows

# Copy all workflow files
cp /workflows/*.json /tmp/workflows/ 2>/dev/null || true

# Rewrite credential references in all workflow files
# Maps any credential ID to our provisioned credential IDs based on type
for wf in /tmp/workflows/*.json; do
    [ -f "$wf" ] || continue
    
    echo "  Processing: $(basename "$wf")"
    
    # Use sed to replace credential IDs based on credential type
    # Pattern: "credType": { "id": "anything", "name": "anything" }
    # Replace with our known credential IDs
    
    # OpenAI credentials -> news-agent-openai
    sed -i 's/"openAiApi"[[:space:]]*:[[:space:]]*{[[:space:]]*"id"[[:space:]]*:[[:space:]]*"[^"]*"/"openAiApi": { "id": "news-agent-openai"/g' "$wf"
    
    # Postgres credentials -> news-agent-postgres  
    sed -i 's/"postgres"[[:space:]]*:[[:space:]]*{[[:space:]]*"id"[[:space:]]*:[[:space:]]*"[^"]*"/"postgres": { "id": "news-agent-postgres"/g' "$wf"
    
    # SMTP credentials -> news-agent-smtp
    sed -i 's/"smtp"[[:space:]]*:[[:space:]]*{[[:space:]]*"id"[[:space:]]*:[[:space:]]*"[^"]*"/"smtp": { "id": "news-agent-smtp"/g' "$wf"
    
    # Telegram credentials -> news-agent-telegram
    sed -i 's/"telegramApi"[[:space:]]*:[[:space:]]*{[[:space:]]*"id"[[:space:]]*:[[:space:]]*"[^"]*"/"telegramApi": { "id": "news-agent-telegram"/g' "$wf"
done

echo "Credential mappings applied!"

# =====================================================
# Step 4: Import workflows
# =====================================================
echo ""
echo "[4/5] Importing workflows..."
n8n import:workflow --separate --input=/tmp/workflows/
rm -rf /tmp/workflows
echo "Workflows imported!"

# =====================================================
# Step 5: Activate workflows
# =====================================================
echo ""
echo "[5/5] Activating workflows..."
for wfid in $(n8n list:workflow 2>/dev/null | cut -d'|' -f1); do
    echo "  Activating: $wfid"
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
