# Dual-ISP (WAN2) Design Proposal — FortiSASE BOR Spoke

**Status:** proposal / research only. **No generator or template changes** — the single-WAN
template is validated and stays as-is. This is the design we'd wire in *later*, behind a
`dual_wan` toggle (default off).

---

## 1. The binding constraint (why this is a BGP problem, not a WAN problem)

From Fortinet's FortiSASE BOR architecture docs:

- **One BGP peer per BOR node, per branch.** "Each branch FortiGate establishes one BGP peer
  relationship with the BOR node" using the *BGP per-Overlay* method (iBGP only).
- **The branch tunnel IP is mode-config-assigned** — "BOR node has mode-config enabled … and will
  assign a unique IP to each connecting FortiGate." One tunnel = one assigned IP = one BGP session.
- **Redundancy is a *node*-level concept:** "Single branch can connect to multiple BOR **nodes**,
  for redundancy or capacity reasons." (That's our `BOR_Primary` / `BOR_Secondary`.)
- **No documented branch dual-WAN pattern.** FortiSASE leaves branch-side ISP redundancy to the
  SD-WAN/routing layer — i.e. our job, *under* the tunnels.

### The trap (what you correctly stopped us from building)
Dual-homing the **same** BOR node across two WANs would mean **two tunnels → two mode-config IPs →
two iBGP sessions to one node**. That fails three ways:
1. **Not supported** — one mode-config IP / one per-overlay BGP session per FortiGate per node.
2. **Peer-ID collision** — two dial-up SAs with the same peer identity; the node treats the 2nd as
   a re-key and tears down the 1st.
3. **Return-path ambiguity** — even if both peered, the node would see your LAN prefix from two
   next-hops and pick a return path non-deterministically (and we have *no* control on the managed
   BOR side to break the tie).

> **Design principle: exactly one BGP session per BOR node, always. Achieve ISP redundancy by
> dual-homing the transport (the IPsec outer path), never the BGP session.**

Note: advertising your LAN from **two different nodes** (Primary *and* Secondary) is *not* the trap —
that's the intended design, and the hub picks the return node via our community/local-pref scheme
(FortiSASE's sanctioned lever here is **BGP MED for hub priority**, which we can align to).

---

## 2. Pattern A — Circuit-split  ✅ recommended (ship first)

Each BOR node keeps its single tunnel/BGP session; the two nodes are pinned to **different WANs**.

```
BOR_Primary  (Dallas)  tunnel  --> egress WAN1 (wan)
BOR_Secondary (Miami)  tunnel  --> egress WAN2 (lan3)

SD-WAN members:
  1  BOR_Primary    (SDWAN_ZONE)      <- transported over ISP-A
  2  BOR_Secondary  (SDWAN_ZONE)      <- transported over ISP-B
  3  wan   (Underlay_ZONE)  ISP-A      <- local breakout
  4  lan3  (Underlay_ZONE)  ISP-B      <- local breakout
```

**Why it's clean:** one BGP session per node (constraint satisfied), and it slots directly into the
per-overlay failover we already built — `HC_Primary` now implicitly watches ISP-A, `HC_Secondary`
watches ISP-B. A dead ISP simply looks like a dead on-ramp, which our steering + `RM_OUT_FAIL` /
hub `CL_VIA_FAILED` already handle.

### Resilience matrix
| Event | Outcome |
|---|---|
| ISP-A (WAN1) down | `BOR_Primary` drops → `HC_Primary` fails → steer **and** return move to `BOR_Secondary` over ISP-B. **SASE stays up.** |
| ISP-B (WAN2) down | `BOR_Secondary` drops → `BOR_Primary` over ISP-A carries. **SASE stays up.** |
| Primary *node* down (ISP-A fine) | `HC_Primary` fails → Secondary over ISP-B. SASE up. *(Caveat: in Pattern A, Primary is only reachable via ISP-A.)* |
| All healthy | Primary preferred (local-pref/MED); Secondary hot-standby. |
| Both tunnels down, a WAN up | Local internet breakout via the live underlay member. |

### Proposed spoke-side config (review only — NOT in the generator yet)
```bash
# 1) WAN2 physical interface (lan3 on 30G/50G)
config system interface
    edit "lan3"
        set alias "WAN2"
        set role wan
        set mode static                     # or dhcp
        set ip <wan2_ip> <wan2_mask>
        set allowaccess ping https ssh fgfm
    next
end

# 2) Move ONLY the Secondary overlay's transport to WAN2 (single tunnel edit)
config vpn ipsec phase1-interface
    edit "BOR_Secondary"
        set interface "lan3"                # was "wan"
    next
end

# 3) Reach the Secondary PoP's public endpoint out WAN2 (node /32 stays via the tunnel)
config router static
    edit 2
        set gateway <wan2_gateway>          # 2nd default, equal distance = both active
        set distance 20
        set device "lan3"
    next
    edit 21
        set dstaddr "BOR_Secondary_PUBLIC"  # FQDN address object -> out WAN2
        set gateway <wan2_gateway>
        set device "lan3"
    next
end

# 4) WAN2 as a 2nd SD-WAN underlay member (local breakout / fallback)
config system sdwan
    config members
        edit 4
            set interface "lan3"
            set zone "Underlay_ZONE"
            set gateway <wan2_gateway>
        next
    end
end
```
Everything else — health-checks, service rules, return-path route-maps — is **unchanged**.

---

## 2b. Pattern A′ — Same-PoP dual tunnel-config  ✅ preferred realization

**Verified in the FortiSASE console:** the On-Ramp Security PoP edit pane has **"Create New Tunnel
Config"** — one PoP hosts *multiple* tunnel configs, each with its own **Tunnel interface IP** (= its
own BGP peer), **IP range** (mode-config pool), **Subnet mask**, and **Network ID**. Miami PoP
(`ipsec-<tenant>-mia-f3.prod.fortisase.com`):

