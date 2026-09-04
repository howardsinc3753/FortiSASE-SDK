# FortiSASE / on-ramp automation — runnable examples

Working recipes for the automation pipeline. **Daniel runs these himself** (they touch credentials). Set env first:
```bash
export FORTI_API_ID="<apiId>"        # FortiCloud IAM API user
export FORTI_API_SECRET="<secret>"
```

| File | What it does | Portal / client_id |
|---|---|---|
| [`01-forticloud-oauth-token.sh`](01-forticloud-oauth-token.sh) | Mint an OAuth bearer token for any FortiCloud portal | any (`fortiztp`, `fortisase`, …) |
| [`02-fortiztp-list-and-provision.py`](02-fortiztp-list-and-provision.py) | List unprovisioned devices and provision an on-ramp (both patterns) | `fortiztp` |
| [`03-terraform-fortisase-skeleton/`](03-terraform-fortisase-skeleton/) | Minimal Terraform to manage the FortiSASE config plane (SPA service connection) | `fortisase` |

Once the Swagger lands in `../openapi/`, we add `04-fortisase-rest-*` recipes (create SPA connection, push on-ramp config) generated from the real spec.

> The `fortisase` `client_id` is **assumed** until the Swagger confirms it (see `../reference/01-auth.md`). `01`/`02` are confirmed against our working FortiZTP SDK; `03` is confirmed against the published Terraform provider.
