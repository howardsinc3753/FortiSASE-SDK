# =============================================================================
# Site-4 dual-circuit spoke - variables
# Copy terraform.tfvars.example -> terraform.tfvars and set your values.
# =============================================================================

# --- REQUIRED ---

variable "key_pair_name" {
  description = "Name of an existing EC2 key pair for SSH access"
  type        = string
}

variable "admin_password" {
  description = "FortiGate admin password (min 8 chars). Match the config generator (POC: FortiSASE-OnRamp-2026!)."
  type        = string
  sensitive   = true
}

# --- RECOMMENDED ---

variable "admin_cidr" {
  description = "CIDR allowed for admin (:10443 / SSH). Find yours: curl ifconfig.me -> x.x.x.x/32"
  type        = string
  default     = "0.0.0.0/0"
}

# --- OPTIONAL ---

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "availability_zone" {
  description = "AZ (all three subnets share one AZ = simpler/cheaper for a lab)"
  type        = string
  default     = "us-east-1a"
}

variable "fortios_ami" {
  description = "FortiGate BYOL ARM64 AMI (default = 7.6.6 us-east-1; override for 7.6.7 or another region)"
  type        = string
  default     = "ami-0b7030b7e5c00882e"
}

variable "instance_type" {
  description = "EC2 instance type (t4g.small = cheapest ARM64 for FortiGate)"
  type        = string
  default     = "t4g.small"
}

variable "project_name" {
  description = "Name prefix for all resources"
  type        = string
  default     = "bor-site4-dual"
}

variable "hostname" {
  description = "FortiGate hostname (matches the config generator Site-4 baseline)"
  type        = string
  default     = "spoke-4"
}

# --- NETWORK (defaults align with the config generator Dual-ISP Site-4 baseline) ---

variable "vpc_cidr" {
  description = "VPC CIDR"
  type        = string
  default     = "10.204.0.0/16"
}

variable "wan1_subnet_cidr" {
  description = "WAN1 / ISP-A subnet (port1)"
  type        = string
  default     = "10.204.1.0/24"
}

variable "wan2_subnet_cidr" {
  description = "WAN2 / ISP-B subnet (port2)"
  type        = string
  default     = "10.204.2.0/24"
}

variable "lan_subnet_cidr" {
  description = "LAN subnet (port3)"
  type        = string
  default     = "10.204.10.0/24"
}

variable "fgt_wan1_ip" {
  description = "FortiGate port1 (WAN1) private IP - must sit inside wan1_subnet_cidr"
  type        = string
  default     = "10.204.1.10"
}

variable "fgt_wan2_ip" {
  description = "FortiGate port2 (WAN2) private IP - must sit inside wan2_subnet_cidr"
  type        = string
  default     = "10.204.2.10"
}

variable "fgt_lan_ip" {
  description = "FortiGate port3 (LAN) private IP = LAN gateway for clients"
  type        = string
  default     = "10.204.10.10"
}

variable "tags" {
  description = "Tags applied to all resources"
  type        = map(string)
  default = {
    Project     = "FortiSASE-BOR"
    Environment = "lab"
    Site        = "site-4-dual-circuit"
    ManagedBy   = "terraform"
  }
}
