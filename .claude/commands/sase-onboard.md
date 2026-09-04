---
description: Context-load a fresh Claude session into FortiSASE-SME mode and print a state summary
---

You are starting (or resuming) work in the **FortiSASE-SDK** repo. Get oriented before doing anything else.

1. Read [`CLAUDE.md`](../../CLAUDE.md) — adopt FortiSASE-SME mode + the source-of-truth tier rules.
2. Read [`README.md`](../../README.md) — repo map and current status.
3. Skim the three corpus docs in [`corpus/raw/fortinet-docs/`](../../corpus/raw/fortinet-docs/):
   - `01-architecture-and-onramps.md` (on-ramp types — the focus)
   - `02-automation-and-apis.md` (ZTP + REST + Terraform)
   - `03-releases-and-licensing.md` (packaging for the offering)
4. Read [`handoff/local-asset-inventory.md`](../../handoff/local-asset-inventory.md) — reusable local code (FortiZTP SDK, browser tools, SD-WAN templates).
5. Check whether the FortiSASE Swagger has landed in [`api/openapi/`](../../api/openapi/) yet (a `*.json`). If it has, that unblocks the REST/SDK work.
6. Recall relevant memory (FortiSASE/SASE/MSSP/FortiZTP project notes).

Then print a compact **state summary**: what the repo is, what's done, the single biggest open item (currently: the incoming Swagger → confirms FortiSASE `client_id`/base host and unblocks the SDK), and any UNVERIFIED items that matter for the current task. **Wait for Daniel's direction — do not start building until asked.**
