# FortiSASE Automation & APIs — Authoritative Corpus Reference

> **Tier 1/2 (official Fortinet docs + first-party Terraform provider).** Compiled June 2026. Covers FortiSASE 25.x / 26.1.x, FortiCloud IAM 26.x, FortiZTP 25.4 / 26.1.x, and Terraform provider `fortinetdev/fortisase` 1.2.0. Every non-trivial claim carries an inline source. Items not confirmable against an exact page are flagged **UNVERIFIED**.
> **This is the load-bearing doc for the on-ramp automation offering.** Read alongside `api/reference/` (the distilled runnable version) and `handoff/local-asset-inventory.md` (reusable local code).

---

## 0. Executive summary

- **FortiSASE has a public REST API.** Documented as "Appendix B – REST API" in the admin guides; the authoritative reference lives on the Fortinet Developer Network (FNDN). Auth is via **FortiCloud IAM API users** issuing **OAuth 2.0 bearer tokens** — the same `customerapiauth.fortinet.com` token flow used across FortiCloud (and already implemented in our local FortiZTP/SOCaaS SDKs).
- **FortiZTP is the keystone for on-ramp automation.** Portal `https://fortiztp.forticloud.com`, documented **v2.0 REST API**. **FortiSASE is an explicit FortiZTP provision target**, alongside FortiManager, FortiManager Cloud, FortiGate Cloud, FortiEdge Cloud, and FortiExtender Cloud. This is the literal "drop-ship and auto-onboard" mechanism.
- **There is a first-party Terraform provider** `fortinetdev/fortisase` (v1.2.0, Apr 2026) with ~84 resources / ~110 data sources covering endpoints, security profiles, SPA/private access, network, infra, and auth.
- **Important nuance:** FortiZTP-to-FortiSASE provisioning is documented for **edge/thin-edge devices (FortiAP, FortiExtender)**. For a **FortiGate SD-WAN/Branch on-ramp**, the documented automation path is FortiZTP → **FortiManager / FortiManager Cloud** (model device + templates), with the FortiGate then forming the IPsec/SPA on-ramp tunnel to FortiSASE. See §3 and §5 for the precise split.

---

## 1. FortiSASE REST API

### 1.1 Does it exist? Yes.
The admin guide dedicates **"Appendix B – REST API"** to it and points to the canonical reference on the Fortinet Developer Network:
> "See the FortiSASE REST API reference on the Fortinet Developer Network." (Source: https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/268966/appendix-b-rest-api)

FNDN reference URL cited by the docs: `https://fndn.fortinet.net/index.php?app=apicompare&id=2625&name=fortisase&display=2639` (Source: same page).

> **Note on FNDN:** The full machine-readable reference sits behind FNDN (account required). The public docs confirm its existence and link to it but do not reproduce the endpoint catalog. **UNVERIFIED:** a downloadable OpenAPI/Swagger JSON branded for FortiSASE — the docs reference an "apicompare" tool rather than a published `openapi.json`. **➜ This is exactly what Daniel is sourcing; it lands in `api/openapi/`.**

