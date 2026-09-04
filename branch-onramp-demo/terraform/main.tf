# =============================================================================
# Branch On-Ramp Demo — N FortiOS spoke VMs on AWS (default 2)
# Each spoke: public WAN subnet + EIP (port1), unique private LAN subnet (port2).
# =============================================================================

locals {
  # BYOL image names: "FortiGate-VMARM64-AWS build* (<ver>) GA-*" (arm64) or
  # "FortiGate-VM64-AWS build* (<ver>) GA-*" (x86_64). The literal " build" after
  # "-AWS" excludes the PAYG "-AWSONDEMAND" images.
  ami_name = var.architecture == "arm64" ? "FortiGate-VMARM64-AWS build* (${var.fortios_version}) GA-*" : "FortiGate-VM64-AWS build* (${var.fortios_version}) GA-*"

  # Management-return route: pin the trusted admin/management source out the WAN
  # (port1) so admin access survives the FortiSASE on-ramp injecting a default route
  # into the IPsec tunnel. A longest-prefix /32 (or subnet) beats the injected 0.0.0.0/0.
  # Defaults to admin_cidr; override per-partner via mgmt_return_cidr. Skipped when it
  # resolves to 0.0.0.0/0 (that IS the default — nothing to pin).
  mgmt_return_cidr   = var.mgmt_return_cidr != "" ? var.mgmt_return_cidr : var.admin_cidr
  mgmt_route_enabled = local.mgmt_return_cidr != "0.0.0.0/0"
  mgmt_route_dst     = local.mgmt_route_enabled ? cidrhost(local.mgmt_return_cidr, 0) : "0.0.0.0"
  mgmt_route_mask    = local.mgmt_route_enabled ? cidrnetmask(local.mgmt_return_cidr) : "0.0.0.0"

  # Per-spoke derived addressing: FortiGate takes .10 in each subnet, gateway is .1.
  spoke_net = {
    for k, s in var.spokes : k => {
      wan_ip   = cidrhost(s.wan_cidr, 10)
      wan_gw   = cidrhost(s.wan_cidr, 1)
      wan_mask = cidrnetmask(s.wan_cidr)
      lan_ip   = cidrhost(s.lan_cidr, 10)
      lan_mask = cidrnetmask(s.lan_cidr)
    }
  }
}

# Reproducible AMI lookup — owner 679593333241 = Fortinet.
data "aws_ami" "fortios" {
  most_recent = true
  owners      = ["679593333241"]

  filter {
    name   = "name"
    values = [local.ami_name]
  }
  filter {
    name   = "architecture"
    values = [var.architecture]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# =============================================================================
# VPC + networking
# =============================================================================
resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = merge(var.tags, { Name = "${var.project_name}-vpc" })
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.this.id
  tags   = merge(var.tags, { Name = "${var.project_name}-igw" })
}

# WAN (public) + LAN (private, unique CIDR) subnets — one of each per spoke
resource "aws_subnet" "wan" {
  for_each          = var.spokes
  vpc_id            = aws_vpc.this.id
  cidr_block        = each.value.wan_cidr
  availability_zone = var.availability_zone
  tags              = merge(var.tags, { Name = "${var.project_name}-${each.key}-wan" })
}

resource "aws_subnet" "lan" {
  for_each          = var.spokes
  vpc_id            = aws_vpc.this.id
  cidr_block        = each.value.lan_cidr
  availability_zone = var.availability_zone
  tags              = merge(var.tags, { Name = "${var.project_name}-${each.key}-lan" })
}

# Public route table (shared) -> IGW
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
  tags = merge(var.tags, { Name = "${var.project_name}-public-rt" })
}

resource "aws_route_table_association" "wan" {
  for_each       = var.spokes
  subnet_id      = aws_subnet.wan[each.key].id
  route_table_id = aws_route_table.public.id
}

