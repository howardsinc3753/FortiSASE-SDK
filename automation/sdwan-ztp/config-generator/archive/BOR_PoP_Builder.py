"""
BOR PoP Builder — generate FortiSASE On-Ramp *tunnel-config* values (single source of truth).

From ONE PoP definition it emits three consistent artifacts:
  1) a **Console fill-in card** the implementation engineer types into "Create New Tunnel Config",
  2) the exact **portal API body** (for later automation — auth filled in by the engineer),
  3) a **pops[] seed** to paste into the spoke Config Generator.

This tool talks to nothing and touches no template — it only computes values. Schema confirmed from
the portal API:  POST /api/v1/security/sites/{popSiteId}/ipsec_tunnel_config
"""
import json
import re
import streamlit as st

st.set_page_config(page_title="BOR PoP Builder", page_icon="🛰️", layout="wide",
                   initial_sidebar_state="expanded")


def banner(title, subtitle="", color="#eef4ff"):
    sub = (f"<span style='color:#5a6472;font-size:0.85rem;margin-left:0.55rem;'>· {subtitle}</span>"
           if subtitle else "")
    st.markdown(f"<div style='background:{color};color:#1c2733;padding:0.5rem 0.9rem;border-radius:8px;"
                f"margin-bottom:0.5rem;'><span style='font-size:1.1rem;font-weight:700;'>{title}</span>{sub}</div>",
                unsafe_allow_html=True)


st.title("🛰️ BOR PoP Builder — FortiSASE implementation card")
st.info("**This is the FortiSASE *portal* side.** It produces the fill-in **card** your implementation "
        "engineer types into **FortiSASE → On-Ramp → Create New Tunnel Config**. It does *not* produce "
        "FortiGate config — that's the 🏗️ Config Generator (whole box) and ➕ Add On-Ramp (existing box).")
st.caption("Fill in the PoP details → the **📋 Implementation card** near the bottom is your hand-off.")

# ── ① PoP identity ────────────────────────────────────────────────────────────
banner("① PoP location & tenant", "the FortiSASE-assigned FQDN + PoP site-id", "#eef4ff")
c = st.columns(4)
location = c[0].text_input("PoP location", "Miami")
code = c[1].text_input("PoP code (name prefix)",
       (re.sub(r"[^A-Za-z0-9]", "", location)[:3].upper() or "POP"),
       help="Short code → tunnel names <CODE><n> (MIA1, MIA2). Use the airport code if you prefer (DFW).")
fqdn = c[2].text_input("Tunnel gateway FQDN", "ipsec-<tenant>-mia-f3.prod.fortisase.com")
pop_site_id = c[3].text_input("Portal PoP site-id", "3dgnh494", help="From the on-ramp-tunnel URL; used only for the API body.")
c2 = st.columns(4)
bgp_as = int(c2[0].number_input("BGP AS", value=65001, step=1))
psk = c2[1].text_input("Pre-shared key", "<TUNNEL_PSK>", type="password")
device_type = c2[2].text_input("Device type", "fgt")
wan_label = c2[3].text_input("WAN binding hint", "wan, lan3", help="Comma-list; row 1→first WAN, row 2→second. Informational for the pops[] seed.")

# ── ② allocation ──────────────────────────────────────────────────────────────
banner("② Tunnel configs on this PoP", "deterministic /24 (or /21) blocks — override any cell", "#eefaf0")
a = st.columns(5)
count = int(a[0].number_input("How many tunnel configs", 1, 20, 2,
            help="2 = a dual-WAN pair on this PoP (WAN1 + WAN2)."))
mask_choice = a[1].selectbox("Mode-config pool", ["/24", "/21"], index=0,
              help="/24 ≈ 250 branch IPs per config (matches MiamiBOR2). /21 ≈ 2000 (matches fgtOnRamp).")
base3 = int(a[2].number_input("Start 3rd octet (172.16.X.0)", 0, 248, 0,
            help="First free block in your tenant's 172.16.0.0/16 overlay pool."))
netid0 = int(a[3].number_input("Start network-id", 0, 250, 0))
comm_base = int(a[4].number_input("Community base (AS:N)", 10, 9990, 10, step=10,
               help="Per-PoP path community; row i → AS:(base + 10·i)."))

stride = 8 if mask_choice == "/21" else 1
netmask = "255.255.248.0" if mask_choice == "/21" else "255.255.255.0"
wans = [w.strip() for w in wan_label.split(",") if w.strip()] or ["wan"]

