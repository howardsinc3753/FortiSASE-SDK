# FortiManager-Managed FortiSASE — Engineering Reference (Partner / Spectrotel)

> **Tier 1 (official docs).** Compiled June 2026 from docs.fortinet.com. Scope: **FortiManager 7.6.x / 8.0** managing **FortiSASE 25.x / 26.1.x** via Central Management. Every load-bearing claim carries a verbatim quote + source URL and a status label: **CONFIRMED** / **PARTIALLY-CONFIRMED** / **UNVERIFIED** / **CONTRADICTED**. This doc was fact-checked against an earlier 4-slide internal deck; **deck corrections are called out in §0**.
> **Release-velocity warning:** this feature is moving fast — the guide name, object scope, per-FMG tenant count, and ADOM rules differ by release. **Re-read "Adding FortiSASE" (FMG) + "Central management" (FortiSASE) on every upgrade**, and pin the exact FMG ADOM version + FortiSASE build in each tenant runbook.

---

## 0. Corrections to the current 4-slide deck (read first)

| # | Deck said | Reality | Action |
|---|---|---|---|
| C1 | "One FortiSASE per FortiManager" | **CONTRADICTED for 7.6.5+/8.0.** Limit is **one FortiSASE per ADOM**; a single FortiManager manages **multiple** FortiSASE (multi-ADOM **from 7.6.5**; OU/sub-OU at 8.0). True on **≤7.6.4** — 7.6.2 and 7.6.4 both still say *"Only one FortiSASE can be onboarded per FortiManager."* | Replace with "one FortiSASE **per ADOM**; multiple per FortiManager (**7.6.5+**)." Strengthens the MSSP story. |
| C2 | "FortiGates managed in this ADOM **auto-authorize** with this tenant's FortiSASE for ZTNA posture-tag updates" | **Overstated.** ADOM-scoped **ZTNA Fabric Telemetry + tag sync is real** (MSSP arch guide), but per-FortiGate posture exchange is authorized via **FortiClient Cloud connection**, not ADOM placement alone. | Keep the co-location design; change "auto-authorize" → "participate in ZTNA Fabric Telemetry / tag sync within the ADOM; each FortiGate still connects to FortiClient Cloud to be authorized." |
| C3 | Zone-flow maps to "internet access / private access / **SaaS** / etc." | Only **two installable policy types**: **Internet Access** & **Private Access**. SaaS/SSA is a security-profile construct, not a third normalized-interface flow. | Collapse the zone-flow table to **Internet Access vs Private Access**. |
| C4 | "Supported Models & Firmware **matrix**" | **No consolidated FMG-version matrix exists** in the docs. | Cite **version thresholds** instead: FMG **7.4.8** (feature introduced, w/ FortiSASE 24.3/24.4) / **7.6.2** (formal "Adding FortiSASE" connector topic) / **7.6.5** (multi-FortiSASE per FMG, multi-ADOM) / **8.0** (OU/sub-OU multitenancy). |

Everything else in the deck — FortiCare-ticket gate, FortiManager Key, normalized interfaces, 3,000-object ceiling, conditional policy-type sync (proxy-off = failed install), flow→proxy best-match, client-to-client never syncs, Install Preview as law, one-way fix loop — **verified** (details below).

---

## 1. Phase 0 (the gate): Does this need a FortiCare ticket? — YES. **CONFIRMED.**

Central management is a **select availability** feature. Fortinet must enable it **per FortiSASE instance**; it is **not** GA self-service as of 26.1.99.

