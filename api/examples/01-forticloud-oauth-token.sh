#!/usr/bin/env bash
# Mint a FortiCloud OAuth bearer token for any portal.
# Usage:  ./01-forticloud-oauth-token.sh fortiztp        # or: fortisase | assetmanagement | flexvm
# Requires: FORTI_API_ID, FORTI_API_SECRET in the environment (a FortiCloud IAM API user).
# Daniel: run this yourself — it reads credentials.
set -euo pipefail

CLIENT_ID="${1:-fortiztp}"
AUTH_URL="https://customerapiauth.fortinet.com/api/v1/oauth/token/"

: "${FORTI_API_ID:?set FORTI_API_ID (FortiCloud IAM API user id)}"
: "${FORTI_API_SECRET:?set FORTI_API_SECRET}"

resp="$(curl -fsS -X POST "$AUTH_URL" \
  -H 'Content-Type: application/json' \
  -d @- <<JSON
{
  "username":   "${FORTI_API_ID}",
  "password":   "${FORTI_API_SECRET}",
  "client_id":  "${CLIENT_ID}",
  "grant_type": "password"
}
JSON
)"

# Extract token without printing the secret. jq if present, else grep.
if command -v jq >/dev/null 2>&1; then
  echo "$resp" | jq -r '"status=\(.status)  expires_in=\(.expires_in)"'
  TOKEN="$(echo "$resp" | jq -r '.access_token')"
else
  TOKEN="$(echo "$resp" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)"
fi

# Export for the next call; DON'T echo the token to logs in shared sessions.
export FORTI_TOKEN="$TOKEN"
echo "Token acquired for client_id=${CLIENT_ID} (length ${#TOKEN}). Use:  Authorization: Bearer \$FORTI_TOKEN"

# Example use (FortiZTP inventory):
#   curl -fsS https://fortiztp.forticloud.com/public/api/v2/devices \
#     -H "Authorization: Bearer $FORTI_TOKEN" | jq .
