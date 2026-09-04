# Partner FortiSASE Service Offering — Blueprint

> Working blueprint for the partner-delivered, MSSP-style FortiSASE service. Pricing/packaging facts trace to `corpus/raw/fortinet-docs/03-releases-and-licensing.md` (Ordering Guide, Tier 3) — **quote the current Ordering Guide before any customer commitment.** This is a sales/delivery scaffold, not a price sheet.

## The thesis
Sell **secure connectivity as a managed outcome**: every user and every site is onboarded to FortiSASE with **zero on-site touch**, one console, and consumption-based economics. The partner's differentiation is the **on-ramp automation** (this repo) — fast, repeatable branch + user onboarding the customer can't easily build themselves.

## Who it's for
- SMB/mid-market with **distributed branches** and a remote/hybrid workforce.
- Customers with an existing **FortiGate / SD-WAN estate** (warmest entry — SPA/SASE bundle rides existing boxes).
- Regulated orgs needing **data residency** → FortiSASE-Sovereign.

## Service tiers (map to FortiSASE subscriptions)
| Partner tier | FortiSASE sub | Headline value | Notable inclusions |
|---|---|---|---|
| **Essentials** | Standard | Secure internet + SaaS for managed users; branch on-ramp | SIA, inline CASB/DLP, ZTNA, Fortinet-Cloud PoPs, branch on-ramp (25.3+) |
| **Plus** | Advanced | + unmanaged-device coverage + experience monitoring | Secure Browser, **Agentless ZTNA**, **DEM**, FortiGuard Forensics, **Public-Cloud PoPs**, assisted onboarding |
| **Managed SOC** | Comprehensive | + SOC integration + global reach | **SOC-as-a-Service integration**, Global Security PoP add-on |
*(No mixing tiers within one instance — except the Region add-on with Comprehensive. Use separate accounts for separate tiers.)*

## Economics the partner should internalize
- **User-based seats:** a seat is consumed when a user registers their first device; up to **3 devices/user**; released after **45 days** no telemetry. Data transfer ≈ **25 TB per 100 users** globally.
- **Land via the SD-WAN/SPA bundle:** "as little as **5 users**" on **60G+** FortiGate (10 on 100F+) — the cheapest door-opener for an SD-WAN customer. SPA service-connection license is per **hub** (and per HA member).
- **Branch On-Ramp Location** is an add-on SKU (1 Gbps node, Fortinet `-769` / Public-Cloud `-770`); size to ≤2000 branches/node, ≤20 nodes, ≤40,000/tenant.
- **MSSP billing = FortiFlex** (postpaid, monthly consumption credits, pool across the whole customer base, reassignable). The flexible-consumption lever that makes "land-and-expand" painless. *(Pull current per-tier point costs from the FortiFlex portal — UNVERIFIED here.)*
- **FortiManager** counts FortiSASE as **one managed device — no extra FortiSASE license** — if the partner co-manages config from FMG (7.4.4+ syncs profiles/users/groups/objects).

## Delivery model
- **Tenancy:** one FortiCloud account per customer; partner federates with **FortiCloud OUs** + the **FortiSASE MSSP Portal** (single pane across tenants).
- **Onboarding engine:** the zero-touch pipeline in `ZTP_ONRAMP_AUTOMATION_PLAYBOOK.md` (Asset Mgmt → FortiZTP → FortiManager/FortiSASE → Terraform config plane).
- **Golden config as product:** FortiManager SD-WAN templates + Terraform `fortinetdev/fortisase` modules = the partner's repeatable IP. Version it; reuse per tenant.
- **Day-2 managed service:** drift control via Terraform, monitoring via DEM + FortiSASE analytics, optional SOCaaS (Comprehensive).

## Sales motions
1. **SD-WAN → SASE expansion** (warmest): existing FortiGate customer, attach the SASE/SPA bundle, light up SPA + branch on-ramp.
2. **Remote-workforce security**: replace legacy VPN with agent-based FortiClient + ZTNA.
3. **Unmanaged/contractor access**: agentless SWG / Secure Browser — no endpoint project.
4. **Sovereignty play**: FortiSASE-Sovereign + in-region public-cloud PoPs + dedicated egress IPs.

## Positioning one-liners (Fortinet Tier-3 talk track)
- One OS, one agent (FortiClient), one console across cloud PoP + branch FortiGate + endpoint.
- Reuse the existing FortiGate/SD-WAN estate — branch-native SPA, no new appliance.
- User-based (not bandwidth-metered) licensing; FortiFlex consumption for elasticity.
*(Confirm the current-year Gartner Single-Vendor SASE placement before quoting it.)*

## Risks / things to verify before signing a customer
- Current Ordering-Guide SKUs/limits (packaging changes ~each cycle).
- FortiFlex per-tier point cost.
- Multi-tenant API trust model (can one ORG IAM user drive all tenants' FortiSASE config?).
- The FortiSASE Swagger (unblocks deep automation + the SDK).
- Branch on-ramp scale math for the specific customer (nodes, redundancy, 40k ceiling).
