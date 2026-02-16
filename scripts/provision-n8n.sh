#!/bin/sh
# =====================================================
# n8n Provisioning Script
# Automatically imports workflows and credentials
# on first container startup
# =====================================================

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
echo "  + Postgres credential"

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
    echo "  + OpenAI credential"
else
    echo "  - OpenAI credential (OPENAI_API_KEY not set)"
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
    echo "  + SMTP credential"
else
    echo "  - SMTP credential (SMTP_HOST not set)"
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
    echo "  + Telegram credential"
else
    echo "  - Telegram credential (TELEGRAM_ACCESS_TOKEN not set)"
fi

# Internal API key credential for HTTP Request header auth
if [ -n "$API_KEY" ]; then
    cat > /tmp/creds/api-key-header.json << EOF
{
  "id": "news-agent-api-key",
  "name": "News Agent API Key",
  "type": "httpHeaderAuth",
  "data": {
    "name": "X-API-Key",
    "value": "${API_KEY}"
  }
}
EOF
    echo "  + API Header Auth credential"
else
    echo "  - API Header Auth credential (API_KEY not set)"
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

# Use Node.js to rewrite credential IDs in workflow JSON files
# This is reliable for multi-line JSON unlike sed
for wf in /tmp/workflows/*.json; do
    [ -f "$wf" ] || continue
    
    filename=$(basename "$wf")
    echo "  Processing: $filename"
    
    # Node.js script to replace credential IDs
    node -e "
const fs = require('fs');
const file = process.argv[1];
let content = fs.readFileSync(file, 'utf8');
let data;
try {
    data = JSON.parse(content);
} catch (e) {
    console.error('  Warning: Could not parse', file);
    process.exit(0);
}

// Credential ID mapping
const credMap = {
    'openAiApi': 'news-agent-openai',
    'postgres': 'news-agent-postgres',
    'smtp': 'news-agent-smtp',
    'telegramApi': 'news-agent-telegram',
    'httpHeaderAuth': 'news-agent-api-key'
};

// Recursively find and update credential references
function updateCredentials(obj) {
    if (!obj || typeof obj !== 'object') return;
    
    if (obj.credentials && typeof obj.credentials === 'object') {
        for (const [credType, credInfo] of Object.entries(obj.credentials)) {
            if (credMap[credType] && credInfo && typeof credInfo === 'object') {
                credInfo.id = credMap[credType];
            }
        }
    }
    
    // Recurse into arrays and objects
    for (const value of Object.values(obj)) {
        if (Array.isArray(value)) {
            value.forEach(updateCredentials);
        } else if (typeof value === 'object') {
            updateCredentials(value);
        }
    }
}

updateCredentials(data);
fs.writeFileSync(file, JSON.stringify(data, null, 2));
console.log('    Credentials remapped');
" "$wf"
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
sleep 2

workflow_list="$(n8n list:workflow 2>/tmp/n8n-list.err || true)"

if [ -z "$workflow_list" ]; then
    echo "  No workflows returned by n8n list:workflow"
    if [ -s /tmp/n8n-list.err ]; then
        echo "  n8n list:workflow stderr:"
        cat /tmp/n8n-list.err
    fi
    rm -f /tmp/n8n-list.err
else
    rm -f /tmp/n8n-list.err

    workflow_ids="$(printf '%s\n' "$workflow_list" | awk -F'|' '
    function trim(s) {
        gsub(/^[ \t]+|[ \t]+$/, "", s);
        return s;
    }
    {
        id = trim($1);
        lower = tolower(id);
        if (id == "" || lower == "id" || lower == "workflow id" || id ~ /^-+$/) next;
        if (id ~ /^[A-Za-z0-9_-]+$/) print id;
    }
    ' | sort -u)"

    if [ -z "$workflow_ids" ]; then
        echo "  No valid workflow IDs found to publish"
    else
        total=0
        published=0
        failed=0

        for wfid in $workflow_ids; do
            total=$((total + 1))
            echo "  Publishing: $wfid"
            if n8n update:workflow --id="$wfid" --active=true >/dev/null 2>&1; then
                published=$((published + 1))
            else
                failed=$((failed + 1))
                echo "    WARNING: Failed to publish workflow $wfid"
            fi
        done

        echo "  Publish result: $published/$total successful"
        if [ "$failed" -gt 0 ]; then
            echo "  WARNING: Some workflows could not be activated"
        fi
    fi
fi

# Mark as provisioned
touch "$PROVISION_MARKER"

echo ""
echo "========================================"
echo "Provisioning complete! Starting n8n..."
echo "========================================"

# Start n8n
exec n8n start
