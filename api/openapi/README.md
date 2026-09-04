# FortiSASE OpenAPI / Swagger — landing spot

**This folder is where Daniel's incoming FortiSASE Swagger/OpenAPI JSON goes.** Name it `fortisase-api-<version>.json` (e.g. `fortisase-api-26.1.json`) to match the FortiAIGate-SDK convention.

## Why it isn't here yet
The FortiSASE machine-readable API reference is published on the **Fortinet Developer Network (FNDN)** behind an account, via an "apicompare" tool rather than a public `openapi.json` (corpus `02-automation-and-apis.md` §1.1). Until the file lands, the authoritative resource map is the **`fortinetdev/fortisase` Terraform provider** catalog — see `../reference/03-fortisase-rest.md` and `04-terraform.md`.

## When you drop the JSON here, ask Claude to:
1. Extract the **base host** and confirm the FortiSASE **`client_id`** (resolves the open UNVERIFIED item).
2. Diff the spec's resource tree against the Terraform-derived map in `../reference/03-fortisase-rest.md`; correct anything provisional.
3. Generate runnable recipes into `../examples/` (auth → list endpoints → create SPA service connection → on-ramp config).
4. Scaffold the `fortisase/` Python SDK client (mirror the FortiZTP pattern — see `handoff/local-asset-inventory.md`).
5. Stand up a Swagger-UI viewer under `ui/` (mirror `FortiAIGate-SDK/api/openapi/ui/`).

> Sanitize first: if the export embeds tokens, account IDs, or tenant hostnames, scrub them before committing — this repo is shared with a partner.
