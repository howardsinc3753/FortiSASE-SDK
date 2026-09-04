# SLA-triggered return-path failover — BARE-MINIMUM TEST (Spoke-2 + Hub-1)

Built from the **live** config (2026-08-04). Real names, real member IDs.

**Design:** a dedicated probe on the primary (`SIA_Pri`, Dallas/member 3) gates the Dallas
BGP advertisement via `route-map-out-preferable`. Healthy → advertise `RM_OUT_DALLAS` (`:10`).
Degraded → fall back to `route-map-out` = `RM_OUT_FAIL` (`65001:64911`) → hub deprefs → return
path swings to Miami. Steering/service rules are **untouched** (freestanding health check).

Live facts used:
- Spoke-2 neighbors: `172.16.8.1` (Dallas) / `172.16.0.1` (MIA); out-maps `RM_OUT_DALLAS`/`RM_OUT_MIA`.
- Spoke-2 SD-WAN members: **Dallas = 3, MIA = 1**, underlay = 2. Health-check `Google_DNS`, sla 1.
- LAN / `PL_LAN_LOCAL` = `10.200.20.0/24`.
- Hub `RM_FABRIC_IN` rules 1/2/99; add fail rule at **id 3** (failed routes carry `:64911`, not `:10/:20`, so order is fine).

Order matters: **SD-WAN neighbor binding (activation) BEFORE the BGP re-slot** = hitless.

---

## 1 — SPOKE-2  (paste on `18.205.229.241`)

```bash
# --- a. fail map: tag LAN with the "degraded" community ---
config router route-map
    edit "RM_OUT_FAIL"
        config rule
            edit 1
                set match-ip-address "PL_LAN_LOCAL"
                set set-community "65001:64911"
            next
            edit 99
            next
        end
    next
end

# --- b. dedicated PRIMARY probe (Dallas = member 3), so we can fail it alone ---
config system sdwan
    config health-check
        edit "SIA_Pri"
            set server "8.8.8.8" "1.1.1.1"
            set members 3
            config sla
                edit 1
                    set link-cost-factor latency jitter packet-loss
                    set latency-threshold 250
                    set jitter-threshold 50
                    set packetloss-threshold 5
                next
            end
        next
    end
end

# --- c. SD-WAN neighbor bindings = the ACTIVATION switch (apply BEFORE step d) ---
#     (also fixes the stale 172.16.8.1 -> member 1 / sla-id 0 binding)
config system sdwan
    config neighbor
        edit "172.16.8.1"
            set member 3
            set health-check "SIA_Pri"
            set sla-id 1
        next
        edit "172.16.0.1"
            set member 1
            set health-check "Google_DNS"
            set sla-id 1
        next
    end
end

# --- d. re-slot the BGP out-maps: fail map = normal, existing map = preferable ---
config router bgp
    config neighbor
        edit "172.16.8.1"
            set route-map-out "RM_OUT_FAIL"
            set route-map-out-preferable "RM_OUT_DALLAS"
        next
        edit "172.16.0.1"
            set route-map-out "RM_OUT_FAIL"
            set route-map-out-preferable "RM_OUT_MIA"
        next
    end
end
```

## 2 — HUB-1  (paste on `34.228.49.210`)

```bash
config router community-list
    edit "CL_VIA_FAILED"
        config rule
            edit 1
                set action permit
                set match "65001:64911"
            next
        end
    next
end
config router route-map
    edit "RM_FABRIC_IN"
        config rule
            edit 3
                set match-community "CL_VIA_FAILED"
                set set-local-preference 50
                set set-priority 300
            next
        end
    next
end
```

---

## 3 — Baseline check (before firing) — both should show the healthy state
```bash
# SPOKE-2: Dallas advertises the LAN tagged :10
get router info bgp neighbors 172.16.8.1 advertised-routes    # 10.200.20.0/24, community 65001:10
diagnose sys sdwan neighbor                                   # 172.16.8.1 -> SIA_Pri, sla 1, state alive/in-sla
# HUB-1: Dallas path wins (LP200)
get router info bgp network 10.200.20.0/24                    # best via 172.16.8.1, localpref 200
```

## 4 — FIRE THE TEST (spoke-2): fail the primary probe only
```bash
config system sdwan
    config health-check
        edit "SIA_Pri"
            config sla
                edit 1
                    set latency-threshold 5      # real ~30-90ms >> 5ms -> member 3 SLA fails
                next
            end
        next
    end
end
```

## 5 — Verify the failover
```bash
# SPOKE-2:
diagnose sys sdwan health-check status SIA_Pri   # member 3 = OUT-OF-SLA
get router info bgp neighbors 172.16.8.1 advertised-routes   # 10.200.20.0/24 now community 65001:64911
# HUB-1:
get router info bgp network 10.200.20.0/24        # Dallas copy = community 65001:64911, localpref 50
get router info routing-table bgp 10.200.20.0     # best next-hop now the MIA path
#   if the hub doesn't refresh LPs on already-received routes:
execute router clear bgp soft in
```

## 6 — RECOVER (spoke-2): relax the threshold → should flip back to Dallas
```bash
config system sdwan
    config health-check
        edit "SIA_Pri"
            config sla
                edit 1
                    set latency-threshold 250
                next
            end
        next
    end
end
```

---

## Rollback (remove the feature entirely)
```bash
# SPOKE-2
config router bgp
    config neighbor
        edit "172.16.8.1"
            set route-map-out "RM_OUT_DALLAS"
            unset route-map-out-preferable
        next
        edit "172.16.0.1"
            set route-map-out "RM_OUT_MIA"
            unset route-map-out-preferable
        next
    end
end
config system sdwan
    config neighbor
        delete "172.16.0.1"
    end
    config health-check
        delete "SIA_Pri"
    end
end
config router route-map
    delete "RM_OUT_FAIL"
end
# (leave the 172.16.8.1 sdwan-neighbor as-is or delete it too; it was stale to begin with)

# HUB-1
config router route-map
    edit "RM_FABRIC_IN"
        config rule
            delete 3
        end
    next
end
config router community-list
    delete "CL_VIA_FAILED"
end
```

## Notes
- `SIA_Pri` is probe-only — referenced solely by the `172.16.8.1` sdwan-neighbor binding, never by a
  service rule; outbound steering is unaffected.
- Failed routes carry `65001:64911` (not `:10/:20`), so hub rule 3 is the only rule they match —
  order relative to rules 1/2 doesn't matter.
- With hub `:20` at LP100 and `:64911` at LP50: healthy secondary (100) beats degraded primary (50) → return path swings to Miami. Correct without any other change.
