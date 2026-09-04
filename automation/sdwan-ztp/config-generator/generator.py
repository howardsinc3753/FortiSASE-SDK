#!/usr/bin/env python3
"""
BOR / BOR+SPA config generator  ·  Phase 1-2 core.

schema/variables.yaml is the source of truth. This module:
  1. loads tenant defaults + PoPs + platform port-maps from the schema,
  2. merges per-site values, resolves DERIVED fields (lan_subnet, fabric pool,
     port-map, advertised-network ip/mask),
  3. renders the role's Jinja2 template in FortiOS dependency order.

Usage:
    python generator.py --roundtrip           # render the 3 known sites -> generated/
    python generator.py --values site.yaml    # render one site from a values file -> stdout

Deps: jinja2, pyyaml   (pip install jinja2 pyyaml)
"""
import argparse
import ipaddress
import pathlib
import sys

import yaml
from jinja2 import Environment, FileSystemLoader

HERE = pathlib.Path(__file__).parent
SCHEMA = HERE / "schema" / "variables.yaml"
TEMPLATES = HERE / "templates"
OUT = HERE / "generated"


def load_schema():
    return yaml.safe_load(SCHEMA.read_text())


def cidr_to_ip_mask(cidr):
    n = ipaddress.ip_network(cidr, strict=False)
    return f"{n.network_address} {n.netmask}"


