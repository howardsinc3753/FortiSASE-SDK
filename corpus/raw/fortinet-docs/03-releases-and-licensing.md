# FortiSASE — Releases, Licensing & Packaging (SE/MSSP Corpus)

> **Mixed tier — labeled inline.** Tier 1 = docs.fortinet.com release notes. Tier 3 = Fortinet datasheets / **Ordering Guide** `FSS-OG-R40-20260525` (dated May 25, 2026) + positioning copy. Tier 4 = reseller pages (firewalls.com, CDW, Insight, Spectrum-Edge), used only to corroborate SKUs. Compiled June 2026. Anything not confirmable against Tier 1/3 is flagged **UNVERIFIED**.
> **Quote the Ordering Guide verbatim for licensing**, and cite its revision/date — packaging changes ~every cycle.

---

## 1. Release Cadence, Versioning & Tracks

### 1.1 Calendar versioning
FortiSASE uses a **calendar-based scheme** `YY.N.build` (e.g., `24.2`, `25.2`, `25.3`, `25.4`, `26.1`), with build numbers for maintenance increments (e.g., `26.1.107`, `25.3.175`). Releases also carry a label such as `26.1.2.2 Feature` or `25.3.b Mature` (Sources: https://docs.fortinet.com/document/fortisase/latest/feature-release-notes/661728/whats-new ; https://docs.fortinet.com/document/fortisase/26.1.107/mature-release-notes/661728).

### 1.2 Two release tracks — Feature vs. Mature
- **Feature track** — leading-edge stream; gets new capabilities first. Current Feature release: **26.1.107 (26.1.2.2 Feature)** (Source: feature-release-notes whats-new, above).
- **Mature track** — conservative/stable stream. Current Mature: **26.1.2.2 Mature (build 25.3.217)**, maintenance-only ("There are no changes for 26.1.2.2") (Source: https://docs.fortinet.com/document/fortisase/26.1.107/mature-release-notes/661728).

Fortinet periodically **migrates Mature instances onto Feature**; selected Mature instances are incrementally migrated, with automatic migration scheduled for the **week of July 20, 2026** absent tenant action. Active track shows in the portal version tooltip (Sources: above + https://docs.fortinet.com/document/fortisase/26.1.92/mature-release-notes/661728/whats-new).

**SE takeaway:** Feature/Mature ≈ "fast ring / stable ring." There is **no customer-selectable per-tenant LTS** — Fortinet controls maintenance windows and migration.

### 1.3 FortiSASE-Sovereign
A separate product line (doc set `fortisase-sovereign`) for **data-sovereignty / localization**: same SASE stack (SWG, ZTNA, CASB) emphasizing **data residency**, **operational control**, and **compliance** while retaining log ownership/privacy. Version scheme mirrors mainline with a lettered suffix (`26.2.a`, `26.2.b`); **current Sovereign release is 26.2.b** (Source: https://docs.fortinet.com/document/fortisase-sovereign/latest/release-notes/016160/whats-new).
> **Note:** the `26.2.x` family currently appears in the **Sovereign** doc set, not yet as a mainline Feature release — mainline top is still `26.1.x` as of June 2026. Treat "26.2" as Sovereign-specific until a mainline 26.2 release-notes URL exists.

### 1.4 "What's new" highlights, 24.x → 26.x (Tier 1)
| Release | Notable items |
|---|---|
| **24.2.x** | Portal config for **SD-WAN On-Ramp** (certified IPsec devices); ZTNA tagging on Windows OS update-check; endpoint-profile assignment by Entra ID group; REST API token mgmt via FortiCloud IAM (Source: https://docs.fortinet.com/document/fortisase/24.2.63/release-notes/891466/introduction) |
| **24.3.x** | FortiClient 7.2 (beta); **IPsec VPN** option for remote users + pre-logon VPN; FortiGuard **Forensics** requests; **agentless ZTNA** bookmark access (Advanced); **RBI** (beta) (Source: https://docs.fortinet.com/document/fortisase/24.3.56/release-notes/661728/whats-new) |
| **25.1.x** | **Branch On-Ramp connection add-on (1–2000 IPsec connections)**; agentless ZTNA bookmark portal; Network Lockdown grace period; geofencing failover; **DEM TCP latency (beta)**; auto vuln patching by severity |
| **25.2.x** | Reorganized nav + standardized terms; **System License overview page**; integrated **FortiCASB**; **DLP EDM & IDM** (Exact Data / Indexed Document Matching); IPsec to Branch On-ramp from third-party devices; DNS redirection passthrough |
| **25.3.x** | **Branch on-ramp with Standard subscription**; **FIDO2 for FortiClient agent tunnels**; **CDR (Content Disarm & Reconstruction) in AV profile**; **FortiGuard DLP service**; pre-connection posture checks via security tags; SPA application monitoring (up to 20 custom apps); BGP MED hub selection; endpoint-to-endpoint via SPA Hub |
| **25.4.x** | FortiClient 7.4.5; **IPsec over TCP/443**; DNS suffix for IPsec tunnels; **CrowdStrike ZTA** posture tagging; **ZTNA auto OAuth login for Entra ID**; **SCIM** auto user provisioning (select availability); geography-based policy |
| **26.1.x** | **Bandwidth policies/profiles**; FortiClient debug logs per profile; SAML IdP + SSO group sync to policy; **many new Public Cloud PoPs** (Amsterdam, Ashburn, Chicago, Melbourne, Montreal, Osaka, Santiago, Stockholm); **Secure Browser extension** for unmanaged/contractor devices; IPsec **DPD** customization; **RBI to select-availability**; vuln-scan on endpoint software change; SPA external feeds/FSSO over BGP-on-loopback hubs; FortiClient 7.4.7 |
| **26.2.x (Sovereign)** | Classification tags for managed endpoints; logical AND between ZTNA tag groups in firewall policy; off-net network lockdown; ZTNA-enforcement disable on-net; off-fabric endpoint profiles; enhanced FortiOS upgrade workflow |
(25.1–26.1 items: https://docs.fortinet.com/document/fortisase/latest/feature-release-notes/661728/whats-new ; Sovereign: https://docs.fortinet.com/document/fortisase-sovereign/latest/release-notes/016160/whats-new)

**AI/FortiAI:** No discrete FortiAI "what's new" line item found in FortiSASE release notes 24.x–26.1. FortiSASE inherits FortiGuard AI-driven detection (AV/IPS/DLP), but a named in-product "FortiAI for FortiSASE" is **UNVERIFIED** as of June 2026 — flag for follow-up.

---

## 2. Subscription Tiers / Licensing (Tier 3 — Ordering Guide)

Licensed primarily on a **per-user (remote-user) subscription** basis. "All new customers should purchase a User-based license to get started. All other SKUs are registered on top of the initial deployment." Three tiers: **Standard, Advanced, Comprehensive** (Source: https://www.fortinet.com/content/dam/fortinet/assets/data-sheets/og-fortisase.pdf).

### 2.1 Feature matrix (Remote User subscriptions)
(✓ = included; blank = not included) — Source: Ordering Guide (above).

| Capability | Standard | Advanced | Comprehensive |
|---|:--:|:--:|:--:|
| Secure Internet Access — SSL inspection, inline AV, IPS, Web/DNS filter, Botnet C&C | ✓ | ✓ | ✓ |
| **Secure Browser** (SIA) | | ✓ | ✓ |
| Secure SaaS Access — **Inline CASB**, **Inline DLP** | ✓ | ✓ | ✓ |
| Cloud API CASB & DLP license | ✓ | ✓ | ✓ |
| FortiGate Private Access (SPA) — *requires SD-WAN Service Bundle* | ✓ | ✓ | ✓ |
| ZTNA | ✓ | ✓ | ✓ |
| **Agentless ZTNA** | | ✓ | ✓ |
| Devices per user | Up to 3 | Up to 3 | Up to 3 |
| Dedicated Public IPs | ✓ | ✓ | ✓ |
| Endpoint: Sandbox, Vuln Mgmt, EPP (agent-based) | ✓ | ✓ | ✓ |
| SASE Cloud Logging/Reporting/Forwarding | ✓ | ✓ | ✓ |
| **Digital Experience Monitoring (DEM)** (agent-based) | | ✓ | ✓ |
| **SOC-as-a-Service integration** | | | ✓ |
| **FortiGuard Forensics (Response) Service** (agent-based) | | ✓ | ✓ |
| SASE Cloud Management + REST API | ✓ | ✓ | ✓ |
| **Data center locations** | Fortinet Cloud only | Fortinet **& Public Cloud** | Fortinet **& Public Cloud** |
| **Global Security PoP Coverage** | — | — | **Add-on** |
| 24x7 Premium Support | ✓ | ✓ | ✓ |
| Assisted On-boarding | | ✓ | ✓ |

**Tier deltas to memorize:**
- **Standard → Advanced** unlocks: Secure Browser, Agentless ZTNA, DEM, FortiGuard Forensics, Public Cloud PoP locations, Assisted Onboarding.
- **Advanced → Comprehensive** adds: SOC-as-a-Service integration; ability to add Global Security PoP Coverage add-on.
- **No mixing tiers in one instance** (reseller corroboration, Tier 4: https://www.spectrum-edge.com/fortisase-licensing-guide/). Ordering-Guide qualifier: the **Region Add-on SKU can be mixed when combined with Comprehensive**; otherwise all components in an account must be the same type — use multiple accounts for different types.

### 2.2 User-based licensing mechanics (quote-worthy, Tier 3)
- **Seat counting:** "You start consuming a user license when a user registers their first device. They'll keep consuming that license until either a FortiSASE admin manually removes them, or until all their registered devices have no telemetry check-ins for more than **45 days**, at which point their license will be released. Every user is entitled to register to **three different devices**, if they register to a fourth one, an additional license will be consumed."
- **Bandwidth model:** user-based, not bandwidth-based; data-transfer entitlement derives from user count: "a subscription for 100 users would entitle for **25 TB of Data Transfer globally**" (~250 GB/user). The per-user "1.5 Mbps" framing is **Tier 4/UNVERIFIED**; the TB statement is authoritative.
(Source: Ordering Guide.)

### 2.3 User bands (SKU families) — Tier 3 + Tier 4 corroboration
| User band | Standard | Advanced | Comprehensive |
|---|---|---|---|
| 50–499 | FC2-10-EMS05-547 | FC2-10-EMS05-676 | FC2-10-EMS05-759 |
| 500–1,999 | FC3-…-547 | FC3-…-676 | FC3-…-759 |
| 2,000–9,999 | FC4-…-547 | FC4-…-676 | FC4-…-759 |
| 10,000+ | FC5-…-547 | FC5-…-676 | FC5-…-759 |
Corroboration: FC2-10-EMS05-547 = Standard 50–499 (firewalls.com); FC2-10-EMS05-676 = Advanced 50–499 (Insight). **Caveat (OG):** "Comprehensive subscriptions of less than 200 users have limited PoP availability."

### 2.4 FortiGate SASE Bundle / SD-WAN Service Bundle ("SASE Starter Kit") — the branch-on-ramp-via-SPA motion
"This bundle includes a starter kit of FortiSASE Standard users plus Secure Private Access (SPA) connectivity. It is supported on F-series and G-series FortiGate models starting with the **60G**. Start your SASE adoption with as little as **5 users**!" For models below 60G the bundle includes **SPA connectivity only** (Source: Ordering Guide).

| Hardware | Included Standard seats | SKU family |
|---|---|---|
| 60G+ | 5 | FC-10-XXXXX-1329 / -1389 |
| 100F+ | 10 | FC-10-XXXXX-1329 / -1389 |
| 700G+ | 50 | FC-10-XXXXX-1329 / -1389 |
| 1800F+ | 100 | FC-10-XXXXX-1329 / -1389 |
Notes: "Only SKU 1329 include FortiCare Premium." SPA service-connection license is **only required on Hub locations**, and **each HA member needs its own**. SPA bundle SKUs: FortiGate SPA VM `…-662`; FGT-30G+ SD-WAN bundle `…-1337`; FGT-100F+ SD-WAN bundle w/ starter kit `…-1329`.
> **Memory-correction for Daniel:** your note says "120G+, 10 users." The **current (May 2026) OG** states the Starter Kit starts at **60G+ / 5 users**, 100F+ at 10. The "120G/10-user" framing is an older Tier-4 reference (CDW FC-10-F120G-1230). Use **60G+/5-user** as current/authoritative.

### 2.5 Branch Thin-Edge entitlements (managed hardware on-ramp)
Distinct from Branch-On-Ramp-via-IPsec: "Thin Edge are managed directly in FortiSASE portal. **User license is still required.**" Supported thin-edge hardware: **FortiExtender-200F, FortiBranchSASE-10F-WiFi / -20G / -20G-WiFi**, and **FortiAP** models (FAP-831F/432G/443K). Bundle SKUs use `-595` (cloud mgmt) and `-1070` families (Source: Ordering Guide).

### 2.6 Add-ons (Tier 3)
- **Dedicated Public IP** — `FC1-10-EMS05-658`, 4 IPs/block; **requires min 500-user subscription**. Each instance includes one dedicated IP; more need the add-on.
- **PoP/Location add-ons** — Fortinet Location `…-752`, Public Cloud Location `…-766` (each 1–16 PoPs); **Global Add-On** `…-1136` (all current+future PoPs).
- **Branch On-Ramp Location** (1 Gbps node) — `FC1-10-EMS05-769` (Fortinet Cloud PoP) / `-770` (Public Cloud PoP).
- **FortiCASB-SSPM Add-on** — `…-1282`, banded by user count; seat count need not match core subscription.
- **DEM** — not standalone; **bundled into Advanced & Comprehensive** (agent-based).
- **Sandbox / Vuln Mgmt / EPP** — included in all three tiers (not add-ons).
- **FortiSASE China** — separate offering via a China partner (Beijing/Shanghai/Guangzhou DCs), feature-equivalent to **Standard**.
- **FortiIdentity Cloud** (IDaaS) and **FortiTrust Identity** — complementary identity add-ons.
(Source: Ordering Guide.)

---

## 3. Sizing & Limits (Tier 3 — Ordering Guide FAQ)
- **Locations included with a user subscription:** Standard & Advanced include **up to 4 locations** (chosen at activation). Comprehensive **<200 users** includes **1–2**.
- **Location add-on ceiling:** "Up to **16** additional locations … for a **maximum of 20 total**."
- **Dedicated egress IPs per PoP:** "up to **5 dedicated egress IPs (DEIPs)**, 4 of these … for source IP anchoring rules."
- **Branch On-Ramp capacity:** "Each Branch On-Ramp Location includes **1 Gbps of shared bandwidth for up to 2000 supported connections**. Each account can have a **maximum of 20 Branch On-Ramp locations and a total of 40,000 Branch On-Ramp connections.** Bandwidth is dedicated to the Location and not shared with Remote Users or Edge Devices." **Minimum 2 locations for redundancy.**
- **Data transfer:** ~**25 TB per 100 users** globally.
- **Devices per user:** **up to 3** (4th consumes a seat). Seat released after **45 days** of no telemetry.
- **FortiAP max:** **240** per FortiSASE account.
- **FortiExtender / FortiBranchSASE max:** **1,024** per account.
- **Branch On-Ramp third-party CPEs:** supported.
- **PoC → Production:** an active PoC tenant **can be promoted to production** (no rebuild).
(Source: Ordering Guide. Mature-track corroboration of throughput: https://docs.fortinet.com/document/fortisase/latest/feature-release-notes/661728/whats-new)

---

## 4. MSSP / Partner Angle

### 4.1 Multi-tenant management model (Tier 1)
Built on **FortiCloud Organizational Units (OUs)** + a **FortiSASE MSSP Portal**:
- **FortiCloud Organizations / OUs** — organize each customer's FortiCloud accounts into distinct OUs/sub-OUs.
- **IAM** — RBAC; grant a user MSSP-portal access by adding the FortiSASE portal to their **Permission Profile**.
- **Asset Management** — applies FortiSASE entitlements at onboarding.
- **FortiSASE MSSP Portal** — single unified GUI across tenants; per-tenant active/inactive license + Security PoP distribution views.
- Each customer remains a **separate FortiSASE instance/tenant** (no commingling); the MSSP federates under its OU structure.
(Sources: https://docs.fortinet.com/document/fortisase/latest/multi-tenant-fortisase-deployment-for-mssp-using-ou ; .../26.1.107/.../9907/configuring-identity-and-access-management-iam-for-mssp ; .../25.3.67/.../922847/using-fortisase-mssp-portal-to-manage-fortisase-tenants)

### 4.2 FortiManager integration (Tier 3)
- "FortiManager **7.4.4 and higher** can synchronize Security Profiles, Users, Groups and Firewall Objects with FortiSASE."
- "FortiManager must be purchased separately and **counts FortiSASE as one managed device. No additional FortiSASE license is required.**" (Source: Ordering Guide)

### 4.3 FortiFlex — points-based / consumption licensing (key MSSP lever)
- FortiSASE supports **FortiFlex** points-based entitlements (Source: https://docs.fortinet.com/document/fortisase/latest/feature-administration-guide/748654/fortiflex-licensing).
- **FortiFlex MSSP** is **postpaid**, billed monthly in **consumption credits**, MSSP-partner-only, covering VMs/hardware/cloud services (Source: https://docs.fortinet.com/document/flex-vm/26.1.0/fortiflex-concept-guide/310137/enterprise-and-mssp).
- Pooling: a single FortiFlex account can **pool licenses across the entire customer base** and reassign/migrate easily; consumption calculated daily (PST/PDT).
- **UNVERIFIED:** exact per-user **points cost** per tier — pull current point tables from the FortiFlex portal/partner pricing before quoting numbers.

### 4.4 Partner portal / programs
- MSSP enablement = **FortiCloud IAM + FortiSASE MSSP Portal** + **FortiFlex MSSP Program** (postpaid credits). Reference design: **Unified SASE for MSSP Architecture Guide** (https://docs.fortinet.com/document/fortisase/latest/unified-sase-for-mssp-architecture-guide/793766/fortinet-unified-sase-design-overview).
- **UNVERIFIED:** a distinct "FortiPartner portal" branded for FortiSASE — documented mechanics are FortiCloud IAM/OU + FortiFlex MSSP.

---

## 5. Competitive / Positioning One-Liners (Tier 3 — Fortinet marketing; SE talk-track, not independent fact)
- **One OS, one agent, one console:** "FortiSASE's SWG, ZTNA, CASB, FWaaS, RBI, SSPM, secure SD-WAN, and end-to-end DEM run on one OS with one agent, and can be managed with a single console." (https://www.fortinet.com/solutions/unified-sase)
- **Unified agent:** FortiClient consolidates EPP/vuln, ZTNA, CASB, SWG, VPN into one agent. (https://www.fortinet.com/products/sase)
- **Consistent inspection everywhere:** identical FortiOS profiles across cloud PoPs and on-prem FortiGate.
- **SD-WAN + security on one box:** a single FortiGate delivers SASE on-ramp and SD-WAN — no extra appliance.
- **Licensing simplicity / TCO:** "the simplest licensing model and compelling TCO," flat user-based licensing (position as "user-based, not bandwidth-metered").
- **Analyst proof point:** Recognized in the **2024 Gartner MQ for Single-Vendor SASE**. **Confirm latest (2025/2026) placement before quoting — UNVERIFIED for current year.**

**SE framing vs competitors (SE's own argument, not Fortinet-published):** vs **Zscaler** (proxy-led, separate ZTNA/CASB SKUs) and **Netskope** (CASB/DLP-led), Fortinet's edge is the **single FortiOS + FortiClient stack spanning cloud PoP, branch FortiGate, and endpoint**, reusing existing FortiGate/SD-WAN estate. Vs **Palo Alto Prisma Access**, lead with **branch-native SPA via existing FortiGates** and **FortiFlex consumption** for MSSP elasticity.

---

## Open / UNVERIFIED items to close before customer-facing use
1. Named FortiAI feature in FortiSASE — not found 24.x–26.1.
2. Mainline 26.2 FortiSASE release — `26.2.x` is **Sovereign-only** today.
3. Per-user FortiFlex point cost per tier — pull from FortiFlex portal.
4. "FortiPartner portal" branded for FortiSASE — documented path is IAM/OU + FortiFlex MSSP.
5. Per-user Mbps (1.5 Mbps) is Tier-4; authoritative metric is 25 TB/100 users.
6. Starter Kit "120G/10-user" (Daniel's memory) is older — current OG = **60G+/5 users**.
7. Current-year Gartner SV-SASE placement — confirm 2025/2026.

---

## Sources

**Tier 1 — Fortinet docs**
- [Feature Release Notes — What's new (latest)](https://docs.fortinet.com/document/fortisase/latest/feature-release-notes/661728/whats-new)
- [Mature Release Notes (26.1.107)](https://docs.fortinet.com/document/fortisase/26.1.107/mature-release-notes/661728)
- [Mature Release Notes — What's new (26.1.92)](https://docs.fortinet.com/document/fortisase/26.1.92/mature-release-notes/661728/whats-new)
- [FortiSASE-Sovereign Release Notes — What's new (26.2.b)](https://docs.fortinet.com/document/fortisase-sovereign/latest/release-notes/016160/whats-new)
- [24.2.63 Release Notes — Introduction](https://docs.fortinet.com/document/fortisase/24.2.63/release-notes/891466/introduction)
- [24.3.56 Release Notes — What's new](https://docs.fortinet.com/document/fortisase/24.3.56/release-notes/661728/whats-new)
- [Licensing (Feature Admin Guide 26.1.26)](https://docs.fortinet.com/document/fortisase/26.1.26/feature-administration-guide/401254/licensing)
- [FortiFlex licensing for FortiSASE](https://docs.fortinet.com/document/fortisase/latest/feature-administration-guide/748654/fortiflex-licensing)
- [Multi-Tenant FortiSASE for MSSP using OU (latest)](https://docs.fortinet.com/document/fortisase/latest/multi-tenant-fortisase-deployment-for-mssp-using-ou)
- [Using the FortiSASE MSSP Portal (25.3.67)](https://docs.fortinet.com/document/fortisase/25.3.67/multi-tenant-fortisase-deployment-for-mssp-using-ou/922847/using-fortisase-mssp-portal-to-manage-fortisase-tenants)
- [Configuring IAM for MSSP (26.1.107)](https://docs.fortinet.com/document/fortisase/26.1.107/multi-tenant-fortisase-deployment-for-mssp-using-ou/9907/configuring-identity-and-access-management-iam-for-mssp)
- [Unified SASE for MSSP — Design Overview](https://docs.fortinet.com/document/fortisase/latest/unified-sase-for-mssp-architecture-guide/793766/fortinet-unified-sase-design-overview)
- [FortiFlex Concept Guide — Enterprise and MSSP (26.1)](https://docs.fortinet.com/document/flex-vm/26.1.0/fortiflex-concept-guide/310137/enterprise-and-mssp)

**Tier 3 — Fortinet datasheets / ordering / positioning**
- [FortiSASE Ordering Guide (PDF, FSS-OG-R40, May 25 2026)](https://www.fortinet.com/content/dam/fortinet/assets/data-sheets/og-fortisase.pdf)
- [FortiSASE product page](https://www.fortinet.com/products/sase)
- [Fortinet Unified SASE solution page](https://www.fortinet.com/solutions/unified-sase)
- [FortiFlex product page](https://www.fortinet.com/products/fortiflex)
- [FortiFlex MSSP Program brochure (PDF)](https://www.fortinet.com/content/dam/fortinet/assets/brochures/brochure-fortiflex-mssp.pdf)
- [SD-WAN→SASE Expansion Bundle flyer (PDF)](https://www.fortinet.com/content/dam/fortinet/assets/flyer/flyer-fortisase-sdwan.pdf)

**Tier 4 — Reseller (SKU corroboration only)**
- [Spectrum-Edge: FortiSASE Licensing Guide](https://www.spectrum-edge.com/fortisase-licensing-guide/)
- [firewalls.com: FortiSASE Standard 50–499 (FC2-10-EMS05-547)](https://www.firewalls.com/brands/fortinet/fortisase/fortisase-standard-subscription-for-50-499-users.html)
- [Insight: FortiSASE Advanced 50–499 (FC2-10-EMS05-676)](https://www.insight.com/en_US/shop/product/FC210EMS056760136/fortinet/FC2-10-EMS05-676-01-36/)
- [CDW: FortiSASE Starter Kit + SD-WAN SPA (older ref)](https://www.cdw.com/product/fortisase-starter-kit-plus-sd-wan-spa-connector-subscription-license-rene/8481503)
