# Spoke-2 (BOR) — Dynamic Preemptive Failover · **BETA**

LAN `10.200.20.0/24`. Upgrades the static `Send-Communities/spoke-2` to SLA-driven preempt.
**Read `README.md` first** — design, state table, and the two lab gates. Spoke-1 is identical
(swap the prefix). Assumes `PL_LAN_LOCAL` already lists `10.200.20.0/24`.

> ### ⚠️ Before you paste
> - Confirm **`ONRAMP_Dallas` = member 3** (`diagnose sys sdwan member`). Both neighbors bind
>   to the **Dallas** member — wrong ID and the trigger never fires.
> - Pick a probe target reachable via **both** members (`10.30.1.1`, or a host behind Hub-1's
>   LAN). The per-BOR IPs (`10.30.1.5` Miami-only / `10.30.1.6` Dallas-only) are NOT valid.
> - This is BETA — validate the two lab gates in the README before prod.

## 1 — Dedicated health-check + SD-WAN neighbor binding (the trick)
```bash
config system sdwan
    config health-check
        edit "HC_SPA_HUB"
            set server "10.30.1.1"
            set members 3 1                 # 3 = Dallas, 1 = Miami  (VERIFY!)
            set interval 500
            set probe-timeout 1000
            set failtime 5
            set recoverytime 10
            config sla
                edit 1
                    set link-cost-factor latency jitter packet-loss
                    set latency-threshold 150
                    set jitter-threshold 50
                    set packetloss-threshold 3
                next
            end
        next
    end
    config neighbor
        edit "172.16.8.1"                   # Dallas BOR node
            set member 3                    # Dallas member (its own health = normal)
            set health-check "HC_SPA_HUB"
            set sla-id 1
        next
        edit "172.16.0.1"                   # Miami BOR node
            set member 3                    # <-- bound to DALLAS member (the inversion)
            set health-check "HC_SPA_HUB"
            set sla-id 1
        next
    end
end
```

## 2 — Route-maps (4 communities)
```bash
config router route-map
    edit "RM_OUT_DALLAS"                    # Dallas healthy
        config rule
            edit 1
                set match-ip-address "PL_LAN_LOCAL"
                set set-community "65001:10"
            next
            edit 99
            next
        end
    next
    edit "RM_OUT_DALLAS_DEGRADED"           # Dallas brownout (session up)
        config rule
            edit 1
                set match-ip-address "PL_LAN_LOCAL"
                set set-community "65001:30"
            next
            edit 99
            next
        end
    next
    edit "RM_OUT_MIA"                       # Miami standby (Dallas healthy)
        config rule
            edit 1
                set match-ip-address "PL_LAN_LOCAL"
                set set-community "65001:20"
            next
            edit 99
            next
        end
    next
    edit "RM_OUT_MIA_PROMOTE"               # Miami promote (Dallas out-of-SLA/down)
        config rule
            edit 1
                set match-ip-address "PL_LAN_LOCAL"
                set set-community "65001:15"
            next
            edit 99
            next
        end
    next
end
```

## 3 — BGP neighbors (note the inversion on Miami)
```bash
config router bgp
    config neighbor
        edit "172.16.8.1"                                   # Dallas
            set route-map-out "RM_OUT_DALLAS_DEGRADED"      # failure map (member out-of-SLA)
            set route-map-out-preferable "RM_OUT_DALLAS"    # normal map (member in SLA)
            set send-community both
        next
        edit "172.16.0.1"                                   # Miami  (roles read backwards, correct)
            set route-map-out "RM_OUT_MIA_PROMOTE"          # failure map -> PROMOTE (:15)
            set route-map-out-preferable "RM_OUT_MIA"       # normal map -> standby (:20)
            set send-community both
        next
    end
end
```

## 4 — (do it) shrink the stale window — spoke side only
```bash
config router bgp
    set keepalive-timer 5
    set holdtime-timer 15
end
```

## Verify / lab-test (the acceptance gate)
```bash
diagnose sys sdwan health-check status HC_SPA_HUB       # per-member SLA state
diagnose sys sdwan neighbor                             # neighbor<->member binding accepted?
get router info bgp neighbors 172.16.0.1 advertised-routes   # steady state: 10.200.20.0/24 -> 65001:20

# ---- pull the Dallas tunnel, then re-check ----
diagnose sys sdwan health-check status HC_SPA_HUB       # Seq(3 ONRAMP_Dallas): state(dead)  <-- gate #2
get router info bgp neighbors 172.16.0.1 advertised-routes   # 10.200.20.0/24 -> 65001:15  (PROMOTE fired)
# On the hub:  get router info bgp network 10.200.20.0/24  -> best path via Miami, LP 250
```
**Pass = the Miami advertisement flips to `65001:15` when Dallas dies, and the hub best-path
moves to Miami in ~3–4s.** If it doesn't flip, gate #1 or #2 failed — see README fallback.
