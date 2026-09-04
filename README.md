# FortiSASE SDK & Corpus

**Owner:** Daniel Howard, Fortinet SE (MSSP)
**Audience:** Fortinet SE team + partner engineers standing up a **FortiSASE service offering centered on On-Ramp and automation**
**Status (2026-06-11):** Repo scaffolded and seeded. SME corpus complete and cited (architecture/on-ramps, automation/APIs, releases/licensing). Automation reference (FortiCloud IAM OAuth, FortiZTP on-ramp provisioning, FortiSASE REST map, Terraform) + runnable examples in place. **Waiting on the FortiSASE Swagger/OpenAPI JSON** (Daniel sourcing) → lands in [`api/openapi/`](api/openapi/) and unblocks the REST recipes + Python SDK.

This is the working knowledge base + automation reference behind the partner SASE offering. It deliberately **mirrors the structure of the sister repo `FortiAIGate-SDK`** (corpus tiers · `api/` · `use-cases/` · `handoff/` · `.claude/commands/` · `CLAUDE.md` SME mode).

---

## 🛠️ The tool — BOR Config Generator (partners start here)

The flagship **working** deliverable: a schema-driven **Streamlit app** that turns a short form into a
validated, ready-to-deploy **FortiOS BOR / BOR+SPA** config — single- or dual-circuit, with SLA
failover, per-site bandwidth caps, BGP communities, and site-to-site private access — **plus** a
**FortiSASE IPsec-values card** to hand the engineer for the portal side. No FortiOS CLI needed.

```powershell
cd automation\sdwan-ztp\config-generator
pip install -r requirements.txt
streamlit run app.py            # → http://localhost:8501
```

Partner quick-start: [`config-generator/PARTNER-GUIDE.md`](automation/sdwan-ztp/config-generator/PARTNER-GUIDE.md).

---

## Start here

| If you are… | Open this first |
|---|---|
| **A partner/SE building a branch (BOR) config** | **[`automation/sdwan-ztp/config-generator/`](automation/sdwan-ztp/config-generator/)** — the Streamlit generator (`streamlit run app.py`); guide: [`PARTNER-GUIDE.md`](automation/sdwan-ztp/config-generator/PARTNER-GUIDE.md) |
| A new Claude Code session in this repo | Type `/sase-onboard` — reads docs in order, prints state, waits for direction |
| Coming up to speed | [`handoff/README.md`](handoff/README.md) — onboarding pack |
| Learning the product (SME) | [`corpus/raw/fortinet-docs/`](corpus/raw/fortinet-docs/) — 3 cited docs |
| Designing an on-ramp | [`use-cases/ONRAMP_DECISION_GUIDE.md`](use-cases/ONRAMP_DECISION_GUIDE.md) or `/sase-onramp <scenario>` |
| Automating onboarding | [`use-cases/ZTP_ONRAMP_AUTOMATION_PLAYBOOK.md`](use-cases/ZTP_ONRAMP_AUTOMATION_PLAYBOOK.md) + [`api/reference/`](api/reference/) |
| Building the partner offering | [`use-cases/PARTNER_SASE_SERVICE_OFFERING.md`](use-cases/PARTNER_SASE_SERVICE_OFFERING.md) |
| Reusing local code | [`handoff/local-asset-inventory.md`](handoff/local-asset-inventory.md) |

---

## What's in the repo

### 🛠️ BOR Config Generator (the working tool) — `automation/sdwan-ztp/config-generator/`
Schema-driven Streamlit app → validated FortiOS **BOR / BOR+SPA** config (single/dual-circuit, SLA
failover, per-site bandwidth, BGP communities, site-to-site private access) **plus** the FortiSASE
IPsec-values hand-off card for the portal side. `schema/variables.yaml` is the single source of truth
(drives both the config rendering and the form). Run `streamlit run app.py`. Partner guide:
[`PARTNER-GUIDE.md`](automation/sdwan-ztp/config-generator/PARTNER-GUIDE.md) · AI MACD notes:
[`SKILL-READ-FIRST_MACD.md`](automation/sdwan-ztp/config-generator/SKILL-READ-FIRST_MACD.md).

