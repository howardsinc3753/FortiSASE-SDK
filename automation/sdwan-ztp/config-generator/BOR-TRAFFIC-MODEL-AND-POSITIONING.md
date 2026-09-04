# FortiSASE Branch On-Ramp — Traffic Model & Positioning (SE one-pager)

*Source material for the customer Kick-Off deck. Honest framing — north-south vs east-west,
and how we sit next to Cato.*

---

## The one idea (say this first, every call)

**FortiSASE is the cloud security plane (SSE).** It secures **north-south** — your users going to
the **internet, SaaS, and private apps**. It is **not** a private transit backbone for **east-west**
(site-to-site). East-west runs on a **FortiGate SD-WAN fabric (the SPA hub)** — inspected at the
edge NGFW, on infrastructure **you own**.

> SASE modernizes north-south (it kills 25 years of backhaul-to-the-DC-firewall).
> It does not reinvent east-west — that's still an SD-WAN fabric, and we're honest about that.

---

## How traffic flows (the whole model on one slide)

| Traffic | Path | Secured by |
|---|---|---|
| **Internet / SaaS** (no private access) | client → BOR → FortiSASE PoP → internet | FortiSASE cloud (SSE) |
| **Remote/roaming user → any app** | user (agent/agentless ZTNA) → FortiSASE → app | FortiSASE cloud (SSE) |
| **External client → a branch LAN** | client → FortiSASE → **SPA hub** → branch LAN | SASE + hub NGFW |
| **Branch LAN ↔ branch LAN** (east-west) | site-1 → its PoP → **SPA hub** → other PoP → site-2 | edge / hub NGFW |

