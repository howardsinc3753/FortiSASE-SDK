# =============================================================================
# FortiSASE BOR — Site-4 DUAL-CIRCUIT (dual-ISP) test spoke on AWS
# =============================================================================
# ONE FortiGate VM with TWO WAN interfaces (port1/WAN1 + port2/WAN2), each with
# its own EIP = two simulated ISP circuits, plus a LAN (port3). This is the AWS
# underlay for testing the dual-WAN / 4-tunnel BOR design.
#
# Bootstrap only brings the box online + reachable on both EIPs (admin :10443).
# Paste the full dual-circuit BOR config (config generator -> "Dual ISP" baseline)
# afterwards.
#
#   1. cp terraform.tfvars.example terraform.tfvars   (key + admin pw + your IP)
#   2. terraform init && terraform apply
#   3. https://<wan1_eip>:10443   (admin / <admin_password>)
#
# Interface / IP map (matches the config generator Dual-ISP baseline for Site-4):
#   port1 (WAN1/ISP-A) 10.204.1.10/24  gw 10.204.1.1   EIP-A
#   port2 (WAN2/ISP-B) 10.204.2.10/24  gw 10.204.2.1   EIP-B
#   port3 (LAN)        10.204.10.10/24 (LAN gateway for clients)
# =============================================================================

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# =============================================================================
# VPC + NETWORKING
# =============================================================================

resource "aws_vpc" "site4" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = merge(var.tags, { Name = "${var.project_name}-vpc" })
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.site4.id
  tags   = merge(var.tags, { Name = "${var.project_name}-igw" })
}

# --- WAN subnets (public, one per circuit) + LAN subnet (private) ---

resource "aws_subnet" "wan1" {
  vpc_id            = aws_vpc.site4.id
  cidr_block        = var.wan1_subnet_cidr
  availability_zone = var.availability_zone
  tags              = merge(var.tags, { Name = "${var.project_name}-wan1-isp-a" })
}

resource "aws_subnet" "wan2" {
  vpc_id            = aws_vpc.site4.id
  cidr_block        = var.wan2_subnet_cidr
  availability_zone = var.availability_zone
  tags              = merge(var.tags, { Name = "${var.project_name}-wan2-isp-b" })
}

resource "aws_subnet" "lan" {
  vpc_id            = aws_vpc.site4.id
  cidr_block        = var.lan_subnet_cidr
  availability_zone = var.availability_zone
  tags              = merge(var.tags, { Name = "${var.project_name}-lan" })
}

# --- Route tables ---

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.site4.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
  tags = merge(var.tags, { Name = "${var.project_name}-public-rt" })
}

resource "aws_route_table_association" "wan1" {
  subnet_id      = aws_subnet.wan1.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "wan2" {
  subnet_id      = aws_subnet.wan2.id
  route_table_id = aws_route_table.public.id
}

# LAN clients default out through the FortiGate LAN ENI (not the IGW).
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.site4.id
  route {
    cidr_block           = "0.0.0.0/0"
    network_interface_id = aws_network_interface.lan.id
  }
  tags = merge(var.tags, { Name = "${var.project_name}-private-rt" })
}

resource "aws_route_table_association" "lan" {
  subnet_id      = aws_subnet.lan.id
  route_table_id = aws_route_table.private.id
}

# =============================================================================
# SECURITY GROUPS
# =============================================================================

resource "aws_security_group" "wan" {
  name_prefix = "${var.project_name}-wan-"
  description = "FortiGate WAN - IPsec, FGFM, admin (:10443)"
  vpc_id      = aws_vpc.site4.id

  ingress {
    from_port   = 10443
    to_port     = 10443
    protocol    = "tcp"
    cidr_blocks = [var.admin_cidr]
    description = "HTTPS admin (10443 - off 443 for IKE-over-TCP)"
  }
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.admin_cidr]
    description = "SSH admin"
  }
  ingress {
    from_port   = 500
    to_port     = 500
    protocol    = "udp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "IKE"
  }
  ingress {
    from_port   = 4500
    to_port     = 4500
    protocol    = "udp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "IPsec NAT-T"
  }
  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "50"
    cidr_blocks = ["0.0.0.0/0"]
    description = "ESP"
  }
  ingress {
    from_port   = 541
    to_port     = 541
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "FGFM (FortiCloud)"
  }
  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [var.vpc_cidr]
    description = "Intra-VPC"
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "${var.project_name}-wan-sg" })
}