def build_context(site, schema):
    ctx = {}
    # 1. tenant/site defaults declared in the schema
    for v in schema["variables"]:
        if "default" in v:
            ctx[v["key"]] = v["default"]
    # 2. feature toggles
    for fk, fv in schema.get("features", {}).items():
        ctx[fk] = fv.get("default", False)
    # 3. per-site values win
    ctx.update(site)
    # 4. platform port-map. A site may override the WAN/LAN interface (e.g. LAN=port16 on the 120G);
    #    the explicit choice wins over the platform default. ctx.update(site) above already copied any
    #    site["lan_port"] in, but we re-derive from pm below, so capture the override first.
    pm = schema["platforms"][ctx["platform"]]
    _wan_ovr, _lan_ovr = site.get("wan_port"), site.get("lan_port")
    ctx["wan_port"] = _wan_ovr or pm["wan_port"]
    ctx["lan_port"] = _lan_ovr or pm["lan_port"]
    if ctx.get("dual_wan"):
        # dual-circuit shifts LAN (vm: port2->port3) and adds a 2nd WAN; always failover+communities
        ctx["wan2_port"] = site.get("wan2_port") or pm.get("wan2_port")
        ctx["lan_port"] = _lan_ovr or pm.get("lan_port_dual", pm["lan_port"])
        ctx["sla_failover"] = True
        ctx["bgp_communities"] = True
        if "TBD" in (ctx["wan_port"], ctx["wan2_port"], ctx["lan_port"]):
            raise ValueError(f"platform {ctx['platform']} has TBD dual-circuit port names — fill them in schema")
    elif "TBD" in (ctx["wan_port"], ctx["lan_port"]):
        raise ValueError(f"platform {ctx['platform']} has TBD port names — fill them in schema")
    # 5. PoPs (tenant objects) — form/values may override; dual uses the cross-mesh pops_dual
    # COPY the pops (we may mutate pop["community"] below for bor_private_access; must not
    # leak back into the caller's values["pops"] or the shared schema dict).
    _pops_src = site.get("pops") or (schema["pops_dual"] if ctx.get("dual_wan") else schema["pops"])
    ctx["pops"] = [dict(p) for p in _pops_src]
    # SLA probe pool: one UNIQUE, pingable target per overlay. PoP peers don't answer ICMP and
    # FortiOS rejects a detect server shared across health-checks, so each HC_<PoP> draws a distinct
    # slot from this pool by PoP order (a PoP's own `probe:` overrides its slot in the template).
    ctx["sla_probe_pool"] = site.get("sla_probe_pool") or schema.get("sla_probe_pool") or ctx.get("sla_servers") or ["8.8.8.8"]
    # 6. DERIVED
    ctx["lan_subnet"] = str(ipaddress.ip_network(f"{ctx['lan_ip']}/{ctx['lan_mask']}", strict=False).network_address)
    ctx["advertised_networks"] = [cidr_to_ip_mask(n) for n in ctx.get("advertised_networks", []) or []]
    ctx["trusted_host_routes"] = [cidr_to_ip_mask(n) for n in ctx.get("trusted_host_routes", []) or []]
    # per-branch BGP community: AS:(1000+site_id) — unique per branch, tagged alongside
    # the shared per-PoP path community so each site's routes are identifiable at the hub.
    if str(ctx.get("site_id", "")).strip():
        ctx["site_community"] = f"{ctx['bgp_as']}:{1000 + int(ctx['site_id'])}"
    # SLA-failover: the "degraded" community tagged by RM_OUT_FAIL; depends on the community infra
    ctx["fail_community"] = f"{ctx['bgp_as']}:64911"
    # Canonical hub RM_FABRIC_IN covers on-ramp communities AS:(10k) for k=1..hub_lp_slots (+ fail),
    # independent of any single spoke's pop count -> single/dual/mixed/5G all steer, no ID collisions.
    ctx["hub_lp_slots"] = int(ctx.get("hub_lp_slots") or 8)
    if ctx.get("sla_failover"):
        ctx["bgp_communities"] = True
        # each on-ramp needs its own unique probe; running short would re-duplicate a detect server (-7)
        n_unpinned = sum(1 for p in ctx["pops"] if not p.get("probe"))
        if n_unpinned > len(ctx["sla_probe_pool"]):
            raise ValueError(f"{len(ctx['pops'])} PoPs but only {len(ctx['sla_probe_pool'])} probe-pool "
                             f"entries — extend sla_probe_pool or pin per-PoP `probe:` values")
    # BOR_Private_Access steering order: which on-ramp(s) LEAD this site's private (site-to-site)
    # path. Default = Primary (pops order). bor_private_access anchors it on the SECONDARY BOR node
    # so the site lands on a DIFFERENT node than default (Primary) sites and the hub can bridge them:
    # lead with the secondary-PoP tunnel(s) — BOTH circuits on dual — flipping the service member
    # order AND the LAN communities (secondary tunnels take the hub-preferred LP slots). Generalizes
    # the single-circuit 2-way swap to a PoP-group reorder (PoP key = name minus trailing digits, so
    # Dallas1/Dallas2 group as "Dallas", Primary/Secondary as themselves).
    pa = list(enumerate(ctx["pops"], start=1))                 # original LP order
    if ctx.get("bor_private_access") and len(ctx["pops"]) >= 2:
        pref_comms = [p["community"] for p in ctx["pops"]]     # original LP order (:10,:20,:30,:40)
        primary_key = str(ctx["pops"][0]["name"]).rstrip("0123456789")   # PoP of the top pref (e.g. Dallas)
        secondary = [x for x in pa if str(x[1]["name"]).rstrip("0123456789") != primary_key]
        primary = [x for x in pa if str(x[1]["name"]).rstrip("0123456789") == primary_key]
        if secondary:                                          # only if a distinct 2nd PoP exists
            pa = secondary + primary
            for i, (_, p) in enumerate(pa):
                p["community"] = pref_comms[i]                 # secondary tunnels take the top LP slots
    ctx["pa_members"] = [{"num": n, "name": p["name"]} for n, p in pa]
    # Spoke-side BGP local-pref per on-ramp, DERIVED from the community (matches the hub RM_FABRIC_IN):
    # community AS:(10*k) -> lp 200-(k-1)*5 (:10->200, :20->195, :30->190, :40->185), fail -> 50.
    # WHY: the FortiSASE BOR fabric collapses a spoke's two LAN advertisements to ONE best-path BEFORE
    # the hub, and community does NOT affect best-path — so the SPOKE must set lp to steer which path
    # the fabric delivers (confirmed live 2026-08-17). Auto-follows the anchor (its community is :10).
    for p in ctx["pops"]:
        try:
            k = int(str(p["community"]).split(":")[-1]) // 10
        except (ValueError, AttributeError):
            k = 1
        p["local_pref"] = 200 - (k - 1) * 5
    ctx["fail_local_pref"] = 50
    # per-site bandwidth shaper: UP = site_bandwidth_mbps; DOWN defaults to match unless overridden.
    up_mbps = int(ctx.get("site_bandwidth_mbps") or 0)
    down_mbps = int(ctx.get("site_bandwidth_down_mbps") or 0) or up_mbps
    ctx["shaper_up_mbps"], ctx["shaper_down_mbps"] = up_mbps, down_mbps
    ctx["shaper_up_kbps"], ctx["shaper_down_kbps"] = up_mbps * 1000, down_mbps * 1000
    if ctx.get("role") == "bor-spa":
        net = ipaddress.ip_network(ctx["fabric_overlay"], strict=False)
        base = net.network_address
        ctx["fabric_overlay_ip"] = str(base)
        ctx["fabric_hub_ip"] = str(base + 253)
        ctx["fabric_hub_remote"] = str(base + 254)
        ctx["fabric_pool_start"] = str(base + 1)
        ctx["fabric_pool_end"] = str(base + 252)
        # network-id (network-overlay) is a LOCAL demux tag scoped to tunnels sharing the same remote
        # gateway / public IP — NOT a box-global id. The SASE_Hub fabric (inbound dial-in) and the
        # on-ramps (outbound to the PoPs) are different remotes, so the fabric may reuse an on-ramp
        # network-id (e.g. 1) with no collision (Daniel, FortiGate SME, 2026-08-30). The only real
        # uniqueness is BETWEEN a single PoP's two tunnel-configs (net-id 0/1), which pops_dual already
        # guarantees — so no fabric-vs-onramp guard.
    return ctx


