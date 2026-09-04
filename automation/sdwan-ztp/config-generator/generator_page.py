"""
Streamlit UI for the BOR / BOR+SPA config generator  ·  Phase 3 (partner-UX pass).

Schema-driven: the form is built by walking schema/variables.yaml — no field is
hard-coded. Built for non-technical partners:
  • Quick-start buttons pre-fill a working baseline (Site 1-5) to edit from
  • every input shows a shadow example + a help bubble (the FortiOS format)
  • BGP communities are auto-assigned + tucked in Advanced (rarely touched)

Run:  pip install -r requirements.txt  &&  streamlit run app.py
"""
import ipaddress
import re
import zoneinfo

import streamlit as st

from generator import (build_context, fmg_blueprint_name, fmg_csv, fmg_csv_row,
                       fmg_headers_for, load_schema, render)

# FortiOS accepts IANA timezone names (US/Pacific, America/New_York, ...); zoneinfo has the full set.
_TIMEZONES = sorted(zoneinfo.available_timezones())
# Selectable physical interfaces per platform, for the LAN-interface picker.
PLATFORM_PORTS = {
    "vm":       ["port1", "port2", "port3", "port4"],
    "fgt-30g":  ["wan", "lan1", "lan2", "lan3"],
    "fgt-50g":  ["wan", "lan1", "lan2", "lan3"],
    "fgt-71f":  ["wan1", "wan2", "internal"],
    "fgt-120g": [f"port{i}" for i in range(1, 17)] + ["x1", "x2", "x3", "x4"] + [f"port{i}" for i in range(17, 25)],
}

st.set_page_config(page_title="BOR Config Generator", page_icon="🛰️", layout="wide",
                   initial_sidebar_state="expanded")
schema = load_schema()
VARS = schema["variables"]
GROUPS = ["Identity & Model", "WAN", "LAN", "Bandwidth", "BGP", "SPA Fabric",
          "SD-WAN SLA", "Routing", "Management", "IPsec", "Secrets"]

# Shadow examples (ghost text) for fields with no default — shows the expected format.
EXAMPLES = {
    "hostname": "spoke-1", "wan_ip": "10.200.1.10", "wan_gateway": "10.200.1.1",
    "lan_ip": "10.1.10.1", "router_id": "10.30.1.100",
    "hub_loopback": "10.123.123.1", "fabric_overlay": "10.10.1.0/24",
    # list fields — CIDR (a host with no /prefix becomes /32):
    "advertised_networks": "10.7.20.0/24", "trusted_host_routes": "203.0.113.0/24  (host = /32)",
    "sla_servers": "8.8.8.8",
}

# Plain-language explainer shown under a section header (for non-technical partners).
GROUP_HELP = {
    "Bandwidth": "Set this site's internet **speed limit** — its slice of the shared 2 Gbps BOR "
                 "pool. One number limits upload and download together. The advanced box is only "
                 "for sites whose plan gives a *different* (usually faster) download speed.",
}

# Soft per-section shades so non-technical partners can eyeball each fill-in block.
_SECTION_COLORS = ["#eef4ff", "#eefaf0", "#fff6e9", "#fdeef4", "#eef8fb", "#f3eefb", "#fbf1ea"]


def _banner_html(title, subtitle, color):
    sub = (f"<span style='color:#5a6472;font-size:0.85rem;margin-left:0.55rem;'>· {subtitle}</span>"
           if subtitle else "")
    return (f"<div style='background:{color};color:#1c2733;padding:0.5rem 0.9rem;border-radius:8px;"
            f"margin-bottom:0.5rem;'><span style='font-size:1.1rem;font-weight:700;'>{title}</span>{sub}</div>")


def banner(title, subtitle="", color="#eef4ff"):
    """A standalone shaded section header (no card)."""
    st.markdown(_banner_html(title, subtitle, color), unsafe_allow_html=True)


def section(title, subtitle="", color="#eef4ff"):
    """A titled, softly-shaded CARD. Returns the container; use `with section(...):` for the body."""
    box = st.container(border=True)
    box.markdown(_banner_html(title, subtitle, color), unsafe_allow_html=True)
    return box


