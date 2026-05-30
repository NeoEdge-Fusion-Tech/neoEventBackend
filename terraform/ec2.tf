# SSH Key Pair for access
# Note: You must generate an SSH key locally (ssh-keygen -t rsa -b 4096 -f ~/.ssh/neoevents)
# and update the public key path below, or pass it via variable.
resource "aws_key_pair" "deployer" {
  key_name   = "neoevents-deployer-key"
  public_key = file("~/.ssh/id_rsa.pub") # Replace with your actual public key path
}

# Fetch the latest Ubuntu 22.04 AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

# IAM Instance Profile for EC2 to access S3
resource "aws_iam_role" "ec2_role" {
  name = "neoevents-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "s3_access_policy" {
  name = "neoevents-ec2-s3-access"
  role = aws_iam_role.ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Effect   = "Allow"
        Resource = [
          aws_s3_bucket.media_bucket.arn,
          "${aws_s3_bucket.media_bucket.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "neoevents-ec2-profile"
  role = aws_iam_role.ec2_role.name
}

# The Single EC2 Instance
resource "aws_instance" "app_server" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.medium" # Minimum for FastAPI/InsightFace memory requirements
  
  subnet_id                   = aws_subnet.public.id
  vpc_security_group_ids      = [aws_security_group.server_sg.id]
  key_name                    = aws_key_pair.deployer.key_name
  iam_instance_profile        = aws_iam_instance_profile.ec2_profile.name
  associate_public_ip_address = true

  root_block_device {
    volume_size = 50
    volume_type = "gp3"
  }

  tags = {
    Name = "neoevents-server-${var.environment}"
  }

  # Auto-install Docker and Docker Compose on boot
  user_data = <<-EOF
              #!/bin/bash
              apt-get update -y
              apt-get install -y apt-transport-https ca-certificates curl software-properties-common git
              curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
              echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
              apt-get update -y
              apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
              
              # Install older docker-compose just in case
              curl -L "https://github.com/docker/compose/releases/download/v2.20.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
              chmod +x /usr/local/bin/docker-compose
              
              usermod -aG docker ubuntu
              systemctl enable docker
              systemctl start docker
              EOF
}

# Output the Public IP
output "server_public_ip" {
  value       = aws_instance.app_server.public_ip
  description = "The public IP of the Neoevents server"
}
