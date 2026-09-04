# Fortinet SOC-as-a-Service (SOCaaS) — Engineering & Partner Reference

> **Tier 1/2/3 (labeled inline).** Compiled June 2026 from docs.fortinet.com + Fortinet datasheets/ordering guides. Primary sources: **SOCaaS Data Sheet `SOC-DAT-R15-20260311`**, **SOCaaS Ordering Guide `SOCaaS-OG-R3-20260323`**, **FortiSASE Ordering Guide `FSS-OG-R40-20260525`**, the SOCaaS docs library (`forticloud-socaas`, build 26.2.0), and the 2025-11-11 SOCaaS-expansion blog. Every load-bearing claim carries a verbatim quote + source + status (**CONFIRMED / PARTIALLY-CONFIRMED / UNVERIFIED**).
> **Scope/answers the partner's questions:** what SOCaaS is, **third-party (non-Fortinet) log support**, **why a partner needs it**, **what to expect in an engagement**, and the **global response teams**. SOCaaS is the **Comprehensive/Advanced-tier** SOC piece of FortiSASE, but it's a broader standalone Fortinet service — both views are covered.
> **Sourcing caveat:** docs.fortinet.com pages render client-side; some quotes were captured from Fortinet's own doc-search index. Wording is corroborated across the datasheet + ordering guide (high confidence).

---

## 0. Taxonomy — SOCaaS vs MDR vs Incident Response (nail this first)

Three distinct, separately-licensed FortiGuard services that **collaborate** — not synonyms.

| Service | What it is | Acts or advises? |
|---|---|---|
| **FortiGuard SOCaaS** | 24×7 managed **log/event monitoring + triage + escalation** across the Fortinet fabric **and** third-party sources. Backend = **FortiAnalyzer** (fabric model) or **FortiSIEM** (multi-vendor model). | **Advises** — triages, validates, escalates verified threats + IR guidance; does **not** take network action itself. |
| **FortiGuard MDR** | Managed detection & response **add-on to FortiEDR/FortiEndpoint** (endpoint), per-seat. | **Acts** — "takes actions on behalf of customers" (endpoint containment via FortiEDR). |
| **FortiGuard Incident Response (IR)** | Emergency/breach **DFIR** service, **vendor-agnostic**, available even to non-customers; retainer = **Incident Readiness Subscription**. | **Acts** — containment, forensics, breach investigation. |