def render(site, schema=None):
    schema = schema or load_schema()
    ctx = build_context(site, schema)
    env = Environment(loader=FileSystemLoader(str(TEMPLATES)), keep_trailing_newline=True)
    if ctx["role"] == "bor-spa":
        tmpl = "bor-spa-dual.conf.j2" if ctx.get("dual_wan") else "bor-spa.conf.j2"
    elif ctx.get("dual_wan"):
        tmpl = "bor-dual.conf.j2"
    else:
        tmpl = "bor.conf.j2"
    return env.get_template(tmpl).render(**ctx)


# ---- FortiManager model-device CSV export -----------------------------------
# Maps a built context to one row of the FMG "Add Model Device from CSV" import.
# Spec: fmg-export/FMG-CSV-COLUMN-SPEC.md (34 columns, header is FIXED + case-sensitive).
# Per-device columns are always filled; tenant-scope columns are BLANK when they equal the
# schema default so the ADOM-level metadata default resolves. DERIVED come pre-computed.
FMG_CSV_HEADERS = [
    "Serial Number", "Device Blueprint", "Name", "HOSTNAME", "SITE_ID", "ADMIN_PASSWORD",
    "WAN_PORT", "LAN_PORT", "WAN_MODE", "WAN_IP", "WAN_MASK", "WAN_GATEWAY", "WAN_DHCP_DIST",
    "MGMT_GATEWAY", "LAN_IP", "LAN_MASK", "LAN_SUBNET", "ROUTER_ID",
    "TIMEZONE", "ADMIN_SPORT", "ADMIN_TIMEOUT", "DEVICE_ALIAS",
    "BGP_AS", "BGP_KEEPALIVE", "BGP_HOLDTIME",
    "SLA_LATENCY_MS", "SLA_JITTER_MS", "SLA_PKTLOSS_PCT",
    "SITE_BW_MBPS", "SITE_BW_DOWN_MBPS",
    "POP1_FQDN", "POP2_FQDN", "POP1_PROBE", "POP2_PROBE",
]
# platform -> blueprint suffix (NOT platform.upper(): fgt-30g -> 30G, not FGT-30G)
_FMG_PLATFORM_SUFFIX = {"vm": "VM", "fgt-30g": "30G", "fgt-50g": "50G", "fgt-120g": "120G", "fgt-71f": "71F"}
# tenant-scope CSV column -> variables.yaml key (blanked when value == schema default)
_FMG_TENANT_OPTIONAL = {
    "TIMEZONE": "timezone", "ADMIN_SPORT": "admin_sport", "ADMIN_TIMEOUT": "admintimeout",
    "DEVICE_ALIAS": "device_alias", "BGP_AS": "bgp_as", "BGP_KEEPALIVE": "bgp_keepalive",
    "BGP_HOLDTIME": "bgp_holdtime", "SLA_LATENCY_MS": "sla_latency_threshold",
    "SLA_JITTER_MS": "sla_jitter_threshold", "SLA_PKTLOSS_PCT": "sla_packetloss_threshold",
    "SITE_BW_MBPS": "site_bandwidth_mbps", "SITE_BW_DOWN_MBPS": "site_bandwidth_down_mbps",
}
# --- SPA hub (bor-spa) adds the fabric columns ON TOP of the 34 BOR columns (superset) ---
# per-device fabric cols -> ctx key (the 4 fabric_* derived ones are pre-computed by build_context)
_FMG_SPA_PERDEVICE = {
    "HUB_LOOPBACK": "hub_loopback",            # optional — blank omits the loopback
    "FABRIC_OVERLAY": "fabric_overlay",        # required for a hub (e.g. 10.10.7.0/24)
    "FABRIC_HUB_IP": "fabric_hub_ip",          # derived host(overlay, 253)
    "FABRIC_HUB_REMOTE": "fabric_hub_remote",  # derived host(overlay, 254)
    "FABRIC_POOL_START": "fabric_pool_start",  # derived host(overlay, 1)
    "FABRIC_POOL_END": "fabric_pool_end",      # derived host(overlay, 252)
}
# tenant-scope fabric cols (blanked when == schema default). NOTE: the SASE_Hub fabric tunnel PSK
# is seed_psk ($(SEED_PSK) ADOM meta), same as BOR — so there is NO FABRIC_PSK column (fabric_psk
# is declared in the schema but not wired into the templates).
_FMG_SPA_TENANT_OPTIONAL = {
    "FABRIC_NETWORK_ID": "fabric_network_id",
    "HUB_PROPOSAL": "hub_proposal",
}
FMG_CSV_HEADERS_SPA = FMG_CSV_HEADERS + list(_FMG_SPA_PERDEVICE) + list(_FMG_SPA_TENANT_OPTIONAL)
# --- dual-circuit (dual_wan) adds the WAN2 per-device columns. WAN_MODE + WAN_DHCP_DIST are SHARED
# across both circuits (one column each). The 4 cross-mesh tunnels reuse the SAME 2 PoP FQDNs,
# differing only by tenant-baked network-id/bor_node -> so NO POP3/POP4 columns. ---
_FMG_DUAL_PERDEVICE = {
    "WAN2_PORT": "wan2_port", "WAN2_IP": "wan2_ip", "WAN2_MASK": "wan2_mask",
    "WAN2_GATEWAY": "wan2_gateway", "MGMT_GATEWAY2": "mgmt_gateway2",
}


