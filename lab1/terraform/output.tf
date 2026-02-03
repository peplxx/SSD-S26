output "instance_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.ubuntu.public_ip
}

output "ssh_command" {
  description = "SSH command to connect"
  value       = "ssh -i ../keys/key.pem ubuntu@${aws_instance.ubuntu.public_ip}"
}