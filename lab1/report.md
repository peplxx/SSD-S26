# SSD Lab 1: Infrastructure Provisioning, Application Deployment & SAST

## General

**Lab:** SSD-S26 Lab 1  

**Student:** Melnikov Sergei (s.melnikov@innopolis.university)

**Full Video Report [4min on 2x speed]:** [yandex-disk](https://disk.yandex.ru/i/PVEYmPs4jPCPcQ) 

**Sources (Pushed after deadline):** [github](https://github.com/peplxx/SSD-S26)


## Table of Contents
1. [Lab Summary](#lab-summary)
2. [Task 1: Infrastructure Provisioning with Terraform](#task-1-infrastructure-provisioning-with-terraform)
4. [Task 2: Application Deployment](#task-2-application-deployment)
5. [Task 3: Static Application Security Testing](#task-3-static-application-security-testing)

---

## Lab Summary

**Task 1: Infrastructure Provisioning**
- Automated AWS EC2 provisioning using Terraform IaC
- Created reproducible infrastructure: Ubuntu 24.04 t2.large instance with security groups
- Achieved single-command deployment replacing 15-minute manual process

**Task 2: Application Deployment**
- Deployed self-hosted Gitea + Drone CI/CD platform using Docker Compose
- Configured automatic HTTPS with Caddy reverse proxy and Let's Encrypt certificates
- Integrated DuckDNS for stable domain names on dynamic IP infrastructure
- Established OAuth-based authentication between services

**Task 3: Security Testing Integration**
- Integrated Semgrep SAST into CI/CD pipeline for automated vulnerability detection
- Successfully identified SQL injection vulnerability (CWE-89) in sample application
- Implemented fail-fast security gates using OWASP Top 10 ruleset
- Demonstrated shift-left security principles with sub-minute scan feedback

### Technologies Utilized
- **Infrastructure**: Terraform, AWS (EC2, Security Groups, Key Pairs)
- **Containerization**: Docker, Docker Compose
- **CI/CD**: Gitea, Drone CI with Docker runner
- **Security**: Semgrep SAST, OWASP Top 10 rulesets
- **Networking**: Caddy (reverse proxy), DuckDNS (dynamic DNS)

---

## Task 1: Infrastructure Provisioning with Terraform

### Detailed Terraform Setup
```
lab1/terraform
├── main.tf
├── output.tf
├── terraform.tf
└── variables.tf
```

#### Components

##### 1. Provider Configuration (`terraform.tf`)
```hcl
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.30.0" }
  }
  required_version = ">= 1.2"
}

provider "aws" {
  region = "us-east-1"
}
```

##### 2. Security Group (Firewall Rules) (`main.tf`)
```hcl
resource "aws_security_group" "security_group" {
  name = "instance-security-group"
  
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
```

**Rules:** SSH, HTTP, HTTPS ingress | All egress allowed

##### 3. SSH Key Pair (`main.tf`)
> Public key generated from original .pem file
```hcl
resource "aws_key_pair" "deployer" {
  key_name   = "vockey"
  public_key = file("../keys/key.pub")
}
```

##### 4. Variables (`variables.tf`)
```hcl
variable "instance_name" {
  type    = string
  default = "ubuntu"
}

variable "instance_type" {
  type    = string
  default = "t2.large"  # Sufficient for Gitea + Drone + apps
}
```

#### 5. EC2 Instance (`main.tf`)
```hcl
data "aws_ami" "ubuntu" {
  most_recent = true
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }
  owners = ["099720109477"]
}

resource "aws_instance" "ubuntu" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type  # t2.large
  key_name               = aws_key_pair.deployer.key_name
  vpc_security_group_ids = [aws_security_group.security_group.id]
  
  root_block_device {
    volume_size = 16
  }
  
  tags = {
    Name = var.instance_name  # ubuntu
  }
}
```


##### 6. Outputs (`output.tf`)
```hcl
output "instance_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.ubuntu.public_ip
}

output "ssh_command" {
  description = "SSH command to connect"
  value       = "ssh -i ../keys/key.pem ubuntu@${aws_instance.ubuntu.public_ip}"
}
```

### Deployment Process

```bash
# Initialize Terraform
cd lab1/terraform
terraform init

# Review planned changes
terraform plan

# Apply infrastructure
terraform apply -auto-approve

# Outputs:
# instance_public_ip = "xx.xx.xx.xx"
# ssh_command = "ssh -i ../keys/key.pem ubuntu@xx.xx.xx.xx"
```

### Results

**Benefits of IaC Approach:**

- [+] **Reproducibility**: Same infrastructure every time
- [+] **Version Control**: Infrastructure changes tracked in Git
- [+] **Documentation**: Code serves as infrastructure documentation
- [+] **Automation**: Single command deployment
- [+] **Consistency**: Eliminates manual configuration errors

---

## Task 2: Application Deployment

### Reverse Proxy Schema
```
Internet
    ↓
Caddy (Reverse Proxy)
    ├─→ my-gitea.duckdns.org → Gitea:3000
    └─→ my-drone.duckdns.org → Drone:80
                                    ↓
                              Drone Runner
```
### Services Overview

1. **Caddy - Reverse Proxy**
   ```yaml
   # docker-compose.yaml
   caddy:
     image: caddy:latest
     ports:
       - "80:80"
       - "443:443"
     volumes:
       - ./Caddyfile:/etc/caddy/Caddyfile
       - caddy_data:/data
       - caddy_config:/config
   ```

    ```caddyfile
    # Caddyfile
    my-gitea.duckdns.org {
    reverse_proxy gitea:3000
    }

    my-drone.duckdns.org {
    reverse_proxy drone:80
    }
    ```

2. **Gitea - Git Server**
   ```yaml
   # docker-compose.yaml
   gitea:
     image: gitea/gitea:latest
     environment:
       - GITEA__server__ROOT_URL=${GITEA__server__ROOT_URL}
       - GITEA__server__DOMAIN=${GITEA__server__DOMAIN}
       - GITEA__server__HTTP_PORT=3000
     volumes:
       - gitea_data:/data
   ```

3. **Drone - CI/CD Server**
   ```yaml
   # docker-compose.yaml
   drone:
     image: drone/drone:latest
     environment:
       - DRONE_GITEA_SERVER=${DRONE_GITEA_SERVER}
       - DRONE_GITEA_CLIENT_ID=${GITEA_CLIENT_ID}
       - DRONE_GITEA_CLIENT_SECRET=${GITEA_CLIENT_SECRET}
       - DRONE_RPC_SECRET=${DRONE_RPC_SECRET}
       - DRONE_SERVER_HOST=${DRONE_SERVER_HOST}
       - DRONE_SERVER_PROTO=https
       - DRONE_USER_CREATE=username:${DRONE_ADMIN},admin:true
     volumes:
       - drone_data:/data
     depends_on:
       - gitea
   ```
4. **Drone Runner - Pipeline Executor**
   ```yaml
   # docker-compose.yaml
   drone-runner:
     image: drone/drone-runner-docker:latest
     environment:
       - DRONE_RPC_PROTO=http
       - DRONE_RPC_HOST=drone
       - DRONE_RPC_SECRET=${DRONE_RPC_SECRET}
       - DRONE_RUNNER_CAPACITY=2
     volumes:
       - /var/run/docker.sock:/var/run/docker.sock
     depends_on:
       - drone
   ```

#### 2.Dynamic DNS Setup

**DuckDNS Configuration:**
1. Register account at duckdns.org
2. Create subdomains: `my-gitea`, `my-drone` using public Ip address of machine

### Deployment Steps

```bash
# 1. Configure environment variables
cat > .env << EOF
GITEA__server__ROOT_URL=https://my-gitea.duckdns.org
GITEA__server__DOMAIN=my-gitea.duckdns.org
DRONE_GITEA_SERVER=https://my-gitea.duckdns.org
DRONE_SERVER_HOST=my-drone.duckdns.org
DRONE_RPC_SECRET=$(openssl rand -hex 16)
DRONE_ADMIN=your-username
EOF

# 2. Start services
docker compose up -d

# 3. Check service status
docker compose ps

# 4. View logs
docker compose logs -f
```

### Post-Deployment Configuration

**Gitea OAuth Application Setup:**
1. Access Gitea at `https://my-gitea.duckdns.org`
2. Navigate to Settings → Applications → Manage OAuth2 Applications
3. Create new OAuth2 application:
   - Application Name: `Drone CI`
   - Redirect URI: `https://my-drone.duckdns.org/login`
4. Copy Client ID and Client Secret to `.env` file
5. Restart Drone service: `docker compose restart drone`

### Drone Test Pipeline

```yaml
kind: pipeline
type: docker
name: default

steps:
  - name: test
    image: alpine
    commands:
      - echo "Hello from Drone CI!"
      - date
```

### Results

**Successfully Deployed:**
- [+] Gitea Git server accessible at `https://my-gitea.duckdns.org`
- [+] Drone CI server accessible at `https://my-drone.duckdns.org`
- [+] Automatic HTTPS with valid Let's Encrypt certificates
- [+] OAuth integration between Gitea and Drone

---

## Task 3: Static Application Security Testing

### Sample Application (`app/app.py`)
```python
import sqlite3
from flask import Flask, request

app = Flask(__name__)

@app.route("/user")
def get_user():
    username = request.args.get('username')
    conn = sqlite3.connect('example.db')
    c = conn.cursor()
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    c.execute(query)
    return str(c.fetchone())
```

### Drone CI Pipeline Configuration  (`app/.drone.yml`)

```yaml
kind: pipeline
type: docker
name: sast-semgrep

workspace:
  path: /src

steps:
  - name: semgrep-owasp-top-ten
    image: returntocorp/semgrep:latest
    commands:
      - semgrep scan --config p/owasp-top-ten --error
```

**Configuration Details:**

1. **Pipeline Type:** Docker-based execution
2. **Workspace:** Custom path for consistent scanning
3. **Semgrep Image:** Official Semgrep container
4. **Ruleset:** `p/owasp-top-ten` - comprehensive security patterns
5. **Error Mode:** `--error` flag fails build on findings

### Semgrep Rulesets

**OWASP Top 10 Coverage:**
- A01:2021 - Broken Access Control
- A02:2021 - Cryptographic Failures
- A03:2021 - Injection (SQL, Command, etc.)
- A04:2021 - Insecure Design
- A05:2021 - Security Misconfiguration
- A06:2021 - Vulnerable Components
- A07:2021 - Authentication Failures
- A08:2021 - Software and Data Integrity Failures
- A09:2021 - Security Logging Failures
- A10:2021 - Server-Side Request Forgery

### Local Testing

```bash
# Install Semgrep
pipx install --include-deps semgrep

# Run scan locally
cd lab1/app
semgrep scan --config p/owasp-top-ten app.py
```

---

**Lab:** SSD-S26 Lab 1  

**Student:** Melnikov Sergei (s.melnikov@innopolis.university)

**Full Video Report [4min on 2x speed]:** [yandex-disk](https://disk.yandex.ru/i/PVEYmPs4jPCPcQ) 

**Sources (Pushed after deadline):** [github](https://github.com/peplxx/SSD-S26)
