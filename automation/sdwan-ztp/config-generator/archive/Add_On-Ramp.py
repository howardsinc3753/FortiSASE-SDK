"""
Day-2 tool: ADD one FortiSASE on-ramp (PoP) to a LIVE spoke.
Separate page from the full-site generator. FortiSASE-assigned values (FQDN / BOR-node BGP IP /
community) are ENTERED, not invented.

Emits the BARE-MINIMUM bring-up by default (IPsec + static + BGP neighbor + SD-WAN member -> zone).
The return-path steering + SLA failover integration (route-map / HC / service-rule append / hub) is
an optional Step-2 block.
"""
import re
import streamlit as st

st.set_page_config(page_title="Add BOR On-Ramp", page_icon="➕", layout="wide",
                   initial_sidebar_state="expanded")


def banner(title, subtitle="", color="#eef4ff"):
    """Shaded section header (matches the main generator's look)."""
    sub = (f"<span style='color:#5a6472;font-size:0.85rem;margin-left:0.55rem;'>· {subtitle}</span>"
           if subtitle else "")
    st.markdown(f"<div style='background:{color};color:#1c2733;padding:0.5rem 0.9rem;border-radius:8px;"
                f"margin-bottom:0.5rem;'><span style='font-size:1.1rem;font-weight:700;'>{title}</span>{sub}</div>",
                unsafe_allow_html=True)


st.title("➕ Add a BOR On-Ramp (PoP) to a live site")
st.caption("More SASE bandwidth → allocate another FortiSASE PoP and provision it on an EXISTING spoke. "
           "Incremental only — nothing existing is removed. FQDN / BOR-node IP / community must **match "
           "what FortiSASE assigned**.")

banner("① Existing site", "the live spoke you're adding capacity to", "#eef4ff")
a = st.columns(4)
site_id = a[0].number_input("Site ID", 1, 9999, 1, help="For the per-branch community AS:(1000+id).")
hostname = a[1].text_input("Hostname", "spoke-1")
bgp_as = int(a[2].number_input("BGP AS", value=65001, step=1))
existing = int(a[3].number_input("On-ramps already live", 1, 19, 2,
               help="How many BOR on-ramps this spoke has today. Drives the member/route defaults."))
b = st.columns(3)
wan_port = b[0].text_input("WAN port", "port1")
wan_gw = b[1].text_input("WAN gateway (blank if DHCP)", "")
seed_psk = b[2].text_input("IPsec PSK", "<TUNNEL_PSK>", type="password")

banner("② New on-ramp", "from FortiSASE — not thin-air (FQDN / BOR-node IP / community)", "#eefaf0")
n = st.columns(4)
name = n[0].text_input("PoP name", "DFW3",
       help="Anchor pair stays Primary / Secondary. Name growth nodes <LOC><n> (e.g. DFW3, MIA4) — "
            "a location can host up to 20 BOR nodes, so the node index keeps it unique. "
            "-> BOR_<name>, HC_<name>, RM_OUT_<NAME>, CL_VIA_<NAME>")
fqdn = n[1].text_input("FortiSASE FQDN", "ipsec-<tenant>-<pop>.prod.fortisase.com")
bor_node = n[2].text_input("BOR-node BGP IP", "172.16.16.1", help="iBGP peer + static /32. From FortiSASE.")
community = n[3].text_input("PoP community", f"{bgp_as}:30", help="Return-path tag (Step 2 only). Distinct per PoP.")

# Unique, ICMP-pingable, USA-based probe targets (mirrors schema sla_probe_pool). PoP peers don't
# answer ICMP and FortiOS rejects a probe server reused across health-checks (-7), so each on-ramp
# must use a DISTINCT entry — or pin an internal DNS reachable through this overlay.
PROBE_POOL = ["8.8.8.8", "8.8.4.4", "1.1.1.1", "9.9.9.9", "149.112.112.112", "208.67.222.222",
              "208.67.220.220", "4.2.2.1", "4.2.2.2", "4.2.2.3", "4.2.2.4", "64.6.64.6", "64.6.65.6",
              "156.154.70.1", "156.154.71.1", "8.26.56.26", "8.20.247.20", "74.82.42.42",
              "209.244.0.3", "209.244.0.4"]
p = st.columns(2)
_probe_sel = p[0].selectbox("SLA probe IP — pingable, USA (used in Step 2)",
             PROBE_POOL + ["Custom / internal DNS…"], index=min(existing, len(PROBE_POOL) - 1),
             help="FortiSASE PoP peers don't answer ICMP, and FortiOS rejects the SAME probe across two "
                  "health-checks (return -7). Default lands on the next unused pool slot — pick one NOT "
                  "already used by another on-ramp, or choose Custom for an internal DNS.")
probe = (p[1].text_input("↳ custom probe IP", "10.100.0.53")
         if _probe_sel.startswith("Custom") else _probe_sel)

integrate = st.checkbox("Also emit Step 2 — return-path steering + SLA failover "
                        "(route-map, HC, neighbor binding, service-rule append, hub rule)", value=False,
                        help="Leave off for a first bring-up/reachability test; turn on once the tunnel + BGP are healthy.")

NAME = re.sub(r"[^A-Za-z0-9]", "_", name).upper()
site_comm = f"{bgp_as}:{1000 + int(site_id)}"
idx0 = existing

