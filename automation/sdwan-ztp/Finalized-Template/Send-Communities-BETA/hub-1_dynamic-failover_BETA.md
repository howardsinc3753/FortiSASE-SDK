# Hub-1 (BOR + SPA) — Dynamic Preemptive Failover · **BETA**

Extends the baseline `RM_FABRIC_IN` (from `../Send-Communities/hub-1`) with the two new
preference levels so the 4-community scheme resolves. **Read `README.md` first.**

| Received community | Community-list | Local-Pref | Result |
|---|---|---|---|
| `65001:15` Miami promoted | `CL_MIA_PROMOTED` | **250** | preempts stale Dallas :10 |
| `65001:10` Dallas active | `CL_VIA_DALLAS` *(exists)* | 200 | steady-state winner |
| `65001:20` Miami standby | `CL_VIA_MIA` *(exists)* | 100 | backup |
| `65001:30` Dallas degraded | `CL_DALLAS_DEGRADED` | 50 | loses to Miami standby |

> ### ⚠️ Neighbor-group name
> The `route-map-in` must attach to your fabric RR-client group — **`fabric_vpn_1`** on the
> Orchestrator-built hub (your routing table shows that interface), or `SASE_Hub` if renamed.
> Confirm with `show router bgp`. Your existing `CL_VIA_DALLAS` / `CL_VIA_MIA` and the
> `fabric_vpn_1` attachment stay as-is; this only **adds** to them.

## 1 — Add the two new community-lists
```bash
config router community-list
    edit "CL_MIA_PROMOTED"
        config rule
            edit 1
                set action permit
                set match "65001:15"
            next
        end
    next
    edit "CL_DALLAS_DEGRADED"
        config rule
            edit 1
                set action permit
                set match "65001:30"
            next
        end
    next
end
```

## 2 — Re-declare RM_FABRIC_IN with all four tiers (ordered high→low)
```bash
config router route-map
    edit "RM_FABRIC_IN"
        config rule
            edit 1
                set match-community "CL_MIA_PROMOTED"     # 65001:15
                set set-local-preference 250
            next
            edit 2
                set match-community "CL_VIA_DALLAS"       # 65001:10
                set set-local-preference 200
            next
            edit 3
                set match-community "CL_VIA_MIA"          # 65001:20
                set set-local-preference 100
            next
            edit 4
                set match-community "CL_DALLAS_DEGRADED"  # 65001:30
                set set-local-preference 50
            next
            edit 99
            next
        end
    next
end
```
> Rule order matters — a prefix carries exactly one of these communities at a time, but keep
> the tiers ordered so intent is obvious. `edit 99` = permit-all for everything else.

## 3 — Attachment (unchanged — already applied from baseline)
```bash
config router bgp
    config neighbor-group
        edit "fabric_vpn_1"            # <-- your fabric RR-client group (verify name)
            set route-map-in "RM_FABRIC_IN"
        next
    end
end
```

## Verify
```bash
show router community-list                       # CL_MIA_PROMOTED / CL_DALLAS_DEGRADED present
show router route-map RM_FABRIC_IN               # four tiers 250/200/100/50
# steady state:
get router info bgp network 10.200.10.0/24       # Community 65001:10, LP 200, via Dallas
get router info bgp network 10.200.20.0/24
# after you fail Dallas on the spoke:
get router info bgp network 10.200.10.0/24       # Community 65001:15, LP 250, via Miami  <-- preempt
get router info routing-table bgp 10.200.10.0    # single next-hop (Miami), no ECMP
```

## Notes
- The hub is passive here — it just maps communities → LP. All the intelligence (which
  community to send) lives on the **spokes** (the SLA + route-map-out-preferable trick).
- Depends on FortiSASE preserving `:15` and `:30` through the fabric, same as `:10`/`:20`.
  The `get router info bgp network` checks prove it.
- Forward-path reminder (spoke side): add `10.30.1.0/24` to the hub-bound SD-WAN service
  rule's dst so the loopbacks stop riding ECMP (forward asymmetry).