def fortisase_ipsec_card(pops, psk):
    """FortiSASE-side 'Create New Tunnel Config' values — the implementation engineer's hand-off.
    IP range is derived from the BOR node IP (= Tunnel interface IP) + the pool mask."""
    out = ["FortiSASE On-Ramp — IPsec tunnel-config values",
           "(FortiSASE portal -> Network -> On-Ramp -> PoP -> Create New Tunnel Config)",
           "=" * 62, ""]
    for p in pops:
        intf = str(p.get("bor_node", "")).strip()
        mask = str(p.get("netmask", "255.255.255.0")).strip() or "255.255.255.0"
        try:
            net = ipaddress.ip_network(f"{intf}/{mask}", strict=False)
            rng = f"{net.network_address + 11} - {net.broadcast_address - 1}"
        except ValueError:
            rng = "(check BOR node IP + mask)"
        try:
            nid = int(p.get("network_id", 0))
        except (TypeError, ValueError):
            nid = 0
        out += [
            f"PoP FQDN            : {p.get('fqdn', '')}",
            f"Name                : {p.get('name', '')}",
            f"Device type         : Remote device (FortiGate)",
            f"Tunnel interface IP : {intf}",
            f"IP range            : {rng}",
            f"Subnet mask         : {mask}",
            f"Pre-shared key      : {psk}",
            f"Network ID          : {nid}",
            "-" * 62, "",
        ]
    return "\n".join(out)


def baseline(n, role="bor"):
    """A working starting point for Site n. Octet math keeps it valid for site IDs up to ~250."""
    o = ((n - 1) % 254) + 1                 # 3rd octet 1..254 (wraps for very large IDs)
    rid = 100 + ((n - 1) % 150)             # router-id host 100..249 (avoids PoP-reserved .1-.6)
    b = {
        "site_id": n,
        "role": role, "platform": "vm", "wan_mode": "static",
        "hostname": f"{'hub' if role == 'bor-spa' else 'spoke'}-{n}",
        "wan_ip": f"10.200.{o}.10", "wan_mask": "255.255.255.0", "wan_gateway": f"10.200.{o}.1",
        "lan_ip": f"10.{o}.10.1", "lan_mask": "255.255.255.0",
        "router_id": f"10.30.1.{rid}",
        "admin_password": "FortiSASE-OnRamp-2026!", "seed_psk": "<TUNNEL_PSK>",
    }
    if role == "bor-spa":
        b["hub_loopback"] = f"10.123.123.{o}"
        b["fabric_overlay"] = f"10.10.{o}.0/24"
    return b


def baseline_dual(n, role="bor"):
    """Dual-ISP cross-mesh starting point (IPs align with the aws-site4-dual-wan terraform).
    role-aware: bor-spa loads a dual-circuit HUB (adds the SPA fabric fields)."""
    o = ((n - 1) % 254) + 1
    rid = 100 + ((n - 1) % 150)
    b = {
        "site_id": n, "role": role, "platform": "vm", "wan_mode": "static",
        "hostname": f"{'hub' if role == 'bor-spa' else 'spoke'}-{n}",
        "wan_ip": "10.204.1.10", "wan_mask": "255.255.255.0", "wan_gateway": "10.204.1.1",
        "wan2_ip": "10.204.2.10", "wan2_mask": "255.255.255.0", "wan2_gateway": "10.204.2.1",
        "lan_ip": "10.204.10.10", "lan_mask": "255.255.255.0",
        "router_id": f"10.30.1.{rid}",
        "admin_password": "FortiSASE-OnRamp-2026!", "seed_psk": "<TUNNEL_PSK>",
    }
    if role == "bor-spa":
        b["hub_loopback"] = ""                       # optional loopback, off by default
        b["fabric_overlay"] = f"10.10.{o}.0/24"      # SPA fabric overlay (SASE_Hub dial-up pool)
        # fabric_network_id stays at the schema default (1) for single AND dual — network-id is a
        # local per-overlay demux tag, so reusing an on-ramp net-id on the fabric is fine.
    return b


def applies(v, role):
    if v["scope"] in ("derived", "const"):
        return False
    if v.get("roles") and role not in v["roles"]:
        return False
    return True


def show_if_ok(v, values):
    cond = v.get("show_if")
    if not cond:
        return True
    m = re.match(r"(\w+)\s*==\s*(\w+)", cond)
    return str(values.get(m.group(1))) == m.group(2) if m else True


