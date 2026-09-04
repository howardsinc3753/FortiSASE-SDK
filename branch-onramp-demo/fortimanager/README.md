# Self-hosted FortiManager (AWS) — Branch On-Ramp demo

Terraform for a **FortiManager 7.6.7 GA BYOL** VM that the branch spokes register to over **FGFM (541)**. Deploys **into the same VPC as the spokes** (looked up by tag) so device management works over the shared VPC. Reproducible — AMI, VPC, and IGW are all resolved live, no hardcoded IDs.

```
   spoke VPC (10.200.0.0/16, tag sase-spoke-vpc)
  ┌─────────────────────────────────────────────┐
  │  spoke-1 / spoke-2  (10.200.{1,2}.0/24 WAN)   │
  │        │ FGFM 541                             │
  │        ▼                                      │
  │  FortiManager  10.200.254.0/24 (mgmt) + EIP   │
  └─────────────────────────────────────────────┘
```

## What it deploys
- **FMG 7.6.7 GA BYOL**, **`m5.xlarge` (4 vCPU / 16 GiB)** by default — `m5` is non-burstable (a management/DB server shouldn't throttle on t3 CPU credits). Bump `instance_type` to `m5.2xlarge` (8/32) for many ADOMs/devices.
- **Two disks:** 30 GiB gp3 root + **200 GiB gp3 data on `/dev/sdb`** (encrypted). The data disk is **required** — FMG stores its database + device logs there.
- Dedicated **`10.200.254.0/24` mgmt subnet** in the spoke VPC + route to the shared IGW + **EIP**.
- Auto-generated SSH key stored in **Secrets Manager** (never in state as plaintext output).
- SG: GUI `443` + SSH `22` from `admin_cidr`, **FGFM `541`** from the VPC + on-ramp overlay.

## Reproducible / partner-safe
- **AMI looked up live** — `FortiManager-VM64-AWS build* (7.6.7) GA-*`, owner Fortinet `679593333241` (the ` build` literal excludes PAYG `-AWSONDEMAND`). No hardcoded AMI.
- **VPC + IGW looked up by tag** — deploy the spoke stack (`../terraform`) first; this stack finds it.
- Secrets gitignored via the repo-root `.gitignore` (`*.tfvars`, `*.tfstate*`, `.terraform/`).

## Deploy
```bash
# 1) spokes first (../terraform) so the VPC exists
cd fortimanager
cp terraform.tfvars.example terraform.tfvars   # set admin_cidr to your IP
export AWS_PROFILE=faig-corp                     # SSO accounts; aws sso login first
terraform init
terraform apply        # ~3-4 min
```
Outputs give the **admin URL**, private IP, and the exact `aws secretsmanager` command to fetch the SSH key.

## After `apply` (your steps)
1. **First login** — browse the admin URL, user `admin` / blank password → set a strong one.
2. **Confirm the data disk** — FMG should auto-detect `/dev/sdb`; if not, add it under *System Settings*.
3. **License** — apply the FortiManager FortiFlex/BYOL license.
4. **Add devices** — register spoke-1/spoke-2 (and rl-1) over FGFM; on each FortiGate set `config system central-management` → the FMG's IP.

## Tear down
```bash
terraform destroy
```
> Stop the instance when idle to save budget — the EBS volumes (root + 200 GiB data) persist. FMG on `m5.xlarge` is ~\$0.19/hr running; the data disk is ~\$16/mo whether on or off.
