"""
FortiSASE Tenant Status — a READ-ONLY dashboard.

Enter a FortiSASE API user (or use saved lab creds), Connect, and see live status with
greenlights: BGP routing design · Secure Private Access hubs · Branch On-Ramp PoPs · live
IPsec tunnels · public-IP feed. Compact index by default — expand a row for detail. No writes.
"""
import pathlib
import sys

import streamlit as st

# The FortiSASE client lives in the repo's api/fortisase package (4 dirs up: pages -> config-
# generator -> sdwan-ztp -> automation -> <repo root>/api/fortisase).
_CLIENT_DIR = pathlib.Path(__file__).resolve().parents[4] / "api" / "fortisase"
sys.path.insert(0, str(_CLIENT_DIR))
try:
    import importlib

    import requests
    import client as _fsclient
    importlib.reload(_fsclient)          # pick up edits to client.py without restarting Streamlit
    FortiSASEClient = _fsclient.FortiSASEClient
except ImportError as e:  # noqa: BLE001
    st.set_page_config(page_title="FortiSASE Tenant Status", page_icon="🛰️", layout="wide")
    st.error(f"Can't load the FortiSASE client from {_CLIENT_DIR}: {e}\n\nInstall deps: `pip install requests pyyaml`")
    st.stop()

st.set_page_config(page_title="FortiSASE Tenant Status", page_icon="🛰️", layout="wide")
st.title("🛰️ FortiSASE Tenant Status")
st.caption("**Read-only.** Connect a FortiSASE API user to poll live status. Rows are collapsed to a "
           "greenlight index — expand any for detail. Nothing here writes to the tenant.")


def light(state):
    return {"success": "🟢", "running": "🟢", "up": "🟢",
            "updating": "🟡", "pending": "🟡",
            "failed": "🔴", "error": "🔴", "down": "🔴"}.get(str(state).lower(), "⚪")


def errmsg(e):
    if isinstance(e, requests.HTTPError):
        return f"HTTP {e.response.status_code} · {e.response.text[:180]}"
    return f"{type(e).__name__}: {str(e)[:180]}"


def connect(client):
    try:
        client.login()
        st.session_state["sase"] = client
        st.session_state["sase_err"] = None
    except Exception as e:  # noqa: BLE001
        st.session_state["sase"] = None
        st.session_state["sase_err"] = errmsg(e)