def widget(v, key):
    t, label, default, help_ = v["type"], f"{v['label']}  ·  {v['scope']}", v.get("default"), v.get("help")
    ph = EXAMPLES.get(v["key"], "")
    if v["key"] == "timezone":
        idx = _TIMEZONES.index(default) if default in _TIMEZONES else 0
        return st.selectbox(label, _TIMEZONES, index=idx, key=key,
                            help=help_ or "Searchable — type to filter (IANA name, e.g. US/Eastern).")
    if t == "enum":
        opts = v["values"]
        return st.selectbox(label, opts, index=opts.index(default) if default in opts else 0, help=help_, key=key)
    if t == "int":
        return int(st.number_input(label, value=int(default) if default is not None else 0, step=1, help=help_, key=key))
    if t == "secret":
        return st.text_input(label, value=str(default or ""), type="password", help=help_, key=key)
    if t == "list":
        seed = st.session_state.get(key)
        if not isinstance(seed, list):
            seed = default if isinstance(default, list) else []
        ex = EXAMPLES.get(key, "")
        cap = f"**{v['label']}**  ·  {v['scope']}" + (f" — {help_}" if help_ else "")
        if ex:
            cap += f"  ·  e.g. `{ex}`"
        st.caption(cap)
        edited = st.data_editor(
            [{"value": x} for x in seed] or [{"value": ""}],
            num_rows="dynamic", use_container_width=True, key=f"{key}__editor",
            column_config={"value": st.column_config.TextColumn(
                v["label"] + (f"  ·  e.g. {ex}" if ex else ""),
                help=(help_ or "") + "  ·  click + below the last row to add another", width="large")})
        recs = edited.to_dict("records") if hasattr(edited, "to_dict") else [dict(r) for r in edited]
        return [str(r.get("value", "")).strip() for r in recs if str(r.get("value", "")).strip()]
    return st.text_input(label, value=str(default or ""), placeholder=ph, help=help_, key=key)


def validate(values, role):
    errs = []
    for v in VARS:
        if not applies(v, role) or not show_if_ok(v, values):
            continue
        val = values.get(v["key"])
        if (v.get("required") or v.get("required_if")) and (val in (None, "", [])):
            errs.append(f"**{v['label']}** is required")
        elif val and v.get("validate") and not re.match(v["validate"], str(val)):
            errs.append(f"**{v['label']}** — `{val}` doesn't match the expected format")
    # mgmt_gateway must be ON the WAN subnet (static WAN only): an off-subnet next-hop on a
    # `set device <wan>` static route is unreachable, so the bastion/mgmt return route goes
    # INACTIVE (silent mgmt lockout). On DHCP mgmt_gateway is ignored (dynamic-gateway), so skip.
    if str(values.get("wan_mode")) == "static":
        _mg = [("Mgmt next-hop gateway", values.get("mgmt_gateway"),
                values.get("wan_ip"), values.get("wan_mask"))]
        if values.get("dual_wan"):
            _mg.append(("Mgmt next-hop gateway — WAN2", values.get("mgmt_gateway2"),
                        values.get("wan2_ip"), values.get("wan2_mask")))
        for label, gw, ip, mask in _mg:
            if gw and ip and mask:
                try:
                    net = ipaddress.ip_network(f"{ip}/{mask}", strict=False)
                    if ipaddress.ip_address(str(gw)) not in net:
                        errs.append(f"**{label}** `{gw}` is off-subnet from the WAN ({net}) — an off-subnet "
                                    f"next-hop on a `set device` WAN route is unreachable, so the route goes "
                                    f"inactive. Use a gateway inside {net}, or blank it to reuse the WAN gateway.")
                except ValueError:
                    pass  # malformed IP/mask already flagged by the per-field format validators above
    return errs


# ---- readiness lights (per-section greenlights + the at-a-glance card) ------
_LIGHT = {"ready": "🟢", "incomplete": "⚪", "invalid": "🔴"}


def field_state(v, role, cur):
    """One field's readiness: 'ready' | 'incomplete' | 'invalid', or None if N/A (wrong role / hidden)."""
    if v["key"] in ("role", "platform") or not applies(v, role) or not show_if_ok(v, cur):
        return None
    val = cur.get(v["key"])
    if (v.get("required") or v.get("required_if")) and val in (None, "", []):
        return "incomplete"
    if val and v.get("validate") and not re.match(v["validate"], str(val)):
        return "invalid"
    return "ready"


def section_state(g, role, cur):
    """Roll a section up to one light: 🔴 any invalid, else ⚪ any required-empty, else 🟢.
    None when the section has no applicable fields for this role."""
    states = [s for s in (field_state(v, role, cur) for v in VARS if v["group"] == g) if s is not None]
    if not states:
        return None
    return "invalid" if "invalid" in states else ("incomplete" if "incomplete" in states else "ready")