**Key rule:** two branches on the **same** FortiSASE PoP do **not** hairpin (no PoP ingress-to-ingress
policy; per-PoP CGNAT /20s aren't shared). They meet at the **SPA hub** instead — so the same-PoP
hairpin case simply never has to work.

---

## The requirement (put this on a slide of its own)

### 🔴 Private access (LAN-to-LAN reachability) REQUIRES a SPA Hub.

- No private access needed → **FortiSASE alone** (internet/SSE + ZTNA to cloud apps). No hub.
- Private access needed → add a **SPA hub** (FortiGate — physical **or a cloud VM**).
- BOR-to-BOR hairpin is **confirmed not on the FortiSASE roadmap** (PM) — design for the hub, permanently.

---

## FortiSASE vs Cato — the honest cut

| | **Cato** | **Fortinet (FortiSASE + FortiGate fabric)** |
|---|---|---|
| Model | One converged **private backbone**; east-west + north-south both cloud-inspected | **Two planes**: FortiSASE = SSE (N-S), FortiGate = SD-WAN fabric (E-W) |
| Native site-to-site | ✅ core use case, on their backbone | Via **your** SPA hub / ADVPN — edge-NGFW inspected |
| **LAN switches + WiFi** | ❌ **second vendor/portal** (Meraki/Aruba/etc.) | ✅ **FortiSwitch + FortiAP via FortiLink — same console/FMG** |
| Where it wins | Simplicity, no hardware, native cloud-inspected east-west | **NGFW depth**, **data sovereignty** (E-W stays on *your* hub/region), **no backbone lock-in**, leverages existing Fortinet estate, TCO at scale |
| Green-field, no hardware | Cleanest fit | FortiSASE-only if cloud-only apps; **cloud-VM hub** if private LANs |

**The differentiator to lead with:** with Cato your inter-site traffic rides *their* backbone and
*their* inspection. With Fortinet it stays on *your* inspected fabric, in *your* region/cloud —
**no third-party backbone ever touches your internal traffic.** For sovereignty / regulated /
data-residency customers, that's a win, not a concession.

---

## Real managed edge (LAN Fabric) — the switches-and-WiFi gap Cato leaves open

The branch FortiGate isn't just firewall + SD-WAN — with the Security Fabric it's the **LAN
controller** too:

- **FortiSwitch + FortiAP managed via FortiLink** — one console (FortiGate / FortiManager) for
  firewall, SD-WAN, **switching, and WiFi**.
- **ASIC-accelerated** (NP/CP) — real encrypted-SD-WAN throughput, not a thin-edge CPU box (FEX-20).
- **FMG lifecycle** — firmware, config templates, compliance, OS insight across the fleet.
  Thin-edge / FEX has **zero** lifecycle management from FortiSASE — which is exactly why we run FMG.
- **Hub-and-spoke IPsec** your engineers already run — not an opaque VXLAN fabric to take on faith.

**The Cato gap:** Cato secures your traffic but does **not** manage your switches or APs — every
Cato customer runs a **second portal / vendor** for the LAN access layer. Fortinet converges
**WAN + LAN + WiFi + security** under **one fabric**, and moves only the **security edge** to the
cloud (FortiSASE).

> **Pitch:** "Keep your whole branch — SD-WAN, firewall, switches, WiFi — on one Fortinet console.
> Move the *security edge* to the cloud, not your *LAN management* to a second portal."

---

## Qualify the deal to the traffic profile

- **North-south heavy** (branches + remote users → internet/SaaS/ZTNA, little inter-site): FortiSASE
  BOR is a clean win — security depth + thin-edge economics + one policy on/off-net.
- **East-west heavy, wants cloud-inspected transit, no on-prem hub, doesn't want to run SD-WAN:**
  that's **Cato's designed sweet spot.** Don't fight it with BOR-as-transit. Answer with **FortiGate
  Secure SD-WAN fabric** (hub inspection / ADVPN + edge NGFW) **+ FortiSASE for the users**, and lead
  on sovereignty, NGFW depth, and TCO.

---

## Talk tracks (two audiences)

- **Network engineer:** "RFC-1918 destined for another *site* rides the SPA fabric through the hub;
  RFC-1918 destined for a *SASE-delivered private app* rides the PoP. Longest-prefix picks the plane."
- **Exec / business:** "**Cloud security for your people; your own inspected fabric for your sites.**
  You're not backhauling to a firewall anymore, and your internal traffic never leaves your control."

---

## Why FortiSASE at all (when the customer already has FortiGates)

FortiSASE is for the **users and places a branch FortiGate can't cover**:
1. **Roaming / hybrid workforce** — no FortiGate in front of them; secured anywhere.
2. **Thin-edge economics** — offload inspection to the cloud → smaller/cheaper edge, fewer UTM
   licenses, no per-box refresh for peak encrypted-inspection throughput.
3. **One policy** — identical posture on-net and off-net from one console.

It is **not** a replacement for your data-center NGFW, and **not** your east-west backbone.

---

## Slide brief: "How East-West Traffic Works (via SPA)"

**Anchor the whole slide on this:** Gartner defines SASE = **SD-WAN (network) + SSE (security)**,
converged. FortiSASE is the **SSE half**; your **FortiGate SPA fabric is the SD-WAN half**. East-west
on the SPA hub isn't a gap in SASE — it's the **network half of SASE doing its job.**

**Title:** East-West Traffic — The SPA Hub *Is* the SASE Fabric
**Sub:** North-south to the cloud. East-west on your own inspected fabric. By design.

**Diagram (two planes — designer to render):**
```
        NORTH–SOUTH  —  FortiSASE / SSE (cloud security)
   ┌────────────────────────────────────────────────────┐
   │      internet · SaaS · private apps · ZTNA          │
   └──────▲──────────────────────────────────▲──────────┘
      BOR │ (Dallas PoP)        (Miami PoP)  │ BOR
   ┌──────┴──────┐                    ┌───────┴─────┐
   │   Site-1    │                    │   Site-2    │
   └──────┬──────┘                    └───────┬─────┘
          │      EAST–WEST — your fabric      │
          └────────►  SPA HUB (Site-3) ◄──────┘
                    FortiGate · NGFW-inspected · yours
```

**Flow (Site-1 LAN → Site-2 LAN):**
1. Each site rides its own BOR PoP for internet / SSE (north-south).
2. For site-to-site, each site reaches the **SPA hub** (your FortiGate).
3. The hub learns every branch LAN via BGP and bridges east-west — **NGFW-inspected**.
4. Two sites on the same PoP never hairpin it — they meet at the hub.

**Why it's architecture, not a limitation:**
- The SASE PoP secures your **egress** (north-south) — it was never meant to be your **core router**.
- East-west stays on **your** inspected fabric, in **your** region — sovereignty + full NGFW, no
  third-party backbone.
- The same fabric already runs your SD-WAN, firewall, switches, and WiFi — east-west is just more of
  what it already does.

**Takeaway line (bottom of slide):** *"North-south to the cloud. East-west on your fabric. That's
SASE — not a workaround."*
