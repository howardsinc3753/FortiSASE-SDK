# Spoke-2 (BOR) — BGP Community Tagging · **Restore Script**

**Purpose:** tag Site-2's LAN (`10.200.20.0/24`) with a distinct BGP community per
on-ramp so the Hub can prefer one path and **drop the ECMP** on the return. This
restores the config the CSE deleted.

| On-ramp | BGP neighbor | Community set | Meaning |
|---|---|---|---|
| Dallas | `172.16.8.1` | `65001:10` | "arrived via Dallas" (preferred) |
| Miami  | `172.16.0.1` | `65001:20` | "arrived via Miami" (backup) |

> **Baseline = same scheme as Spoke-1** (both prefer Dallas → deterministic, no ECMP).
> This matches the 2-community hub config. See the *Load-share* note at the bottom if you
> instead want Site-2 to prefer Miami.

## Drop-in (paste whole block into the CLI)
```bash
config router prefix-list
    edit "PL_LAN_LOCAL"
        config rule
            edit 1
                set prefix 10.200.20.0 255.255.255.0
            next
        end
    next
end
config router route-map
    edit "RM_OUT_DALLAS"
        config rule
            edit 1
                set match-ip-address "PL_LAN_LOCAL"
                set set-community "65001:10"
            next
            edit 99
            next
        end
    next
    edit "RM_OUT_MIA"
        config rule
            edit 1
                set match-ip-address "PL_LAN_LOCAL"
                set set-community "65001:20"
            next
            edit 99
            next
        end
    next
end
config router bgp
    config neighbor
        edit "172.16.8.1"
            set route-map-out "RM_OUT_DALLAS"
            set send-community both
        next
        edit "172.16.0.1"
            set route-map-out "RM_OUT_MIA"
            set send-community both
        next
    end
end
```

## Verify
```bash
show router route-map
get router info bgp neighbors 172.16.8.1 advertised-routes     # 10.200.20.0/24 advertised out Dallas
get router info bgp neighbors 172.16.0.1 advertised-routes
# On the HUB:  get router info bgp network 10.200.20.0/24  -> "Community: 65001:10"
```

## Notes
- **`send-community both` is mandatory.**
- `edit 99` = permit-all (route-maps deny unmatched by default).

### Optional — load-share (Site-2 prefers Miami instead)
If you'd rather spread return traffic (Site-1 via Dallas, Site-2 via Miami) instead of
both-via-Dallas, **swap the communities here**: set `65001:20` in `RM_OUT_DALLAS` and
`65001:10` in `RM_OUT_MIA`. No hub change needed — Site-2's Miami path then carries `:10`
(LP200) and wins. Leave as-is above for the plain symmetric baseline.
