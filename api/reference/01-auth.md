# 01 — Auth: FortiCloud IAM + OAuth 2.0

> The single auth substrate for FortiZTP, FortiSASE, FortiFlex, Asset Management, SOCaaS — all of it. Confirmed against Fortinet docs (Tier 1) **and** our working local SDKs (Tier 2: `MSSP-SE-Tools/FortiZTP/fortiztp/client.py`). **Daniel runs credential commands himself.**

## Step 0 — create an API user (one-time, in the portal)
FortiCloud IAM → **Users > Add New > API User**. A **permission profile must exist first**. After creating, **Download Credentials** (resets the secret each time) → you get an **API ID (`apiId`)** and an **encrypted password**.
- **FortiZTP requires a Local IAM user (not ORG type).** For cross-tenant MSSP automation, ORG/IAM users federate across an Organization — but verify per-portal (corpus 02 §2.1).
- Grant the profile the portals you'll automate: **FortiZTP**, **Asset Management**, **FortiSASE**, (FortiFlex for MSSP).

## Step 1 — get a token
```
POST https://customerapiauth.fortinet.com/api/v1/oauth/token/
Content-Type: application/json

{
  "username":   "<apiId>",
  "password":   "<api-password>",
  "client_id":  "<portal>",          // see table
  "grant_type": "password"
}
```
Response:
```json
{ "access_token": "eyJ…", "token_type": "Bearer", "expires_in": 3600,
  "refresh_token": "…", "scope": "read write", "status": "success" }
```

## Step 2 — use it
```
Authorization: Bearer eyJ…
```

## Step 3 — refresh (don't re-password every call)
```json
{ "client_id": "<portal>", "grant_type": "refresh_token", "refresh_token": "…" }
```
House pattern (from our SDK): cache the token, refresh **60s before** `expires_in`, and retry once on a `401` with a fresh token.

## `client_id` per portal
| Portal | `client_id` | Confidence |
|---|---|---|
| FortiZTP | `fortiztp` | Confirmed (local SDK) |
| FortiFlex | `flexvm` | Confirmed (local tool) |
| SOCaaS | `socaas` | Confirmed (local SDK) |
| Asset Management | `assetmanagement` | Confirmed (docs) |
| IAM | `iam` | Confirmed (docs) |
| **FortiSASE** | **`fortisase`** *(assumed)* | **UNVERIFIED — confirm from incoming Swagger / FNDN / TF provider source** |

The same `apiId`/password mints a **different token per `client_id`**. An MSSP harness typically holds three live tokens at once (assetmanagement + fortiztp + fortisase).

## Things that have NO REST API (use browser automation)
IAM **API-user creation** and some FortiSASE portal actions are GUI-only. We already automate these with Playwright — see `handoff/local-asset-inventory.md` §4 (`adk-fabric/.../forticloud-iam-user-create`, `fortisase-user-create`).

## Security rules
- Never commit `apiId`, passwords, tokens, or credential YAMLs. `.gitignore` excludes `*_credentials.yaml`, `secrets/`, `.env`.
- Credential file search order (house standard): `~/.config/mcp/` → `~/AppData/Local/mcp/` → `C:/ProgramData/mcp/` → `C:/ProgramData/Ulysses/config/` → `/etc/mcp/`.

Sources: https://docs.fortinet.com/document/forticloud/26.1.0/identity-access-management-iam/19322/accessing-fortiapis · https://docs.fortinet.com/document/forticloud/26.1.0/identity-access-management-iam/282341/adding-an-api-user
