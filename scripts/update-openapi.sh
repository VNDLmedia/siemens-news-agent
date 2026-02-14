#!/bin/bash
#
# Update openapi.yaml from running API
#
# Usage: ./scripts/update-openapi.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
API_URL="${API_URL:-http://localhost:3000}"
OUTPUT_FILE="$PROJECT_ROOT/openapi.yaml"

echo "📄 Updating OpenAPI specification..."
echo "   Source: $API_URL/openapi.yaml"
echo "   Target: $OUTPUT_FILE"

# Check if API is reachable
if ! curl -s --connect-timeout 5 "$API_URL/api/health" > /dev/null 2>&1; then
    echo "❌ Error: API not reachable at $API_URL"
    echo "   Make sure the API container is running: docker compose up -d api"
    exit 1
fi

# Fetch and save OpenAPI spec
if curl -s "$API_URL/openapi.yaml" -o "$OUTPUT_FILE"; then
    # Verify it's valid YAML (basic check)
    if head -1 "$OUTPUT_FILE" | grep -q "openapi:"; then
        ENDPOINTS=$(grep -c "^  /api" "$OUTPUT_FILE" || echo "0")
        echo "✅ OpenAPI spec updated successfully!"
        echo "   Endpoints found: $ENDPOINTS"
    else
        echo "❌ Error: Downloaded file doesn't look like a valid OpenAPI spec"
        exit 1
    fi
else
    echo "❌ Error: Failed to download OpenAPI spec"
    exit 1
fi