resource "aws_security_group" "lan" {
  name_prefix = "${var.project_name}-lan-"
  description = "FortiGate LAN - internal traffic"
  vpc_id      = aws_vpc.site4.id

  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [var.vpc_cidr]
    description = "All internal"
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "${var.project_name}-lan-sg" })
}

# =============================================================================
# NETWORK INTERFACES  (device_index 0=port1, 1=port2, 2=port3)
# =============================================================================

resource "aws_network_interface" "wan1" {
  subnet_id         = aws_subnet.wan1.id
  security_groups   = [aws_security_group.wan.id]
  source_dest_check = false
  private_ips       = [var.fgt_wan1_ip]
  tags              = merge(var.tags, { Name = "${var.project_name}-port1-wan1" })
}

resource "aws_network_interface" "wan2" {
  subnet_id         = aws_subnet.wan2.id
  security_groups   = [aws_security_group.wan.id]
  source_dest_check = false
  private_ips       = [var.fgt_wan2_ip]
  tags              = merge(var.tags, { Name = "${var.project_name}-port2-wan2" })
}

resource "aws_network_interface" "lan" {
  subnet_id         = aws_subnet.lan.id
  security_groups   = [aws_security_group.lan.id]
  source_dest_check = false
  private_ips       = [var.fgt_lan_ip]
  tags              = merge(var.tags, { Name = "${var.project_name}-port3-lan" })
}

# =============================================================================
# ELASTIC IPs  (two circuits = two public IPs)
# =============================================================================

resource "aws_eip" "wan1" {
  domain = "vpc"
  tags   = merge(var.tags, { Name = "${var.project_name}-wan1-eip-a" })
}

resource "aws_eip" "wan2" {
  domain = "vpc"
  tags   = merge(var.tags, { Name = "${var.project_name}-wan2-eip-b" })
}

resource "aws_eip_association" "wan1" {
  allocation_id        = aws_eip.wan1.id
  network_interface_id = aws_network_interface.wan1.id
}

resource "aws_eip_association" "wan2" {
  allocation_id        = aws_eip.wan2.id
  network_interface_id = aws_network_interface.wan2.id
}

# =============================================================================
# FORTIGATE INSTANCE  (Site-4 dual-circuit spoke)
# =============================================================================

resource "aws_instance" "fgt" {
  ami           = var.fortios_ami
  instance_type = var.instance_type
  key_name      = var.key_pair_name

  network_interface {
    network_interface_id = aws_network_interface.wan1.id
    device_index         = 0
  }
  network_interface {
    network_interface_id = aws_network_interface.wan2.id
    device_index         = 1
  }
  network_interface {
    network_interface_id = aws_network_interface.lan.id
    device_index         = 2
  }

  user_data = templatefile("${path.module}/bootstrap_fgt_dual.tftpl", {
    hostname       = var.hostname
    admin_password = var.admin_password
    wan1_ip        = var.fgt_wan1_ip
    wan1_mask      = "255.255.255.0"
    wan1_gw        = cidrhost(var.wan1_subnet_cidr, 1)
    wan2_ip        = var.fgt_wan2_ip
    wan2_mask      = "255.255.255.0"
    wan2_gw        = cidrhost(var.wan2_subnet_cidr, 1)
    lan_ip         = var.fgt_lan_ip
    lan_mask       = "255.255.255.0"
  })

  tags = merge(var.tags, { Name = "${var.project_name}-${var.hostname}" })
}
