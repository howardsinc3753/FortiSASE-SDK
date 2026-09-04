output "fortimanager" {
  description = "FMG access info."
  value = {
    public_ip    = aws_eip.fmg.public_ip
    private_ip   = aws_instance.fmg.private_ip
    admin_url    = "https://${aws_eip.fmg.public_ip}/"
    instance_id  = aws_instance.fmg.id
    instance_type = var.instance_type
    vpc_id       = data.aws_vpc.spoke.id
    mgmt_subnet  = var.fmg_subnet_cidr
  }
}

output "ssh" {
  description = "How to SSH in (private key is in Secrets Manager)."
  value = {
    command     = "ssh -i fmg-key.pem admin@${aws_eip.fmg.public_ip}"
    fetch_key   = "aws secretsmanager get-secret-value --secret-id ${aws_secretsmanager_secret.ssh_key.name} --query SecretString --output text > fmg-key.pem"
    key_secret  = aws_secretsmanager_secret.ssh_key.name
  }
}

output "fmg_ami" {
  description = "Resolved FortiManager AMI (proves the version lookup worked)."
  value       = { id = data.aws_ami.fortimanager.id, name = data.aws_ami.fortimanager.name }
}

output "first_login" {
  description = "FMG first-login reminder."
  value       = "Browse the admin_url; default user 'admin' with a blank password on first boot -> set a strong password. Then add the /dev/sdb data disk if not auto-detected (System Settings), register FortiFlex, and add the spokes."
}
