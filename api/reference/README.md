# FortiSASE API & Automation Reference

Distilled, runnable reference for automating FortiSASE on-ramp onboarding at MSSP scale. The narrative source-of-truth is `corpus/raw/fortinet-docs/02-automation-and-apis.md`; this folder is the "how do I actually call it" companion.

| File | What it covers |
|---|---|
| [`01-auth.md`](01-auth.md) | FortiCloud IAM API users + OAuth 2.0 token flow (the auth substrate for **all** Forti* automation) |
| [`02-fortiztp-onramp.md`](02-fortiztp-onramp.md) | FortiZTP v2 REST API — zero-touch provisioning of on-ramp devices (the two patterns) |
| [`03-fortisase-rest.md`](03-fortisase-rest.md) | FortiSASE REST API surface (SPA confirmed; full map from the Terraform provider) — **awaiting the Swagger in `../openapi/`** |
| [`04-terraform.md`](04-terraform.md) | `fortinetdev/fortisase` Terraform provider — the config-plane IaC |

**Automation pipeline shape:** `FortiZTP (onboard) → FortiManager (edge config, FortiGate branches) → Terraform fortisase (SASE config plane)`.

**Auth in one line:** every call below is `Authorization: Bearer <token>`, where the token comes from `https://customerapiauth.fortinet.com/api/v1/oauth/token/` with a per-portal `client_id`. See `01-auth.md`.

> Tier labels per `CLAUDE.md`. Endpoint paths confirmed against our working FortiZTP SDK are Tier 2; FortiSASE REST paths are **provisional** until the Swagger lands.
