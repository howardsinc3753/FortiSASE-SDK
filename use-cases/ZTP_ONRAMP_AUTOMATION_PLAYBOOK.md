# Zero-Touch Branch On-Ramp Automation Playbook

> The "drop-ship a box → it becomes a FortiSASE on-ramp with zero on-site touch" runbook for an MSSP/partner. Backed by `corpus/raw/fortinet-docs/02-automation-and-apis.md` and `api/reference/02-fortiztp-onramp.md`. **Daniel runs the credentialed steps himself.**

## The pipeline (memorize this)
```
Asset Mgmt (register)  →  FortiZTP (provision target)  →  [FortiManager Cloud (FortiGate edge config) OR FortiSASE (thin-edge)]  →  IPsec/SPA on-ramp tunnel up  →  Terraform fortisase (SASE config plane / SPA)
```
- **Onboarding** = FortiZTP. **Edge config** (FortiGate branches) = FortiManager. **SASE config plane** (profiles/policies/SPA) = Terraform `fortinetdev/fortisase`. Three planes, one IAM API user (different `client_id` per token).

## Pre-flight (once per tenant)
1. **FortiCloud account** per tenant (tenancy boundary). MSSP federates via **FortiCloud OUs**.
2. **IAM API user** + permission profile scoped to **Asset Management + FortiZTP + FortiSASE** (+ FortiFlex for MSSP billing). *FortiZTP needs a Local IAM user.*
3. **FortiSASE tenant** stood up: 4 security PoPs + 1 log PoP chosen.
4. **SPA network configuration created FIRST** (Branch On-ramp shares its BGP config). Only iBGP between BOR and branches.
5. **Branch On-ramp location(s)** deployed — min 2 for redundancy; size for 2000 branches/1 Gbps per node, ≤20 nodes, ≤40,000 branches/tenant.

## Pattern A — FortiExtender / FortiAP thin-edge → FortiSASE (lightest)
1. Register device (serial + cloud key) **and the FortiSASE sub code** to the tenant's Asset Management; confirm "FortiSASE Subscription" entitlement.
2. FortiZTP **Settings** → enable **FortiSASE** for that device tab.
3. `PUT /devices/{SN}` → `provisionTarget: "FortiSASE"` (+ region). (Bulk: many serials per call; stay under 2,000 calls/hr.)
4. Device boots, calls home, becomes a **FortiSASE-managed** on-ramp. No box config.

## Pattern B — FortiGate branch → FortiManager Cloud → IPsec/SPA on-ramp (the workhorse)
1. **Register** the FortiGate to Asset Management (tenant account).
2. **Golden template** on FortiManager Cloud: a **model device** + **device template** + **SD-WAN template** carrying the on-ramp config — WAN interfaces, **dual IPsec overlays to the FortiSASE BOR location**, **BGP per-overlay with bootstrap static routes to hub loopbacks** (solves the BGP chicken-and-egg), health checks, and the security profile set. *(Reuse the local `fortigate-sdwan-spoke-template` generator — see `handoff/local-asset-inventory.md` §4.)*
3. **FortiZTP** `PUT /devices/{SN}` → `provisionTarget: "FortiManagerCloud"` (optionally `scriptOid` for a pre-run CLI delta).
4. First boot: **FGFM tunnel + auto-link** establish automatically (without preconfig the unit lands in *Unauthorized Devices* for manual auth). **Reboot / factory-reset hardware.**
5. FortiManager **installs the templates** → the FortiGate dials **IPsec to the FortiSASE Branch On-ramp location**. Endpoints behind it need no agent and no proxy config — they use the FortiGate as default gateway into FortiSASE FWaaS.
6. **Decommission caveat:** FortiZTP deprovision does **not** delete the device from FortiManager Cloud — remove it there too.

## Bulk site onboarding (day-0 at scale)
- Drive FortiZTP with **multiple serials per call**; throttle under 2,000 calls/hr.
- Keep the golden config in **FortiManager templates** (config of record) + **Terraform `fortinetdev/fortisase`** (SASE config plane, versioned, per-tenant workspace/state).
- Idempotency: re-running the provision call is safe; the template install is the source of truth.

## Day-2
- **Drift/change:** Terraform plan/apply (`fortisase` resources); FortiManager for edge changes; `fortios` provider for deep FortiGate tweaks.
- **Visibility:** FortiSASE data sources (`endpoints_details`, `infra_data_transfer`) + REST reads.
- **SPA service connections:** fully REST/Terraform-managed (the one explicitly documented REST surface) — except health/tunnel status, which is read in the portal.

## Open items to validate on a live tenant / FNDN
- Exact JSON for `provisionTarget: "FortiSASE"` (region requirements; entitlement pre-check).
- FortiSASE **`client_id`** + REST base host (resolved when the Swagger lands in `api/openapi/`).
- Whether one ORG-level IAM API user can drive FortiSASE config across tenant accounts (multi-tenant trust model).
- 7.6/8.0 drop-ship bootstrap CLI text for the FortiGate first-contact.
