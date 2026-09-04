# Hub-1 (BOR + SPA) — BGP Community Match + Local-Pref · **Restore Script**

**Purpose:** match the community the spokes tagged onto their LAN prefixes and set
**local-preference** so one path strictly wins — this removes the ECMP tie and gives a
single, deterministic **return path** (fixes the asymmetry). Restores the config the CSE
deleted.

| Received community | Community-list | Local-Pref | Result |
|---|---|---|---|
| `65001:10` (via Dallas) | `CL_VIA_DALLAS` | **200** | wins — installed as the single path |
| `65001:20` (via Miami) | `CL_VIA_MIA` | 100 | backup |

> ### ⚠️ Confirm your fabric neighbor-group name before pasting the LAST stanza
> The route-map-in must attach to the **RR-client group the spoke LANs arrive on**.
> - Orchestrator-built hub (your live config — routing table shows the `fabric_vpn_1`
>   interface) → the group is **`fabric_vpn_1`** (used below).
> - If you hand-built / renamed it → **`SASE_Hub`**.
>
> Check with: `show router bgp` → look under `config neighbor-group`. Swap the name in the
> last stanza if needed, or the route-map silently won't apply.

## Drop-in (paste whole block into the CLI)
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
            edit 1
                set match-community "CL_VIA_DALLAS"
                set set-local-preference 200
            next
            edit 2
                set match-community "CL_VIA_MIA"
                set set-local-preference 100
            next
            edit 99
            next
        end
    next
end
config router bgp
    config neighbor-group
        edit "fabric_vpn_1"
            set route-map-in "RM_FABRIC_IN"
        next
    end
end
```

## Verify
```bash
show router community-list
show router route-map
# Confirm the community arrived + LP applied, and that there is now ONE best path (no ECMP):
get router info bgp network 10.200.10.0/24     # -> Community 65001:10, Local Pref 200
get router info bgp network 10.200.20.0/24
get router info routing-table bgp 10.200.10.0  # -> single next-hop, not two
```
Before this, the same `get router info routing-table bgp` showed the spoke LANs with **two**
ECMP next-hops; after, each is a single deterministic path.

## Notes
- `edit 99` = permit-all so all other received routes pass with their normal attributes.
- Local-preference is iBGP-wide and higher wins → the `:10`/Dallas path beats `:20`/Miami,
  so BGP installs one path → ECMP gone.
- Depends on FortiSASE **preserving the community** through the fabric reflection — the
  `get router info bgp network` check above proves it survives.

## Next (your idea — captured for later)
`route-map-out-preferable` for faster BGP route updates on the SPA hub
(<https://community.fortinet.com/fortigate-3/troubleshooting-tip-using-route-map-out-preferable-in-bgp-for-route-tag-use-in-an-sd-wan-rule-178513>).
Get this baseline back up first; then walk me through the design and we'll fold it in.