def hub_companion(values):
    """CANONICAL, community-keyed return-path steering for the HUB — paste ONCE per hub.
    Maps every on-ramp community AS:(10k) -> a distinct local-pref, independent of how many
    on-ramps any given spoke has. So single-WAN, dual-WAN, mixed, and a future 5G on-ramp all
    steer correctly with NO per-spoke change and NO rule-ID collisions; re-paste is a no-op.
    LP higher wins (BGP best-path); priority lower wins (FIB / SD-WAN)."""
    gas = values.get("bgp_as", 65001)
    slots = int(values.get("hub_lp_slots") or 8)
    cls, rules = [], []
    for k in range(1, slots + 1):
        comm = f"{gas}:{10 * k}"
        lp = 200 - (k - 1) * 5     # 200 down; stays above the 50 fail floor through k=30
        pr = 100 + (k - 1) * 5
        cls.append(f'    edit "CL_ONRAMP_{k}"\n'
                   f'        config rule\n'
                   f'            edit 1\n'
                   f'                set action permit\n'
                   f'                set match "{comm}"\n'
                   f'            next\n'
                   f'        end\n'
                   f'    next')
        rules.append(f'            edit {100 + k}\n'
                     f'                set match-community "CL_ONRAMP_{k}"\n'
                     f'                set set-local-preference {lp}\n'
                     f'                set set-priority {pr}\n'
                     f'            next')
    cls.append(f'    edit "CL_ONRAMP_FAIL"\n'
               f'        config rule\n'
               f'            edit 1\n'
               f'                set action permit\n'
               f'                set match "{gas}:64911"\n'
               f'            next\n'
               f'        end\n'
               f'    next')
    rules.append('            edit 190\n'
                 '                set match-community "CL_ONRAMP_FAIL"\n'
                 '                set set-local-preference 50\n'
                 '                set set-priority 300\n'
                 '            next')
    return (
        "# ============================================================\n"
        "# HUB companion - CANONICAL return-path steering. Paste ONCE per hub.\n"
        "# Design-agnostic + idempotent: maps EVERY on-ramp community to a distinct\n"
        "# local-pref, so single-WAN / dual-WAN / mixed / future 5G spokes all steer\n"
        "# with ONE return path and NO rule-ID collisions. Re-paste is a no-op.\n"
        "# ============================================================\n"
        "config router community-list\n" + "\n".join(cls) + "\nend\n"
        "config router route-map\n"
        '    edit "RM_FABRIC_IN"\n'
        "        config rule\n" + "\n".join(rules) + "\n"
        "            edit 999\n"
        "            next\n"
        "        end\n"
        "    next\n"
        "end\n"
        "config router bgp\n"
        "    config neighbor-group\n"
        '        edit "fabric_vpn_1"        # confirm name: show router bgp -> config neighbor-group\n'
        '            set route-map-in "RM_FABRIC_IN"\n'
        "        next\n"
        "    end\n"
        "end\n"
        f"# Covers up to {slots} on-ramps (+ fail) for EVERY spoke; bump if a spoke exceeds it.\n"
        "# Per-spoke steering needs NO hub change — the spoke's community tags do the work."
    )


with st.sidebar:
    st.markdown("### 🛰️ BOR Toolkit")
    st.markdown("**Single-circuit (single-WAN) design**")
    st.markdown("**Steps**\n\n"
                "1. ⚡ Load a baseline\n"
                "2. Pick your **FortiGate model**\n"
                "3. Fill the shaded sections\n"
                "4. ⚙️ **Generate FortiGate config** (device side)\n"
                "5. ⬇ **Download FortiSASE IPsec values** (portal side — for the engineer)")

st.title("🛰️ FortiSASE BOR Config Generator")
_ccol = st.columns([2, 3])
circuit_mode = _ccol[0].radio("Circuit design", ["Single circuit", "Dual ISP circuit"], horizontal=True,
                              key="circuit_mode",
                              help="Single = one WAN + 2 BOR on-ramps (validated). Dual ISP = two WANs + 4 on-ramps "
                                   "cross-meshed across circuits (each PoP reachable on either circuit).")
is_dual = circuit_mode.startswith("Dual")
dual_active = False
if is_dual:
    dual_active = _ccol[1].checkbox("Active-active (both circuits load-share; default = primary-backup)",
                                    key="dual_active_cb",
                                    help="Off = primary-backup (mode sla, LP order). On = ECMP across healthy on-ramps.")
_badge = "Dual-ISP (dual-circuit) design" if is_dual else "Single-circuit (single-WAN) design"
st.markdown(f"<span style='background:#eef4ff;border:1px solid #cdd9ee;border-radius:6px;"
            f"padding:0.15rem 0.6rem;font-weight:600;color:#1c3d7a;'>{_badge}</span>",
            unsafe_allow_html=True)
