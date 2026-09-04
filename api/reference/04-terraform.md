# 04 — Terraform: `fortinetdev/fortisase` (config-plane IaC)

> First-party provider. **v1.2.0** (~Apr 2026). Implements the **FortiSASE Service Resource API V2** (covers ~25.2.b). ~84 resources / ~110 data sources. MPL-2.0, Terraform 0.12+. This is how we keep each tenant's FortiSASE config versioned and reproducible.

## Provider config (auth = IAM API user)
```hcl
terraform {
  required_providers {
    fortisase = { source = "fortinetdev/fortisase", version = "~> 1.2" }
  }
}

# Mode 1 — API user ID + secret
provider "fortisase" {
  username = var.fsase_api_id     # never hardcode; use TF_VAR_/vault
  password = var.fsase_api_secret
}

# Mode 2 — pre-minted OAuth token (from 01-auth.md)
# provider "fortisase" { access_token = var.fsase_token }
```
Schema: `username`, `password`, `access_token`, `refresh_token` (all optional). No base-URL/region knob — the provider encapsulates the endpoint.

## What it's good for (on-ramp/MSSP service)
- **SPA / private access:** `fortisase_private_access_network_configuration`, `fortisase_private_access_service_connections` (+ `_auth`, `_region_cost`) — the SPA hub plumbing for site/private-app on-ramps.
- **Endpoints / ZTNA:** `endpoint_policies`, `endpoint_ztna_{profiles,rules,tags}`, `endpoint_protection_profiles`, `endpoints_enable_management`.
- **Security golden config:** the full `security_*` profile suite + `security_internal_policies` / `security_outbound_policies` — define once, reuse per tenant.
- **Network/auth:** `network_hosts`, `network_dns_rules`, `infra_ipam_setting`, `auth_*`.

## What it can't do (by design)
- `infra_fortigates`, `infra_extenders` are **read-only data sources** → no device onboarding here. Use FortiZTP/FortiManager (`02-fortiztp-onramp.md`).
- No PoP lifecycle resource (Fortinet-operated).

## Pipeline placement
```
FortiZTP (onboard device)  →  FortiManager (branch FortiGate edge config)  →  Terraform fortisase (SASE config plane)
```
Per-tenant: separate Terraform workspace/state; feed the provider a per-tenant token (`client_id=fortisase`).

## Adjacent providers for the edge
- `fortinetdev/fortios` — deep FortiOS config of the branch/on-ramp FortiGate (SD-WAN, IPsec, BGP).
- `fortinetdev/fortimanager` — FortiManager device DB, policy packages, SD-WAN/provisioning templates.

Sources: https://registry.terraform.io/providers/fortinetdev/fortisase/latest · https://github.com/fortinetdev/terraform-provider-fortisase