# Per-spoke private route table -> default route through that spoke's LAN ENI
resource "aws_route_table" "lan" {
  for_each = var.spokes
  vpc_id   = aws_vpc.this.id
  route {
    cidr_block           = "0.0.0.0/0"
    network_interface_id = aws_network_interface.lan[each.key].id
  }

  # Force EAST-WEST (site-to-site) traffic through this spoke's FGT so it transits
  # the SASE/SPA fabric instead of the AWS VPC-local shortcut. AWS honors routes
  # MORE SPECIFIC than the VPC local route pointing at an ENI, so each spoke's LAN
  # routes every OTHER spoke's LAN /24 at its own FortiGate.
  # SCOPED to deploy_test_clients: with no clients there is nothing in the LAN to
  # bypass, so these routes are NOT added — a base apply leaves the live route
  # tables untouched (terraform plan => no changes). They come in only alongside
  # the clients, and only while route_intersite_via_fgt is true (the enforced
  # default; flip false to demo the direct AWS path).
  dynamic "route" {
    for_each = (var.deploy_test_clients && var.route_intersite_via_fgt) ? {
      for ok, os in var.spokes : ok => os.lan_cidr if ok != each.key
    } : {}
    content {
      cidr_block           = route.value
      network_interface_id = aws_network_interface.lan[each.key].id
    }
  }

  tags = merge(var.tags, { Name = "${var.project_name}-${each.key}-lan-rt" })
}

resource "aws_route_table_association" "lan" {
  for_each       = var.spokes
  subnet_id      = aws_subnet.lan[each.key].id
  route_table_id = aws_route_table.lan[each.key].id
}

# =============================================================================
# Security groups
# =============================================================================
resource "aws_security_group" "wan" {
  name_prefix = "${var.project_name}-wan-"
  description = "FortiGate WAN: admin + IPsec on-ramp"
  vpc_id      = aws_vpc.this.id

  ingress {
    from_port   = var.admin_sport
    to_port     = var.admin_sport
    protocol    = "tcp"
    cidr_blocks = concat([var.admin_cidr], var.extra_admin_cidrs)
    description = "HTTPS admin GUI (moved off 443 to free it for IKE-over-TCP)"
  }
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = concat([var.admin_cidr], var.extra_admin_cidrs)
    description = "SSH admin"
  }
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "IKE-over-TCP (RFC 8229) to/from the FortiSASE on-ramp"
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
  description = "FortiGate LAN: internal traffic"
  vpc_id      = aws_vpc.this.id

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
# Interfaces, EIPs, instances (per spoke)
# =============================================================================
resource "aws_network_interface" "wan" {
  for_each          = var.spokes
  subnet_id         = aws_subnet.wan[each.key].id
  security_groups   = [aws_security_group.wan.id]
  source_dest_check = false
  private_ips       = [local.spoke_net[each.key].wan_ip]
  tags              = merge(var.tags, { Name = "${var.project_name}-${each.key}-wan-nic" })
}

resource "aws_network_interface" "lan" {
  for_each          = var.spokes
  subnet_id         = aws_subnet.lan[each.key].id
  security_groups   = [aws_security_group.lan.id]
  source_dest_check = false
  private_ips       = [local.spoke_net[each.key].lan_ip]
  tags              = merge(var.tags, { Name = "${var.project_name}-${each.key}-lan-nic" })
}

resource "aws_eip" "wan" {
  for_each = var.spokes
  domain   = "vpc"
  tags     = merge(var.tags, { Name = "${var.project_name}-${each.key}-eip" })
}

resource "aws_eip_association" "wan" {
  for_each             = var.spokes
  allocation_id        = aws_eip.wan[each.key].id
  network_interface_id = aws_network_interface.wan[each.key].id
}

resource "aws_instance" "fgt" {
  for_each      = var.spokes
  ami           = data.aws_ami.fortios.id
  instance_type = var.instance_type
  key_name      = var.key_pair_name != "" ? var.key_pair_name : null

  network_interface {
    network_interface_id = aws_network_interface.wan[each.key].id
    device_index         = 0
  }
  network_interface {
    network_interface_id = aws_network_interface.lan[each.key].id
    device_index         = 1
  }

  user_data = templatefile("${path.module}/bootstrap_fgt.tftpl", {
    hostname       = each.key
    admin_password = var.admin_password
    admin_sport    = var.admin_sport
    wan_ip         = local.spoke_net[each.key].wan_ip
    wan_mask       = local.spoke_net[each.key].wan_mask
    wan_gw         = local.spoke_net[each.key].wan_gw
    lan_ip         = local.spoke_net[each.key].lan_ip
    lan_mask       = local.spoke_net[each.key].lan_mask
    flex_token     = lookup(var.flex_tokens, each.key, "")

    mgmt_route_enabled = local.mgmt_route_enabled
    mgmt_route_dst     = local.mgmt_route_dst
    mgmt_route_mask    = local.mgmt_route_mask
  })

  tags = merge(var.tags, { Name = "${var.project_name}-${each.key}" })

  lifecycle {
    # Bootstrap runs only at first boot; don't churn (stop/start) live FGTs when the
    # template changes. New instances still get the current bootstrap at creation.
    ignore_changes = [user_data]
  }
}
