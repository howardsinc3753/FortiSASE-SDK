---
description: Pick the right FortiSASE on-ramp for a scenario and sketch the ZTP automation path
argument-hint: <scenario, e.g. "200 retail branches, no on-site IT">
---

Design the on-ramp for: **$ARGUMENTS**

Use `corpus/raw/fortinet-docs/01-architecture-and-onramps.md` (on-ramp matrix) and `02-automation-and-apis.md` (ZTP patterns). Produce:

1. **Recommended on-ramp** — one of: agent-based (FortiClient) · agentless SWG (PAC / Secure Browser) · branch on-ramp (FortiGate IPsec / thin-edge FortiExtender·FortiAP) · SPA hub. Justify against the scenario (managed vs unmanaged endpoints, whole-site vs per-user, private-app access, sovereignty).
2. **Key limits to check** — e.g. BOR: 2–20 nodes/tenant, 1 Gbps & 2000 branches/node, 40,000/tenant; **SPA network config must precede Branch On-ramp**; ZTNA = TCP-only; agentless = web-only.
3. **ZTP automation path** — Pattern A (FortiAP/FortiExtender → FortiSASE directly) or Pattern B (FortiGate → FortiManager Cloud → IPsec/SPA on-ramp). Reference `api/reference/02-fortiztp-onramp.md` and the example script.
4. **Licensing touchpoints** — user-based seats + any add-on (Branch On-Ramp Location SKU, SD-WAN/SPA bundle, thin-edge entitlement). Cite the Ordering Guide via corpus doc 03.
5. **Open/UNVERIFIED flags** relevant to this design.

Be concrete and SE-grade. Flag anything that needs a live-tenant or FNDN check.
