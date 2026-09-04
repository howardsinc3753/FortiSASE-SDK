output "wan1_eip" {
  description = "Public IP of circuit A (port1 / WAN1) - admin here"
  value       = aws_eip.wan1.public_ip
}

output "wan2_eip" {
  description = "Public IP of circuit B (port2 / WAN2)"
  value       = aws_eip.wan2.public_ip
}

output "admin_url" {
  description = "FortiGate admin GUI (circuit A)"
  value       = "https://${aws_eip.wan1.public_ip}:10443"
}

output "admin_url_wan2" {
  description = "FortiGate admin GUI (circuit B - use if WAN1 is the one you're testing failover on)"
  value       = "https://${aws_eip.wan2.public_ip}:10443"
}

output "ssh" {
  description = "SSH to the FortiGate CLI (circuit A)"
  value       = "ssh -i <your_key.pem> admin@${aws_eip.wan1.public_ip}"
}

output "fgt_interface_map" {
  description = "port -> role / IP / gateway (paste-ready reference for the config generator)"
  value = {
    port1_wan1 = "${var.fgt_wan1_ip}/24  gw ${cidrhost(var.wan1_subnet_cidr, 1)}  (EIP ${aws_eip.wan1.public_ip})"
    port2_wan2 = "${var.fgt_wan2_ip}/24  gw ${cidrhost(var.wan2_subnet_cidr, 1)}  (EIP ${aws_eip.wan2.public_ip})"
    port3_lan  = "${var.fgt_lan_ip}/24  (LAN gateway for clients)"
  }
}

output "instance_id" {
  description = "EC2 instance ID (for SSM / console)"
  value       = aws_instance.fgt.id
}