### 1.2 Confirmed functional surface (SPA example)
The most concretely documented API use case is **Secure Private Access (SPA)** configuration:
> "You can perform secure private access (SPA) configuration using the FortiSASE REST API to manage the common SPA network connection and service connections to FortiGate SPA hubs and retrieve the status of these connections." … "All SPA configuration operations are possible in the REST API except for viewing health and VPN tunnel status." (Source: https://docs.fortinet.com/document/fortisase/25.3.57/mature-administration-guide/702423/configuring-spa-using-the-rest-api)

### 1.3 Resource families (derived authoritatively from the Terraform provider)
The public docs prose does not enumerate the endpoint tree, but the **first-party Terraform provider is a faithful mirror of the FortiSASE "Service Resource API V2."** The provider's catalog is therefore the best authoritative map of the REST resource families:

| Family | Representative resources (Terraform → REST resource group) |
|---|---|
| **Endpoints / FortiClient mgmt** | `endpoint_*` profiles (connection, protection, sandbox, ZTNA, settings), `endpoints_enable_management`, `endpoints_access_proxy_authorize` |
| **Users & auth** | `auth_users`, `auth_user_groups`, `auth_ldap_servers`, `auth_radius_servers`, `auth_*_saml_server`, `auth_fsso_agents` |
| **Security profiles** | `security_antivirus_profile`, `security_web_filter_profile`, `security_ips_profile`, `security_dlp_*`, `security_dns_filter_profile`, `security_ssl_ssh_profile`, `security_application_control_profile`, threat feeds |
| **Policies** | `security_internal_policies`, `security_outbound_policies`, `security_endpoint_to_endpoint_policies` |
| **Network config** | `network_hosts`, `network_host_groups`, `network_dns_rules`, `infra_ipam_setting`, `infra_ssids` |
| **Private access (SPA)** | `private_access_network_configuration`, `private_access_service_connections`, `private_access_service_connections_auth`, `private_access_service_connections_region_cost` |
| **Infra / deployment (PoP-adjacent)** | data sources `infra_fortigates`, `infra_extenders`, `infra_data_transfer`, `infra_secure_web_gateway_supplementary_data` |
| **Reporting / visibility** | data sources `endpoints_details`, `endpoints_donut`, `security_botnet_domains_stat`, `infra_data_transfer` |
| **DEM (Digital Experience)** | `dem_spa_applications`, `dem_custom_saas_apps` |

(Source: https://github.com/fortinetdev/terraform-provider-fortisase/tree/main/docs/resources and `.../docs/data-sources`)

> **On "deployment / PoPs":** There is **no resource for creating/destroying FortiSASE PoPs** — PoPs are Fortinet-operated infrastructure. The closest API surface is **read** visibility (`infra_*` data sources) plus on-ramp/SPA configuration. Treat PoP lifecycle as platform-managed. (Inferred from the catalog; **UNVERIFIED** that any write API for PoP deployment exists.)

### 1.4 Auth model and base URL
Authenticated by **FortiCloud IAM API users** issuing **OAuth 2.0 bearer tokens** (§2). The provider accepts either `username`/`password` (API user ID + secret) or a pre-minted `access_token` (Source: https://github.com/fortinetdev/terraform-provider-fortisase/blob/main/docs/index.md). The **exact public REST base host** is not published in the open docs and is encapsulated by the provider and FNDN reference. **UNVERIFIED:** the literal API hostname — confirm via FNDN, the incoming Swagger, or by inspecting the Terraform provider source.

---

## 2. FortiCloud IAM & authentication for automation

All FortiSASE / FortiZTP / FortiCloud automation rides on the **FortiCloud Identity & Access Management (IAM)** API-user + OAuth 2.0 model. **We already implement this exact flow locally** in `MSSP-SE-Tools/FortiZTP/fortiztp/client.py` and `SOCaaS-SDK/socaas/client.py`.

### 2.1 Creating an API user
FortiCloud IAM portal: **Users > Add New > API User**.
1. A **permission profile must exist first**.
2. Add New > API User → optional description → select Permission Profile → **Add**.
3. **Download Credentials** (security check requires your password) → yields the **API ID (`apiId`)** and **encrypted password**.
4. Caution: "Downloading API user credentials will reset the user's security credentials each time." API-user scope is at the **account level**.
(Source: https://docs.fortinet.com/document/forticloud/26.1.0/identity-access-management-iam/282341/adding-an-api-user)

> "API users can only use OAuth 2.0 for authentication then access web service APIs provided by each FortiCloud service portal." (Source: https://docs.fortinet.com/document/forticloud/26.1.0/identity-access-management-iam/927656/api-users)

**Local vs ORG/IAM API users:** FortiCloud distinguishes **Local IAM users** (created inside one account) from **ORG/external IAM users** (federated across an Organization). For an MSSP, the org/IAM model scales across tenant accounts. **Note our FortiZTP SDK requires a Local IAM user** (`client.py` docstring: "FortiZTP requires LOCAL IAM API Users, not ORG type"). **UNVERIFIED:** whether the Local-vs-ORG distinction changes the OAuth token call for FortiSASE specifically — the documented token flow is identical for both.

### 2.2 Obtaining an OAuth token (the canonical flow)
**Token endpoint:** `https://customerapiauth.fortinet.com/api/v1/oauth/token/`

Initial request (`grant_type: password`):
```json
{
  "username":   "<apiId>",
  "password":   "<encrypted password from credentials ZIP>",
  "client_id":  "<FortiCloud service ID>",
  "grant_type": "password"
}
```
Successful response:
```json
{
  "access_token": "<access_token>",
  "expires_in": 3660,
  "token_type": "Bearer",
  "scope": "read write",
  "refresh_token": "<refresh_token>",
  "message": "successfully authenticated",
  "status": "success"
}
```
Use it: `Authorization: Bearer <access_token>`. Refresh with `grant_type: refresh_token`.
(Source: https://docs.fortinet.com/document/forticloud/26.1.0/identity-access-management-iam/19322/accessing-fortiapis)

### 2.3 Scoping a token to a portal — the `client_id`
The **`client_id` selects which FortiCloud service portal the token is valid for.** Documented examples include `"iam"`, `"assetmanagement"`, `"forticameracloud"` (Source: same accessing-fortiapis page). Known/used client_ids:

| Target portal | `client_id` |
|---|---|
| Asset Management (register/import devices) | `assetmanagement` |
| IAM | `iam` |
| FortiZTP | `fortiztp` (confirmed in our local SDK `client.py`) |
| FortiFlex | `flexvm` (confirmed in local SD-WAN onboarding tool) |
| SOCaaS | `socaas` (confirmed in local SOCaaS SDK) |
| **FortiSASE** | **UNVERIFIED** literal value — the Terraform provider obtains/accepts the token transparently; confirm via FNDN / provider source / incoming Swagger |

> **Practical takeaway:** the same IAM API-user credentials mint **separate tokens per portal** by changing `client_id`. An MSSP harness typically mints an `assetmanagement` token (register/move assets), a `fortiztp` token (provision), and a FortiSASE token (push config) — all from one API user, scoped by the IAM permission profile.

---

## 3. FortiZTP (Zero-Touch Provisioning) — the on-ramp automation core

### 3.1 What it is
> "FortiZTP is a cloud service to manage zero touch provisioning of devices or virtual machines (VM) to cloud or on-premise management solutions from a centralized console." (Source: https://docs.fortinet.com/document/fortiztp/26.1.a/administration-guide/756835/introduction)

**Portal:** `https://fortiztp.forticloud.com`. **API base (v2):** `https://fortiztp.forticloud.com/public/api/v2` (confirmed in our local SDK).

### 3.2 Supported device types and provision targets (26.1.a)
**Device types:** FortiGate, FortiGate-VM, FortiWiFi, FortiAP, FortiSwitch, FortiExtender.
**Provision targets:** FortiGate Cloud, FortiManager, FortiManager Cloud, FortiEdge Cloud, FortiExtender Cloud, **FortiSASE**.
(Source: https://docs.fortinet.com/document/fortiztp/26.1.a/administration-guide/756835/introduction)

> **FortiSASE is a first-class FortiZTP provision target — but only for thin-edge device types (FortiAP, FortiExtender/FortiBranchSASE), NOT FortiGate.** A branch FortiGate has no FortiSASE target in FortiZTP; it provisions to FortiManager(Cloud) and then dials IPsec into the BOR. This is the load-bearing nuance for the on-ramp automation offering — see [`05-on-ramp-deep-dive.md`](05-on-ramp-deep-dive.md) §4b (pothole P2), verbatim-confirmed in FortiZTP 26.1.a. (Our local `fortiztp/devices.py` predates this and only lists FortiManager/FortiGateCloud/FortiEdgeCloud/ExternalController — **it needs a `FortiSASE` target added** for the thin-edge path. See `handoff/local-asset-inventory.md`.)

### 3.3 How devices get into FortiZTP
> "You must register or import devices to the Asset Management portal in the same FortiCloud account." FortiZTP "automatically loads devices that are registered to Asset Management" using Cloud/FortiDeploy key verification. Unprovisioned devices appear on the **UNPROVISIONED** tab. (Source: same introduction page)

### 3.4 The FortiZTP REST API
- **Reference:** `https://fndn.fortinet.net/index.php?/fortiapi/1584-fortiztp/` (FNDN, account required).
- **Version:** "The FortiZTP **v2.0 API** is available."
- **Rate limit:** "The API usage limit is **2,000 calls per hour**."
- **Bulk:** "You can do a single API call on multiple devices by entering multiple device serial numbers."
(Source: https://docs.fortinet.com/document/fortiztp/latest/administration-guide/182159/api)

**Auth:** standard FortiCloud IAM OAuth (§2). Endpoint/field reference (confirmed against our working SDK):
- `GET /devices` — list inventory
- `GET /devices/{deviceSN}` — device status
- `PUT /devices/{deviceSN}` — set/clear provision target (body: `deviceType`, `provisionStatus`, `provisionTarget`, `region`, `fortiManagerOid`, `scriptOid`, `useDefaultScript`, `externalControllerSn`, `externalControllerIp`, `firmwareProfile`)
- `GET/POST/PUT/DELETE /setting/scripts[...]` — bootstrap CLI scripts
- `GET /setting/fortimanagers` — registered FortiManagers
**UNVERIFIED:** the exact JSON for `provisionTarget: "FortiSASE"` (region field requirements, whether a FortiSASE entitlement must be pre-verified) — confirm in the FNDN v2.0 reference and against a live tenant.

### 3.5 End-to-end "drop-ship → FortiSASE branch on-ramp" flows
Two documented patterns; choosing correctly matters:

**Pattern A — Edge/thin-edge device directly to FortiSASE (FortiAP / FortiExtender):** the literal "FortiZTP target = FortiSASE" path.
1. Register the device (serial + cloud key) **and** the FortiSASE subscription registration code to the **same FortiCloud account** in Asset Management; verify the device shows a **"FortiSASE Subscription"** entitlement.
2. In FortiZTP **Settings**, on the device tab (e.g. FortiAP), ensure **FortiSASE** is enabled → **Update**.
3. On the **UNPROVISIONED** tab, select the device(s) → **Provision**.
4. In the Provision dialog, set **TARGET LOCATION = FortiSASE** → **Provision Now**.
5. Device boots, calls home, becomes a **FortiSASE-managed edge/thin-edge** on-ramp.
(Sources: https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/299731/connecting-a-fortiap-to-fortisase-using-fortiztp ; https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/213023/sd-wan-on-ramp). FortiExtender 200F thin-edge: https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/344098/thin-edge

**Pattern B — FortiGate SD-WAN / Branch on-ramp (classic branch box):** the documented automated path is **FortiZTP → FortiManager / FortiManager Cloud**, not FortiZTP→FortiSASE directly:
1. Register the FortiGate to Asset Management (same FortiCloud account).
2. (Preferred) Pre-create a **model device** on FortiManager Cloud with the on-ramp config (preconfiguration method).
3. In FortiZTP, provision with **TARGET LOCATION = FortiManager Cloud** (or FortiManager + serial/IP).
4. "After the FortiGate comes online, the **FGFM tunnel is established**" and the "**auto-link process is performed automatically**"; without preconfig, the FortiGate lands in **Unauthorized Devices** for manual authorization.
5. **Reboot the FortiGate**; for physical units "you must perform a **factory reset**."
6. FortiManager pushes templates (SD-WAN + on-ramp/SPA), and the FortiGate forms the **IPsec/SPA tunnel to the FortiSASE Branch On-ramp location** (§5).
(Source: https://docs.fortinet.com/document/fortimanager-cloud/7.6.6/cloud-deployment/552626/using-fortiztp-with-fortimanager-cloud)
> "Deprovisioning a device from the FortiZTP portal will not delete the device from FortiManager Cloud. The device must be manually deleted." (Source: same page)

### 3.6 Bootstrap / pre-run CLI
FortiZTP supports **pre-run CLI scripts** when provisioning to FortiManager (Source: https://docs.fortinet.com/document/fortiztp/25.4.0/administration-guide/574054/provisioning-a-fortigate). For FortiOS-native ZTP, FortiGate also supports **device blueprints** for zero-touch SD-WAN (Source: https://docs.fortinet.com/document/fortigate/7.2.0/sd-wan-architecture-for-enterprise/372716/zero-touch-provisioning-ztp-using-device-blueprints). The traditional drop-ship bootstrap (USB/`config-script`/DHCP option) to point a fresh FortiGate at FortiManager-Cloud's FGFM is the underlying primitive. **UNVERIFIED:** exact bootstrap CLI text for 7.6/8.0 — confirm in the matching FortiOS deployment guide. (Our local SD-WAN spoke template tool generates the spoke-side config — see inventory.)

---

## 4. Terraform / IaC

### 4.1 First-party FortiSASE provider — `fortinetdev/fortisase`
- **Exists and current.** Latest **v1.2.0** (~Apr 29, 2026); v1.1.0 Jan 15, 2026. Implements the **FortiSASE Service Resource API V2**; covers FortiSASE ~**25.2.b**. Go 1.21.x, Terraform 0.12+, MPL-2.0. (Sources: https://registry.terraform.io/providers/fortinetdev/fortisase/latest ; https://github.com/fortinetdev/terraform-provider-fortisase)

**Provider config (auth = IAM API user, two modes):**
```hcl
# Mode 1 — API user ID + secret
provider "fortisase" {
  username = "<apiId>"
  password = "<apiPassword>"
}
# Mode 2 — pre-minted OAuth token
provider "fortisase" {
  access_token  = "<access_token>"
  # refresh_token = "<refresh_token>"   # optional
}
```
Schema fields: `username`, `password`, `access_token`, `refresh_token` (all optional strings). No explicit base-URL/region knob — the provider encapsulates the endpoint. (Source: https://github.com/fortinetdev/terraform-provider-fortisase/blob/main/docs/index.md)

**Catalog scale:** ~**84 resources** / ~**110 data sources**. Highlights for an on-ramp/SASE service: `private_access_*` (SPA), `endpoint_ztna_*`, full `security_*` profile suite + `security_internal/outbound_policies`, `network_*`/`infra_ipam_setting`, `auth_*`. **Gap:** `infra_fortigates`/`infra_extenders` are **read-only data sources** — no Terraform resource onboards a physical FortiGate into FortiSASE. Device onboarding stays in FortiZTP / FortiManager; Terraform handles the **FortiSASE config plane**.

> **Pipeline shape:** **FortiZTP (onboard) + FortiManager (edge config) + Terraform `fortisase` (SASE config plane).**

### 4.2 Adjacent providers usable for the SASE edge
- **`fortinetdev/fortios`** — full FortiOS config of the branch/on-ramp FortiGate (SD-WAN, IPsec, BGP, policies). (https://registry.terraform.io/providers/fortinetdev/fortios/latest/docs)
- **`fortinetdev/fortimanager`** — drive FortiManager device DB, policy packages, SD-WAN/provisioning templates the on-ramp FortiGates inherit (pairs with §5).

### 4.3 Community / other SDKs
- **`pyFortiSASE`** — **UNVERIFIED**; no first-party Fortinet Python SDK by that name confirmed. Supported automation SDKs are the Terraform provider and direct REST against the IAM-OAuth API. Our own SDK should mirror the **FortiZTP/SOCaaS client pattern** (see inventory).

---

## 5. FortiManager-driven automation (branch on-ramp FortiGates)
For FortiGate-based on-ramps, FortiManager (or FortiManager Cloud) is the provisioning brain; FortiZTP is the delivery mechanism.

**Day-0/Day-1 sequence:**
1. **Asset registration** → FortiGate in the FortiCloud account (§3.3).
2. **Model device + templates** on FortiManager Cloud: a **device blueprint/model device** plus a **device template** and **SD-WAN template** carrying the on-ramp config (interfaces, IPsec overlays to the FortiSASE PoP, BGP-per-overlay, security profiles). (Source: https://docs.fortinet.com/document/fortimanager-cloud/7.6.6/cloud-deployment/552626/using-fortiztp-with-fortimanager-cloud)
3. **FortiZTP provision → FortiManager Cloud** (§3.5 Pattern B). FGFM + auto-link on first boot; reboot/factory-reset for hardware.
4. **Template install** pushes the golden config; the FortiGate establishes the **IPsec/SPA tunnel to the FortiSASE Branch On-ramp location**.

**FortiSASE side — SD-WAN/Branch On-Ramp:**
> "FortiGate is the only supported IPsec device that you can use for Branch On-ramp." Configure it "by setting up an IPsec tunnel between the certified IPsec device located at the branch and a FortiSASE Branch On-ramp location," after which endpoints behind it need **no FortiClient and no explicit web-proxy settings**. (Sources: https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/213023/sd-wan-on-ramp ; https://docs.fortinet.com/document/fortisase/latest/architecture-guide/213023/site-based-remote-users-using-branch-on-ramp)

**SPA automation:** once the SPA hub side is up, the **FortiSASE REST API** (or Terraform `private_access_*` resources) manages the **common SPA network connection** and **service connections** to the FortiGate SPA hubs and reads their status (§1.2).

---

## 6. Automation use cases for an MSSP / partner SASE service

**Bulk site onboarding (day-0):**
- One FortiZTP call provisions **many serial numbers** at once (2,000 calls/hr ceiling — §3.4); batch well under it.
- FortiGate branch on-ramps: pre-stage **model devices + SD-WAN templates** in FortiManager Cloud so every drop-shipped unit inherits the golden on-ramp config (§5).
- FortiAP/FortiExtender thin-edge: FortiZTP **TARGET = FortiSASE** directly (§3.5 Pattern A).

**Golden bootstrap config:**
- FortiManager device/SD-WAN templates are the golden config of record; FortiZTP **pre-run CLI** covers first-contact deltas (§3.6). Keep FortiSASE config-plane (profiles/policies/SPA) in **Terraform `fortinetdev/fortisase`** so it's versioned and reproducible across tenants (§4).

**Multi-tenant considerations:**
- Tenancy boundary = the **FortiCloud account** (each tenant typically its own account/sub-account; assets, FortiSASE subscription, and FortiZTP inventory are account-scoped — §2.1, §3.3).
- Use **FortiCloud IAM Organizations + ORG/IAM API users** to let one MSSP automation identity operate across tenant accounts under controlled **permission profiles** (§2.1). Mint **per-portal tokens** by `client_id`; consider per-tenant Terraform workspaces/state.
- **UNVERIFIED:** whether a single ORG-level API user can mint a FortiSASE token directly against a managed tenant account without per-account credentials — validate against IAM Organizations docs + the FortiSASE multi-tenant/MSSP architecture guide before designing the trust model.

**Day-2 operations:**
- Drift/change: Terraform plan/apply against `fortisase` resources; FortiManager for edge config; FortiOS provider for deep branch tweaks.
- Visibility: FortiSASE data sources (`endpoints_details`, `infra_data_transfer`, `security_botnet_domains_stat`) + REST reads.
- Decommission: FortiZTP **deprovision** (does **not** delete the device from FortiManager Cloud — clean up there manually — §3.5).

**MSSP architecture reference:** the **"Unified SASE for MSSP" architecture guide** includes the **Branch On-Ramp (BOR)** model — align tenant/on-ramp design to it. (Source: https://docs.fortinet.com/document/fortisase/latest/unified-sase-for-mssp-architecture-guide/438696/branch-on-ramp-bor)

---

## 7. Verified vs. unverified — quick ledger

**Verified (cited above):** FortiSASE has a REST API (FNDN ref; SPA configurable via REST); FortiCloud IAM API-user + OAuth flow, token endpoint, JSON bodies, bearer usage, refresh; `client_id` selects portal scope; FortiZTP portal URL, v2.0 API, 2,000/hr limit, bulk-by-serial, **FortiSASE is a provision target**, device-type/target list; FortiZTP→FortiManager Cloud FortiGate flow; FortiAP/FortiExtender→FortiSASE direct ZTP; Terraform `fortinetdev/fortisase` v1.2.0 auth + catalog; SD-WAN/Branch On-Ramp FortiGate-only IPsec device.

**Unverified — confirm on FNDN / provider source / incoming Swagger / IAM Org docs:** literal FortiSASE REST hostname/base path + published OpenAPI file; exact FortiZTP `provisionTarget: FortiSASE` JSON; literal `client_id` for FortiSASE; existence/status of `pyFortiSASE`; whether one ORG/IAM API user can drive FortiSASE config across tenant accounts; exact 7.6/8.0 drop-ship bootstrap CLI text.

---

## Sources

- [FortiSASE — Appendix B: REST API](https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/268966/appendix-b-rest-api)
- [FortiSASE — Configuring SPA using the REST API (25.3.57)](https://docs.fortinet.com/document/fortisase/25.3.57/mature-administration-guide/702423/configuring-spa-using-the-rest-api)
- [FortiSASE — SD-WAN On-Ramp](https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/213023/sd-wan-on-ramp)
- [FortiSASE — Site-based remote users using Branch On-ramp](https://docs.fortinet.com/document/fortisase/latest/architecture-guide/213023/site-based-remote-users-using-branch-on-ramp)
- [FortiSASE — Branch On-Ramp (BOR), Unified SASE for MSSP](https://docs.fortinet.com/document/fortisase/latest/unified-sase-for-mssp-architecture-guide/438696/branch-on-ramp-bor)
- [FortiSASE — Thin Edge (FortiExtender 200F)](https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/344098/thin-edge)
- [FortiSASE — Connecting a FortiAP using FortiZTP](https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/299731/connecting-a-fortiap-to-fortisase-using-fortiztp)
- [FortiCloud IAM — Adding an API user (26.1.0)](https://docs.fortinet.com/document/forticloud/26.1.0/identity-access-management-iam/282341/adding-an-api-user)
- [FortiCloud IAM — API users (26.1.0)](https://docs.fortinet.com/document/forticloud/26.1.0/identity-access-management-iam/927656/api-users)
- [FortiCloud IAM — Accessing FortiAPIs (OAuth flow)](https://docs.fortinet.com/document/forticloud/26.1.0/identity-access-management-iam/19322/accessing-fortiapis)
- [FortiZTP — Introduction (26.1.a)](https://docs.fortinet.com/document/fortiztp/26.1.a/administration-guide/756835/introduction)
- [FortiZTP — API (latest): v2.0, rate limit, FNDN ref](https://docs.fortinet.com/document/fortiztp/latest/administration-guide/182159/api)
- [FortiZTP — Provisioning a FortiGate (25.4.0)](https://docs.fortinet.com/document/fortiztp/25.4.0/administration-guide/574054/provisioning-a-fortigate)
- [FortiManager Cloud — Using FortiZTP with FortiManager Cloud (7.6.6)](https://docs.fortinet.com/document/fortimanager-cloud/7.6.6/cloud-deployment/552626/using-fortiztp-with-fortimanager-cloud)
- [FortiOS — ZTP using device blueprints (7.2.0)](https://docs.fortinet.com/document/fortigate/7.2.0/sd-wan-architecture-for-enterprise/372716/zero-touch-provisioning-ztp-using-device-blueprints)
- [Terraform Registry — fortinetdev/fortisase](https://registry.terraform.io/providers/fortinetdev/fortisase/latest)
- [GitHub — fortinetdev/terraform-provider-fortisase](https://github.com/fortinetdev/terraform-provider-fortisase)
- [GitHub — fortisase provider docs/index (auth)](https://github.com/fortinetdev/terraform-provider-fortisase/blob/main/docs/index.md)
- [Terraform Registry — fortinetdev/fortios](https://registry.terraform.io/providers/fortinetdev/fortios/latest/docs)
- [FNDN — FortiSASE REST API reference (account required)](https://fndn.fortinet.net/index.php?app=apicompare&id=2625&name=fortisase&display=2639)
- [FNDN — FortiZTP REST API reference (account required)](https://fndn.fortinet.net/index.php?/fortiapi/1584-fortiztp/)