st.caption("Two outputs from one form: **⚙️ the FortiGate config** to deploy on the device, and "
           "**⬇ the FortiSASE IPsec values** to hand your implementation engineer for the portal side. "
           "**New here?** Click a Quick-start button to load a working baseline, then edit what differs.")

# ---- Quick-start baselines (pick any site ID + role, then load) ----
banner("⚡ Quick start", "pick a site, load a baseline, then tweak", _SECTION_COLORS[0])
qc = st.columns([1, 2, 1])
qs_id = qc[0].number_input("Site ID", min_value=1, max_value=9999, value=1, step=1,
                           key="qs_site_id", help="Any branch number (1-9999) — e.g. 6, 7, 8 … 100.")
qs_role = qc[1].selectbox("Role", ["bor", "bor-spa"], key="qs_role",
                          format_func=lambda r: "BOR Node (spoke)" if r == "bor" else "BOR + SPA Hub (bridge)")
qc[2].markdown("<div style='height:1.75rem'></div>", unsafe_allow_html=True)  # drop button to input baseline
if qc[2].button("⬇  Load baseline", key="qs_load", use_container_width=True):
    b = baseline_dual(int(qs_id), qs_role) if is_dual else baseline(int(qs_id), qs_role)
    for k, val in b.items():
        st.session_state[k] = val
    st.rerun()
st.caption("**Dual-ISP** baseline loads the Site-4 cross-mesh (2 WANs + 4 on-ramps, aligned to the AWS box); pick the model, then Generate."
           if is_dual else
           "Loads a full working config for that site; you then change only what differs. Re-run for site 6, 7, 8 … as many as you need.")
st.divider()

# ---- drivers ----
banner("① Site role & FortiGate model", "pick these first — they shape the whole form", _SECTION_COLORS[1])
c1, c2 = st.columns(2)
role = c1.selectbox("Site role", ["bor", "bor-spa"], key="role",
                    format_func=lambda r: "BOR Node (spoke)" if r == "bor" else "BOR + SPA Hub (bridge)")
platform = c2.selectbox("FortiGate model", list(schema["platforms"].keys()), key="platform")
pm = schema["platforms"][platform]
_tbd = (pm["wan_port"], pm["lan_port"]) + ((pm.get("wan2_port"), pm.get("lan_port_dual")) if is_dual else ())
if "TBD" in _tbd:
    st.warning(f"Model **{platform}** has TBD port names in the schema — fill them before generating.")
values = {"role": role, "platform": platform, "dual_wan": is_dual, "dual_active": dual_active}

# LAN interface picker (platform-aware). Default = the model's LAN port; override to any physical port
# (e.g. port16 on the 120G). Only set values["lan_port"] when changed, so the generator otherwise
# falls back to the platform map. (VLAN sub-interfaces: coming soon.)
_lan_default = pm.get("lan_port_dual") if is_dual else pm.get("lan_port")
_ports = PLATFORM_PORTS.get(platform, [])
if _ports and "TBD" not in str(_lan_default):
    _idx = _ports.index(_lan_default) if _lan_default in _ports else 0
    _lan_sel = st.selectbox("LAN interface  ·  site", _ports, index=_idx,
               help="Physical LAN/gateway port. Auto-set per model — change it here (e.g. port16 on the "
                    "120G, or a 10GE x1-x4). VLAN sub-interfaces are coming soon.")
    if _lan_sel != _lan_default:
        values["lan_port"] = _lan_sel

# ---- BOR site-to-site private access (per-site; spoke + single-circuit only) ----
private_access = False
if role == "bor":
    _pa_label = ("🔒 BOR site-to-site private access — anchor this site's private (RFC1918) path on the "
                 + ("SECONDARY PoP (both circuits)" if is_dual else "SECONDARY on-ramp"))
    private_access = st.checkbox(_pa_label, key="bor_private_access_cb",
                                 help=schema["features"]["bor_private_access"]["help"])
values["bor_private_access"] = private_access

# ---- feature toggles (schema-driven); dual_wan/dual_active are the top Circuit-design toggle,
#      bor_private_access is the dedicated checkbox above ----
feats = {k: v for k, v in schema.get("features", {}).items()
         if k not in ("dual_wan", "dual_active", "bor_private_access")}
if feats:
    with st.expander("⚙️ Advanced — feature blocks (all ON by default; you can ignore this)", expanded=False):
        st.caption("These are on for a standard BOR build. Only change one for a special case.")
        fcols = st.columns(min(4, len(feats)))
        for i, (fk, fv) in enumerate(feats.items()):
            with fcols[i % len(fcols)]:
                values[fk] = st.checkbox(fk.replace("_", " ").title(),
                                         value=bool(fv.get("default", False)),
                                         help=fv.get("help"), key=f"feat_{fk}")

