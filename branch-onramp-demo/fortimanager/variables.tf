# ---------- AWS placement ----------
variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "availability_zone" {
  description = "AZ for the FMG subnet. Match the spokes' AZ (they are all in us-east-1a)."
  type        = string
  default     = "us-east-1a"
}

variable "aws_profile" {
  description = "Named AWS CLI/SSO profile. Empty = default chain / AWS_PROFILE env. (Uncomment the line in versions.tf to use.)"
  type        = string
  default     = ""
}

# ---------- Shared VPC (deploy alongside the spokes) ----------
variable "spoke_vpc_tag" {
  description = "Name tag of the branch-onramp-demo VPC to deploy FMG INTO, so FGFM (541) reaches the spokes over the shared VPC. Looked up live — no hardcoded VPC ID."
  type        = string
  default     = "sase-spoke-vpc"
}

variable "fmg_subnet_cidr" {
  description = "Dedicated public management subnet for FMG, carved from the spoke VPC (10.200.0.0/16). Must not overlap the spoke subnets (10.200.{1,2,10,20}.0/24)."
  type        = string
  default     = "10.200.254.0/24"
}

# ---------- FortiManager image (reproducible lookup — NO hardcoded AMI) ----------
variable "fmg_version" {
  description = "FortiManager GA version. Resolved live from the Fortinet-owned AMI catalog (owner 679593333241). 7.6.7 aligns with the spokes' FortiOS 7.6.7."
  type        = string
  default     = "7.6.7"
}

# ---------- Sizing (give it enough — FMG is not a spoke) ----------
variable "instance_type" {
  description = "EC2 type for FMG. Default m5.xlarge (4 vCPU / 16 GiB) — the m5 family is NON-burstable (a management/DB server should not throttle on CPU credits like t3). Bump to m5.2xlarge (8 vCPU / 32 GiB) for many ADOMs/devices or heavy logging."
  type        = string
  default     = "m5.xlarge"
}

variable "root_volume_size" {
  description = "OS disk (GiB). FMG-VM root is small; keep 30+."
  type        = number
  default     = 30
}

variable "data_volume_size" {
  description = "Dedicated FMG database/log disk (GiB) on /dev/sdb. REQUIRED — FMG stores its DB + device logs here, formats it on first boot. 200 GiB is a comfortable PoC size."
  type        = number
  default     = 200
}

# ---------- Access ----------
variable "admin_cidr" {
  description = "CIDRs allowed to reach the FMG GUI (443) + SSH (22). Set to YOUR public IP/32 — don't leave 0.0.0.0/0."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "fgfm_cidrs" {
  description = "CIDRs allowed to reach FGFM (TCP 541) — the FortiGates that register to FMG. Defaults cover the shared VPC (AWS spokes) + the on-ramp overlay pool."
  type        = list(string)
  default     = ["10.200.0.0/16", "172.16.8.0/21"]
}

# ---------- Naming ----------
variable "project_name" {
  description = "Name prefix for all resources."
  type        = string
  default     = "sase-fmg"
}

variable "environment" {
  type    = string
  default = "poc"
}

variable "tags" {
  type    = map(string)
  default = { Project = "sase-branch-onramp-demo", Component = "fortimanager", ManagedBy = "terraform" }
}