> "SOCaaS analyzes security events that you have forwarded, performs alert triage, and escalates verified threat notifications to your security team." — [SOCaaS User Guide, Introduction v26.2.0](https://docs.fortinet.com/document/forticloud-socaas/latest/user-guide/352650/introduction) — **CONFIRMED**
> "An add-on service to FortiEDR, FortiGuard Managed Detection and Response Service focuses on monitoring the alerts and suspicious threats detected by FortiEDR." — [FortiGuard MDR Data Sheet](https://www.fortinet.com/content/dam/fortinet/assets/data-sheets/fortiguard-mdr.pdf) — **CONFIRMED**

**Escalation chain — CONFIRMED:** SOCaaS detects/triages → notifies **MDR** (emails an MDR alias; MDR investigates on the FortiEDR console and contacts the customer) → if a breach is confirmed, the customer's **IR** provider/FortiGuard IR is engaged and SOCaaS "will continue collaborative investigation with the MDR and IR teams." ([Collaboration with MDR](https://docs.fortinet.com/document/forticloud-socaas/latest/user-guide/858679/collaboration-with-mdr))

---

## 1. SOCaaS as part of FortiSASE

**Tier inclusion — CONFIRMED (two corroborating sources):**
> "Log Forwarding to SOCaaS requires an **Advanced or Comprehensive** remote users FortiSASE subscription." — [FortiSASE Admin Guide, Forwarding logs to SOCaaS v26.1.107](https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/404308/forwarding-logs-to-socaas)
> "FortiSASE: **Included with FortiSASE Advanced or Comprehensive Subscriptions**." — [SOCaaS Data Sheet R15](https://www.fortinet.com/content/dam/fortinet/assets/data-sheets/fortiguard-socaas.pdf)

> **Note vs the FortiSASE feature matrix:** doc `03-releases-and-licensing.md` shows "SOC-as-a-Service integration" as a **Comprehensive** column item. The authoritative answer is **Advanced *and* Comprehensive** (admin guide + SOCaaS datasheet + SOCaaS ordering guide all say "Advanced or Comprehensive"). The SOCaaS SKUs ride the FortiSASE Advanced (`FCx-10-EMS05-676`) and Comprehensive (`-759`) subscriptions and bundle **FortiGuard Forensics + SOCaaS**. **Use "Advanced or Comprehensive."**

**What feeds it — CONFIRMED:**
> "When log forwarding to SOCaaS is enabled, **all traffic and event logs from FortiSASE** are forwarded to SOCaaS." — Admin Guide v26.1.107. Source = FortiSASE Analytics. Enable: `Analytics > Settings > Enable Log Forwarding to SOCaaS` → completes onboarding in the SOCaaS portal. **Same SOCaaS backend** as standalone (FortiSASE is just one fabric source feeding the same SOC).

---

## 2. Log sources — and the THIRD-PARTY answer (the SE objection)

SOCaaS runs on **two distinct collection-and-analytics models**, and the supported sources + backend differ. This is the single most important architectural fact.
> "SOCaaS threat detection capabilities are based on two data collection and analytics models." — [SOCaaS Data Sheet R15](https://www.fortinet.com/content/dam/fortinet/assets/data-sheets/fortiguard-socaas.pdf) — **CONFIRMED**

### Model A — Fortinet Fabric Monitoring (FortiAnalyzer-based) = Fortinet-only in practice
> "Network traffic and endpoint activity can be monitored when supported Fortinet Security Fabric devices, such as FortiGate or FortiClient/FortiEndpoint, are onboarded… **FortiAnalyzer serves as the primary analytics platform** to collect, process, and forward logs to the SOC. Onboarding typically takes only a few days." — Data Sheet R15 — **CONFIRMED**

Named fabric sources (datasheet diagram + ordering-guide matrix): **FortiGate/FortiWiFi, FortiClient/FortiEndpoint, FortiSASE, FortiWeb/FortiAppSec, FortiEDR, FortiRecon, FortiAnalyzer(Cloud)**. Notes:
- FortiSASE path: "logs will be sent from **FortiSASE Analytics** to SOCaaS." — **CONFIRMED**
- **FortiEDR is not standalone:** "FortiEDR Monitoring is only available if Network is monitored by SOCaaS i.e. FortiSASE or at least one FortiGate must be monitored." — **CONFIRMED**
- FortiMail / FortiAuthenticator / FortiSandbox as *named* fabric sources — **UNVERIFIED** (would fall under the multi-vendor model). FortiGate **Cloud** as a current feed path — **UNVERIFIED** (current docs say FortiAnalyzer/FAZ-Cloud).

### Model B — Multi-Vendor Monitoring (FortiSIEM-based) = THE third-party path ✅
**YES — SOCaaS ingests non-Fortinet logs (M365, Entra/Azure AD, AWS, third-party firewalls, EDR) — but ONLY via this model, powered by FortiSIEM, licensed separately.**
> "A wide range of assets including applications, network devices such as firewalls, and cloud services from **Fortinet and third-party vendors** can be monitored under this model. Onboarding additional data sources may take **several weeks**… Deployment of on-premises or cloud-based log collectors, as well as agent installation, may be required." — Data Sheet R15 — **CONFIRMED**
> "**FortiSIEM serves as the primary security analytics platform for this monitoring model**… As a result, **all data sources and connectors supported by FortiSIEM are available** for integration." — Data Sheet R15 — **CONFIRMED**
> "Support for key third-party detection sources, including **Microsoft Defender** and more, extend security monitoring coverage into mixed environments… without the need to rip-and-replace existing tools." — [SOCaaS blog 2025-11-11](https://www.fortinet.com/blog/security-operations/fortinet-expands-managed-socaas-accessible-cyber-defense-for-every-organization) — **CONFIRMED**

**The crisp answer for Spectrotel:** *"Yes, SOCaaS monitors third-party logs — Microsoft 365/Entra, AWS, other-vendor firewalls, EDR — through its **Multi-Vendor Monitoring** model, which runs on **FortiSIEM** with Fortinet-supplied collectors/agents. It's a **separate SKU (1 GB/day)**, the source catalog = the FortiSIEM connector list, and third-party onboarding takes **several weeks** vs a few days for Fortinet devices."* (The FortiAnalyzer fabric path is effectively Fortinet-only; **"FortiSOAR ingests your third-party logs" is UNVERIFIED** — SOAR is internal SOC automation, not the ingest engine.)

---

## 3. What the SOC actually does (automated vs human)

Pipeline (all CONFIRMED, Data Sheet R15 + Intro v26.2.0):
1. **Ingest** — fabric/FortiSASE → FortiAnalyzer (or FortiSIEM for multi-vendor) → SOC cloud.
2. **Automated** — "Automated correlation, analysis, and context enrichment using **SOAR playbooks**" + "**AI-driven alert triage**… enriched by CMDB meta data as well as historical activities of affected assets."
3. **Human analyst** — "verification by expert SOC analysts… validation of events as verified incidents with customer escalation via **phone and email**." Only **escalated, validated** alerts reach the customer (false-positive reduction).
4. **Guided remediation** — "SOC provides an analysis, verdict, severity and **Incident Response guidance** to contain and mitigate… Source of detection, IOCs, affected users and entities, triage reports… are made available."
5. **Tuning loop** — "Feedback channels… to reduce noise and false-positive alerts. Requests can be made to tune detection rules, define exceptions and exclusions."

**SOCaaS does not block/contain on the network itself** — it guides; containment happens via Managed FortiGate / MDR / FortiEDR. **CONFIRMED.**

---

## 4. Global response teams (who staffs the SOC)

- **24×7×365, "Global Response Teams," follow-the-sun** — CONFIRMED (Data Sheet R15; FAQ: "The service runs on a 24x7x365 basis with security experts leading investigations and incident triage").
- **Regions: North America, EMEA, APAC** — CONFIRMED.
- **Named SOC data-center/response cities (datasheet graphic):** Burnaby (CA), Plano TX (US), Nice (FR), Madrid (ES), Paris (FR), Frankfurt (DE), Prague (CZ), Singapore, Tokyo (JP), Sydney (AU) — **CONFIRMED**. ⚠ The "San Jose / Ottawa" 9-city version that circulates is **UNVERIFIED/contradicted** — use the datasheet list.
- **Analysts** described as "**certified SOC analysts**" — CONFIRMED. Specific certs (CISSP/CEH/OSCP) and a Tier-1/2/3 structure — **UNVERIFIED (not published)**.
- **Scale:** "nearly **1,000 FortiGuard Labs researchers**, global SOC analysts, and hundreds of threat intelligence partners" — CONFIRMED (blog; combined figure, not SOC-analyst headcount). The "200 researchers" figure floating around is **UNVERIFIED** — don't cite.

---

## 5. FortiGuard Incident Response (the breach-response muscle behind SOCaaS)

- IR is **vendor-agnostic** and serves **non-customers**: "The FortiGuard Labs team provides a vendor-agnostic response to those experiencing an emergency" / "able to support all victims including those who may not already be Fortinet or FortiGuard customers… available 24/7 throughout all stages of the incident response lifecycle." — [/respond](https://www.fortinet.com/solutions/enterprise-midsize-business/security-as-a-service/respond) + [community tip](https://community.fortinet.com/t5/FortiGuard/Technical-Tip-Engaging-FortiGuard-Incident-Response-Services-to/ta-p/263137) — **CONFIRMED**
- **DFIR scope:** compromised hosts/accounts, timeline, malware analysis, IOCs, exfiltration, initial-access/patient-zero. — **CONFIRMED**
- **Retainer = FortiGuard Incident Readiness Subscription**, points-based ("Incident Response Support," "Incident Response Playbook Development"), with a subscriber response commitment: "**Respond to Security Incidents Within One Hour**" (footnote: "For subscribers. Others, shortly thereafter."). — [/respond](https://www.fortinet.com/solutions/enterprise-midsize-business/security-as-a-service/respond) + [FortiCare IR 26.2.0](https://docs.fortinet.com/document/forticloud/26.2.0/forticare/102154/incident-response) — **CONFIRMED**
- ⚠ The specific retainer tiers ("Standard 25 pts/100 hrs, Lite 10 pts/40 hrs, 1-hr vs 24-hr SLO") are **UNVERIFIED** — confirm against current SKU sheets before quoting numbers.

---

## 6. Why a PARTNER/MSSP needs it (build-vs-buy) — Tier-3 positioning, page-verified

- **Building a SOC is hard:** needs "advanced tooling, mature processes, and highly trained analysts, all of which are scarce and costly" — "beyond the reach of most organizations." — blog 2025-11-11 — CONFIRMED.
- **Partners can monetize directly:** "MSSP can **resell, OEM, or integrate** SOC capabilities into their portfolios." — CONFIRMED.
- **Augments the partner's own NOC/team:** "supplements your existing teams with Fortinet expertise and AI-driven processes"; "eliminates the struggle of hiring and retaining experienced professionals for critical, continuous security operations." — CONFIRMED.
- **Speed/value claims (Tier-3 marketing — quote with care):** "Go live in days, not months," "cut false positives by **up to 85%**," "response times as fast as **15 minutes**." — CONFIRMED as published; treat 85%/15-min as marketing.
- **Built multi-tenant for MSSPs:** "Multi-tenancy is **in the core of SOCaaS design** and **meets ISO and SOC2** compliance… Partners can choose to grant access to their clients." MSSP can "purchase and register SOCaaS on behalf of their customers." — Data Sheet R15 + SOCaaS OG — CONFIRMED.

---

## 7. What to expect in an engagement

**Onboarding (CONFIRMED):** 4 steps — register/license devices in FortiCloud → submit onboarding request (wizard) → set up log forwarding (FortiGate→FortiAnalyzer→SOC-supplied destination URL) → add more devices. **Fortinet-device onboarding: "a few days"** (welcome within ~3 business days PST); **third-party: "several weeks."** A free FortiAnalyzer is included in the trial.
**Who does what:** customer registers/licenses, enables+forwards logging, runs the wizard, points FAZ at the SOC URL; Fortinet preps the tenant, supplies the destination URL, then monitors/triages/escalates 24×7.
**Service Delivery Manager (SDM):** "dedicated Service Delivery Managers provide guidance through your SOCaaS journey… On-demand service reviews." — CONFIRMED. (Analysts are a **pooled** global team, not named — pooling is implied, PARTIALLY-CONFIRMED.)
**Escalation tree / comms:** email + phone; customer-configurable primary/secondary contacts. Escalation email carries Alert ID/Severity/Type/Detection Time. SOC outbound phone numbers (outgoing only — cannot call in): **AMER +1 (866) 648 4638 · EMEA +33 4 89 87 05 55 · APAC +60 3 2719 7600** (backup +60 3 9770 7600). Secure portal to "track threats, review escalations, and message Fortinet experts." — CONFIRMED.
**Escalation SLAs (datasheet targets — see caveat):** **P1 = 15 min · P2 = 45 min · P3 = 90 min · P4 = 6 hr**; **24×7×365**; **99.99% availability**. — CONFIRMED as published (datasheet carries a non-binding disclaimer; restate in the signed Service Description to make contractual).
**Reporting cadence:** **weekly summary reports auto-generated every Sunday** (covering Sun–Sat) + a **monthly asset-inventory report** + **on-demand/quarterly SDM service reviews** + reports on request. — CONFIRMED. ⚠ ("Monthly" applies to the asset inventory; the security summary is **weekly** — don't say "monthly reports" generically.)
**Threat hunting:** **on request**, not a proactive default — "Requests for threat hunting and further investigations into incidents can be made." — CONFIRMED.

---

## 8. Data handling

- **Regions:** data centers / SOC in **North America, EMEA, APAC**; customer provisions **FortiAnalyzer Cloud in the region of choice** and the **SOC collection point is in that same region** (residency control). — CONFIRMED / PARTIALLY-CONFIRMED (region-of-choice from doc search snippet).
- **Retention:** "By default, logs are retained for **90 days**" (FortiAnalyzer Cloud default; longer needs a storage-expansion SKU). — CONFIRMED.
- **Log limit:** "SOCaaS does not enforce a daily log limit" / "Unlimited Log Capacity" — CONFIRMED (but the multi-vendor SKU is *billed* per 1 GB/day, and the complimentary FAZ-Cloud has storage caps).
- **Multi-tenancy / compliance:** "Multi-tenancy is in the core… meets **ISO and SOC2**… **data boundary is maintained**." — CONFIRMED. A formal DPA/privacy/sovereignty clause is **UNVERIFIED** in public docs — request the Service Description.

---

## 9. Licensing & prerequisites

- **Mandatory prereq: a FortiAnalyzer (on-prem or Cloud)** with FortiGate forwarding to it; trial includes a free FAZ. — CONFIRMED.
- **Three service lines (Data Sheet R15) — CONFIRMED:**
  1. **SOCaaS Multi-Vendor Monitoring** — per **1 GB/day** of logs, Fortinet + third-party (FortiSIEM). SKU `FC1-10-SOCAS-1314-02-DD`.
  2. **SOCaaS Fabric Monitoring** — per-device/bundle: FortiGate add-on `FC-10-[model]-464` (incl. limited FAZ-Cloud; `-463` GB/day storage expansion; each HA member licensed); **FortiSASE = bundled with Advanced/Comprehensive** (`FCx-10-EMS05-676/-759`); FortiWeb/FortiAppSec; FortiClient (with FortiGuard Forensics); FortiEndpoint; FortiEDR (with XDR/Managed-XDR).
  3. **SOCaaS Managed FortiAnalyzer Service** — FAZ G-series platform monitoring **only** (NOT threat analysis of its logs — that needs a separate license).
- **Billing models:** per-device (FGT/FWB/FAZ), per-seat-bundle (FCT/FEP/FEDR), per-GB/day (Multi-Vendor). **FortiFlex & FortiPoints accepted** (incl. FortiFlex MSSP postpaid consumption). — CONFIRMED.
- **MSSP:** "MSSP can purchase and register SOCaaS on behalf of their customers… define multiple tenants." Multi-Vendor tenancy = **dedicated devices/data sources only** (no shared-device mode). — CONFIRMED.

---

## 10. Partner / MSSP SOCaaS API (maps to our local SDK)

There's an official **SOCaaS Portal API** for partners — and it lines up with our local `MSSP-SE-Tools/SOCaaS-SDK` (`socaas.mss.fortinet.com`, `client_id=socaas`, FortiCloud OAuth):
> The API lets MSSPs/partners "integrate with SOCaaS to ingest SOC alerts and their correlations, as well as Service Requests into their ticketing system." Operations: "**Get alert lists**," "Get alert details by UUID," "Update the alert status," "Get comment list," "Create a comment," "Download files and attachments," "Get list of Service Requests," "**Create Service Request**," "Get Service Request details," "**Get MSSP client list**," "Download SOC reports," "Get Account information," "Submit MSSP Client Onboarding Request." — [SOCaaS Portal APIs for customers](https://docs.fortinet.com/document/forticloud-socaas/latest/user-guide/162337/socaas-portal-apis-for-customers) — **CONFIRMED**

Maps to our SDK: `list_alerts` → *Get alert lists*; `create_service_request` → *Create Service Request*; `list_clients` → *Get MSSP client list*; plus `comments.py`/`files.py`/`reports.py` → the comment/file/report ops. **Auth:** "A FortiCloud API user is required." Exact endpoint **path strings are FNDN-gated** (UNVERIFIED publicly) — our SDK already encodes them; confirm against FNDN on the next API change.

---

## 11. Potholes / gotchas

| # | Pothole | Status |
|---|---|---|
| S1 | Third-party logs need the **Multi-Vendor (FortiSIEM) SKU** — separate 1 GB/day license, "several weeks" to onboard. The fabric (FortiAnalyzer) path is Fortinet-only. | CONFIRMED |
| S2 | **A FortiAnalyzer (on-prem or Cloud) is mandatory**; the FortiGate add-on's bundled FAZ-Cloud is storage-limited (plan the `-463` expansion). | CONFIRMED |
| S3 | SOCaaS **advises, doesn't act** on the network — containment needs Managed FortiGate / MDR / FortiEDR. | CONFIRMED |
| S4 | FortiEDR monitoring **requires** an existing FortiGate/FortiSASE network feed. | CONFIRMED |
| S5 | Reporting: **weekly** security summary (Sundays) + **monthly** asset inventory — don't say "monthly reports" generically. | CONFIRMED |
| S6 | Datasheet SLAs (P1 15 min, 99.99%) are **non-binding** until restated in the signed Service Description. | CONFIRMED |
| S7 | SOC phone numbers are **outbound-only** (can't call in) — escalations come *to* you. | CONFIRMED |
| S8 | Don't quote MTTD/MTTR or a fixed %-alert-reduction — only "up to 85%" (marketing) is published; no MTTD/MTTR numbers exist. | CONFIRMED (absence) |
| S9 | IR retainer point/hour **tiers** unverified — confirm SKUs. | UNVERIFIED |
| S10 | Formal DPA/privacy/sovereignty clause not in public docs — get the Service Description. | UNVERIFIED |

---

## 12. Verdict ledger (key claims)

| Claim | Status | Source |
|---|---|---|
| SOCaaS = managed monitoring + triage + escalation (advises, not acts) | CONFIRMED | Intro 26.2.0 / DS R15 |
| SOCaaS, MDR, IR are 3 distinct collaborating services | CONFIRMED | MDR DS / Collab-MDR doc |
| In FortiSASE: requires **Advanced or Comprehensive** | CONFIRMED | FortiSASE Admin Guide 26.1.107 + SOCaaS DS R15 |
| FortiSASE forwards **all traffic + event logs** to SOCaaS | CONFIRMED | Admin Guide 26.1.107 |
| **Third-party logs YES — via Multi-Vendor/FortiSIEM model, separate 1 GB/day SKU, ~weeks to onboard** | CONFIRMED | DS R15 / OG R3 / blog 2025-11-11 |
| Fabric model = FortiAnalyzer = Fortinet-fabric in practice | CONFIRMED | DS R15 |
| Microsoft Defender named 3rd-party source | CONFIRMED | blog 2025-11-11 |
| Automated SOAR+AI triage, then human analyst validation | CONFIRMED | DS R15 / Intro 26.2.0 |
| 24×7×365, NA/EMEA/APAC, named SOC cities (Burnaby/Plano/Nice/Madrid/Paris/Frankfurt/Prague/Singapore/Tokyo/Sydney) | CONFIRMED | DS R15 / FAQ |
| "San Jose/Ottawa" 9-city SOC list | UNVERIFIED/contradicted | — |
| ~1,000 FortiGuard Labs researchers + SOC analysts + partners | CONFIRMED | blog 2025-11-11 |
| IR is vendor-agnostic, non-customers, 24/7; retainer = Incident Readiness Subscription; subscriber 1-hr response | CONFIRMED | /respond / FortiCare 26.2.0 |
| IR retainer point/hour tiers | UNVERIFIED | — |
| Partners can resell/OEM/integrate; multi-tenant core; ISO/SOC2 | CONFIRMED | blog / DS R15 |
| Onboarding wizard; Fortinet "a few days," 3rd-party "several weeks"; SDM assigned | CONFIRMED | DS R15 / onboarding QSG / FAQ |
| Escalation P1 15m/P2 45m/P3 90m/P4 6h; 99.99%; email+phone (outbound-only) | CONFIRMED | DS R15 / alert-escalation doc |
| Reporting weekly (Sun) + monthly asset inventory + on-demand SDM review | CONFIRMED | Reports doc / Intro |
| Threat hunting on request (not default) | CONFIRMED | DS R15 |
| Data centers NA/EMEA/APAC; 90-day default retention; region-of-choice | CONFIRMED / PARTIALLY | FAQ / onboarding |
| FortiAnalyzer mandatory; free FAZ in trial | CONFIRMED | onboarding FAQ |
| 3 service lines (Multi-Vendor / Fabric / Managed FAZ); FortiFlex+FortiPoints | CONFIRMED | DS R15 / OG R3 |
| Partner API (Get alert lists / Create Service Request / Get MSSP client list) → maps to local SOCaaS SDK | CONFIRMED (paths FNDN-gated) | SOCaaS Portal APIs doc |

---

## 13. Sources
- [SOCaaS Data Sheet (SOC-DAT-R15-20260311)](https://www.fortinet.com/content/dam/fortinet/assets/data-sheets/fortiguard-socaas.pdf)
- [SOCaaS Ordering Guide (SOCaaS-OG-R3-20260323)](https://www.fortinet.com/content/dam/fortinet/assets/data-sheets/og-socaas.pdf)
- [FortiSASE Ordering Guide (FSS-OG-R40-20260525)](https://www.fortinet.com/content/dam/fortinet/assets/data-sheets/og-fortisase.pdf)
- [FortiGuard MDR Data Sheet](https://www.fortinet.com/content/dam/fortinet/assets/data-sheets/fortiguard-mdr.pdf)
- [FortiSASE — Forwarding logs to SOCaaS (26.1.107)](https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/404308/forwarding-logs-to-socaas)
- [SOCaaS User Guide — Introduction (26.2.0)](https://docs.fortinet.com/document/forticloud-socaas/latest/user-guide/352650/introduction)
- [SOCaaS — Collaboration with MDR](https://docs.fortinet.com/document/forticloud-socaas/latest/user-guide/858679/collaboration-with-mdr)
- [SOCaaS — Alert Escalation](https://docs.fortinet.com/document/forticloud-socaas/latest/user-guide/229890/alert-escalation)
- [SOCaaS — Reports](https://docs.fortinet.com/document/forticloud-socaas/latest/user-guide/563306/reports)
- [SOCaaS — Service overview FAQ](https://docs.fortinet.com/document/forticloud-socaas/latest/frequently-asked-questions/466773/service-overview)
- [SOCaaS — Subscription & onboarding FAQ](https://docs.fortinet.com/document/forticloud-socaas/latest/frequently-asked-questions/317544/subscription-and-onboarding)
- [SOCaaS — Portal APIs for customers](https://docs.fortinet.com/document/forticloud-socaas/latest/user-guide/162337/socaas-portal-apis-for-customers)
- [SOCaaS — MSSP Onboarding Guide (26.2.0)](https://docs.fortinet.com/document/forticloud-socaas/26.2.0/mssp-onboarding-guide)
- [FortiGuard IR / Respond](https://www.fortinet.com/solutions/enterprise-midsize-business/security-as-a-service/respond)
- [FortiCloud FortiCare — Incident Response (26.2.0)](https://docs.fortinet.com/document/forticloud/26.2.0/forticare/102154/incident-response)
- [Fortinet Expands Managed SOCaaS (blog, 2025-11-11)](https://www.fortinet.com/blog/security-operations/fortinet-expands-managed-socaas-accessible-cyber-defense-for-every-organization)
- [FortiFlex Concept Guide — Enterprise & MSSP (26.1.0)](https://docs.fortinet.com/document/flex-vm/26.1.0/fortiflex-concept-guide/310137/enterprise-and-mssp)