### Corpus (the SME knowledge base) — `corpus/raw/fortinet-docs/`
| File | What it is | Tier |
|---|---|---|
| [`01-architecture-and-onramps.md`](corpus/raw/fortinet-docs/01-architecture-and-onramps.md) | FortiSASE architecture, PoPs, and the **four on-ramp types** in depth (the focus) | 1 |
| [`02-automation-and-apis.md`](corpus/raw/fortinet-docs/02-automation-and-apis.md) | FortiSASE REST, FortiCloud IAM OAuth, **FortiZTP on-ramp provisioning**, Terraform | 1/2 |
| [`03-releases-and-licensing.md`](corpus/raw/fortinet-docs/03-releases-and-licensing.md) | Feature/Mature tracks, 24.x→26.x what's-new, subscriptions, SKUs, MSSP/FortiFlex | 1/3 |
| [`04-fortimanager-managed-fortisase.md`](corpus/raw/fortinet-docs/04-fortimanager-managed-fortisase.md) | **FMG-managed FortiSASE** (Spectrotel) — FortiCare-ticket gate, ADOM rules, zone→policy mapping, sync potholes, MSSP model; every claim verbatim-cited + verdict ledger | 1 |
| [`05-on-ramp-deep-dive.md`](corpus/raw/fortinet-docs/05-on-ramp-deep-dive.md) | **On-Ramp deep-dive (the core strategy)** — taxonomy map, Branch On-Ramp (BOR) IPsec/BGP/scale, provisioning runbooks (FortiGate-via-FMG, thin-edge, 3rd-party), agent/agentless, PoP selection, licensing; 27-row pothole catalog + verdict ledger | 1 |
| [`06-socaas.md`](corpus/raw/fortinet-docs/06-socaas.md) | **SOCaaS** — SOCaaS vs MDR vs IR, FortiSASE Advanced/Comprehensive inclusion, **3rd-party logs (FortiSIEM Multi-Vendor model)**, SOC workflow, global response teams, FortiGuard IR, partner/MSSP value + API, engagement/SLAs/onboarding; verdict ledger | 1/2/3 |

Every non-trivial claim carries an inline `(Source: <url>)`; **UNVERIFIED** items are flagged for SE confirmation.

### Automation reference — `api/`
- [`api/reference/`](api/reference/) — `01-auth` (FortiCloud OAuth), `02-fortiztp-onramp` (ZTP v2), `03-fortisase-rest` (REST map), `04-terraform`.
- [`api/examples/`](api/examples/) — runnable: OAuth token, FortiZTP list+provision (both on-ramp patterns), Terraform skeleton.
- [`api/openapi/`](api/openapi/) — **landing spot for the incoming Swagger.**

### Use-cases (partner-presentable) — `use-cases/`
On-ramp decision guide · zero-touch ZTP playbook · partner service-offering blueprint.

### Cross-session — `handoff/`
Onboarding pack · kickoff prompt · **local-asset inventory** (reusable FortiZTP SDK, browser tools, SD-WAN templates).

### Meta
[`CLAUDE.md`](CLAUDE.md) (SME mode + tier rules) · [`.claude/commands/`](.claude/commands/) (`/sase-onboard`, `/sase-lookup`, `/sase-onramp`).

---

## The one-paragraph pitch
FortiSASE is Fortinet's single-vendor SASE (SSE + SD-WAN) built on FortiOS/FortiClient/EMS-in-the-cloud, delivered through global security PoPs. This repo turns it into a **repeatable partner service** by nailing the hard part — **on-ramps and zero-touch onboarding**. Users come on via FortiClient (agent) or agentless SWG; whole sites come on via **branch on-ramp** (FortiGate IPsec or FortiExtender/FortiAP thin-edge); private apps via **SPA hubs**. Onboarding is automated through **Asset Management → FortiZTP → FortiManager/FortiSASE → Terraform**, all on one FortiCloud IAM OAuth substrate, billed via **FortiFlex** consumption for MSSP elasticity.

## Source-of-truth tiers (see `CLAUDE.md`)
1 Official docs · 2 Dev/code (Terraform provider, incoming Swagger) · 3 Datasheets/Ordering Guide/positioning · 4 Community/reseller · 5 Model prior knowledge (be skeptical — calendar releases move fast).

## Biggest open item
The **FortiSASE Swagger** → confirms the FortiSASE `client_id` + REST base host and unblocks the Python SDK. Drop it in `api/openapi/` and ask Claude to wire it up (see that folder's README).

---

## License
Licensed under the **Apache License, Version 2.0** — see [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).
Fortinet product names are trademarks of Fortinet, Inc.; this is an independent automation
reference, not an official Fortinet release.

---

*Sister repo:* `FortiAIGate-SDK` · *Daniel Howard, Fortinet SE — MSSP*
