# ---------- Required ----------
variable "key_pair_name" {
  description = "OPTIONAL existing EC2 key pair. FortiGate admin login is the password, so this is not required; leave empty if the account has no key pair."
  type        = string
  default     = ""
}

variable "admin_password" {
  description = "FortiGate admin password (min 8 chars). Applied to every spoke."
  type        = string
  sensitive   = true
}

# ---------- AWS placement ----------
variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "availability_zone" {
  description = "Single AZ for the PoC (same AZ for both = simplest/cheapest)."
  type        = string
  default     = "us-east-1a"
}

variable "aws_profile" {
  description = "Named AWS CLI/SSO profile. Empty = default credential chain. (Uncomment the line in versions.tf to use.)"
  type        = string
  default     = ""
}

variable "admin_cidr" {
  description = "PRIMARY CIDR allowed to reach admin GUI/SSH. Set to YOUR public IP/32 (`curl ifconfig.me`). This one also anchors the mgmt-return route (see mgmt_return_cidr)."
  type        = string
  default     = "0.0.0.0/0"
}

variable "extra_admin_cidrs" {
  description = "ADDITIONAL CIDRs allowed to reach admin GUI (admin_sport) + SSH — e.g. coworkers' public IPs. These get SG access only; they do NOT get a mgmt-return route. Example: [\"198.51.100.7/32\"]."
  type        = list(string)
  default     = []
}

variable "mgmt_return_cidr" {
  description = "Trusted management/trust-host subnet whose RETURN path is pinned out the WAN (port1) via a longest-prefix static route, so admin access survives the FortiSASE on-ramp injecting a default route into the IPsec tunnel. Empty = reuse admin_cidr (fine for a single-IP demo). Set per-partner to their management subnet when it differs from the SG allow-list. Ignored if it resolves to 0.0.0.0/0 (nothing to pin)."
  type        = string
  default     = ""
}

variable "admin_sport" {
  description = "HTTPS admin GUI port. Defaults to 10443, NOT 443 — FortiOS IKE-over-TCP (RFC 8229), which the FortiSASE on-ramp tunnel uses, binds local TCP 443 and collides with the GUI's httpsd, RST-ing the TLS handshake. Keeping admin on 10443 leaves 443 free for IKE-over-TCP."
  type        = number
  default     = 10443
}

# ---------- FortiOS image (reproducible lookup — NO hardcoded AMI) ----------
variable "fortios_version" {
  description = "FortiOS GA version to deploy. Resolved live via the Fortinet-owned AMI catalog."
  type        = string
  default     = "7.6.7"
}

variable "architecture" {
  description = "CPU arch: 'arm64' (t4g/c7g, cheapest) or 'x86_64' (t3/c5). Must match instance_type."
  type        = string
  default     = "arm64"
  validation {
    condition     = contains(["arm64", "x86_64"], var.architecture)
    error_message = "architecture must be 'arm64' or 'x86_64'."
  }
}

variable "instance_type" {
  description = "EC2 type. t4g.medium (2 vCPU / 4 GiB) is the practical minimum — FortiOS 7.6.x on 2 GiB (t4g.small) hits memory conserve mode and the GUI (httpsd) resets the TLS handshake. Verified 2026-07-01."
  type        = string
  default     = "t4g.medium"
}

# ---------- Licensing (BYOL / FortiFlex) ----------
variable "flex_tokens" {
  description = "OPTIONAL per-spoke FortiFlex token to bake into the bootstrap, keyed by spoke name (e.g. {\"spoke-1\"=\"ABCD...\"}). Leave empty to license manually after boot (execute vm-license <token>)."
  type        = map(string)
  default     = {}
  sensitive   = true
}

# ---------- Topology ----------
variable "project_name" {
  description = "Name prefix for all resources."
  type        = string
  default     = "sase-spoke"
}

variable "vpc_cidr" {
  type    = string
  default = "10.200.0.0/16"
}

variable "spokes" {
  description = "The FortiOS spoke VMs. Each gets a public WAN subnet+EIP and a UNIQUE private LAN subnet. Add/remove entries to change VM count."
  type = map(object({
    wan_cidr = string
    lan_cidr = string
  }))
  default = {
    "spoke-1" = { wan_cidr = "10.200.1.0/24", lan_cidr = "10.200.10.0/24" }
    "spoke-2" = { wan_cidr = "10.200.2.0/24", lan_cidr = "10.200.20.0/24" }
  }
}

variable "tags" {
  type    = map(string)
  default = { Project = "sase-branch-onramp-demo", ManagedBy = "terraform" }
}

