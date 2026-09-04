"""
fortisase/client.py — a minimal FortiSASE API client.

WHAT THIS IS (for the network engineer reading it): the Python object your automation
talks to instead of clicking the FortiSASE portal by hand. Create it once (or via
.from_config()), then call methods like get_vpn_sessions() / create_ipsec_tunnel_config();
it builds the HTTP request, attaches the Bearer token, and hands back parsed JSON.
Think netmiko-for-a-FortiGate, but for the FortiSASE API.

CONFIRMED auth + base (lab tenant, 2026-08):
  • OAuth token — POST https://customerapiauth.fortinet.com/api/v1/oauth/token/
        body: {username, password, client_id:"FortiSASE", client_secret:"", grant_type:"password"}
        -> {access_token, refresh_token, expires_in:3600, token_type:"Bearer", scope:"read write", ...}
    Refresh — same URL, {client_id:"FortiSASE", grant_type:"refresh_token", refresh_token}.
  • API base — https://portal.prod.fortisase.com  (ONE token: the OAuth access_token used as Bearer)
        /monitor-api/v1/...  read-only monitoring (traffic-history, user/vpn/sessions, …)
        /api/v1/...          config/security (incl. on-ramp ipsec_tunnel_config)

CONFIRMED live (2026-08-14, lab tenant): the on-ramp ipsec_tunnel_config CREATE body + the
sites/ipsec list (popSiteId resolver) — see the methods below. Remaining unknown: a DELETE
endpoint for tunnel-config cleanup (needed for full CRUD + staying under the 5-profile cap).

Deps: requests, pyyaml   (pip install -r requirements.txt)
"""
import ipaddress

import requests

TOKEN_URL = "https://customerapiauth.fortinet.com/api/v1/oauth/token/"
FORTISASE_CLIENT_ID = "FortiSASE"                       # CONFIRMED (lab tenant)
PORTAL_BASE = "https://portal.prod.fortisase.com"
MONITOR_API = f"{PORTAL_BASE}/monitor-api/v1"           # read-only monitoring
SECURITY_API = f"{PORTAL_BASE}/api/v1"                  # config/security (on-ramp create)
RESOURCE_API = f"{PORTAL_BASE}/resource-api/v1"         # portal "flat UI" API (SPA / BGP design)
                                                        # needs the view-account header (tenant ID)


