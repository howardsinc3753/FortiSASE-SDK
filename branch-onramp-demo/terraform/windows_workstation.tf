# =============================================================================
# Windows browser workstations — test a real web browser THROUGH the branch
# on-ramp. Opt-in (var.deploy_test_workstations). No public IP.
#
# Each box sits in a branch LAN, so its default route is the FortiGate -> the
# browser's traffic egresses FGT -> BOR on-ramp -> FortiSASE (SIA + captive
# portal). Reached by RDP tunneled over SSM (AWS-StartPortForwardingSession) —
# no inbound rule, no public IP. Windows Server ships Edge + RDP + the SSM agent,
# so there's nothing to install.
# =============================================================================

locals {
  workstations = var.deploy_test_workstations ? var.workstations : {}
}

# Reproducible AMI lookup — latest Windows Server 2022 Full Base (x86_64).
data "aws_ssm_parameter" "workstation_ami" {
  count = var.deploy_test_workstations ? 1 : 0
  name  = var.workstation_ami_ssm_param
}

# Egress-only SG: RDP arrives via the SSM agent (outbound channel), so no inbound
# rule is needed. Stateful returns for the browser's own sessions are auto-allowed.
resource "aws_security_group" "workstation" {
  count       = var.deploy_test_workstations ? 1 : 0
  name_prefix = "${var.project_name}-winws-"
  description = "Windows browser workstations: egress only (RDP via SSM, no inbound)"
  vpc_id      = aws_vpc.this.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All egress (browser via the FGT default route; SSM to endpoints)"
  }
  tags = merge(var.tags, { Name = "${var.project_name}-winws-sg" })
}

resource "aws_network_interface" "workstation" {
  for_each        = local.workstations
  subnet_id       = aws_subnet.lan[each.value.spoke].id
  security_groups = [aws_security_group.workstation[0].id]
  private_ips     = [each.value.private_ip]
  tags            = merge(var.tags, { Name = "${var.project_name}-${each.key}-nic" })
}

resource "aws_instance" "workstation" {
  for_each             = local.workstations
  ami                  = data.aws_ssm_parameter.workstation_ami[0].value
  instance_type        = var.workstation_instance_type
  iam_instance_profile = aws_iam_instance_profile.test_client[0].name

  network_interface {
    network_interface_id = aws_network_interface.workstation[each.key].id
    device_index         = 0
  }

  user_data = templatefile("${path.module}/workstation_userdata.ps1.tftpl", {
    admin_password = var.workstation_admin_password
  })

  tags = merge(var.tags, { Name = "${var.project_name}-${each.key}", Role = "win-workstation" })
}
