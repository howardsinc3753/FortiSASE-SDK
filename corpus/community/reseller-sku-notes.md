---
title: Reseller SKU corroboration notes (FortiSASE)
source_url: https://www.spectrum-edge.com/fortisase-licensing-guide/
authority: reseller
caveat: SKU prices, user bands, and the "1.5 Mbps/user" framing are reseller interpretation and may be stale. ALWAYS confirm against the current Fortinet Ordering Guide (Tier 3) before quoting. The authoritative bandwidth metric is 25 TB / 100 users, NOT a per-user Mbps figure.
captured: 2026-06-11
---

# Reseller SKU corroboration (use only to cross-check Tier-3)

These third-party listings were used **only to corroborate** SKUs already stated in the FortiSASE Ordering Guide. They are not independent authority.

- FC2-10-EMS05-547 = FortiSASE **Standard**, 50–499 users (firewalls.com).
- FC2-10-EMS05-676 = FortiSASE **Advanced**, 50–499 users (Insight).
- FC-10-F120G-1230 = older Starter Kit + SD-WAN SPA reference (CDW). **Superseded** — the current Ordering Guide starts the SASE/SPA bundle at **60G+ / 5 users**, not 120G/10.
- "No mixing tiers within a single instance" (Spectrum-Edge) — corroborates the Ordering Guide, with the OG exception that the Region add-on can combine with Comprehensive.
- "~1.5 Mbps per user" (Spectrum-Edge) — **distrust**; use 25 TB/100 users from the OG.

➜ Canonical licensing lives in [`../raw/fortinet-docs/03-releases-and-licensing.md`](../raw/fortinet-docs/03-releases-and-licensing.md) §2.
