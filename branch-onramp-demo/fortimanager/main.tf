# =============================================================================
# Self-hosted FortiManager (AWS) for the Branch On-Ramp demo.
# Deploys INTO the existing spoke VPC (looked up by tag) so FGFM reaches the
# spokes over the shared VPC. Reproducible: AMI + VPC + IGW are all looked up
# live — no hardcoded IDs.
# =============================================================================

locals {
  # BYOL image: "FortiManager-VM64-AWS build* (<ver>) GA-*". The literal " build"
  # after "-AWS" excludes the PAYG "-AWSONDEMAND" images. (FMG-VM is x86_64 only.)
  ami_name = "FortiManager-VM64-AWS build* (${var.fmg_version}) GA-*"
}

# ---- Look up the shared spoke VPC + its IGW (deployed by ../terraform) ----
data "aws_vpc" "spoke" {
  filter {
    name   = "tag:Name"
    values = [var.spoke_vpc_tag]
  }
}

data "aws_internet_gateway" "spoke" {
  filter {
    name   = "attachment.vpc-id"
    values = [data.aws_vpc.spoke.id]
  }
}

# ---- Reproducible FMG AMI lookup — owner 679593333241 = Fortinet ----
data "aws_ami" "fortimanager" {
  most_recent = true
  owners      = ["679593333241"]

  filter {
    name   = "name"
    values = [local.ami_name]
  }
  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# =============================================================================
# Dedicated public management subnet for FMG (in the shared VPC)
# =============================================================================
resource "aws_subnet" "fmg" {
  vpc_id                  = data.aws_vpc.spoke.id
  cidr_block              = var.fmg_subnet_cidr
  availability_zone       = var.availability_zone
  map_public_ip_on_launch = false
  tags                    = merge(var.tags, { Name = "${var.project_name}-mgmt-subnet" })
}

resource "aws_route_table" "fmg" {
  vpc_id = data.aws_vpc.spoke.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = data.aws_internet_gateway.spoke.id
  }
  tags = merge(var.tags, { Name = "${var.project_name}-mgmt-rt" })
}

resource "aws_route_table_association" "fmg" {
  subnet_id      = aws_subnet.fmg.id
  route_table_id = aws_route_table.fmg.id
}

# =============================================================================
# SSH key -> Secrets Manager (private key never leaves AWS)
# =============================================================================
resource "tls_private_key" "fmg" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "fmg" {
  key_name   = "${var.project_name}-key-${var.environment}"
  public_key = tls_private_key.fmg.public_key_openssh
  tags       = merge(var.tags, { Name = "${var.project_name}-ssh-key" })
}

resource "aws_secretsmanager_secret" "ssh_key" {
  name        = "${var.project_name}-ssh-key-${var.environment}"
  description = "SSH private key for the Branch On-Ramp FortiManager"
  tags        = var.tags
}

resource "aws_secretsmanager_secret_version" "ssh_key" {
  secret_id     = aws_secretsmanager_secret.ssh_key.id
  secret_string = tls_private_key.fmg.private_key_pem
}

# =============================================================================
# Security group
# =============================================================================
resource "aws_security_group" "fmg" {
  name_prefix = "${var.project_name}-"
  description = "FortiManager: admin GUI/SSH + FGFM device tunnel"
  vpc_id      = data.aws_vpc.spoke.id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = var.admin_cidr
    description = "HTTPS admin GUI"
  }
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.admin_cidr
    description = "SSH admin"
  }
  ingress {
    from_port   = 541
    to_port     = 541
    protocol    = "tcp"
    cidr_blocks = var.fgfm_cidrs
    description = "FGFM - FortiGate management tunnel"
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound (FortiGuard, updates, device mgmt)"
  }
  tags = merge(var.tags, { Name = "${var.project_name}-sg" })
}

# =============================================================================
# FortiManager instance + EIP
# =============================================================================
resource "aws_instance" "fmg" {
  ami                         = data.aws_ami.fortimanager.id
  instance_type               = var.instance_type
  key_name                    = aws_key_pair.fmg.key_name
  subnet_id                   = aws_subnet.fmg.id
  vpc_security_group_ids      = [aws_security_group.fmg.id]
  associate_public_ip_address = true

  root_block_device {
    volume_type = "gp3"
    volume_size = var.root_volume_size
    encrypted   = true
    tags        = merge(var.tags, { Name = "${var.project_name}-root" })
  }

  # REQUIRED data disk — FMG database + device logs. Formatted by FMG on first boot.
  ebs_block_device {
    device_name = "/dev/sdb"
    volume_type = "gp3"
    volume_size = var.data_volume_size
    encrypted   = true
    tags        = merge(var.tags, { Name = "${var.project_name}-data" })
  }

  tags = merge(var.tags, { Name = "${var.project_name}-${var.environment}", Type = "Management" })
}

resource "aws_eip" "fmg" {
  domain   = "vpc"
  instance = aws_instance.fmg.id
  tags     = merge(var.tags, { Name = "${var.project_name}-eip" })
}
