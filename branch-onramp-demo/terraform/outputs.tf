output "spokes" {
  description = "Per-spoke access info — public IP, admin URL, LAN subnet."
  value = {
    for k, s in var.spokes : k => {
      public_ip   = aws_eip.wan[k].public_ip
      admin_url   = "https://${aws_eip.wan[k].public_ip}:${var.admin_sport}/"
      ssh         = "ssh -i <your-key.pem> admin@${aws_eip.wan[k].public_ip}"
      lan_subnet  = s.lan_cidr
      lan_gateway = local.spoke_net[k].lan_ip
      instance_id = aws_instance.fgt[k].id
    }
  }
}

output "fortios_ami" {
  description = "Resolved FortiOS AMI (proves the version/arch lookup worked)."
  value       = { id = data.aws_ami.fortios.id, name = data.aws_ami.fortios.name }
}

output "test_clients" {
  description = "Per-LAN test clients: name -> {private_ip, instance_id, ssm_connect}."
  value = var.deploy_test_clients ? {
    for k, inst in aws_instance.test_client : k => {
      private_ip  = inst.private_ip
      instance_id = inst.id
      ssm_connect = "aws ssm start-session --target ${inst.id}${var.aws_profile != "" ? " --profile ${var.aws_profile}" : ""}"
    }
  } : {}
}

output "test_client_hints" {
  description = "How to drive the test clients once connected."
  value = var.deploy_test_clients ? join("\n", [
    "Connect:      aws ssm start-session --target <instance_id>   (see test_clients output)",
    "Site-to-site: iperf3 -c <peer-client-private-ip>             (every client runs iperf3 -s)",
    "SASE egress:  portal-check                                   (SSO captive-portal redirect + egress IP)",
    "Throughput:   dl-speed                                       (100 MB download via the BOR on-ramp)",
  ]) : ""
}

output "test_workstations" {
  description = "Windows browser boxes: name -> {private_ip, instance_id, rdp_via_ssm command}."
  value = var.deploy_test_workstations ? {
    for k, inst in aws_instance.workstation : k => {
      private_ip  = inst.private_ip
      instance_id = inst.id
      rdp_via_ssm = "aws ssm start-session --target ${inst.id} --document-name AWS-StartPortForwardingSession --parameters portNumber=3389,localPortNumber=13389${var.aws_profile != "" ? " --profile ${var.aws_profile}" : ""}"
    }
  } : {}
}

output "test_workstation_hints" {
  description = "How to reach a Windows workstation's desktop + browse through the branch."
  value = var.deploy_test_workstations ? join("\n", [
    "1. Port-forward RDP over SSM:  (see rdp_via_ssm in the test_workstations output)",
    "2. RDP to the tunnel:          mstsc /v:localhost:13389",
    "3. Log in:                     Administrator / <workstation_admin_password>",
    "4. Open Edge and browse        -> traffic egresses FGT -> BOR -> FortiSASE (SSO portal, web filtering)",
  ]) : ""
}
