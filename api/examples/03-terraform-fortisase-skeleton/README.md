# Terraform FortiSASE skeleton

Minimal example of managing the FortiSASE **config plane** with the first-party `fortinetdev/fortisase` provider. See `../../reference/04-terraform.md`.

```bash
export TF_VAR_fsase_api_id="<apiId>"
export TF_VAR_fsase_api_secret="<secret>"
terraform init
terraform plan
```

**Before you apply:** the SPA resource arguments in `main.tf` are commented and illustrative. Confirm exact argument names against the [provider docs](https://registry.terraform.io/providers/fortinetdev/fortisase/latest/docs) and the incoming Swagger — then uncomment. `data.fortisase_infra_fortigates` is read-only and safe to plan immediately as a connectivity smoke test.

**Ordering rule:** SPA network configuration must exist before a Branch On-ramp location is deployed (they share BGP config) — corpus `01-architecture-and-onramps.md` §3.3.