with st.expander("Advanced — seq / route IDs / hub preference (computed defaults; override to match your box)"):
    ad = st.columns(4)
    new_seq = int(ad[0].number_input("New SD-WAN member seq", 2, 60, existing + 2,
              help="Skips the underlay member at N+1. Verify free with `show system sdwan`."))
    sr_node = int(ad[1].number_input("Static route id (BOR node)", 5, 899, 5 + existing))
    sr_pub = int(ad[2].number_input("Static route id (PoP public)", 5, 899, 20 + existing))
    hub_ruleid = int(ad[3].number_input("Hub RM_FABRIC_IN rule id", 4, 98, 10 + existing))
    ad2 = st.columns(2)
    hub_lp = int(ad2[0].number_input("Hub local-pref (return)", 51, 200, max(51, 200 - idx0 * 5),
             help="Higher wins. Must be > 50 (fail floor) and distinct from existing PoPs."))
    hub_pri = int(ad2[1].number_input("Hub priority", 1, 299, 100 + idx0 * 5, help="Lower wins."))

if st.button("⚙️  Generate on-ramp config", type="primary", use_container_width=True):
    gw = f"\n        set gateway {wan_gw}" if wan_gw.strip() else ""
    bare = f"""# ============================================================
# ADD BOR ON-RAMP (bring-up): {name} -> SD-WAN member {new_seq} on {hostname} (Site {site_id})
# Bare minimum: tunnel + peer reachability + BGP neighbor + member in SDWAN_ZONE. Incremental.
# ============================================================
config vpn ipsec phase1-interface
    edit "BOR_{name}"
        set type ddns
        set interface "{wan_port}"
        set ike-version 2
        set peertype any
        set net-device disable
        set mode-cfg enable
        set proposal aes256-sha256
        set dhgrp 5 14
        set network-overlay enable
        set network-id 0
        set transport auto
        set fortinet-esp enable
        set dpd on-idle
        set remotegw-ddns "{fqdn}"
        set psksecret {seed_psk}
    next
end
config vpn ipsec phase2-interface
    edit "BOR_{name}"
        set phase1name "BOR_{name}"
        set proposal aes256-sha256
        set dhgrp 5 14
    next
end
config firewall address
    edit "BOR_{name}_PUBLIC"
        set type fqdn
        set allow-routing enable
        set fqdn "{fqdn}"
    next
end
config router static
    edit {sr_node}
        set dst {bor_node} 255.255.255.255
        set device "BOR_{name}"
        set comment "BOR {name} node (BGP peer)"
    next
    edit {sr_pub}
        set dstaddr "BOR_{name}_PUBLIC"{gw}
        set device "{wan_port}"
        set comment "{name} BOR PoP public via WAN"
    next
end
config router bgp
    config neighbor
        edit "{bor_node}"
            set interface "BOR_{name}"
            set update-source "BOR_{name}"
            set remote-as {bgp_as}
            set advertisement-interval 1
            set connect-timer 1
            set capability-graceful-restart enable
            set link-down-failover enable
            set next-hop-self enable
            set soft-reconfiguration enable
        next
    end
end
config system sdwan
    config members
        edit {new_seq}
            set interface "BOR_{name}"
            set zone "SDWAN_ZONE"
        next
    end
end"""

    integ = f"""# ============================================================
# STEP 2 — steering + return-path SLA failover for {name}
# Apply AFTER the tunnel + BGP are healthy.
# ============================================================
config router route-map
    edit "RM_OUT_{NAME}"
        config rule
            edit 1
                set match-ip-address "PL_LAN_LOCAL"
                set set-community "{community}" "{site_comm}"
            next
            edit 99
            next
        end
    next
end
config router bgp
    config neighbor
        edit "{bor_node}"
            set route-map-out "RM_OUT_FAIL"
            set route-map-out-preferable "RM_OUT_{NAME}"
            set send-community both
        next
    end
end
config system sdwan
    config health-check
        edit "HC_{name}"
            set server "{probe}"
            set failtime 2
            set recoverytime 3
            set members {new_seq}
            config sla
                edit 1
                    set link-cost-factor latency jitter packet-loss
                    set latency-threshold 250
                    set jitter-threshold 50
                    set packetloss-threshold 5
                next
            end
        next
    end
    config neighbor
        edit "{bor_node}"
            set member {new_seq}
            set health-check "HC_{name}"
            set sla-id 1
        next
    end
    config service
        edit 1
            append priority-members {new_seq}
            config sla
                edit "HC_{name}"
                    set id 1
                next
            end
        next
        edit 2
            append priority-members {new_seq}
            config sla
                edit "HC_{name}"
                    set id 1
                next
            end
        next
    end
end"""

    hub = f"""# ============================================================
# STEP 2 — HUB: return-path match for PoP {name} (community {community})
# ============================================================
config router community-list
    edit "CL_VIA_{NAME}"
        config rule
            edit 1
                set action permit
                set match "{community}"
            next
        end
    next
end
config router route-map
    edit "RM_FABRIC_IN"
        config rule
            edit {hub_ruleid}
                set match-community "CL_VIA_{NAME}"
                set set-local-preference {hub_lp}
                set set-priority {hub_pri}
            next
        end
    next
end"""

    st.success(f"On-ramp **{name}** → member {new_seq} on {hostname}.")
    st.markdown("**① SPOKE — bare bring-up (copy 📋, paste into the spoke CLI):**")
    st.code(bare, language="bash")
    st.caption(f"Verify up: `diagnose vpn ike gateway list name BOR_{name}` and "
               f"`get router info bgp neighbors {bor_node}` (Established).")
    if integrate:
        st.divider()
        st.markdown("**② SPOKE — Step 2 steering + failover:**")
        st.code(integ, language="bash")
        st.warning("⚠️ **Don't forget the HUB** — add the new PoP's community-match + return rule:")
        st.code(hub, language="bash")
    else:
        st.info("Steering + failover (route-map, HC, service-rule, hub) not shown — tick the Step-2 box above once BGP is up.")
