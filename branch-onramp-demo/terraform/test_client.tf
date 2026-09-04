# =============================================================================
# Per-LAN Linux test clients — CLIENTLESS SASE/BOR test endpoints.
# Opt-in (var.deploy_test_clients). No public IP; reachable via SSM Session Mgr.
#
# These simulate an unmanaged / IoT device behind the branch FortiGate: no
# FortiClient, relies entirely on the network path (FortiGate -> BOR on-ramp ->
# FortiSASE) for security + WAN connectivity.
#
# NOTE (AWS): EC2 clients get their IP from AWS VPC DHCP, NOT a FortiGate DHCP
# server. We assign STATIC ENI IPs (.100, .101, ...) — deterministic. The FGT is
# still the L3 gateway/enforcement point via the LAN route table default.
# =============================================================================

locals {
  # Any test host present (Linux clients OR Windows workstations) — the shared
  # IAM role + SSM endpoints must exist whenever either is deployed.
  any_test_hosts = var.deploy_test_clients || var.deploy_test_workstations

  # Fan out clients_per_lan clients per spoke; static IPs from .100 upward.
  test_clients = var.deploy_test_clients ? merge([
    for sk, s in var.spokes : {
      for i in range(var.clients_per_lan) :
      "${sk}-client-${i + 1}" => {
        spoke      = sk
        subnet_id  = aws_subnet.lan[sk].id
        private_ip = cidrhost(s.lan_cidr, 100 + i)
      }
    }
  ]...) : {}
}

# Reproducible AMI lookup — latest Amazon Linux 2023 arm64 (SSM agent baked in).
data "aws_ssm_parameter" "test_client_ami" {
  count = var.deploy_test_clients ? 1 : 0
  name  = var.test_client_ami_ssm_param
}

# ---- IAM: SSM Session Manager access (shared by Linux clients + Win workstations) ----
data "aws_iam_policy_document" "test_client_assume" {
  count = local.any_test_hosts ? 1 : 0
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "test_client" {
  count              = local.any_test_hosts ? 1 : 0
  name_prefix        = "${var.project_name}-testcli-"
  assume_role_policy = data.aws_iam_policy_document.test_client_assume[0].json
  tags               = var.tags
}

resource "aws_iam_role_policy_attachment" "test_client_ssm" {
  count      = local.any_test_hosts ? 1 : 0
  role       = aws_iam_role.test_client[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "test_client" {
  count       = local.any_test_hosts ? 1 : 0
  name_prefix = "${var.project_name}-testcli-"
  role        = aws_iam_role.test_client[0].name
}

# ---- Per-site client SG: enforce NO client-to-client bypass (Linux clients) ----
# Cross-site traffic transits the FGT -> BOR/SASE and arrives with the REMOTE
# client's real source IP (no SNAT on the private fabric), so we allow only the
# OTHER spokes' LAN CIDRs — deliberately NOT this spoke's own LAN. That denies
# same-subnet peer traffic. Fail-closed.
resource "aws_security_group" "test_client" {
  for_each    = var.deploy_test_clients ? var.spokes : {}
  name_prefix = "${var.project_name}-${each.key}-testcli-"
  description = "Test clients at ${each.key}: cross-site via FGT allowed, same-subnet peers denied"
  vpc_id      = aws_vpc.this.id

  dynamic "ingress" {
    for_each = { for ok, os in var.spokes : ok => os.lan_cidr if ok != each.key }
    content {
      from_port   = 0
      to_port     = 0
      protocol    = "-1"
      cidr_blocks = [ingress.value]
      description = "Cross-site from ${ingress.key} (via FGT to BOR/SASE)"
    }
  }

  # The site's FortiGate LAN interface (ICMP PMTUD, health checks).
  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["${cidrhost(each.value.lan_cidr, 10)}/32"]
    description = "FortiGate LAN interface (.10)"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All egress (routed via the FGT default route)"
  }
  tags = merge(var.tags, { Name = "${var.project_name}-${each.key}-testcli-sg" })
}

# ---- ENI (static IP in the LAN) + instance, per client ----
resource "aws_network_interface" "test_client" {
  for_each        = local.test_clients
  subnet_id       = each.value.subnet_id
  security_groups = [aws_security_group.test_client[each.value.spoke].id]
  private_ips     = [each.value.private_ip]
  tags            = merge(var.tags, { Name = "${var.project_name}-${each.key}-nic" })
}

resource "aws_instance" "test_client" {
  for_each             = local.test_clients
  ami                  = data.aws_ssm_parameter.test_client_ami[0].value
  instance_type        = var.test_client_instance_type
  iam_instance_profile = aws_iam_instance_profile.test_client[0].name
  key_name             = var.key_pair_name != "" ? var.key_pair_name : null

  network_interface {
    network_interface_id = aws_network_interface.test_client[each.key].id
    device_index         = 0
  }

  user_data = templatefile("${path.module}/test_client_userdata.tftpl", {
    hostname = each.key
  })

  tags = merge(var.tags, { Name = "${var.project_name}-${each.key}", Role = "test-client" })
}