def fmg_headers_for(ctx):
    """Column set for a site: BOR 34, + WAN2 (5) if dual_wan, + fabric (8) if bor-spa.
    So bor=34, bor-dual=39, bor-spa=42, bor-spa-dual=47."""
    h = list(FMG_CSV_HEADERS)
    if ctx.get("dual_wan"):
        h += list(_FMG_DUAL_PERDEVICE)
    if ctx.get("role") == "bor-spa":
        h += list(_FMG_SPA_PERDEVICE) + list(_FMG_SPA_TENANT_OPTIONAL)
    return h


def fmg_blueprint_name(ctx):
    """role + circuit + platform -> named FMG Device Blueprint:
    BOR-{SPA-}{SINGLE|DUAL}-STD-{VM|30G|50G|120G}."""
    spa = "SPA-" if ctx.get("role") == "bor-spa" else ""
    circ = "DUAL" if ctx.get("dual_wan") else "SINGLE"
    suffix = _FMG_PLATFORM_SUFFIX.get(ctx.get("platform"), str(ctx.get("platform", "")).upper())
    return f"BOR-{spa}{circ}-STD-{suffix}"


def fmg_csv_row(ctx, serial, schema):
    """One FMG-import CSV row (dict keyed by FMG_CSV_HEADERS) from a BUILT context
    (ctx = build_context output, so lan_subnet/wan_port/lan_port/pops are resolved)."""
    defaults = {v["key"]: v.get("default") for v in schema["variables"]}
    pops = ctx.get("pops", [])
    s = lambda x: "" if x is None else str(x)                                # noqa: E731
    def blank_if_default(key):
        val = ctx.get(key)
        return "" if val is None or s(val) == s(defaults.get(key)) else s(val)
    dhcp = s(ctx.get("wan_mode")).lower() == "dhcp"
    row = {
        "Serial Number": s(serial).strip(),
        "Device Blueprint": fmg_blueprint_name(ctx),
        "Name": s(ctx.get("hostname")),
        "HOSTNAME": s(ctx.get("hostname")),
        "SITE_ID": s(ctx.get("site_id")),
        "ADMIN_PASSWORD": s(ctx.get("admin_password")),
        "WAN_PORT": s(ctx.get("wan_port")),
        "LAN_PORT": s(ctx.get("lan_port")),
        "WAN_MODE": s(ctx.get("wan_mode")),
        "WAN_IP": "" if dhcp else s(ctx.get("wan_ip")),
        "WAN_MASK": "" if dhcp else s(ctx.get("wan_mask")),
        "WAN_GATEWAY": "" if dhcp else s(ctx.get("wan_gateway")),
        "WAN_DHCP_DIST": s(ctx.get("wan_dhcp_distance")),
        "MGMT_GATEWAY": s(ctx.get("mgmt_gateway")),
        "LAN_IP": s(ctx.get("lan_ip")),
        "LAN_MASK": s(ctx.get("lan_mask")),
        "LAN_SUBNET": s(ctx.get("lan_subnet")),
        "ROUTER_ID": s(ctx.get("router_id")),
        # PoPs: app is the source of truth, so fill FQDNs; probe only when a PoP pins one.
        "POP1_FQDN": s(pops[0].get("fqdn")) if len(pops) > 0 else "",
        "POP2_FQDN": s(pops[1].get("fqdn")) if len(pops) > 1 else "",
        "POP1_PROBE": s(pops[0].get("probe")) if len(pops) > 0 else "",
        "POP2_PROBE": s(pops[1].get("probe")) if len(pops) > 1 else "",
    }
    for col, key in _FMG_TENANT_OPTIONAL.items():
        row[col] = blank_if_default(key)
    if ctx.get("dual_wan"):                             # dual-circuit: WAN2 (same static/dhcp rule as WAN1)
        row["WAN2_PORT"] = s(ctx.get("wan2_port"))
        row["WAN2_IP"] = "" if dhcp else s(ctx.get("wan2_ip"))
        row["WAN2_MASK"] = "" if dhcp else s(ctx.get("wan2_mask"))
        row["WAN2_GATEWAY"] = "" if dhcp else s(ctx.get("wan2_gateway"))
        row["MGMT_GATEWAY2"] = s(ctx.get("mgmt_gateway2"))
    if ctx.get("role") == "bor-spa":                    # SPA hub: append the fabric superset
        for col, key in _FMG_SPA_PERDEVICE.items():
            row[col] = s(ctx.get(key))
        for col, key in _FMG_SPA_TENANT_OPTIONAL.items():
            row[col] = blank_if_default(key)
    return row