| Tunnel config | Tunnel-int IP (BGP peer) | IP range | Mask | Net-ID |
|---|---|---|---|---|
| #1 (existing "fgtOnRamp") | 172.16.0.1 | 172.16.0.21 – 172.16.7.250 | /21 | 0 |
| #2 (new "MIA2") | 172.16.8.1 | 172.16.8.21 – 172.16.15.250 | /21 | 1 |

Dual-home the **same PoP** by pointing WAN1 → config #1 and WAN2 → config #2. Two **distinct
tunnel-int IPs + Network IDs** → two **separate BGP sessions to separate peers**. This is *not* the
rejected "two sessions to one peer" trap — it's a second node that lives in the same city. Keeps
both circuits on the same low-latency PoP.

> §1 rule stands: one BGP session **per tunnel-int IP**. A new tunnel config = a new peer = a legal
> new session. Distinct **Network IDs are mandatory** when configs share the PoP FQDN (the IKE
> selector that lands each tunnel on the right config) — **validate in lab.**

Branch side = Pattern A, except `BOR_Secondary`'s `remotegw-ddns` is the *same* FQDN as Primary with
`set network-id 1` instead of a different city's FQDN.

## 3. Pattern B — Floating transport  ⚗️ advanced / validate in lab

Gives **each node its own ISP redundancy** while still using **one BGP session** — by letting a
node's single tunnel's *outer* path float across both WANs (route to the PoP public IP is
dual-homed). The overlay IP + BGP session never move, so it's invisible to BGP → return path stays
symmetric by construction.

```bash
# Route BOR_Primary's PUBLIC endpoint via BOTH WANs; tunnel rebuilds on whichever is live.
config router static
    edit 30
        set dstaddr "BOR_Primary_PUBLIC"
        set gateway <wan1_gateway>
        set device "wan"
        set distance 10                     # preferred transport = ISP-A
    next
    edit 31
        set dstaddr "BOR_Primary_PUBLIC"
        set gateway <wan2_gateway>
        set device "lan3"
        set distance 15                     # backup transport = ISP-B
    next
end
```

**Open items to validate before trusting Pattern B:**
- `phase1 set interface` pins egress. To truly float a dial-up tunnel, the tunnel likely must be
  sourced from a **loopback with the PoP-public route steered by SD-WAN** (the "IPsec-over-SD-WAN"
  pattern), not just two static routes. **Needs a lab proof.**
- **Dial-up roaming:** confirm the BOR responder accepts the branch reconnecting from a new public
  source IP, keeps the mode-config IP stable per peer-ID, and BGP re-converges quickly.
- If it validates, Pattern B is the *ideal* — per-node circuit redundancy, one BGP session, no
  return-path ambiguity. If it doesn't converge cleanly on managed BOR, **fall back to Pattern A.**

---

## 4. Return path & default routes (answering the two questions)

- **Default routes:** both active, **equal distance** — SD-WAN steers local breakout over the best
  live circuit. (Use unequal distance only if you want WAN2 as pure standby.)
- **Return path is safe in both patterns** *because there is one BGP session per node.* WAN failover
  happens *under* the tunnel (Pattern B) or is expressed as node failover (Pattern A) — the BOR/hub
  always has exactly one next-hop per node, so it can't split or flap the return. The only return
  *steering* that matters is Primary-vs-Secondary **node** preference, which our existing
  community + hub local-pref (aligns with FortiSASE **MED-for-hub-priority**) already resolves.

---

## 5. Recommendation

