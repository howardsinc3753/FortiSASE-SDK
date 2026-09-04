# FortiSASE On-Ramp Decision Guide

> Partner-presentable. Picks the right on-ramp per scenario and names the automation path. Backed by `corpus/raw/fortinet-docs/01-architecture-and-onramps.md` (Tier 1). An **on-ramp** = how traffic reaches a FortiSASE security PoP; the **pillar** (SIA/SPA/SSA) = what inspection happens there.

## The four on-ramps at a glance

| On-ramp | Endpoint needs | How it connects | Best for | Hard limits |
|---|---|---|---|---|
| **Agent-based** | FortiClient + FortiClient Cloud | Always-on Cloud Security tunnel (SSL/IPsec; IPsec-over-TCP/443 in 25.4); ZTNA optional | Managed laptops/roaming users; full SIA + ZTNA(SPA) + SSA | ZTNA = TCP apps only; agent required |
| **Agentless SWG** | None (browser/OS proxy + PAC) or **Secure Browser** ext (26.1) | Explicit proxy via hosted PAC file | Unmanaged/BYOD/contractors; web SIA + inline-CASB | Web/proxy traffic only; no ZTNA |
| **Branch on-ramp (site/thin-edge)** | FortiGate (Mature: FortiGate only) / FortiExtender / FortiAP; or 3rd-party IKEv2 | IPsec dial-up + iBGP to a BOR node; endpoints use it as default gateway | Whole branch sites, agentless, at scale | 2–20 BOR nodes/tenant; 1 Gbps & 2000 branches/node; 40,000/tenant; **SPA config must exist first** |
| **SPA hub** | FortiGate SPA hub(s) | PoPs become spokes; IPsec overlays + BGP/ADVPN | Private/DC app access for remote users | Up to 12 hubs; hub-select via health/priority or BGP MED |

## Decision tree

```
Is it a whole SITE (branch) or individual USERS?
│
├─ SITE ──────────────────────────────────────────────────────────────────────
│   Do you want a managed Fortinet box at the branch?
│   ├─ Yes, FortiGate already there / SD-WAN estate ─► BRANCH ON-RAMP (FortiGate IPsec)
│   │        automation: Pattern B  (FortiZTP → FortiManager Cloud → template)
│   ├─ Yes, want simplest thin edge (no full FortiGate) ─► THIN-EDGE (FortiExtender 200F / FortiAP)
│   │        automation: Pattern A  (FortiZTP target = FortiSASE)
│   └─ Non-Fortinet CPE only ─► BRANCH ON-RAMP via 3rd-party IKEv2 dial-up (custom device type)
│
└─ USERS ─────────────────────────────────────────────────────────────────────
    Managed device you control?
    ├─ Yes ─► AGENT-BASED (FortiClient). Add ZTNA for TCP private apps.
    └─ No (BYOD/contractor/unmanaged) ─► AGENTLESS SWG (PAC) or Secure Browser extension
    
Need remote users to reach PRIVATE / data-center apps?
    └─► add SPA: ZTNA (agent, TCP) and/or SPA hub via FortiGate (any on-ramp can ride it)
```

## Scenario cheat-sheet
- **"200 retail branches, no on-site IT"** → Branch on-ramp. If they're standardizing on FortiGate, Pattern B with FortiManager Cloud golden templates. If they want the lightest box, FortiExtender thin-edge (Pattern A). Watch the 2000-branches/node and 20-node ceilings → plan node placement + a 2nd node for redundancy.
- **"Mostly remote knowledge workers on company laptops"** → Agent-based FortiClient; ZTNA for internal TCP apps.
- **"Call-center contractors on their own PCs"** → Agentless SWG (PAC) or Secure Browser; no agent to manage.
- **"Need users to hit private apps in two data centers"** → SPA hubs on existing FortiGates; if multiple hubs advertise the same prefix, use **BGP MED** hub selection for deterministic steering.
- **"Sovereignty / data-residency mandate (e.g., public sector, EU, APAC)"** → consider **FortiSASE-Sovereign** (26.2.x line) + dedicated public-cloud PoPs in-region; dedicated egress IPs for compliance allowlisting.

## Gotchas an SE must pre-empt
- **Branch on-ramp depends on SPA:** "You must configure the SPA network configuration first before deploying a Branch On-ramp location" — they share BGP config, and only **iBGP** runs between BOR and branches.
- **TLS inspection:** inline-CASB/DLP need **SSL deep inspection on + QUIC blocked**, or SaaS controls go dark.
- **Nearest-PoP is geo-by-egress-IP, not anycast:** recommend **EDNS Client Subnet (ECS)**-capable resolvers for correct PoP selection.
- **FIDO2 on Windows agent tunnels** also requires IdP-side config (Entra ID), unlike macOS.

See `ZTP_ONRAMP_AUTOMATION_PLAYBOOK.md` for the zero-touch build, and `/sase-onramp <scenario>` to design one interactively.
