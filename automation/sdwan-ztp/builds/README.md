# Raw builds intake — AWS SD-WAN spokes → FortiSASE BOR

Drop the **real FortiGate builds + optional live diagnostics** here. I standardize *from* these into the canonical param set + role templates (`bor-spoke`, `bor-spoke+spa-hub`) and a per-site gap report. **Raw text only — no hand-conversion to YAML** (I emit the YAML blueprint).

## Layout
```
builds/
├── site-1/   raw/  diag/     # BOR spoke
├── site-2/   raw/  diag/     # BOR spoke
└── site-3/   raw/  diag/     # BOR spoke + SPA HUB  ← the bridge (dual role)
```
> If your spoke↔site numbering differs, just tell me which folder is the SPA-hub box; **site-3 is assumed to be the bridge** per the model.

## `raw/` — the build (static config)
The `show full-configuration` output, or at minimum these stanzas per box:
- `config vpn ipsec phase1-interface` / `phase2-interface`
- `config router bgp`
- `config router route-map` / `config router prefix-list`  (if any)
- `config system sdwan`
- `config router static`
- `config system interface`  (WAN + tunnels + **loopbacks**)

Name it anything obvious, e.g. `site-3/raw/site-3-fgt.conf`.

## `diag/` — dynamic output (optional, but gold for the gap report)
Live CLI to confirm intent vs reality — especially for the SPA-hub bridge:
- `get router info bgp summary`
- `get router info bgp neighbors <peer> advertised-routes`
- `get router info bgp neighbors <peer> received-routes`
- `get router info routing-table all`
- `diagnose ip address list`
- `diagnose vpn tunnel list` (or `get vpn ipsec tunnel summary`)
- `get system sdwan health-check status` (or `diagnose sys sdwan health-check`)

Name by content, e.g. `site-3/diag/bgp-received-routes.txt`.

## Reminder on scope
Security is pushed to the cloud PoPs — **these edges are transport-only** (SD-WAN/BGP/IPsec/routing). No local UTM/NGFW expected; don't worry if security profiles are absent.