# ---- ① Connect --------------------------------------------------------------
with st.container(border=True):
    st.subheader("① Connect to your FortiSASE tenant")
    with st.expander("ℹ️ How do I get an API user ID + password?"):
        st.markdown(
            "A FortiSASE API user is **not** your portal login — it's a machine credential from FortiCloud IAM:\n\n"
            "1. Go to **FortiCloud → IAM → API Users** (support.fortinet.com).\n"
            "2. **Add API User**, name it, and give it access to the **FortiSASE** portal.\n"
            "3. Permissions: **read-only is enough** for this status page.\n"
            "4. Copy the generated **API User ID** (a GUID) and set/copy its **password**.\n"
            "5. Paste those two below. **Client ID** is `FortiSASE`.\n\n"
            "The API user is scoped to one tenant — no `view-account` needed.")
    st.caption("The password never leaves this machine. It's only saved to disk if you tick **Save** below.")
    c1, c2, c3 = st.columns([3, 3, 2])
    api_id = c1.text_input("API user ID", key="sase_api_id", placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
    pw = c2.text_input("API password", type="password", key="sase_pw")
    cid = c3.text_input("Client ID", value="FortiSASE", key="sase_cid")
    save = st.checkbox("💾 Save these creds for next time",
                       help="Writes them to ~/.config/fortisase/fortisase_credentials.yaml (plaintext, "
                            "your user profile, this machine only — never committed). Then 'Use saved' reloads them.")
    b1, b2, _ = st.columns([2, 3, 3])
    if b1.button("🔌 Connect", type="primary", use_container_width=True):
        cl = FortiSASEClient(api_id=api_id, api_secret=pw, client_id=(cid or "FortiSASE"))
        connect(cl)
        if save and st.session_state.get("sase"):
            st.session_state["saved_path"] = cl.save_config()
    if b2.button("🔑 Use saved lab creds", use_container_width=True,
                 help="Load ~/.config/fortisase/fortisase_credentials.yaml"):
        try:
            connect(FortiSASEClient.from_config())
        except FileNotFoundError:
            st.session_state["sase_err"] = "No saved creds at ~/.config/fortisase/fortisase_credentials.yaml"

sase = st.session_state.get("sase")
if st.session_state.get("sase_err"):
    st.error(f"🔴 Not connected — {st.session_state['sase_err']}")
if not sase:
    st.info("Enter API credentials above and **Connect** to view tenant status.")
    st.stop()
if st.session_state.get("saved_path"):
    st.caption(f"💾 Saved to `{st.session_state['saved_path']}` — use **🔑 Use saved lab creds** next time.")

top = st.columns([2, 6])
top[0].success("🟢 Connected")
if top[1].button("🔄 Refresh"):
    st.rerun()

# ---- fetch everything once (each guarded) ----------------------------------
data = {}


def safe(key, fn):
    try:
        data[key] = fn()
        data[key + "_err"] = None
    except Exception as e:  # noqa: BLE001
        data[key] = None
        data[key + "_err"] = errmsg(e)


safe("bgp", lambda: sase.get_private_access_network_config().get("data", {}))
safe("hubs", sase.get_service_connections)
safe("sites", lambda: sase.list_ipsec_sites().get("data", {}).get("config_sites", []))
safe("conns", lambda: sase.get_ipsec_connections().get("data", {}))
safe("pubips", sase.get_public_ip_feed)
for site in (data.get("sites") or []):
    safe("cfg_" + site["site_id"], lambda sid=site["site_id"]: sase.get_site_ipsec_configs(sid).get("data", []))


def agg(items, key):
    """Aggregate greenlight: 🟢 if all success/running, 🟡 if mixed, 🔴 if any failed/empty-error."""
    states = [str(i.get(key, "")).lower() for i in items]
    if not states:
        return "⚪"
    if all(s in ("success", "running") for s in states):
        return "🟢"
    if any(s in ("failed", "error") for s in states):
        return "🔴"
    return "🟡"


# ---- ② BGP routing design ---------------------------------------------------
b = data["bgp"]
lbl = (f"🗺️ BGP Routing Design — {light(b.get('config_state'))} {b.get('config_state')} · "
       f"AS {b.get('as_number')} · {b.get('bgp_router_ids_subnet')}") if b else "🗺️ BGP Routing Design — 🔴 read failed"
with st.expander(lbl, expanded=False):
    st.caption("The BGP config **shared** by Secure Private Access AND the SD-WAN On-Ramp — every BOR/hub config must match this.")
    if b:
        m = st.columns(4)
        m[0].metric("ASN", b.get("as_number"))
        m[1].metric("Router-ID subnet", b.get("bgp_router_ids_subnet"))
        m[2].metric("Health-check IP", b.get("sdwan_health_check_vm"))
        m[3].metric("BGP design", b.get("bgp_design"))
        st.caption(f"end-to-end client traffic: **{b.get('end_to_end_traffic_enable')}** · "
                   f"recursive-next-hop: **{b.get('recursive_next_hop')}** · "
                   f"advertise-hub-priority: **{b.get('advertise_hub_priority')}** · "
                   f"always-compare-MED: **{b.get('always_compare_med')}**")
    else:
        st.error(data["bgp_err"])

# ---- ③ SPA hubs -------------------------------------------------------------
hubs = data["hubs"]
lbl = (f"🔗 Secure Private Access — {agg(hubs, 'config_state')} {len(hubs)} hub(s)"
       if hubs is not None else "🔗 Secure Private Access — 🔴 read failed")
with st.expander(lbl, expanded=False):
    if hubs is None:
        st.error(data["hubs_err"])
    for h in (hubs or []):
        cfg = h.get("config", {})
        st.markdown(f"**{light(h.get('config_state'))} {cfg.get('alias')}** · seq {h.get('seq_num')} · _{h.get('config_state')}_")
        cc = st.columns(4)
        cc[0].write(f"BGP peer IP\n\n`{cfg.get('bgp_peer_ip')}`")
        cc[1].write(f"Remote GW\n\n`{cfg.get('ipsec_remote_gw')}`")
        cc[2].write(f"Overlay ID\n\n`{cfg.get('overlay_network_id')}`")
        cc[3].write(f"Auth\n\n`{cfg.get('auth')}`")
        assigns = h.get("ip_assigned", [])
        with st.expander(f"PoP BGP router-id assignments ({len(assigns)})"):
            st.table([{"region": a.get("region"), "router-id": a.get("bgp_router_id"),
                       "site_id": a.get("site_id")} for a in assigns])

# ---- ④ BOR on-ramp PoPs -----------------------------------------------------
sites = data["sites"]
lbl = (f"🌐 Branch On-Ramp — {agg(sites, 'resource_status')} {len(sites)} PoP(s)"
       if sites is not None else "🌐 Branch On-Ramp — 🔴 read failed")
with st.expander(lbl, expanded=False):
    if sites is None:
        st.error(data["sites_err"])
    for site in (sites or []):
        st.markdown(f"**{light(site.get('resource_status'))} {site.get('airport_name')}** · _{site.get('resource_status')}_ · "
                    f"capacity {site.get('connections')} · `{site.get('site_id')}`")
        st.caption(site.get("fqdn"))
        cfgs = data.get("cfg_" + site["site_id"])
        with st.expander(f"Tunnel configs ({len(cfgs) if cfgs else 0})"):
            if cfgs:
                st.table([{"tunnel": c["tunnel_1"]["tunnel_name"],
                           "intf_ip (= BOR node)": c["tunnel_1"]["intf_ip"],
                           "pool": f'{c["tunnel_1"]["start_ip"]} – {c["tunnel_1"]["end_ip"]}',
                           "net_id": c["tunnel_1"]["network_id"]} for c in cfgs])
            else:
                st.caption(data.get("cfg_" + site["site_id"] + "_err") or "none")

# ---- ⑤ Live tunnels ---------------------------------------------------------
conns = data["conns"]
rows = []
if conns:
    for airport, csites in conns.items():
        for sid, tuns in csites.items():
            for t in tuns:
                rows.append({"": light("up" if t.get("phase1Status") else "down"),
                             "PoP": airport, "tunnel": t.get("name"),
                             "remote gateway": t.get("remoteGateway"),
                             "up (hrs)": round(t.get("lifetimeInSec", 0) / 3600, 1)})
up = sum(1 for r in rows if r[""] == "🟢")
lbl = (f"📡 Live IPsec Tunnels — 🟢 {up}/{len(rows)} up" if conns is not None
       else "📡 Live IPsec Tunnels — 🔴 read failed")
with st.expander(lbl, expanded=False):
    if conns is None:
        st.error(data["conns_err"])
    else:
        st.dataframe(rows, use_container_width=True, hide_index=True)

# ---- ⑥ Public IP feed (for correlation) ------------------------------------
ips = data["pubips"]
lbl = (f"🌍 Public IP Feed — 🌍 {len(ips)} egress IP(s)" if ips is not None
       else "🌍 Public IP Feed — 🔴 read failed")
with st.expander(lbl, expanded=False):
    st.caption("FortiSASE egress **public IPs** (per-PoP FortiGate). Use these to correlate FortiSASE "
               "traffic in your SIEM / to allowlist. Source: `/monitor-api/v1/infra/public-ip-feed`.")
    if ips is None:
        st.error(data["pubips_err"])
    else:
        st.code("\n".join(ips), language="text")
        if st.button("🔍 Map IPs to PoP regions (~5s)", key="map_pubips",
                     help="Enumerates the per-region feed to group each IP by its PoP region."):
            with st.spinner("Enumerating per-region feed…"):
                st.session_state["pubip_map"] = sase.get_public_ips_by_region()
        pmap = st.session_state.get("pubip_map")
        if pmap:
            st.table([{"PoP region": reg, "public IP(s)": ", ".join(v)} for reg, v in pmap.items()])
        st.caption("Region codes are opaque (`region16`, …). The **airport-name + serial** breakdown "
                   "needs the **Infrastructure** IAM permission on the API user — read-only users get "
                   "403 on `/infra/*`. Grant it and we can show `dfw-f3 → IP → serial` directly.")

st.divider()
st.caption("Read-only status. Next (separate, gated): push a generated BOR config's tunnel-configs to the "
           "tenant — we'll wire that once the reads here check out.")