# ---- at-a-glance readiness card (per-section greenlights) -------------------
_cur = {v["key"]: st.session_state.get(v["key"], v.get("default")) for v in VARS}
_cur["role"], _cur["platform"] = role, platform
_sec = {g: s for g in GROUPS if (s := section_state(g, role, _cur)) is not None}
_ready = sum(1 for s in _sec.values() if s == "ready")
with st.container(border=True):
    st.markdown("#### " + ("✅ Ready to generate" if _sec and _ready == len(_sec)
                           else f"📋 Config readiness — {_ready}/{len(_sec)} sections ready"))
    st.caption("🟢 ready · ⚪ needs a required value · 🔴 invalid format — updates as you fill the form below.")
    _chips = list(_sec.items())
    for _rs in range(0, len(_chips), 4):
        _cols = st.columns(4)
        for _i, (_g, _s) in enumerate(_chips[_rs:_rs + 4]):
            _cols[_i].markdown(f"{_LIGHT[_s]} **{_g}**")

# ---- form, grouped by section ----
for gi, g in enumerate(GROUPS):
    gvars = [v for v in VARS if v["group"] == g and applies(v, role) and v["key"] not in ("role", "platform")]
    if not gvars:
        continue
    with section(f"{_LIGHT.get(_sec.get(g), '')} {g}".strip(), "", _SECTION_COLORS[gi % len(_SECTION_COLORS)]):
        if g in GROUP_HELP:
            st.caption(GROUP_HELP[g])
        basic = [v for v in gvars if not v.get("advanced")]
        adv = [v for v in gvars if v.get("advanced")]
        cols = st.columns(2)
        for i, v in enumerate(basic):
            if show_if_ok(v, values):
                with cols[i % 2]:
                    values[v["key"]] = widget(v, v["key"])
        if adv:
            with st.expander(f"Advanced — {g}"):
                for v in adv:
                    if show_if_ok(v, values):
                        values[v["key"]] = widget(v, v["key"])

# ---- tenant PoPs (editable — unique per customer) ----
banner("Tenant On-Ramps (PoPs)", "one row per BOR tunnel — drives BOTH the FortiGate config and the FortiSASE card", _SECTION_COLORS[5])
st.caption("⚠️ **Per customer.** Names are generic — **Primary** = preferred path, **Secondary** = backup — "
           "and build the tunnel interface `BOR_<name>`. The **FQDN** and **BOR-node IP** are unique per "
           "tenant/PoP (`ipsec-<tenant>-<pop>.prod.fortisase.com`). **Network ID** and **Pool mask** are the "
           "FortiSASE-side tunnel-config fields — they feed the downloadable IPsec values card below "
           "(IP range is derived from BOR-node IP + mask). Add/remove rows to change PoP count.")

# --- SLA probe pool: the tested "whitelist" each overlay draws from (blank cell = auto by order) ---
_pool = schema.get("sla_probe_pool", [])
with st.expander(f"🎯 SLA probe pool — {len(_pool)} tested, SASE-reachable IPs "
                 "(this is where a health-check's probe like 64.6.64.6 comes from — NOT 8.8.8.8)"):
    st.caption("FortiSASE PoP peers don't answer ICMP, and FortiOS rejects the *same* probe on two "
               "health-checks — so **each overlay gets a UNIQUE probe from this list, by order** "
               "(slot 0 → first PoP). Leave a PoP's **SLA probe** cell blank to auto-assign it; or "
               "copy one below into a cell, or type your own internal DNS reachable through that overlay.")
    st.dataframe([{"slot": i, "probe IP": ip} for i, ip in enumerate(_pool)],
                 use_container_width=True, hide_index=True)
    _pick = st.selectbox("Browse / copy a tested probe", [""] + list(_pool), key="probe_pick")
    if _pick:
        st.code(_pick, language="text")

_pop_src = schema["pops_dual"] if is_dual else schema["pops"]
pop_seed = [{"name": p["name"], "fqdn": p["fqdn"], "bor_node": p["bor_node"],
             **({"circuit": p.get("circuit", 1)} if is_dual else {}),
             "network_id": p.get("network_id", 0), "netmask": p.get("netmask", "255.255.255.0"),
             "probe": p.get("probe", "")}
            for p in _pop_src]
