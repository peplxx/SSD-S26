# https://developer.hashicorp.com/terraform/tutorials/aws-get-started/aws-create

provider "aws" {
  region = "us-east-1"
}

data "aws_ami" "ubuntu" {
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  owners = ["099720109477"]
}
resource "aws_security_group" "security_group" {
  name        = "instance-security-group"
  description = "Allow SSH, HTTP, and HTTPS"

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress {
    description = "Gitea"
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Gitea"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
resource "aws_key_pair" "deployer" {
  key_name   = "vockey"
  public_key = file("../keys/key.pub")
}

resource "aws_instance" "ubuntu" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type

  key_name      = aws_key_pair.deployer.key_name

  vpc_security_group_ids = [aws_security_group.security_group.id]

  root_block_device {
    volume_size = 16
  }

  tags = {
    Name = var.instance_name
  }
}
