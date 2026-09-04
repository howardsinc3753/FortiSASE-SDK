# Branch On-Ramp — Spoke Overlay & BGP Plan

Per-spoke convention for onboarding FortiOS spokes (the AWS VMs, or any physical branch FortiGate) to the **FortiSASE Branch On-Ramp** over IPsec + iBGP.

Proven against **`rl-1`** (physical branch, overlay `172.16.8.23`, BGP established, learning hub loopbacks `10.30.1.x` and the overlay `/21`). The AWS spokes follow the same template — only the per-spoke identity values change.

---

## Fabric constants — identical on every spoke
| Item | Value | Notes |
|---|---|---|
| BGP AS | `65001` | **iBGP** — hub + all spokes share one AS |
| Hub BGP peer (overlay) | `172.16.8.1` | the on-ramp; acts as **route-reflector** for spoke↔spoke reachability |
| On-ramp public IP | `160.223.174.119` | the IPsec tunnel endpoint — pin a `/32` to it via each spoke's WAN gateway |
| Overlay pool | `172.16.8.0/21` | on-ramp hands out tunnel IPs from here via IKE mode-config |
| Tunnel interface name | `ONRAMP` | keep the name consistent across spokes |

---

## Per-spoke addressing — Spoke-ID `N`
Deterministic scheme (matches the terraform `var.spokes` map). Good for **up to 9 spokes**; past that the WAN/LAN third octets collide — renumber.

| Field | Formula | Spoke-1 | Spoke-2 | Spoke-3 |
|---|---|---|---|---|
| Hostname | `spoke-N` | `spoke-1` | `spoke-2` | `spoke-3` |
| WAN subnet | `10.200.N.0/24` | `10.200.1.0/24` | `10.200.2.0/24` | `10.200.3.0/24` |
| **port1 gateway** | `10.200.N.1` | `10.200.1.1` | `10.200.2.1` | `10.200.3.1` |
| **LAN (advertised)** | `10.200.(N×10).0/24` | `10.200.10.0/24` | `10.200.20.0/24` | `10.200.30.0/24` |
| **Overlay IP = router-id** | `172.16.8.(23+N)` | `172.16.8.24` | `172.16.8.25` | `172.16.8.26` |
| **IKE local-id** | `sase-spoke-N` | `sase-spoke-1` | `sase-spoke-2` | `sase-spoke-3` |

> `rl-1` is the reference spoke at overlay `172.16.8.23`.

**Router-id / overlay IP:** the `ONRAMP` tunnel IP is normally assigned by the on-ramp via IKE **mode-config** out of `172.16.8.0/21`. Confirm the assigned IP with `get system interface ONRAMP`, then set `router-id` to it. The table values are the *target* plan — if the pool assigns differently, use the assigned IP. The only hard rule is **unique per spoke** (duplicate router-id breaks the route-reflector). For determinism independent of the pool, use a per-spoke loopback as router-id instead.

---

## Required static routes — every spoke
Two longest-prefix `/32` pins keep the box reachable once the default rides the tunnel (both survive the on-ramp's injected default because prefix length beats distance):

```
config router static
    edit 3
        # On-ramp tunnel endpoint via WAN — prevents the tunnel recursing into itself (blackhole/flap).
        # This is the AWS analog of rl-1's:  S 160.223.174.119/32 via 192.168.209.62, wan
        set dst 160.223.174.119 255.255.255.255
        set gateway 10.200.N.1
        set device "port1"
    next
    edit 10
        # Management return path via WAN — admin survives the injected default.
        # Already baked into the terraform bootstrap (keyed on admin_cidr / mgmt_return_cidr).
        set dst <mgmt-subnet> <mask>
        set gateway 10.200.N.1
        set device "port1"
    next
end
```

---

## IPsec phase1 — NAT identity
AWS spokes sit behind a **1:1 EIP NAT**, so IKE rides NAT-T / IKE-over-TCP and the dial-up on-ramp identifies each spoke by **IKE local-id, not source IP**. Give every spoke a **unique** local-id or the on-ramp can't tell them apart:

```
config vpn ipsec phase1-interface
    edit "ONRAMP"
        set localid "sase-spoke-N"
        ...
    next
end
```

---

## BGP template — per spoke
Substitute the Spoke-ID `N` values from the table above.

```
config router bgp
    set as 65001
    set router-id 172.16.8.<23+N>          # UNIQUE per spoke
    set ibgp-multipath enable              # dual-hub ECMP (primary + secondary on-ramp)
    set recursive-next-hop enable          # REQUIRED — BGP next-hops resolve recursively via ONRAMP
    set scan-time 5
    set graceful-restart enable
    config neighbor
        edit "172.16.8.1"                  # on-ramp overlay peer (route-reflector)
            set next-hop-self enable
            set soft-reconfiguration enable
            set interface "ONRAMP"
            set remote-as 65001
            set update-source "ONRAMP"
        next
    end
    config network
        edit 1
            set prefix 10.200.<N×10>.0 255.255.255.0   # the spoke's OWN LAN only
        next
    end
end
```

**Advertise only the spoke's own LAN.** Never advertise the AWS WAN transit (`10.200.N.0/24`). Leave `redistribute connected` **off** (use explicit `config network`) so you don't leak the WAN/overlay/management segments — same as `rl-1`.

---

## Verify (per spoke)
```
get router info routing-table bgp          # learned hub loopbacks + overlay /21
get router info bgp summary                # neighbor 172.16.8.1 State = Established
diagnose vpn ike gateway list name ONRAMP  # tunnel up, NAT-T detected
get system interface ONRAMP                # confirm assigned overlay IP == router-id
```
