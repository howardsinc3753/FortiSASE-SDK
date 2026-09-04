# FortiSASE Branch On-Ramp — Site Intake Checklist

**What this is:** the handful of site-local details I need from you to generate each branch's
FortiGate ZTP config. Please copy the **"Fill-in per site"** block below once per FortiGate and
email it back.

**You do _not_ need FortiSASE set up first.** Everything on the FortiSASE side — the on-ramp
tunnel FQDNs, the BGP peer IPs, the route communities, the tunnel pre-shared key, and the BGP
ASN — I pull when we stand up your FortiSASE tenant together. Don't wait on any of that.

---

## 1. Fill-in per site  (copy this block once for each FortiGate)

```
SITE NAME / LABEL      :  __________________   (e.g. Charlotte-HQ, Store-42)
FORTIGATE MODEL        :  __________________   (30G / 50G / 120G / VM)

WAN (internet) TYPE    :  Static  /  DHCP      (circle one)
   If Static:
   WAN IP / MASK       :  ____________ / ____________   (e.g. 203.0.113.10 / 255.255.255.0)
   WAN GATEWAY         :  ____________            (your ISP's gateway, e.g. 203.0.113.1)

LAN GATEWAY IP / MASK  :  ____________ / ____________   (the FortiGate's inside IP, e.g. 10.50.50.1 /24)
LAN SUBNETS TO PROTECT :  ______________________________
   (every internal subnet/VLAN behind this firewall that should reach the internet via SASE,
    comma-separated — e.g. 10.50.50.0/24, 10.50.60.0/24)

SITE SPEED LIMIT (Mbps):  __________   (this site's slice of the SASE bandwidth, e.g. 100)
   Different download?  :  __________   (only if plan is asymmetric, e.g. 100 up / 500 down → put 500; else leave blank)
```

## 2. Once for the whole network  (send just once, not per site)

```
MANAGEMENT / ADMIN SUBNET(S) THAT MUST REACH THE FIREWALLS :  ______________________________
   (your NOC / jump-host / monitoring subnets — e.g. 192.168.99.0/24, 198.51.100.0/24.
    We pin a return route for these OUT the internet port so remote management keeps working
    even after the on-ramp becomes the default route. ← this is the "management route-back".)

TIME ZONE              :  __________   (e.g. US/Eastern — used for logs/certs)

DO ANY BOXES HAVE A LIVE CONFIG ALREADY?  :  Yes / No
   (No = factory/new → we include the one-time green-field cleanup. Yes = we tailor it.)
```

## 3. I handle these — no action needed from you  (listed so nothing looks missing)

| Item | Where it comes from |
|------|--------------------|
| BOR on-ramp **FQDN(s)** (`ipsec-…prod.fortisase.com`) | Grabbed when we configure your FortiSASE tenant |
| BOR-node **BGP peer IPs** + route **communities** | Assigned during FortiSASE/onboarding |
| Tunnel **pre-shared key (PSK)** | From your FortiSASE BOR location |
| **BGP ASN** (65001), **router-IDs**, SLA thresholds, IPsec crypto, feature blocks | Our standard tenant defaults |
| SLA health-check probe IPs | Auto-assigned (pingable US pool) |

---

### Confirmed rollout (for reference)
- **30G / 50G** → branch **BOR** (on-ramp to SASE).
- **120G** → **BOR + SPA hub** — on-ramp *and* the site-to-site bridge the branches mesh through.
- Boxes are **net-new / factory** → we include the one-time green-field cleanup automatically.
- Target firmware: **FortiOS 7.6.7**. Please upgrade before we ZTP, then confirm the GUI loads and
  the license / FortiGuard shows valid on each box.

### Still need from you
- **How many branch sites** in the first wave?
- **One-time per model:** from the **120G** and **one 30G**, send the output of
  `show system interface` (or `get system interface physical`) so I can lock the exact WAN / LAN
  port names in the generator (the **50G is already confirmed**; 120G + 30G are not yet).
- Admin password: I'll set our POC default unless you want a specific one.
- Unsure of a mask / gateway / which port is WAN? Send what you have — I'll fill gaps from defaults.