# ---------- Test clients (opt-in) ----------
variable "deploy_test_clients" {
  description = "Deploy per-LAN Linux test clients (clientless SASE/BOR test endpoints). OFF by default so a base apply never creates billed VMs. Set true in tfvars to add them."
  type        = bool
  default     = false
}

variable "clients_per_lan" {
  description = "Number of test-client VMs per spoke LAN. Static IPs assigned from .100 upward (.100, .101, .102, ...)."
  type        = number
  default     = 3
}

variable "test_client_instance_type" {
  description = "EC2 type for the test clients. t4g.small (arm64, bursts to 5 Gbps) is the default for BW-throughput headroom — the FortiGate VM + SASE tunnel are the real ceiling, not the client. Drop to t4g.micro (~half cost) for functional-only; bump to t4g.medium for sustained multi-Gbps. Cost scales with clients_per_lan x #spokes."
  type        = string
  default     = "t4g.small"
}

variable "test_client_ami_ssm_param" {
  description = "SSM public parameter resolving the test-client AMI. Default = latest Amazon Linux 2023 arm64 (matches the arm64 FortiGates; SSM agent preinstalled)."
  type        = string
  default     = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64"
}

variable "enable_ssm_endpoints" {
  description = "Create SSM VPC interface endpoints (ssm/ssmmessages/ec2messages) so Session Manager reaches the private clients WITHOUT going through the FortiGate/SASE — the mgmt plane then survives the SASE captive portal blocking data-plane egress. Only created when deploy_test_clients is also true. NOTE: interface endpoints bill ~$22/mo even while EC2 is stopped; set false to egress SSM through the FGT instead (the captive portal will then gate SSM until satisfied)."
  type        = bool
  default     = true
}

variable "mgmt_subnet_cidr" {
  description = "Dedicated management /28 for the SSM interface endpoints. Deliberately NOT one of the spoke LANs, so the east-west no-bypass routes never redirect SSM/RDP management traffic onto the FortiGate/SASE fabric. Keeps management direct + out-of-band even with site-to-site enforcement on. Must be inside vpc_cidr and not overlap any spoke WAN/LAN."
  type        = string
  default     = "10.200.250.0/28"
}

variable "route_intersite_via_fgt" {
  description = "Enforced default (true) — but ONLY takes effect when deploy_test_clients is also true, so a base apply never touches the live LAN route tables. When clients are deployed, this forces site-to-site (east-west) traffic through the FortiGates -> BOR/SPA tunnels instead of the AWS VPC-local shortcut (all spokes share one VPC, so without it inter-LAN traffic bypasses the FGTs/SASE). Adds more-specific-than-local routes (every other spoke's LAN /24 -> this spoke's FGT LAN ENI); fail-closed (blackholes if the FGT is down rather than bypassing). Set false to deploy clients but demo the direct AWS path."
  type        = bool
  default     = true
}

# ---------- Windows browser workstations (opt-in) ----------
variable "deploy_test_workstations" {
  description = "Deploy Windows browser workstations behind the branch on-ramps. Test a REAL web browser through the branch: the box's default route is the FortiGate, so browser traffic egresses FGT -> BOR -> FortiSASE (SIA + SSO captive portal). Reached by RDP tunneled over SSM (no public IP). Opt-in."
  type        = bool
  default     = false
}

variable "workstations" {
  description = "Windows browser boxes: name -> {spoke = which branch LAN, private_ip}. One browser box per entry — add entries to scale out."
  type = map(object({
    spoke      = string
    private_ip = string
  }))
  default = {
    "win-1" = { spoke = "spoke-1", private_ip = "10.200.10.150" } # behind BOR-1
    "win-2" = { spoke = "spoke-2", private_ip = "10.200.20.150" } # behind BOR-2
  }
}

variable "workstation_instance_type" {
  description = "EC2 type for the Windows workstations (x86_64 — Windows Server AMIs are x86). t3.medium (2 vCPU / 4 GiB) is comfortable for Edge; t3.small (2 GiB) is tight."
  type        = string
  default     = "t3.medium"
}

variable "workstation_ami_ssm_param" {
  description = "SSM public parameter for the Windows AMI. Default = latest Windows Server 2022 Full Base (x86_64) — ships Edge + RDP + SSM agent."
  type        = string
  default     = "/aws/service/ami-windows-latest/Windows_Server-2022-English-Full-Base"
}

variable "workstation_admin_password" {
  description = "Local Administrator password set on the Windows workstations for RDP-over-SSM. SET THIS IN terraform.tfvars (gitignored) — never in committed code. Must meet Windows complexity (upper/lower/digit/symbol, 8+). Lab credential; rotate for anything lasting."
  type        = string
  default     = ""
  sensitive   = true
}