def fmg_csv(rows, headers=None):
    """rows = list of dicts -> CSV text. headers defaults to the BOR 34; pass FMG_CSV_HEADERS_SPA
    (or fmg_headers_for(ctx)) for SPA-hub rows so the fabric columns are emitted."""
    import csv
    import io
    headers = headers or FMG_CSV_HEADERS
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=headers, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({h: r.get(h, "") for h in headers})
    return buf.getvalue()


# ---- Round-trip test sites (the 3 known-good references) --------------------
POC_SECRETS = {"admin_password": "FortiSASE-OnRamp-2026!", "seed_psk": "<TUNNEL_PSK>"}
SITES = {
    "site-1_bor": {**POC_SECRETS, "role": "bor", "platform": "vm", "hostname": "spoke-1", "site_id": 1,
                   "wan_mode": "static", "wan_ip": "10.200.1.10", "wan_gateway": "10.200.1.1",
                   "lan_ip": "10.200.10.10", "router_id": "10.30.1.100"},
    "site-5_bor-spa": {**POC_SECRETS, "role": "bor-spa", "platform": "vm", "hostname": "hub-5", "site_id": 5,
                       "wan_mode": "static", "wan_ip": "10.200.5.10", "wan_gateway": "10.200.5.1",
                       "lan_ip": "10.200.50.10", "router_id": "10.30.1.105",
                       "hub_loopback": "", "fabric_overlay": "10.10.50.0/24", "sla_failover": True},  # loopback unused in POC -> blank disables it
    "site-5_bor-50g": {**POC_SECRETS, "role": "bor", "platform": "fgt-50g", "hostname": "spoke-5", "site_id": 5,
                       "device_alias": "FortiGate-50G-Lab", "sla_failover": True,
                       "wan_mode": "dhcp",  # lab 50G WAN is DHCP -> WAN-egress routes use dynamic-gateway
                       "lan_ip": "10.50.50.1", "router_id": "10.30.1.150"},
    "site-6_bor-120g": {**POC_SECRETS, "role": "bor", "platform": "fgt-120g", "hostname": "spoke-6", "site_id": 6,
                        "device_alias": "FortiGate-120G-Lab", "sla_failover": True, "wan_mode": "dhcp",
                        "lan_ip": "10.60.60.1", "router_id": "10.30.1.160", "lan_port": "port16",
                        "timezone": "US/Eastern"},  # DHCP WAN -> WAN-egress routes use dynamic-gateway
    "site-1_bor-priv": {**POC_SECRETS, "role": "bor", "platform": "vm", "hostname": "spoke-1", "site_id": 1,
                        "wan_mode": "static", "wan_ip": "10.200.1.10", "wan_gateway": "10.200.1.1",
                        "lan_ip": "10.200.10.10", "router_id": "10.30.1.100", "bor_private_access": True},
    "site-4_bor-dual": {**POC_SECRETS, "role": "bor", "platform": "vm", "hostname": "spoke-4", "site_id": 4,
                        "dual_wan": True, "device_alias": "FortiGate-Site4-DualISP", "wan_mode": "static",
                        "wan_ip": "10.204.1.10", "wan_gateway": "10.204.1.1",
                        "wan2_ip": "10.204.2.10", "wan2_gateway": "10.204.2.1",
                        "lan_ip": "10.204.10.10", "router_id": "10.30.1.140"},
    "site-4_bor-dual-priv": {**POC_SECRETS, "role": "bor", "platform": "vm", "hostname": "spoke-4", "site_id": 4,
                             "dual_wan": True, "wan_mode": "static",
                             "wan_ip": "10.204.1.10", "wan_gateway": "10.204.1.1",
                             "wan2_ip": "10.204.2.10", "wan2_gateway": "10.204.2.1",
                             "lan_ip": "10.204.10.10", "router_id": "10.30.1.141", "bor_private_access": True},
    # INTERIM (2026-08-22): dual-circuit BOR on-ramps + SINGLE SASE_Hub on WAN1 (SASE_Hub2 tabled).
    "site-7_bor-spa-dual": {**POC_SECRETS, "role": "bor-spa", "platform": "vm", "hostname": "hub-7", "site_id": 7,
                            "dual_wan": True, "device_alias": "FortiGate-Hub7-DualISP", "wan_mode": "static",
                            "wan_ip": "10.207.1.10", "wan_gateway": "10.207.1.1",
                            "wan2_ip": "10.207.2.10", "wan2_gateway": "10.207.2.1",
                            "lan_ip": "10.207.70.10", "router_id": "10.30.1.107",
                            "hub_loopback": "", "fabric_overlay": "10.10.70.0/24",
                            "fabric_network_id": 2},  # must != on-ramp network-ids 0/1 (unique overlay ID)
}


def roundtrip():
    schema = load_schema()
    OUT.mkdir(exist_ok=True)
    for name, site in SITES.items():
        conf = render(site, schema)
        (OUT / f"{name}.rendered.conf").write_text(conf)
        print(f"  [ok] {name:18} -> generated/{name}.rendered.conf  ({len(conf.splitlines())} lines, role={site['role']}, {site['platform']})")
    print("Round-trip complete -- diff each *.rendered.conf against the golden to verify completeness.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roundtrip", action="store_true", help="render the 3 known sites into generated/")
    ap.add_argument("--values", help="YAML file of one site's values -> stdout")
    args = ap.parse_args()
    if args.roundtrip:
        roundtrip()
    elif args.values:
        site = yaml.safe_load(pathlib.Path(args.values).read_text())
        sys.stdout.write(render(site))
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