seed_rows = []
for i in range(count):
    third = base3 + i * stride
    if third > 255 or (mask_choice == "/21" and third + 7 > 255):
        st.warning(f"Config #{i + 1} would exceed 172.16.255.x — lower the count or start octet.")
        break
    if mask_choice == "/21":
        start_ip, end_ip = f"172.16.{third}.21", f"172.16.{third + 7}.250"
    else:
        start_ip, end_ip = f"172.16.{third}.11", f"172.16.{third}.254"
    seed_rows.append({
        "name": f"{code}{i + 1}",
        "intf_ip": f"172.16.{third}.1",
        "start_ip": start_ip,
        "end_ip": end_ip,
        "netmask": netmask,
        "network_id": netid0 + i,
        "community": f"{bgp_as}:{comm_base + i * 10}",
    })

edited = st.data_editor(seed_rows, num_rows="dynamic", use_container_width=True, key="tc_editor",
         column_config={
             "name": st.column_config.TextColumn("Tunnel name", help="→ interface BOR_<name> on the spoke"),
             "intf_ip": st.column_config.TextColumn("Tunnel-int IP (BGP peer)"),
             "start_ip": st.column_config.TextColumn("Pool start"),
             "end_ip": st.column_config.TextColumn("Pool end"),
             "netmask": st.column_config.TextColumn("Subnet mask"),
             "network_id": st.column_config.NumberColumn("Network ID"),
             "community": st.column_config.TextColumn("Community"),
         })
rows = edited.to_dict("records") if hasattr(edited, "to_dict") else [dict(r) for r in edited]
rows = [r for r in rows if str(r.get("intf_ip", "")).strip() and str(r.get("name", "")).strip()]

# ── ③ outputs ─────────────────────────────────────────────────────────────────
if not rows:
    st.info("Add at least one tunnel config above.")
    st.stop()

banner("📋 Implementation card — hand this to the FortiSASE engineer",
       "type into FortiSASE → On-Ramp → Create New Tunnel Config", "#fff6e9")
for r in rows:
    st.markdown(f"**{r['name']}**  ·  PoP: {location} ({fqdn})")
    st.code(
        f"Name                : {r['name']}\n"
        f"Device type         : Remote device (FortiGate)\n"
        f"Tunnel interface IP : {r['intf_ip']}\n"
        f"IP range            : {r['start_ip']} - {r['end_ip']}\n"
        f"Subnet mask         : {r['netmask']}\n"
        f"Pre-shared key      : {psk}\n"
        f"Network ID          : {r['network_id']}",
        language="text")

with st.expander("③b  API bodies (for later automation — fill in your own token)"):
    st.caption("Use a **dedicated API token**, never a browser session cookie. One POST per tunnel config.")
    for r in rows:
        body = {"ipsec_security_config": {"tunnel_1": {
            "tunnel_name": r["name"], "start_ip": r["start_ip"], "end_ip": r["end_ip"],
            "netmask": r["netmask"], "intf_ip": r["intf_ip"], "device_type": device_type,
            "network_id": int(r["network_id"]), "psk": psk}}}
        st.markdown(f"**{r['name']}**")
        st.code(
            f"curl -X POST 'https://portal.prod.fortisase.com/api/v1/security/sites/{pop_site_id}/ipsec_tunnel_config' \\\n"
            f"  -H 'authorization: Bearer <YOUR_PORTAL_API_TOKEN>' \\\n"
            f"  -H 'content-type: application/json' \\\n"
            f"  --data-raw '{json.dumps(body)}'",
            language="bash")

lines = ["pops:"]
for i, r in enumerate(rows):
    lines += [
        f"  - name: {r['name']}",
        f"    fqdn: {fqdn}",
        f"    bor_node: {r['intf_ip']}          # = tunnel-int IP (BGP peer)",
        f"    network_id: {int(r['network_id'])}",
        f"    community: \"{r['community']}\"",
        f"    wan: {wans[i % len(wans)]}          # dual-WAN egress hint",
    ]
with st.expander("Advanced — pops[] seed for the 🏗️ FortiGate Config Generator (later step; optional)"):
    st.caption("This feeds the *FortiGate* side later. Ignore it if you just need the card above.")
    st.code("\n".join(lines), language="yaml")