_colcfg = {
    "name": st.column_config.TextColumn("On-ramp name", help="-> interface BOR_<name>. Rename freely.", required=True),
    "fqdn": st.column_config.TextColumn("FortiSASE FQDN", width="large",
                                        help="From your tenant: ipsec-<tenant>-<pop>.prod.fortisase.com", required=True),
    "bor_node": st.column_config.TextColumn("BOR node IP", help="iBGP peer + static /32 = FortiSASE 'Tunnel interface IP'", required=True),
    "network_id": st.column_config.NumberColumn("Network ID", help="FortiSASE tunnel-config Network ID — unique PER PoP/FQDN (e.g. originals 0, 2nd configs 1). Single-circuit: 0.", default=0),
    "netmask": st.column_config.TextColumn("Pool mask", help="FortiSASE mode-config pool mask (default /24). IP range derived from BOR-node IP + mask.", default="255.255.255.0"),
    "probe": st.column_config.TextColumn("SLA probe (blank = auto)",
             help="Blank -> auto-assigns the next tested pool IP (see the 🎯 pool above). Or paste a pool IP / your own internal DNS reachable through THIS overlay."),
}
if is_dual:
    _colcfg["circuit"] = st.column_config.NumberColumn("Circuit", min_value=1, max_value=2, default=1,
                          help="1 = WAN1 (port1), 2 = WAN2 (port2). Cross-mesh: each PoP has one config per circuit.")
edited = st.data_editor(
    pop_seed, num_rows="dynamic", use_container_width=True, key="pops_editor", column_config=_colcfg)
pops = edited.to_dict("records") if hasattr(edited, "to_dict") else [dict(r) for r in edited]
# auto-assign BGP communities by row order (:10/:20/:30/:40 = the hub LP order)
for i, p in enumerate(pops):
    p["community"] = f"65001:{10 * (i + 1)}"
    # normalize optional probe cell: blank/NaN -> "" so the template falls back to the pool
    pr = p.get("probe")
    p["probe"] = str(pr).strip() if pr and str(pr).strip().lower() != "nan" else ""
    # normalize FortiSASE card fields (blank/NaN -> sensible defaults)
    try:
        p["network_id"] = int(p.get("network_id"))
    except (TypeError, ValueError):
        p["network_id"] = 0
    nm = str(p.get("netmask") or "").strip()
    p["netmask"] = nm if nm and nm.lower() != "nan" else "255.255.255.0"
    if is_dual:
        try:
            p["circuit"] = int(p.get("circuit"))
        except (TypeError, ValueError):
            p["circuit"] = 1
        if p["circuit"] not in (1, 2):
            p["circuit"] = 1
values["pops"] = pops
# SASE_Hub fabric network-id stays at its schema default — network-id is a LOCAL per-overlay demux
# tag (scoped to same-public-IP tunnels), so the fabric may reuse an on-ramp net-id (0/1) with no clash.
# What each overlay will ACTUALLY probe (custom if set, else the pool by order) — no more mystery.
st.caption("🎯 **Effective per-overlay probes:** " + "  ·  ".join(
    f"**{p['name']}** → `{p.get('probe') or (_pool[i] if i < len(_pool) else '(pool exhausted!)')}`"
    for i, p in enumerate(pops)))

# FortiSASE-side hand-off: downloadable IPsec tunnel-config values for the implementation engineer.
_psk = values.get("seed_psk") or "<TUNNEL_PSK>"
st.download_button("⬇  Download FortiSASE IPsec values (for the implementation engineer)",
                   fortisase_ipsec_card(pops, _psk),
                   file_name=f"fortisase-onramp-values-{values.get('hostname', 'site')}.txt",
                   mime="text/plain", use_container_width=True)
st.caption("Hand this to whoever configures the **FortiSASE side** (portal → On-Ramp → Create New Tunnel "
           "Config). The **FortiGate-side** CLI is the *Generate config* button further down.")
with st.expander("Advanced — BGP communities (auto-assigned; two-layer scheme)"):
    gas = values.get("bgp_as", 65001)
    sid = values.get("site_id")
    st.caption("Every LAN route this site advertises is tagged with **two** communities:")
    rows = []
    if sid not in (None, ""):
        rows.append({"Community": f"{gas}:{1000 + int(sid)}", "Layer": "per-BRANCH (unique)",
                     "Meaning": f"Site {sid} — identifies THIS branch at the hub"})
    for p in pops:
        rows.append({"Community": p["community"], "Layer": "per-PoP path (shared)",
                     "Meaning": f"Return via {p['name']} — drives the hub's local-pref (ECMP fix)"})
    st.table(rows)
    st.caption("Per-branch = **AS:(1000 + Site ID)**, unique per site. The per-PoP path communities "
               "are shared on purpose so the hub applies one consistent return-path policy; the branch "
               "community makes each site individually identifiable (and lets you steer one site later).")

