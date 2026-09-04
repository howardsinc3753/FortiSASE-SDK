# Executive Summary — FortiSASE SDK & Corpus

**Date:** 2026-06-11 · **Owner:** Daniel Howard (Fortinet SE, MSSP) · **Purpose:** internal handoff summary.

## Why this repo exists
Daniel and a partner are building a **FortiSASE service offering centered on on-ramp and automation**. This repo is the SME knowledge base + automation reference behind it, mirroring the proven structure of the `FortiAIGate-SDK` repo.

## What was built (initial seed)
- **Repo scaffold** mirroring FortiAIGate-SDK: corpus tiers, `api/` (reference + examples + openapi), `use-cases/`, `handoff/`, `.claude/commands/`, `CLAUDE.md` SME mode.
- **SME corpus** (3 cited Tier-1/2/3 docs): architecture + the four on-ramp types; automation/APIs (FortiCloud IAM OAuth, FortiZTP, FortiSASE REST, Terraform); releases + licensing (Feature/Mature tracks, 24.x→26.x what's-new, subscriptions/SKUs, MSSP/FortiFlex). Every claim cited; UNVERIFIED items flagged.
- **Automation reference + runnable examples:** OAuth token minting, FortiZTP list/provision (both on-ramp patterns), Terraform `fortinetdev/fortisase` skeleton.
- **Local-asset inventory:** mapped the reusable FortiZTP SDK, the adk-fabric FortiCloud/FortiSASE browser-automation tools, FortiManager/SOCaaS/FortiWeb SDK patterns, and SD-WAN spoke-template generators.
- **Use-case playbooks:** on-ramp decision guide, zero-touch ZTP onboarding playbook, partner service-offering blueprint.
- **Three slash commands:** `/sase-onboard`, `/sase-lookup`, `/sase-onramp`.

## Key technical findings
1. **On-ramps are the product.** Four types — agent (FortiClient), agentless SWG (PAC/Secure Browser), branch on-ramp (FortiGate IPsec / FortiExtender·FortiAP thin-edge), SPA hub. Branch on-ramp scale: 2–20 nodes/tenant, 1 Gbps & 2000 branches/node, 40,000/tenant; **SPA config must precede branch on-ramp** (shared iBGP).
2. **FortiSASE is a first-class FortiZTP provision target** (26.1.a) — the literal zero-touch hook. FortiAP/FortiExtender go directly (Pattern A); FortiGate branches go via FortiManager Cloud (Pattern B).
3. **One auth substrate:** FortiCloud IAM API user + OAuth (`customerapiauth.fortinet.com`), per-portal `client_id`. We already implement this in the local FortiZTP/SOCaaS SDKs.
4. **First-party Terraform provider exists** (`fortinetdev/fortisase` v1.2.0) — the config-plane IaC; ~84 resources. Device onboarding stays in FortiZTP/FortiManager (infra resources are read-only).
5. **Licensing is user-based** (Standard/Advanced/Comprehensive), MSSP via **FortiFlex** consumption + FortiCloud OU multi-tenancy. SD-WAN/SPA bundle lands SASE on existing FortiGates from **60G+/5 users** (corrects the older 120G/10-user note).

## The one blocker
The **FortiSASE Swagger/OpenAPI JSON** (Daniel sourcing). It resolves the remaining UNVERIFIED items (FortiSASE `client_id`, REST base host, exact paths/fields) and unblocks the REST recipes and the `fortisase/` Python SDK.

## Recommended next steps
1. Drop the Swagger in `api/openapi/`; wire up REST recipes + the SDK client (mirror FortiZTP pattern).
2. Add `FortiSASE` to the local FortiZTP SDK's provision-target enum.
3. Build a live branch-on-ramp lab (FortiGate → FortiManager Cloud → FortiSASE BOR); capture the golden template.
4. Author the partner-facing deck from `use-cases/`.
5. Work down each corpus doc's UNVERIFIED ledger against a live tenant / FNDN.
