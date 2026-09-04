# Spoke-1 (BOR) — BGP Community Tagging · **Restore Script**

**Purpose:** tag Site-1's LAN (`10.200.10.0/24`) with a distinct BGP community per
on-ramp so the Hub can prefer one path and **drop the ECMP** on the return
(fixes the asymmetric routing). This restores the config the CSE deleted.

| On-ramp | BGP neighbor | Community set | Meaning |
|---|---|---|---|
| Dallas | `172.16.8.1` | `65001:10` | "arrived via Dallas" (preferred) |
| Miami  | `172.16.0.1` | `65001:20` | "arrived via Miami" (backup) |

> Pair this with the **hub-1** script (matches `:10`→LP200, `:20`→LP100). For full
> symmetry, Site-1's **forward** path should also egress Dallas (SD-WAN rule).

## Drop-in (paste whole block into the CLI)
```bash
config router prefix-list
    edit "PL_LAN_LOCAL"
        config rule
            edit 1
                set prefix 10.200.10.0 255.255.255.0
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
show router route-map                                          # RM_OUT_DALLAS / RM_OUT_MIA present
get router info bgp neighbors 172.16.8.1 advertised-routes     # 10.200.10.0/24 advertised out Dallas
get router info bgp neighbors 172.16.0.1 advertised-routes     # ...and out Miami
# On the HUB, confirm the tag actually arrived (community not stripped by FortiSASE):
#   get router info bgp network 10.200.10.0/24   -> look for "Community: 65001:10"
```

## Notes
- **`send-community both` is mandatory** — without it the community never leaves the spoke.
- `edit 99` is an empty **permit-all** rule (FortiOS route-maps deny unmatched routes by
  default) so every other advertised route passes through untouched.
- If the community gets stripped in the FortiSASE fabric, the hub can't match it — pivot to
  preferring by inbound tunnel/next-hop on the hub instead.
