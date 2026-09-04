# HUB update when onboarding a new BOR site — read this first

**TL;DR:** with the **global** `RM_FABRIC_IN` baseline in place (below), a new spoke that
tags the standard `65001:10` / `65001:20` markers is steered **automatically** — you do
**NOT** need to touch the hub per site. The per-site tag (`65001:10NN`, e.g. Site-5 =
`65001:1005`) just rides along as a label. Only touch the hub when a site must **differ**
from the global default (§3).

Community scheme the generator emits on each spoke:

| Path | Marker (global) | Per-site tag | Example (Site-5) |
|---|---|---|---|
| Primary (Dallas) | `65001:10` | `65001:10NN` | `65001:10` + `65001:1005` |
| Secondary (Miami) | `65001:20` | `65001:10NN` | `65001:20` + `65001:1005` |

`NN` = site id (Site-5 → `05` → `1005`; Site-15 → `15` → `1015`).

---

## 1. Hub baseline — ONE TIME (must exist; steers every site)

Paste on the **HUB (BOR + SPA)** once. After this, new sites need no hub change.

```bash
config router community-list
    edit "CL_VIA_DALLAS"
        config rule
            edit 1
                set action permit
                set match "65001:10"
            next
        end
    next
    edit "CL_VIA_MIA"
        config rule
            edit 1
                set action permit
                set match "65001:20"
            next
        end
    next
end
config router route-map
    edit "RM_FABRIC_IN"
        config rule
            edit 100
                set match-community "CL_VIA_DALLAS"
                set set-local-preference 200
                set set-priority 100
            next
            edit 101
                set match-community "CL_VIA_MIA"
                set set-local-preference 100
                set set-priority 200
            next
            edit 999
            next
        end
    next
end
config router bgp
    config neighbor-group
        edit "fabric_vpn_1"          # <-- the RR-client group the spoke LANs arrive on
            set route-map-in "RM_FABRIC_IN"
        next
    end
end
```

> **Two knobs, opposite polarity — both favour Dallas (primary):**
> - `set-local-preference` = BGP best-path, **higher wins** → Dallas **200**, Miami 100.
> - `set-priority` = routing-table / SD-WAN route priority, **lower wins** → Dallas **100**, Miami 200.
>
> LP settles the BGP choice (kills ECMP); priority reinforces it in the FIB + SD-WAN and is the
> tiebreaker if LP is ever equal (`ibgp-multipath`). `unset set-ip-prefsrc` seen on GUI/orchestrator
> builds is the "preferred source IP" override left **off** (default) — no steering effect, safe to
> ignore. Rule IDs are `100`/`101` (not `1`/`2`) on purpose: it keeps `1–99` free for the per-site
> overrides in §3.
> **Confirm the neighbor-group name first:** `show router bgp` → `config neighbor-group`.
> Orchestrator-built hub = `fabric_vpn_1`; hand-built/renamed = `SASE_Hub`. Wrong name =
> the route-map silently never applies.
>
> Note the rule IDs (`100`/`101`/`999`) leave room **below** `100` for per-site overrides (§3).

---

## 2. Adding a normal site — HUB TO-DO: nothing 🎉

If Site-N uses the standard `:10`/`:20` markers (the generator does), the baseline already
gives it a deterministic primary/secondary return path. **No hub paste required.** Just
verify the tag survived the FortiSASE fabric:
```bash
get router info bgp network 10.<lan>.0/24     # -> Community 65001:10 (+ 65001:10NN), Local Pref 200
get router info routing-table bgp 10.<lan>.0  # -> ONE next-hop, not ECMP
```

---

## 3. Per-site OVERRIDE — only when a site must differ (⚠ don't forget the hub)

Use this **only** when one site must break the global rule (e.g. Site-5 should prefer
**Miami**, or gets a special LP). Per-site rules must sit **below** the global rules
(IDs `< 100`) so they win. Example — force Site-5 to prefer its **secondary/Miami** path:

```bash
# HUB — OVERRIDE for Site-5 (community 65001:1005). Paste on the hub.
config router community-list
    edit "CL_SITE5_SECONDARY"
        config rule
            edit 1
                set action permit
                set match "65001:20 65001:1005"    # Site-5 routes arriving via Miami
            next
        end
    next
end
config router route-map
    edit "RM_FABRIC_IN"
        config rule
            edit 5                                  # < 100 => evaluated before the global rules
                set match-community "CL_SITE5_SECONDARY"
                set set-local-preference 300        # beats the global 200 Dallas gets
            next
        end
    next
end
```
Result: Site-5's Miami routes get LP 300 (win); its Dallas routes fall through to the global
rule (LP 200) → Site-5 now prefers Miami, every other site unchanged.

> Verify: `get router info bgp network 10.50.50.0/24` → the Miami path shows Local Pref 300
> and is the single best path.

---

## Notes
- `send-community both` on the spoke neighbors is mandatory or the tag never leaves the spoke.
- The trailing empty rule (`edit 999`) is permit-all — keep it **last** so unmatched routes pass.
- Depends on FortiSASE preserving the community through fabric reflection — the
  `get router info bgp network` check proves it survives.
