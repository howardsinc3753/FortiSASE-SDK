# =============================================================================
# SSM VPC interface endpoints — reach the private test clients via Session
# Manager WITHOUT egressing through the FortiGate/SASE. This keeps the
# MANAGEMENT plane working even while the SASE captive portal is blocking the
# DATA plane (otherwise: to reach the box you'd need egress, but egress needs
# the portal satisfied, which needs the box — a catch-22).
#
# SSM traffic (client -> endpoint) stays on the VPC-local route, never touching
# the FortiGate, so "reach the box" is decoupled from "the path under test".
#
# Gated on deploy_test_clients + enable_ssm_endpoints.
# NOTE: interface endpoints bill (~$0.01/hr each x3) even while EC2 is stopped.
# =============================================================================

locals {
  ssm_endpoints_on   = local.any_test_hosts && var.enable_ssm_endpoints
  ssm_services       = ["ssm", "ssmmessages", "ec2messages"]
  endpoint_subnet_id = local.ssm_endpoints_on ? aws_subnet.mgmt[0].id : null
}

# Dedicated management subnet for the SSM endpoints — kept OUT of the spoke LANs
# so the east-west no-bypass routes never redirect SSM/RDP onto the FGT/SASE
# fabric. Management stays direct + out-of-band even with site-to-site on.
resource "aws_subnet" "mgmt" {
  count             = local.ssm_endpoints_on ? 1 : 0
  vpc_id            = aws_vpc.this.id
  cidr_block        = var.mgmt_subnet_cidr
  availability_zone = var.availability_zone
  tags              = merge(var.tags, { Name = "${var.project_name}-mgmt" })
}

resource "aws_security_group" "ssm_endpoints" {
  count       = local.ssm_endpoints_on ? 1 : 0
  name_prefix = "${var.project_name}-ssm-vpce-"
  description = "SSM interface endpoints: 443 from within the VPC"
  vpc_id      = aws_vpc.this.id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
    description = "HTTPS from VPC (SSM agent on the test clients)"
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = merge(var.tags, { Name = "${var.project_name}-ssm-vpce-sg" })
}

resource "aws_vpc_endpoint" "ssm" {
  for_each = local.ssm_endpoints_on ? toset(local.ssm_services) : []

  vpc_id              = aws_vpc.this.id
  service_name        = "com.amazonaws.${var.aws_region}.${each.value}"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [local.endpoint_subnet_id]
  security_group_ids  = [aws_security_group.ssm_endpoints[0].id]
  private_dns_enabled = true
  tags                = merge(var.tags, { Name = "${var.project_name}-vpce-${each.value}" })
}
