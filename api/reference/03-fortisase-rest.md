# 03 — FortiSASE REST API

> **Status: provisional until the Swagger lands in `../openapi/`.** FortiSASE has a public REST API ("Appendix B – REST API"); the machine-readable reference is FNDN-gated. The resource map below is derived authoritatively from the first-party Terraform provider (Tier 2), which mirrors the **FortiSASE Service Resource API V2**. Auth = Bearer token (see `01-auth.md`); `client_id` for FortiSASE is **UNVERIFIED** — confirm from the Swagger.

## What's confirmed in the open docs
**Secure Private Access (SPA)** is the one resource family with explicit REST documentation:
> "You can perform SPA configuration using the FortiSASE REST API to manage the common SPA network connection and service connections to FortiGate SPA hubs and retrieve the status of these connections." All SPA config ops are possible **except viewing health/VPN-tunnel status**.
(Source: https://docs.fortinet.com/document/fortisase/25.3.57/mature-administration-guide/702423/configuring-spa-using-the-rest-api)

This matters for the on-ramp story: once a FortiGate SPA hub is up, the SPA **network connection** and **service connections** are fully automatable via REST (or the Terraform `private_access_*` resources).

## Resource families (from the Terraform provider catalog → REST groups)
| Family | Representative resources |
|---|---|
| Endpoints / FortiClient | `endpoint_*` (connection, protection, sandbox, ztna, settings), `endpoints_enable_management`, `endpoints_access_proxy_authorize` |
| Users & auth | `auth_users`, `auth_user_groups`, `auth_ldap_servers`, `auth_radius_servers`, `auth_*_saml_server`, `auth_fsso_agents` |
| Security profiles | `security_{antivirus,web_filter,ips,dlp_*,dns_filter,ssl_ssh,application_control}_profile`, threat feeds |
| Policies | `security_internal_policies`, `security_outbound_policies`, `security_endpoint_to_endpoint_policies` |
| Network | `network_hosts`, `network_host_groups`, `network_dns_rules`, `infra_ipam_setting`, `infra_ssids` |
| **Private access (SPA)** | `private_access_network_configuration`, `private_access_service_connections`, `..._auth`, `..._region_cost` |
| Infra (read-only) | `infra_fortigates`, `infra_extenders`, `infra_data_transfer`, `infra_secure_web_gateway_supplementary_data` |
| Reporting | `endpoints_details`, `endpoints_donut`, `security_botnet_domains_stat`, `infra_data_transfer` |
| DEM | `dem_spa_applications`, `dem_custom_saas_apps` |

## Hard limits of the API surface
- **No PoP lifecycle API.** PoPs are Fortinet-operated; `infra_*` are read-only. You configure on-ramps/SPA/profiles, not the PoP fleet.
- **No "onboard a physical FortiGate into FortiSASE" resource.** Device onboarding lives in FortiZTP/FortiManager; the FortiSASE REST/Terraform plane owns config (profiles, policies, SPA, endpoints).

## When the Swagger arrives
Drop the JSON in `../openapi/fortisase-api-<version>.json`, then we can:
1. Confirm the literal **base host** and **`client_id`**.
2. Confirm exact SPA + endpoint + policy paths/fields.
3. Replace the "provisional" labels here and generate `api/examples/` recipes + the FortiSASE SDK client.

Sources: https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/268966/appendix-b-rest-api · https://github.com/fortinetdev/terraform-provider-fortisase/tree/main/docs/resources