1. **Now:** run the single-WAN test as planned.
2. **First dual-ISP build: Pattern A′ (same-PoP dual tunnel-config)** — WAN1 and WAN2 point at two
   tunnel configs on the *same* PoP (distinct tunnel-int IP + `network-id`). Supported, keeps both
   circuits on the low-latency PoP, reuses all our per-overlay failover. Fall back to Pattern A
   (split across cities) only if you'd rather spread PoPs.
3. **Make `network_id` a per-PoP variable.** Same public IP/FQDN → the branch differentiates configs
   with `set network-id N`. The spoke template currently hardcodes `0`; this becomes per-pop.
4. **Lab track:** Pattern B (floating single tunnel) only if we later want per-node circuit
   redundancy from a single session.
5. **Rule:** never two BGP sessions to the **same tunnel-int IP (peer)**. A new tunnel config on the
   same PoP = a new peer = fine.

## 6. Tooling — BOR PoP tunnel-config value generator (proposed)

The tunnel config is the **single source of truth both sides need**: the implementation engineer
types it into the FortiSASE console, and our spoke ZTP config must match it exactly. Today they're
entered independently → drift risk (the "thin air" problem). Proposed generator: from a PoP location
+ tunnel-config count, deterministically allocate and emit BOTH:

- **Console fill-in card** (for the engineer): Name / Tunnel-int IP / IP range / Subnet mask /
  Network ID / PSK.
- **Seed for the spoke `pops[]`**: `name`, `fqdn`, `bor_node` (= tunnel-int IP), `network_id`,
  `community` (and the `wan` binding for dual-ISP).

**Deterministic /21 allocation** (matches the Miami example, and our existing Primary/Secondary
already fit it): tunnel config `i` → base `172.16.(8*i).0/21`, tunnel-int `172.16.(8*i).1`, range
`.(8*i).21`–`.(8*i+7).250`, mask `255.255.248.0`, network-id `i`, community `65001:(10*(i+1))`.
`172.16.0.0/16` holds 32 such blocks (≥ the 20-node max).

**Naming:** `<POP><n>` — `MIA1`, `MIA2`, `DFW1`… → interface `BOR_MIA1`. Keep `Primary`/`Secondary`
as friendly aliases for the anchor pair. **Load-baseline presets:** "Miami dual", "Dallas dual",
"Miami + Dallas", "Dallas ×4" — one click seeds `pops[]` and emits the console card (mirrors the
site load-baseline). Defaults do all allocation; the engineer only supplies the FortiSASE-assigned
**FQDN + PSK** per location; a unique subnet override only drops in if explicitly required.

**No spoke-template change is required to add this generator** — it produces console values + a
`pops[]` seed. Wiring `network_id` / `wan` into the *spoke* render is a separate, later step.

### Confirmed FortiSASE tunnel-config schema (observed from the portal API)

Creating a tunnel config in the console fires
`POST /api/v1/security/sites/{popSiteId}/ipsec_tunnel_config`:

```json
{"ipsec_security_config":{"tunnel_1":{
  "tunnel_name":"MiamiBOR2","intf_ip":"172.16.24.1",
  "start_ip":"172.16.24.11","end_ip":"172.16.24.254","netmask":"255.255.255.0",
  "device_type":"fgt","network_id":1,"psk":"<psk>"}}}
```

| FortiSASE field | Our `pops[]` var | Notes |
|---|---|---|
| `tunnel_name` | `name` | e.g. MIA2 |
| `intf_ip` | `bor_node` | tunnel-int IP = BGP peer |
| `network_id` | `network_id` | IKE selector (shared FQDN) |
| `start_ip`/`end_ip`/`netmask` | — (mode-config pool) | not used spoke-side |
| `psk` | `seed_psk` | tenant default |
| `device_type` | — | constant `"fgt"` |

**Mask is a choice** — first config /21, `MiamiBOR2` /24. Generator defaults **/24** (intf `.1`, pool
`.11`–`.254`); /21 optional (intf `.1`, pool `.21`–`.(+7).250`). So one PoP definition emits the
**console card AND the API body** — API automation is a drop-in later. (Use a dedicated API
token, never a browser session.)

## Sources
- [Branch On-Ramp (BOR) — FortiSASE MSSP Architecture Guide](https://docs.fortinet.com/document/fortisase/latest/unified-sase-for-mssp-architecture-guide/438696/branch-on-ramp-bor)
- [SD-WAN On-Ramp support — FortiSASE Administration Guide](https://docs.fortinet.com/document/fortisase/latest/administration-guide/758254/sd-wan-on-ramp-support)
- [SD-WAN On-Ramp — FortiSASE Mature Administration Guide](https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/213023/sd-wan-on-ramp)
