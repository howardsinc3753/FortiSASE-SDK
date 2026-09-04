# Branch On-Ramp Demo — 2 FortiOS spoke VMs on AWS

Terraform that stands up **two FortiOS 7.6.7 GA VMs** on AWS, each with a public WAN IP and its **own unique LAN subnet**, ready to be configured as **SD-WAN spokes** onto your **FortiSASE Branch On-Ramps** (which are FortiOS hubs behind the scenes).

**Scope of this terraform:** infrastructure only — the two VMs, networking, and a minimal bootstrap (hostname / admin / interfaces). **You** apply the FortiFlex license and configure BGP / IPsec / SD-WAN to the on-ramps once they're up. No FortiManager, no hubs, no config push — keep it simple and reproducible for a partner PoC.

```
        AWS VPC (one region/AZ)
  ┌───────────────────────────────────────────────┐
  │  spoke-1   WAN(EIP)│port1   port2│LAN 10.200.10.0/24  │
  │  spoke-2   WAN(EIP)│port1   port2│LAN 10.200.20.0/24  │   (unique LAN per VM)
  └───────────────────────────────────────────────┘
        │ IPsec/SD-WAN (you configure)
        ▼
   FortiSASE Branch On-Ramps (FortiOS hubs, already deployed, taking IPsec)
```

## What it deploys
- 1 VPC + per-spoke **public WAN subnet + Elastic IP** + per-spoke **private LAN subnet** (unique CIDRs)
- 2× **FortiGate 7.6.7 GA BYOL** instances (ARM64 `t4g.medium` = 2 vCPU / 4 GiB by default — **do not drop to `t4g.small`/2 GiB: FortiOS 7.6.x conserve-mode wedges the GUI**), dual-NIC (port1 WAN / port2 LAN)
- Security group: **admin GUI `10443`** + SSH `22` (from your IP), **IKE-over-TCP `443`**, IPsec (IKE 500, NAT-T 4500, ESP), intra-VPC
- Minimal bootstrap: hostname, admin password, **admin GUI on `10443`** (see below), port1 (WAN) + port2 (unique LAN)
- **Management-return route** pinning your trusted mgmt subnet out the WAN (see below)

## Management survives the tunnel
When you bring up IPsec/SD-WAN to the on-ramp, the on-ramp **injects a default route into the tunnel**. Without a more-specific route, the FortiGate would send admin (GUI/SSH) *replies* to your management IP back through the tunnel → you lose management access.

The bootstrap pre-installs a **longest-prefix static route** (`edit 10`, out `port1`) for your trusted management subnet, which always beats the injected `0.0.0.0/0`. Source of that subnet:
- Defaults to **`admin_cidr`** — perfect for a single-IP demo (your `/32`).
- Set **`mgmt_return_cidr`** per-partner when the management subnet differs from the SG allow-list (e.g. `"10.0.0.0/8"`).
- Resolves to `0.0.0.0/0` → route is skipped (nothing to pin).

> If you later add `port1` to an SD-WAN zone, keep this route pinned to `port1` (or the SD-WAN member) so it isn't overridden.

## Reproducible for partners
- **AMI is looked up live** (`data aws_ami`, owner Fortinet `679593333241`, keyed on `var.fortios_version` + `var.architecture`) — **no hardcoded AMI ID**, works in any region.
- Everything parameterized in `terraform.tfvars`; the example file is committed, the real one is gitignored.
- `terraform fmt`/`validate` clean.

## Quick start
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars   # set key_pair_name + admin_password (+ admin_cidr to your IP)
terraform init
terraform apply        # ~3 min
```
Outputs give each VM's **public IP** and **`https://<ip>:10443/` admin URL**. Default admin user `admin`.

### Admin GUI is on 10443, not 443
The FortiSASE on-ramp tunnel uses **IKE-over-TCP (RFC 8229)**, which binds the FortiGate's local TCP **443** — the same port the admin GUI's `httpsd` uses. Left on 443 they collide and the GUI **RSTs the TLS handshake** (SSH still works — a classic red herring). So the bootstrap sets `admin-sport 10443` and the SG opens `10443` for admin + `443` for IKE-over-TCP. Override with `var.admin_sport` if needed.

## After `apply` (your steps)
1. **License** — apply each VM's FortiFlex token: GUI *System → FortiGuard*, or CLI `execute vm-license <token>` (or bake it in via `var.flex_tokens`).
2. **Configure the on-ramp** — IPsec phase1/phase2 to each FortiSASE on-ramp, BGP, SD-WAN members/rules. **Per-spoke overlay/BGP/static-route plan (Spoke-ID 1..N) is in [`onramp-spoke-bgp-plan.md`](onramp-spoke-bgp-plan.md)** — proven against the `rl-1` reference spoke. (Hub-side templates live in `MSSP-SE-Tools/Agentic-SDWAN-Workflow` + `hub-full-config.cli`.)
3. Verify tunnels up (`get vpn ipsec tunnel summary`) and SD-WAN steering.

## Tear down
```bash
terraform destroy
```

> Account/region/licensing are operator-supplied via `terraform.tfvars` (gitignored). Nothing account-specific is committed.
