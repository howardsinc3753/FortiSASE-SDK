# 02 — FortiZTP v2 REST: zero-touch on-ramp provisioning

> The keystone of the on-ramp automation offering. **Base:** `https://fortiztp.forticloud.com/public/api/v2` · **Auth:** Bearer token, `client_id=fortiztp` (see `01-auth.md`) · **Rate limit:** 2,000 calls/hour · **API version:** v2.0. Endpoint/field shapes confirmed against our working SDK (Tier 2). FNDN reference: `https://fndn.fortinet.net/index.php?/fortiapi/1584-fortiztp/`.

## Prerequisite: the device must be in Asset Management
Register/import the device (serial + cloud/FortiDeploy key) to **Asset Management in the same FortiCloud account**. FortiZTP auto-loads it onto the **UNPROVISIONED** tab. For FortiSASE-managed edges, also register the **FortiSASE subscription code** to that account so the device shows a "FortiSASE Subscription" entitlement.

## Core calls
```
GET  /devices                      # inventory (optionally filter client-side by type/status/target)
GET  /devices/{deviceSN}           # one device's status
PUT  /devices/{deviceSN}           # set/clear provision target  ← the action
GET  /setting/fortimanagers        # registered FortiManagers (oid/sn/ip/scriptOid)
GET/POST/PUT/DELETE /setting/scripts[/{oid}[/content]]   # bootstrap CLI scripts
```

### Provision body (`PUT /devices/{deviceSN}`)
```json
{
  "deviceType": "FortiGate",          // FortiGate | FortiGate-VM | FortiWiFi | FortiAP | FortiSwitch | FortiExtender
  "provisionStatus": "provisioned",   // provisioned | unprovisioned
  "provisionTarget": "FortiManager",  // FortiManager | FortiManagerCloud | FortiGateCloud | FortiEdgeCloud | FortiExtenderCloud | FortiSASE
  "region": "…",                       // required for cloud targets
  "fortiManagerOid": 123,
  "scriptOid": 456,                    // bootstrap CLI script
  "externalControllerIp": "…",
  "firmwareProfile": "…"
}
```
- **Bulk:** one call can carry multiple serial numbers.
- `200` success (body may be empty); `400` check required fields; `401` token; `404` unknown SN; `429` back off.
> **SDK gap:** our local `devices.py` enum lacks `FortiSASE` as a target — add it. Docs confirm `FortiSASE` is a valid FortiZTP target as of 26.1.a (corpus 02 §3.2). **UNVERIFIED:** the exact extra fields (region requirements) for `provisionTarget: "FortiSASE"` — confirm on FNDN / live tenant.

## The two on-ramp patterns (pick by device)
**Pattern A — FortiAP / FortiExtender → FortiSASE directly** (FortiSASE-managed thin edge):
1. Asset-register device + FortiSASE sub code.
2. FortiZTP **Settings** → enable **FortiSASE** for that device tab.
3. `PUT /devices/{SN}` with `provisionTarget: "FortiSASE"` (+ region).
4. Device calls home → becomes a FortiSASE-managed on-ramp.

**Pattern B — FortiGate branch box → FortiManager(Cloud) → IPsec/SPA on-ramp to FortiSASE** (the classic branch):
1. Asset-register the FortiGate.
2. Pre-build a **model device + SD-WAN/device template** on FortiManager Cloud with the on-ramp config.
3. `PUT /devices/{SN}` with `provisionTarget: "FortiManagerCloud"` (+ optional `scriptOid` pre-run CLI).
4. First boot → FGFM tunnel + auto-link; **reboot / factory-reset hardware**.
5. FortiManager installs templates → FortiGate dials IPsec to the **FortiSASE Branch On-ramp location**.
> Deprovisioning in FortiZTP does **not** delete the device from FortiManager Cloud — clean up there manually.

## Branch-on-ramp ordering gotcha
On the FortiSASE side, **SPA network config must exist before you deploy a Branch On-ramp location** (they share BGP config), and **only iBGP** is supported between BOR and branches. Scale: 2–20 BOR nodes/tenant, 1 Gbps & 2000 branches/node, 40,000/tenant (corpus 01 §3.3).

Sources: https://docs.fortinet.com/document/fortiztp/latest/administration-guide/182159/api · https://docs.fortinet.com/document/fortiztp/26.1.a/administration-guide/756835/introduction · https://docs.fortinet.com/document/fortimanager-cloud/7.6.6/cloud-deployment/552626/using-fortiztp-with-fortimanager-cloud · local: `MSSP-SE-Tools/FortiZTP/docs/api_reference.md`
