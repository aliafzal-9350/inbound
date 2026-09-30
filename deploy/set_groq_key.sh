#!/usr/bin/env bash
# Rotate the Groq API key on the server:   bash deploy/set_groq_key.sh gsk_NEWKEY
# (Alternatively use the dashboard: Settings > API keys > Groq - same effect, no SSH needed.)
# Verifies the key with Groq, writes it to .env, and updates the live value in Redis so both
# backend workers switch within ~30 seconds without a restart.
set -euo pipefail
cd "$(dirname "$0")/.."

KEY="${1:-}"
if [[ ! "$KEY" =~ ^gsk_[A-Za-z0-9]{20,}$ ]]; then
    echo "Usage: bash deploy/set_groq_key.sh gsk_...   (a Groq key starts with gsk_)"; exit 1
fi

status=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $KEY" https://api.groq.com/openai/v1/models)
if [ "$status" != "200" ]; then
    echo "Groq rejected this key (HTTP $status). Nothing changed."; exit 1
fi

if grep -q '^GROQ_API_KEY=' .env; then
    sed -i "s|^GROQ_API_KEY=.*|GROQ_API_KEY=$KEY|" .env
else
    printf '\nGROQ_API_KEY=%s\n' "$KEY" >> .env
fi
docker compose exec -T redis redis-cli SET config:GROQ_API_KEY "$KEY" >/dev/null
echo "Groq key updated (…${KEY: -4}). The agent uses it within 30 seconds."