class FortiSASEClient:
    """One instance per FortiSASE tenant. Holds creds + tokens; exposes API methods."""

    def __init__(self, api_id=None, api_secret=None, client_id=FORTISASE_CLIENT_ID,
                 view_account=None, timeout=30):
        self.api_id = api_id
        self.api_secret = api_secret
        self.client_id = client_id
        self.view_account = view_account          # tenant/account ID for resource-api (portal) calls
        self.timeout = timeout
        self._access_token = None
        self._refresh_token = None
        self.http = requests.Session()

    @classmethod
    def from_config(cls, path=None, **kw):
        """Load LAB creds from a YAML file OUTSIDE the repo (default
        ~/.config/fortisase/fortisase_credentials.yaml). NEVER commit that file.
        Keys: api_id, password, client_id."""
        import os
        import yaml
        path = path or os.path.expanduser("~/.config/fortisase/fortisase_credentials.yaml")
        with open(path) as f:
            c = yaml.safe_load(f) or {}
        return cls(api_id=c.get("api_id"), api_secret=c.get("password"),
                   client_id=c.get("client_id", FORTISASE_CLIENT_ID),
                   view_account=c.get("view_account"), **kw)

    def save_config(self, path=None):
        """Write these creds to a YAML file OUTSIDE the repo (default
        ~/.config/fortisase/fortisase_credentials.yaml) so from_config() can reload them.
        Plaintext, user-profile, this machine only — NEVER commit. Returns the path."""
        import os
        import yaml
        path = path or os.path.expanduser("~/.config/fortisase/fortisase_credentials.yaml")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            yaml.safe_dump({"api_id": self.api_id, "password": self.api_secret,
                            "client_id": self.client_id, "view_account": self.view_account}, f)
        return path

    # ---- Auth (FortiCloud IAM OAuth) ---------------------------------------
    def login(self):
        """Mint an access_token (+ refresh_token) from the API user creds. TTL = 3600s."""
        r = self.http.post(TOKEN_URL, json={
            "username": self.api_id,
            "password": self.api_secret,
            "client_id": self.client_id,
            "client_secret": "",
            "grant_type": "password",
        }, timeout=self.timeout)
        r.raise_for_status()
        return self._store(r.json())

    def refresh(self):
        """Get a fresh access_token using the stored refresh_token (use after ~3600s)."""
        r = self.http.post(TOKEN_URL, json={
            "client_id": self.client_id,
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
        }, timeout=self.timeout)
        r.raise_for_status()
        return self._store(r.json())

    def _store(self, tok):
        self._access_token = tok.get("access_token")
        self._refresh_token = tok.get("refresh_token", self._refresh_token)
        return self._access_token

    def _headers(self):
        if not self._access_token:
            self.login()
        return {"Authorization": f"Bearer {self._access_token}"}

    def _get(self, url, **params):
        # Retry once on a transient 500 (monitor API code 51901) or a 401 (token expired -> re-login).
        for attempt in (1, 2):
            r = self.http.get(url, headers=self._headers(), params=params or None, timeout=self.timeout)
            if attempt == 1 and r.status_code == 401:
                self._access_token = None       # force re-login on the retry
                continue
            if attempt == 1 and r.status_code >= 500:
                continue
            r.raise_for_status()
            return r.json()

    # ---- Monitor API (read-only) -------------------------------------------
    def get_traffic_history(self, traffic_type="Outbound"):
        """GET /monitor-api/v1/traffic-history?type=<traffic_type>."""
        return self._get(f"{MONITOR_API}/traffic-history", type=traffic_type)

    def get_vpn_sessions(self):
        """GET /monitor-api/v1/user/vpn/sessions — FortiSASE users currently connected to VPN."""
        return self._get(f"{MONITOR_API}/user/vpn/sessions")

    def get_ipsec_connections(self):
        """GET /monitor-api/v1/ipsec/connections — LIVE on-ramp tunnel status, grouped
        {airport -> {site_id -> [{name, remoteGateway, phase1Name, phase1Status, in/outBytes, ...}]}}."""
        return self._get(f"{MONITOR_API}/ipsec/connections")

    def get_public_ip_feed(self, region=None, resource="FGT"):
        """GET /monitor-api/v1/infra/public-ip-feed — the FortiSASE egress PUBLIC IPs as a
        PLAIN-TEXT CIDR feed (one per line), for correlation / SIEM allowlists. Returns [str].
        Optional region filters to one PoP. (The structured serial+region variant needs extra IAM
        permission — 403 for a read-only API user.)"""
        params = {"resource": resource}
        if region:
            params["region"] = region
        r = self.http.get(f"{MONITOR_API}/infra/public-ip-feed",
                          headers=self._headers(), params=params, timeout=self.timeout)
        r.raise_for_status()
        return [ln.strip() for ln in r.text.splitlines() if ln.strip()]

    def get_public_ips_by_region(self, max_region=40):
        """Map egress public IPs to their PoP REGION by enumerating the per-region feed
        (region1..max_region — ~max_region calls, a few seconds). Returns {region_code: [cidr...]}
        for regions that have IPs. NB: region codes are opaque (region16, ...); the airport-name +
        serial mapping needs the Infrastructure IAM permission (read-only users get 403 on /infra/*)."""
        out = {}
        for n in range(1, max_region + 1):
            r = self.http.get(f"{MONITOR_API}/infra/public-ip-feed", headers=self._headers(),
                              params={"region": f"region{n}", "resource": "FGT"}, timeout=self.timeout)
            if r.status_code == 200 and r.text.strip():
                out[f"region{n}"] = [ln.strip() for ln in r.text.splitlines() if ln.strip()]
        return out

    # ---- Resource API (portal "flat UI"): SPA / BGP routing design ---------
    # These need the view-account (tenant ID) header. The BGP design here is the TENANT
    # BASELINE that BOTH SPA hubs and BOR on-ramps must match (as_number, router-id subnet)
    # -> read it to drive/validate the config-generator; write it only on a fresh tenant.
    def _resource_headers(self):
        # NOTE: do NOT send the 'view-account' header for a normal (single-tenant) API user —
        # it makes the token try to act as an ORG member and 403s ("user does not belong to an
        # organization"). The API user is already scoped to its tenant; Bearer alone works.
        # view-account is a browser/MSSP org-switch header — only relevant for an org-scoped user
        # managing multiple tenants, so it's opt-in via send_view_account=True.
        h = self._headers()
        if self.view_account and getattr(self, "send_view_account", False):
            h["view-account"] = str(self.view_account)
        return h

    def _resource_get(self, url):
        for attempt in (1, 2):
            r = self.http.get(url, headers=self._resource_headers(), timeout=self.timeout)
            if attempt == 1 and r.status_code == 401:
                self._access_token = None
                continue
            if attempt == 1 and r.status_code >= 500:
                continue
            r.raise_for_status()
            return r.json()

    def get_private_access_network_config(self):
        """GET the SPA 'BGP routing design' (the 'configure this FIRST' page). READ-ONLY.
        resource-api/v1/private-access/network-configuration. Returns {code, data:{as_number,
        bgp_router_ids_subnet, sdwan_health_check_vm, ...}} — the tenant BGP contract that BOTH
        SPA hubs and BOR on-ramps must match."""
        return self._resource_get(f"{RESOURCE_API}/private-access/network-configuration")

    def get_service_connections(self):
        """GET the SPA service connections (hubs). READ-ONLY. Returns the hubs[] list — each hub:
        config{alias, bgp_peer_ip, ipsec_remote_gw, overlay_network_id, as_number, region_cost},
        common_config{tenant BGP baseline}, ip_assigned[{bgp_router_id, site_id}].
        resource-api/v1/private-access/service-connections."""
        return self._resource_get(f"{RESOURCE_API}/private-access/service-connections").get("hubs", [])

    def update_private_access_network_config(self, bgp_router_ids_subnet, as_number="65001",
                                             sdwan_health_check_vm="10.11.11.11",
                                             recursive_next_hop=True, multi_as=False,
                                             sdwan_rule_enable=False, end_to_end_traffic_enable=True,
                                             advertise_hub_priority=False, always_compare_med=False,
                                             deterministic_med=False):
        """PUT the SPA BGP routing design. *** LIVE WRITE — SHARED by SPA + SD-WAN On-Ramp. ***
        FortiSASE requires DELETING ALL SERVICE CONNECTIONS before this design can change, so on a
        tenant that already has hubs this will fail (or you'd tear the fabric down). Use only on a
        fresh tenant during onboarding. Body/fields confirmed from the portal PUT (2026-08).
        resource-api/v1/private-access/network-configuration."""
        body = {
            "bgp_router_ids_subnet": bgp_router_ids_subnet,
            "multi_as": multi_as,
            "as_number": str(as_number),
            "recursive_next_hop": recursive_next_hop,
            "sdwan_rule_enable": sdwan_rule_enable,
            "sdwan_health_check_vm": sdwan_health_check_vm,
            "end_to_end_traffic_enable": end_to_end_traffic_enable,
            "advertise_hub_priority": advertise_hub_priority,
            "always_compare_med": always_compare_med,
            "deterministic_med": deterministic_med,
        }
        url = f"{RESOURCE_API}/private-access/network-configuration"
        r = self.http.put(url, json=body,
                          headers={**self._resource_headers(), "Content-Type": "application/json"},
                          timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    # ---- Config/Security API (/api/v1): PoP sites + on-ramp tunnel configs --
    def list_ipsec_sites(self):
        """GET /api/v1/security/sites/ipsec — the tenant's on-ramp PoP sites. Returns
        {code, data:{config_sites:[{airport_name, fqdn, site_id, connections, resource_status}]}}.
        `site_id` here IS the popSiteId used by create_ipsec_tunnel_config()."""
        return self._get(f"{SECURITY_API}/security/sites/ipsec")

    def get_bgp_sites(self):
        """GET /api/v1/security/sites/bgp — tenant BGP baseline ({as_number, bgp_router_ids_subnet})."""
        return self._get(f"{SECURITY_API}/security/sites/bgp")

    def get_site_ipsec_configs(self, site_id):
        """GET /api/v1/security/sites/{site_id}/ipsec_configs — tunnel configs on a PoP site. Returns
        data:[{tunnel_1:{tunnel_name, intf_ip, start_ip, end_ip, netmask, network_id, device_type}}]
        (no psk — write-only). NB: intf_ip == the config-generator's pops[].bor_node."""
        return self._get(f"{SECURITY_API}/security/sites/{site_id}/ipsec_configs")

    def resolve_pop_site_ids(self, by="fqdn"):
        """{fqdn (or airport_name) -> site_id} from list_ipsec_sites() — resolves the popSiteId so
        onboarding can match a PoP by its FQDN (which the config-generator's pops[] already carry)."""
        sites = self.list_ipsec_sites().get("data", {}).get("config_sites", [])
        return {s.get(by): s.get("site_id") for s in sites}

    # ---- Config/Security API: the BOR onboarding WRITE ---------------------
    def create_ipsec_tunnel_config(self, pop_site_id, tunnel_name, intf_ip, start_ip,
                                   end_ip, netmask, network_id, psk, device_type="fgt"):
        """POST /api/v1/security/sites/{popSiteId}/ipsec_tunnel_config — create an on-ramp
        'Tunnel Config' on a PoP (the portal 'Create New Tunnel Config'). *** LIVE WRITE. ***
        CONFIRMED live 2026-08-14: envelope {ipsec_security_config:{tunnel_1:{...}}}, device_type='fgt',
        psk is write-only (response echoes the tunnel WITHOUT psk + a server-assigned default_network_id).
        NB: the tenant caps tunnel configs at max_ipsec_tunnel_configuration_profiles (5 on the lab)."""
        url = f"{SECURITY_API}/security/sites/{pop_site_id}/ipsec_tunnel_config"
        body = {"ipsec_security_config": {"tunnel_1": {
            "tunnel_name": tunnel_name,
            "start_ip": start_ip,
            "end_ip": end_ip,
            "netmask": netmask,
            "intf_ip": intf_ip,
            "device_type": device_type,
            "network_id": network_id,
            "psk": psk,
        }}}
        r = self.http.post(url, json=body, headers={**self._headers(), "Content-Type": "application/json"},
                           timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    # ---- Bridge: config-generator pops[] -> tunnel-config creates ----------
    def push_tunnel_configs_from_pops(self, pops, psk, pop_site_ids=None):
        """Onboarding glue: create one on-ramp tunnel-config per PoP from the config-generator's
        pops[] (name/fqdn/bor_node/netmask/network_id). popSiteId AUTO-RESOLVES by FQDN via
        list_ipsec_sites() unless you pass pop_site_ids={pop_name -> site_id}.
        *** WRITE — creates tunnel configs on the live tenant. TODO(swagger): confirm create body
        (envelope, default_network_id, IP-pool range) before firing on a real tenant."""
        site_by_fqdn = None if pop_site_ids else self.resolve_pop_site_ids("fqdn")
        results = []
        for p in pops:
            site_id = pop_site_ids[p["name"]] if pop_site_ids else site_by_fqdn[p["fqdn"]]
            net = ipaddress.ip_network(f'{p["bor_node"]}/{p.get("netmask", "255.255.255.0")}', strict=False)
            results.append(self.create_ipsec_tunnel_config(
                pop_site_id=site_id,
                tunnel_name=p["name"],
                intf_ip=p["bor_node"],
                start_ip=str(net.network_address + 11),
                end_ip=str(net.broadcast_address - 1),
                netmask=p.get("netmask", "255.255.255.0"),
                network_id=p.get("network_id", 0),
                psk=psk,
            ))
        return results
