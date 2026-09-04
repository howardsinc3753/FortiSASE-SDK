# Site-4 — Dual-Circuit (dual-ISP) BOR test spoke (AWS)

One FortiGate VM with **two WAN interfaces, each with its own EIP** = two simulated ISP circuits,
for testing the dual-WAN / 4-tunnel BOR design. Derived from the OaaS-POC single-WAN pattern.

```
                    ┌───────── EIP-A (circuit A / ISP-A)
   port1 (WAN1) ────┘   10.204.1.10/24
   port2 (WAN2) ────┐   10.204.2.10/24
                    └───────── EIP-B (circuit B / ISP-B)
   port3 (LAN)          10.204.10.10/24  ← LAN gateway for clients
```

## Deploy

```bash
cp terraform.tfvars.example terraform.tfvars   # set key_pair_name, admin_password, admin_cidr
terraform init
terraform apply
```
`terraform apply` needs an active AWS session (SSO): `aws sso login --profile <your-profile>` first
(run it yourself). Outputs give you both EIPs, the admin URL (`https://<wan1_eip>:10443`), and the
`port -> IP` map to plug into the config generator.

## Then

1. Confirm reachable on **both** EIPs (`https://<wan1_eip>:10443` and `<wan2_eip>`).
2. In the config generator, load the **Dual ISP** baseline for Site-4 (WAN/LAN IPs already match
   the defaults here), generate, and paste the dual-circuit BOR config.
3. On the FortiSASE side, create the **4 tunnel configs** (2 per PoP, net-ids 1-4) from the
   downloadable IPsec values card.

## Notes
- AMI default is 7.6.6 BYOL ARM64 (us-east-1). Override `fortios_ami` for 7.6.7 / another region.
- Both default routes are equal-distance in the bootstrap so the box is reachable on either circuit
  before SD-WAN is configured; the full BOR config re-does routing under SD-WAN.
- `terraform destroy` when done — EIPs bill while allocated.