st.divider()

# ---- generate ----
if st.button("⚙️  Generate config", type="primary", use_container_width=True):
    errs = validate(values, role)
    if errs:
        st.error("Fix these first:\n\n" + "\n".join(f"- {e}" for e in errs))
    else:
        try:
            conf = render(values, schema)
            host = values.get("hostname", "config")
            st.success(f"Generated **{host}** — {len(conf.splitlines())} lines, ready for FortiZTP / FortiManager.")
            st.download_button("⬇  Download .conf", conf, file_name=f"{host}.conf",
                               mime="text/plain", use_container_width=True)
            st.code(conf, language="bash")
            if role == "bor":
                st.divider()
                st.warning("⚠️ **Don't forget the Hub** — the spoke config alone won't fix the return "
                           "path. Paste the block below into the **Hub (BOR + SPA)** CLI so "
                           "`RM_FABRIC_IN` recognizes this site's community. The baseline is one-time "
                           "(steers every site); a per-site override is only needed if this site must differ.")
                st.markdown("**Hub route-map — click the 📋 copy icon (top-right of the box) and drop it into the Hub CLI:**")
                st.code(hub_companion(values), language="bash")
                st.caption("Details & per-site override: `Send-Communities/hub-update_when-adding-a-site.md`")
            st.info("Phase 4 (coming): push straight to FortiManager (API) or bundle for FortiZTP.")
        except Exception as ex:  # noqa: BLE001
            st.error(f"Render failed: {ex}")

st.divider()

# ---- FortiManager model-device CSV export (single row for FMG blueprint CSV import) ----
banner("④  Export FortiManager CSV", "one model-device row for FMG Blueprint import",
       _SECTION_COLORS[4])
_bp = fmg_blueprint_name(values)
_ncols = len(fmg_headers_for(values))
_circuit = "dual-circuit" if values.get("dual_wan") else "single-circuit"
_role_label = ("SPA hub — BOR + fabric" if role == "bor-spa" else "BOR spoke") + f" · {_circuit}"
st.caption(f"Blueprint **{_bp}** · {_role_label} · {_ncols}-column FMG import CSV. Per-device values are "
           "filled from this site; tenant-scope columns are left blank so your **ADOM defaults** apply. "
           "Same variables as the config above — no re-entry.")
_serial = st.text_input("FortiFlex / VM Serial Number  ·  device", key="fmg_serial",
                        placeholder="FGVMXXXXXXXXXXXX",
                        help="The real serial FMG matches when the device dials FGFM home. "
                             "FMG rejects a model-device row without it.")
if st.button("⬇  Build FMG CSV", use_container_width=True):
    errs = validate(values, role)
    if errs:
        st.error("Fix these first:\n\n" + "\n".join(f"- {e}" for e in errs))
    elif not _serial.strip():
        st.warning("Enter the device **Serial Number** — FMG rejects a model-device row without it.")
    else:
        try:
            ctx = build_context(values, schema)
            headers = fmg_headers_for(ctx)
            csv_text = fmg_csv([fmg_csv_row(ctx, _serial, schema)], headers)
            host = values.get("hostname", "device")
            st.success(f"FMG CSV ready for **{host}** — blueprint {_bp}, 1 row × {len(headers)} columns.")
            st.download_button("⬇  Download FMG CSV", csv_text, file_name=f"{host}.fmg.csv",
                               mime="text/csv", use_container_width=True)
            st.code(csv_text, language="text")
            st.caption("Import in FMG: **Device Manager → Add Device → Add Model Device from CSV** "
                       "(the ADOM must already carry this blueprint + the metadata schema).")
            if role == "bor-spa":
                st.info("SPA hub adds the **fabric columns** (FABRIC_OVERLAY + derived hub-IP/remote/pool, "
                        "HUB_LOOPBACK, FABRIC_NETWORK_ID, HUB_PROPOSAL) on top of the BOR set. The fabric "
                        "tunnel PSK is `$(SEED_PSK)` (ADOM meta) — same as the on-ramps, so there's no "
                        "FABRIC_PSK column. FMG needs the `BOR-SPA-SINGLE-STD-*` blueprint + these fabric "
                        "meta vars declared before import.")
        except Exception as ex:  # noqa: BLE001
            st.error(f"CSV export failed: {ex}")