> "This feature is a select availability feature in FortiSASE that is not enabled by default on new instances." — [Central Management | FortiSASE feature-admin-guide 26.1.107](https://docs.fortinet.com/document/fortisase/latest/feature-administration-guide/241417/central-management)
> "If you require this feature for your new or existing FortiSASE instance, create a new ticket with FortiCare Support." — same page.
> "Central management is still a select availability feature that requires a Fortinet Support ticket to enable on new and existing instances." — [What's new | FortiSASE 26.1.99](https://docs.fortinet.com/document/fortisase/26.1.99/feature-release-notes/661728)
> "FortiSASE includes several features with select availability… A customer can request enabling a select availability feature for an existing FortiSASE instance by creating a new ticket with FortiCare Support." — [Select availability features | FortiSASE](https://docs.fortinet.com/document/fortisase/latest/administration-guide/391950/select-availability-features)

**The portal toggle is the operator step AFTER the ticket** (not a substitute):
> "To enable central management on FortiSASE: 1. Go to System > Central Management. 2. Set Status as Enabled and click Apply." — [Enabling central management | FortiSASE](https://docs.fortinet.com/document/fortisase/latest/administration-guide/311995/enabling-central-management)

**Sequence:** ① FortiCare ticket (per instance, select availability) → ② portal `System > Central Management > Enable` → ③ copy FortiManager Key → ④ add to FortiManager.

> **Spectrotel ops note:** the ticket is the **longest-lead item** — open it at deal signature, per tenant instance. No ticket = the portal toggle does nothing.

---

## 2. The road — six phases

### Phase 1 — Prerequisites
- **FortiCare ticket** done (§1).
- **FortiManager version** (no formal matrix — use thresholds): **7.4.8** first introduced FortiSASE central management (paired with FortiSASE 24.3/24.4); **7.6.2** formalized the "Adding FortiSASE" connector topic; **7.6.5** is the first build to support **multiple FortiSASE across ADOMs**; **8.0** adds OU/sub-OU multitenancy. *(version thresholds confirmed; no single compatibility table published.)* **➜ For MSSP: deploy 7.6.5+ — see the version-delta box below.**

> **Version delta — FMG 7.4 vs 7.6 managing a FortiSASE tenant (CONFIRMED).** The *sync model is identical across 7.4.8 and 7.6.x* — one-way sync, read-only synced objects, 3,000-object cap, the SASE_ingress/SASE_public/SASE_secure_private_access zones, the limited supported-object set, partial firewall+proxy policy support, Install Preview, and "Install Device Settings (only)" all shipped in **7.4.8** ([FMG 7.4 New Features 921494](https://docs.fortinet.com/document/fortimanager/7.4.0/new-features/921494/central-policy-management-and-synchronization-for-fortisase-7-4-8)). The decisive difference is **scale**: 7.4.x (and 7.6.0–7.6.4) is hard-capped at **one FortiSASE per FortiManager** — *"Only one FortiSASE can be onboarded per FortiManager"* ([7.6.2](https://docs.fortinet.com/document/fortimanager/7.6.2/administration-guide/907875/adding-fortisase), [7.6.4](https://docs.fortinet.com/document/fortimanager/7.6.4/administration-guide/907875/adding-fortisase)). **7.6.5** is the first build that reads *"Multiple FortiSASE can be added to the FortiManager… in different ADOMs"* ([7.6.5](https://docs.fortinet.com/document/fortimanager/7.6.5/administration-guide/907875/adding-fortisase)). 7.4.x also lacks a standalone "Adding FortiSASE" onboarding topic and the explicit ADOM-placement guardrails (documented from 7.6.2). **Net for an MSSP managing many tenants: 7.4.x = one tenant per FMG (dealbreaker); deploy 7.6.5+ (ideally 7.6.6 or 8.0).**
- **Account model:** **same FortiCloud account = auto-detect** (no key paste); **cross-account / MSSP = unique FortiManager Key per tenant**.
  > "When the FortiManager and FortiSASE are under the same FortiCloud account, you do not need to specify this key when adding the FortiSASE device." — [Adding FortiSASE | FMG 8.0.0](https://docs.fortinet.com/document/fortimanager/8.0.0/administration-guide/907875/adding-fortisase) — **CONFIRMED**
  > "When FortiSASE is on the same FortiCloud account as FortiManager, you will receive a notification in the FortiManager toolbar that the FortiSASE management license is detected. Click on the notification to begin." — same — **CONFIRMED**

### Phase 2 — ADOM design (a one-shot decision)
- **One FortiSASE per ADOM** (a "dedicated" ADOM in effect):
  > "Currently, each ADOM in FortiManager supports synchronizing configuration with a single FortiSASE instance." — [What's new | FortiSASE 26.1.99](https://docs.fortinet.com/document/fortisase/26.1.99/feature-release-notes/661728) — **CONFIRMED**
- **Disallowed ADOMs:**
  > "FortiSASE cannot be added to version 7.0 ADOMs or the Global Database ADOM. FortiSASE cannot be added to ADOMs operating in Backup mode." — [Adding FortiSASE | FMG 7.6.6](https://docs.fortinet.com/document/fortimanager/7.6.6/administration-guide/907875/adding-fortisase) — **CONFIRMED**
- **No moves after add (8.0):** "Once added, FortiSASE devices cannot be moved to other ADOMs." — [Adding FortiSASE | FMG 8.0.0](https://docs.fortinet.com/document/fortimanager/8.0.0/administration-guide/907875/adding-fortisase) — **CONFIRMED**
- **Standardize** ADOM naming to the customer/OU, lock admin RBAC + change-control ownership **before the first sync**.
- **Co-locate the managed FortiGate fleet** in the tenant's ADOM for **ZTNA Fabric Telemetry + tag sync** (see §5c) — but each FortiGate is still authorized to FortiSASE via **FortiClient Cloud** (correction C2).
- **Global Database caveat:** SASE normalized interfaces are auto-created **only inside the ADOM**, not in the Global DB ADOM — "In the Global Database ADOM, you must manually configure the normalized interfaces that the Connector to FortiSASE automatically configures within an ADOM." — [Central management | FortiSASE](https://docs.fortinet.com/document/fortisase/latest/feature-administration-guide/25704/central-management) — **CONFIRMED**

### Phase 3 — Connect
1. **Tenant portal:** `System > Central Management > Enable` → copy the **FortiManager Key**.
   > "The FortiManager Key is a non-expiring token which can be used when adding FortiSASE to FortiManager…" — [Adding FortiSASE | FMG 8.0.0](https://docs.fortinet.com/document/fortimanager/8.0.0/administration-guide/907875/adding-fortisase) — **CONFIRMED** (non-expiring)
2. **FortiManager:** `Fabric View > Fabric Connectors > FortiSASE Connector` → paste the key (cross-account). Same-account tenants appear as a **toolbar notification** instead.
3. **Verify both ends:**
   > "In Fabric View > Fabric Connectors, observe that the FortiSASE Connector is enabled" and "a Managed FortiSASE device has been added after the FortiSASE Connector has been enabled." — [Configuring FortiManager for central management | FortiSASE](https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/329531/configuring-fortimanager-for-central-management) — **CONFIRMED**
   - Portal central-management header naming the linked FMG + bound ADOM — **UNVERIFIED** (validate visually in-product; no doc sentence found).
- **Direction of sync — CONFIRMED one-way:**
  > "Currently, central management supports only one-way synchronization of configurations from FortiManager to FortiSASE." — [Adding FortiSASE | FMG 8.0.0](https://docs.fortinet.com/document/fortimanager/8.0.0/administration-guide/907875/adding-fortisase)

### Phase 4 — Build (zones → policy types → objects)
**Normalized interfaces auto-created by the connector** (`Policy & Objects > Normalized Interface`):
> "When the Connector to FortiSASE is enabled in FortiManager, this connector automatically configures normalized interfaces within the selected ADOM… with these interfaces specified as incoming and outgoing interfaces and the resulting traffic flow used to define FortiSASE policy types." — [Normalized interfaces used with FortiSASE | FortiSASE 26.1.99](https://docs.fortinet.com/document/fortisase/26.1.99/feature-administration-guide/318650/normalized-interfaces-used-with-fortisase) — **CONFIRMED**

**Three zones:** `SASE_ingress_zone` · `SASE_public_zone` · `SASE_secure_private_access_zone`.

**Zone-flow → policy-type mapping (CONFIRMED; correction C3 — two types only):**
| Incoming → Outgoing | FortiSASE policy type | Notes |
|---|---|---|
| `SASE_ingress_zone` → `SASE_public_zone` | **Internet Access (SIA)** | the public/internet egress flow |
| `SASE_ingress_zone` → `SASE_secure_private_access_zone` | **Private Access (SPA)** | requires **Secure Private Access enabled** to install |
| `SASE_ingress_zone` → `SASE_ingress_zone` | **client-to-client — NOT synced** | stays portal-side (see §3 pothole) |
> "Using the normalized interfaces created by the FortiSASE connector, you can configure policies in FortiManager which map to specific FortiSASE policies based on the traffic flow from incoming to outgoing interfaces." — [Mapping of FortiManager policies to FortiSASE policies | FortiSASE](https://docs.fortinet.com/document/fortisase/latest/feature-administration-guide/204861/mapping-of-fortimanager-policies-to-fortisase-policies)

**Dedicated policy package per tenant — CONFIRMED:**
> "FortiSASE security policies require dedicated Security Policy Package on FortiManager, because they have special requirements and limitations compared to the regular FortiGate policies. This is to align to the security policy structure designed on FortiSASE." — [Supported objects | FortiSASE](https://docs.fortinet.com/document/fortisase/latest/feature-administration-guide/441430/supported-objects-for-policies-and-proxy-policies)
**Never reuse/share a FortiGate policy package.** One SASE-only package per tenant.

**Object staging — two methods, both CONFIRMED:**
- **Implicit:** "The objects used in policies are implicitly synced to FortiSASE during the policy package installation." — [Central management | FortiSASE](https://docs.fortinet.com/document/fortisase/latest/feature-administration-guide/25704/central-management)
- **Explicit:** in *Edit FortiSASE Connector*, click **Specify** next to the object type → select objects → run Install Wizard → **"Install Device Settings (only)"**. — [Configuring settings using Device Manager in FortiManager | FortiSASE](https://docs.fortinet.com/document/fortisase/26.1.99/feature-administration-guide/414683/configuring-settings-using-device-manager-in-fortimanager)

### Phase 5 — First install
- **Install Preview is law** — review the exact CLI before commit:
  > "Click on Install Preview to see a CLI command preview of the configuration settings to be installed in FortiSASE." — [Configuring settings using Device Manager in FortiManager | FortiSASE](https://docs.fortinet.com/document/fortisase/26.1.99/feature-administration-guide/414683/configuring-settings-using-device-manager-in-fortimanager) — **CONFIRMED**. Make this a NOC standard for every install.
- **Pre-install check (the sneakiest pothole):** confirm the tenant has each pushed policy's **feature enabled + licensed** *before* the install — not after the failure (§3, pothole P1).
- **Verify status:** Device Manager **Config Status** flips **Modified → Installed**; spot-check the tenant portal (synced objects show **read-only**).

### Phase 6 — Steady state
See §6 (verification chain + troubleshooting). The golden rule: **FMG is the source of truth; fix-and-reinstall is the only sanctioned remediation; never hand-patch the portal.**

---

## 3. Pothole catalog (all CONFIRMED unless noted)

**P1 — Conditional policy-type sync (the big one).** A policy type syncs **only if its feature is enabled + licensed** in the tenant.
> "You can only synchronize a policy type when it is visible in FortiSASE and the corresponding feature is enabled with the proper licensing and configuration dependencies. For example, if you attempt to synchronize a Proxy policy from FortiManager to FortiSASE, and the Proxy feature is not enabled, then the synchronization attempt will fail." — [Central management | FortiSASE](https://docs.fortinet.com/document/fortisase/latest/feature-administration-guide/25704/central-management)

**P2 — Flow → proxy "best match"; Internet Access groups only.**
> "FortiSASE treats all flow-based features synchronized from FortiManager as proxy-based features (best match)." / "Security profiles are synchronized with FortiSASE for use with Internet Access security profile groups only." — [Central management | FortiSASE](https://docs.fortinet.com/document/fortisase/latest/feature-administration-guide/25704/central-management)

**P3 — Client-to-client rules never sync.**
> "Central management does not support synchronizing client-to-client traffic policies, that is, policies where the incoming interface and outgoing interface are both specified as SASE_ingress_zone." — [Mapping of FortiManager policies to FortiSASE policies | FortiSASE](https://docs.fortinet.com/document/fortisase/latest/feature-administration-guide/204861/mapping-of-fortimanager-policies-to-fortisase-policies)

**P4 — ~3,000-object sync ceiling.**
> "Central management supports synchronizing a maximum of 3000 objects at once from FortiManager." — [Supported objects | FortiSASE](https://docs.fortinet.com/document/fortisase/latest/feature-administration-guide/441430/supported-objects-for-policies-and-proxy-policies). Keep object libraries lean; sync only what the tenant's policies use.

**P5 — Unsupported objects are silently dropped (not flagged).**
> "If you attempt to synchronize any security profiles or other configuration settings from FortiManager that FortiSASE does not support, they are ignored and not synchronized to FortiSASE." — [Central management | FortiSASE](https://docs.fortinet.com/document/fortisase/latest/feature-administration-guide/25704/central-management)

**P6 — Wildcard FQDN objects unsupported (and their SSL-inspection exclusions).** A *host* object of Type=FQDN with a wildcard value is fine; the dedicated **wildcard-FQDN object type** is not — so SSL-inspection exclusions that rely on it won't sync. — [Central management | FortiSASE](https://docs.fortinet.com/document/fortisase/latest/feature-administration-guide/25704/central-management) — **CONFIRMED**

**P7 — FortiSASE special objects aren't represented in FMG** ("All Agent Devices," "All Edge Devices"). — **CONFIRMED**

**P8 — Don't delete objects in FMG.** One-way sync makes deletions one-way mistakes.
> "…avoid deleting objects from FortiManager to prevent any conflicts." — [Central management | FortiSASE](https://docs.fortinet.com/document/fortisase/latest/feature-administration-guide/25704/central-management). Bake "no FMG deletes without a tested change window" into change-control. (Exact tenant-side delete behavior — clean remove vs orphan — **PARTIALLY-CONFIRMED**.)

**P9 — Bad install is fixed in FMG and re-installed, never patched in the portal.** Synced objects are **read-only** in FortiSASE:
> "After enabling central management, objects synchronized from FortiManager to FortiSASE are considered read-only and you cannot modify them directly in FortiSASE." — [Central management | FortiSASE](https://docs.fortinet.com/document/fortisase/latest/feature-administration-guide/25704/central-management)

**P10 — One-time schedules sync in GMT/UTC (timezone trap).** Schedules **do** sync — but **only one-time schedules**, carried with firewall/proxy policies via policy packages. The gotcha: a one-time schedule set with the FMG **date/time picker is interpreted in GMT** on sync, so it will fire in GMT, not the remote user's local time. **Use the `start-utc` / `end-utc` epoch fields in Advanced Options** to remove the ambiguity. — [Example: one-time schedule | FortiSASE 26.1.99](https://docs.fortinet.com/document/fortisase/26.1.99/feature-administration-guide/306985/example-creating-a-secure-internet-access-policy-with-one-time-schedule) — **CONFIRMED**. (Recurring schedules: **UNVERIFIED** — only one-time is documented as supported.)

---

## 4. Ownership boundary — what FMG owns vs what the portal owns

**FMG-owned (synced down, read-only in portal) — CONFIRMED:** SSL-Inspection / AntiVirus / Web Filter / IPS / File Filter / DLP / DNS Filter / Application Control / Video Filter profiles (Internet Access groups only); external/threat feeds; firewall addresses & groups; services & groups; **firewall schedules (one-time — synced via policy packages; see pothole P10)**; users & user groups (Local/PKI/LDAP); auth sources (LDAP/RADIUS); ZTNA posture tags (Fabric Telemetry — §5c).

**Portal-owned (NOT managed by FMG):**
- **SAML/SSO user groups — CONFIRMED out of scope:** "User groups used for single sign on authentication (SAML) are outside the scope of central management."
- **Special objects** (All Agent/Edge Devices), **SSID configs**, **client-to-client flows**, **ThinEdge/edge-device config** — **PARTIALLY-CONFIRMED** (MSSP arch guide *Configuration management*).
- **Endpoints/user enrollment, on-ramp/edge devices, network/SPA underlay, PoP/security-location selection** — **UNVERIFIED as a clean list** (strongly implied portal-owned; validate in-product before asserting to the customer).

> MSSP arch guide policy directions for the SASE package: **SIA, SPA-To-Hub, SPA-From-Hub**.

---

## 5. MSSP multi-tenant model (Spectrotel scale-out)

- **a) FortiCloud Organizations / OUs / sub-OUs — CONFIRMED.** Organize each customer's FortiCloud accounts into distinct OUs/sub-OUs; multi-level nesting (max **3 levels** from root — **PARTIALLY-CONFIRMED**).
- **b) One ADOM per tenant FortiSASE; one FMG serves many tenants — CONFIRMED.** "In case FortiManager is placed in the Root FortiCare account, all FortiSASE instances from the child-OUs underneath the Root account will be able to connect to FortiManager; one FortiSASE connection per ADOM." — [Adding FortiSASE | FMG 8.0.0](https://docs.fortinet.com/document/fortimanager/8.0.0/administration-guide/907875/adding-fortisase)
- **c) ZTNA Fabric Telemetry + tag sync — CONFIRMED (the one bidirectional exception):** "Each FortiSASE will be able to form ZTNA Fabric Telemetry with a multitenant FortiManager and managed FortiGates of its dedicated ADOM, and synchronize ZTNA tags with them." Synced tags are usable in FMG security policies pushed to **both** FortiSASE and the ADOM's managed FortiGates. — [Multitenancy | Unified SASE for MSSP Arch Guide](https://docs.fortinet.com/document/fortisase/latest/unified-sase-for-mssp-architecture-guide/169721/multitenancy)
- **d) License registration — CONFIRMED:** multitenant devices under the **MSSP Root FortiCare account**; **FortiSASE licenses under the customer's child-OU** FortiCare account.
- **e) FortiSASE MSSP Portal — CONFIRMED:** single unified GUI across tenants, **OU context switch**, per-tenant license/throughput dashboards, all-tenant notification bell. IAM permission profiles = read-only/read-write per area (RBAC detail PARTIALLY-CONFIRMED).
- **f) Multitenancy by version — CONFIRMED:** **7.6.5** is the first build to allow **multiple FortiSASE on one FMG** (*"Multiple FortiSASE can be added to the FortiManager… in different ADOMs"*). **8.0** layers **OU/sub-OU scoping** on top: *"Multiple FortiSASE devices can be added to the FortiManager when they are in the same FortiCloud OU or sub OU; they can be added to the same or different ADOMs"* — feature title *"FortiManager support FortiSASE multitenancy."* So multi-tenant consolidation starts at **7.6.5**; 8.0 adds the OU hierarchy controls.

**Scale-out answer:** target **FMG 7.6.5+ (ideally 7.6.6 or 8.0), one ADOM per tenant, under a Root-account multitenant FortiManager** (N tenants : N ADOMs : 1 FMG). On **≤7.6.4 (and all of 7.4.x)** you're hard-capped at **one FortiSASE per FortiManager** — one FMG per tenant. **8.0** adds OU/sub-OU scoping (parent-OU FMG manages child-OU tenants) for the cleanest MSSP hierarchy. Bind each ADOM's RBAC to the matching child-OU IAM profile so blast radius stays tenant-isolated.

---

## 6. Verification & troubleshooting runbook

**Verification chain (healthy steady state):**
1. **Connector tooltip** (Fabric View) — hover shows status + the live synchronized-object list. **CONFIRMED**
2. **Device Manager → Config Status** — `Modified` (pending) → `Installed` (after Install Wizard). Healthy = **Installed**. **CONFIRMED** (separate "Policy Package Status = Synchronized" wording **PARTIALLY-CONFIRMED** — confirm column label in your build).
3. **Portal central-management header** — should show linked FMG + bound ADOM. **UNVERIFIED** — confirm visually.
4. **Synced objects read-only in the portal** — positive proof the plane is FMG-owned. **CONFIRMED**

**Sync-failure flow — CONFIRMED:**
- Portal raises a **notification** that central-management sync completed with an error → click **View** → **Operations → Logs → Central management synchronizations** → open the **Central Management Synchronization Error Details** slide-in for per-attempt detail. From there you can open a FortiCare ticket, copy details, and download FortiSASE logs. — [Displaying error messages for failed synchronization attempts | FortiSASE 26.1.99](https://docs.fortinet.com/document/fortisase/26.1.99/feature-administration-guide/898041/displaying-error-messages-for-failed-synchronization-attempts)
- **Documented example failure:** a **duplicate network-protocol-enforcement entry in a custom Application Control profile** defined in FortiManager. **CONFIRMED**

**Failure classification (engineering model):**
1. **Unsupported object / policy type** — CONFIRMED class (P5/P7, the duplicate-entry example).
2. **Tenant feature not enabled / not licensed** — the P1 pothole. *Inference labeled as engineering hypothesis — not a single doc sentence (PARTIALLY-CONFIRMED).*
3. **Conflict from an FMG-side deletion** — P8.
→ **Fix in FMG, re-install. Never hand-correct the tenant portal.**

**FMG CLI sync diagnostics — DO NOT hand-copy invented strings.** Pull the version-matching commands from **FortiManager CLI Reference → `diagnose` → `debug`** for your exact build (this is where `diagnose debug enable` and `diagnose debug application <app> <level>` are authoritatively listed). The exact **FortiSASE-sync application keyword is UNVERIFIED** — confirm in your version's CLI reference or via TAC. — [debug (diagnose) | FMG 7.6.3 CLI Reference](https://docs.fortinet.com/document/fortimanager/7.6.3/cli-reference/576677/debug)

**TAC bundle:** portal **Error Details** text + downloaded FortiSASE logs **+** FortiManager-side `diagnose debug` output from the failed run.

**Six golden rules (steady state):**
1. FMG is the source of truth — policy is born there, only there.
2. Install Preview before every install. No exceptions, no Fridays.
3. Deletions ride change control — one-way sync makes them one-way mistakes.
4. Portal work = platform work: endpoints, edge devices, network/SPA, SSO/SAML groups, PoP selection.
5. Keep object libraries lean — the 3,000-object ceiling rewards hygiene.
6. Re-verify limits at every FortiSASE / FMG release — this feature is moving fast.

---

## 7. Verdict ledger (deck claims → status → version)

| Claim | Status | Version |
|---|---|---|
| Central mgmt requires a FortiCare ticket (select availability, per instance) | **CONFIRMED** (still gated) | FortiSASE 26.1.99 |
| Portal `System > Central Management > Enable` + non-expiring FortiManager Key | **CONFIRMED** (operator step *after* ticket) | FortiSASE 26.1.x / FMG 7.6–8.0 |
| Feature went GA self-service | **CONTRADICTED** — still select availability | as of 26.1.99 |
| Same-account auto-detect; MSSP unique key per tenant; FMG 8.0 OU/sub-OU | **CONFIRMED** | FMG 8.0 |
| One FortiSASE **per FortiManager** | **CONTRADICTED** — one per **ADOM**, multiple per FMG from **7.6.5** | ≤7.6.4 vs 7.6.5/8.0 |
| FortiSASE central mgmt first available in FMG | **CONFIRMED** — introduced **7.4.8** (w/ FortiSASE 24.3/24.4); identical sync model in 7.6 | FMG 7.4.8 |
| Supported models/firmware **matrix** | **PARTIALLY** — no matrix; use thresholds 7.4.8 / 7.6.2 / 7.6.5 / 8.0 | FMG 7.4.8–8.0 |
| Dedicated ADOM; not 7.0 / Global / Backup-mode ADOMs | **CONFIRMED** | FMG 7.6.x–8.0 |
| FortiGates in ADOM **auto-authorize** ZTNA posture tags | **CONTRADICTED (wording)** — ZTNA Fabric Telemetry/tag sync is ADOM-scoped, but per-FGT auth is via FortiClient Cloud | FortiSASE latest |
| One-way sync FMG→FortiSASE | **CONFIRMED** | FMG 7.6.x–8.0 |
| Connector auto-creates normalized interfaces; 3 zones | **CONFIRMED** | FortiSASE 26.1.x |
| Zone-flow → policy type (IA / PA only, not SaaS) | **CONFIRMED** (SaaS corrected) | FortiSASE 26.1.x |
| One dedicated SASE policy package per tenant | **CONFIRMED** | FortiSASE 26.1.x |
| Implicit vs explicit object staging ("Install Device Settings only") | **CONFIRMED** | FortiSASE 26.1.x |
| Policy type syncs only if feature enabled+licensed (proxy-off = fail) | **CONFIRMED** (verbatim) | FortiSASE 26.1.x |
| Flow→proxy best-match; Internet Access groups only | **CONFIRMED** | FortiSASE 26.1.x |
| Client-to-client never syncs | **CONFIRMED** (verbatim) | FortiSASE 26.1.x |
| ~3,000-object sync ceiling | **CONFIRMED** (exactly 3000) | FortiSASE 26.1.x |
| Install Preview shows exact CLI | **CONFIRMED** | FortiSASE 26.1.x / FMG 7.6–8.0 |
| One-way fix loop; portal read-only | **CONFIRMED** | FortiSASE 26.1.x |
| Extra potholes: unsupported silently ignored; wildcard-FQDN + SSL exclusions; special objects; Global-DB manual interfaces | **CONFIRMED** | FortiSASE 26.1.x / FMG 7.6–8.0 |
| Firewall **schedules** sync (one-time only, via policy packages); one-time schedules interpreted in **GMT** unless `start-utc`/`end-utc` used | **CONFIRMED** (recurring UNVERIFIED) | FortiSASE 26.1.99 |
| Portal central-mgmt header names FMG+ADOM | **UNVERIFIED** — validate in-product | — |
| Exact FMG `diagnose debug application` sync keyword | **UNVERIFIED** — pull from version CLI ref / TAC | — |

---

## Sources

- [Central Management — FortiSASE feature-admin-guide 26.1.107](https://docs.fortinet.com/document/fortisase/latest/feature-administration-guide/241417/central-management)
- [Central management — FortiSASE feature-admin-guide (25704)](https://docs.fortinet.com/document/fortisase/latest/feature-administration-guide/25704/central-management)
- [Enabling central management — FortiSASE](https://docs.fortinet.com/document/fortisase/latest/administration-guide/311995/enabling-central-management)
- [Select availability features — FortiSASE](https://docs.fortinet.com/document/fortisase/latest/administration-guide/391950/select-availability-features)
- [What's new — FortiSASE feature-release-notes 26.1.99](https://docs.fortinet.com/document/fortisase/26.1.99/feature-release-notes/661728)
- [Normalized interfaces used with FortiSASE — FortiSASE 26.1.99](https://docs.fortinet.com/document/fortisase/26.1.99/feature-administration-guide/318650/normalized-interfaces-used-with-fortisase)
- [Mapping of FortiManager policies to FortiSASE policies — FortiSASE](https://docs.fortinet.com/document/fortisase/latest/feature-administration-guide/204861/mapping-of-fortimanager-policies-to-fortisase-policies)
- [Supported objects for policies and proxy policies — FortiSASE](https://docs.fortinet.com/document/fortisase/latest/feature-administration-guide/441430/supported-objects-for-policies-and-proxy-policies)
- [Configuring settings using Device Manager in FortiManager — FortiSASE 26.1.99](https://docs.fortinet.com/document/fortisase/26.1.99/feature-administration-guide/414683/configuring-settings-using-device-manager-in-fortimanager)
- [Configuring FortiManager for central management — FortiSASE](https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/329531/configuring-fortimanager-for-central-management)
- [Configuring FortiManager for central management of an MSSP tenant — FortiSASE 26.1.99](https://docs.fortinet.com/document/fortisase/26.1.99/feature-administration-guide/449663/configuring-fortimanager-for-central-management-of-an-mssp-tenant)
- [Displaying error messages for failed synchronization attempts — FortiSASE 26.1.99](https://docs.fortinet.com/document/fortisase/26.1.99/feature-administration-guide/898041/displaying-error-messages-for-failed-synchronization-attempts)
- [Adding FortiSASE — FortiManager 8.0.0](https://docs.fortinet.com/document/fortimanager/8.0.0/administration-guide/907875/adding-fortisase)
- [Adding FortiSASE — FortiManager 7.6.6](https://docs.fortinet.com/document/fortimanager/7.6.6/administration-guide/907875/adding-fortisase)
- [New features — FortiManager 8.0.0 ("FortiManager support FortiSASE multitenancy")](https://docs.fortinet.com/document/fortimanager/8.0.0/new-features/380910/overview)
- [Multitenancy — Unified SASE for MSSP Architecture Guide](https://docs.fortinet.com/document/fortisase/latest/unified-sase-for-mssp-architecture-guide/169721/multitenancy)
- [Configuration management — Unified SASE for MSSP Architecture Guide](https://docs.fortinet.com/document/fortisase/latest/unified-sase-for-mssp-architecture-guide/211587/configuration-management)
- [debug (diagnose) — FortiManager 7.6.3 CLI Reference](https://docs.fortinet.com/document/fortimanager/7.6.3/cli-reference/576677/debug)
