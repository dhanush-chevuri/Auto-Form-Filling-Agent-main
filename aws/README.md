# AWS ECS Deployment Guide

## 🔐 Security Features

- **Secrets Manager**: API keys stored securely
- **Non-root container**: Runs as unprivileged user
- **IAM roles**: Minimal required permissions
- **VPC networking**: Private subnets with ALB
- **CloudWatch logs**: Centralized logging

## 🚀 Deployment Steps

### ✨ **Automatic Infrastructure Creation:**
- ✅ ECR Repository
- ✅ ECS Cluster  
- ✅ CloudWatch Log Group
- ✅ ECS Service (on first deploy)

### 1. Prerequisites
```bash
# Install AWS CLI
aws configure

# Note: ECR repo, ECS cluster, and CloudWatch logs are created automatically
```

### 2. Setup Infrastructure
```bash
# Export your API keys as environment variables
export OPENROUTER_API_KEY="your_openrouter_key_here"
export LLAMA_CLOUD_API_KEY="your_llama_cloud_key_here"

# Run infrastructure setup
chmod +x aws/setup-infrastructure.sh
./aws/setup-infrastructure.sh
```

### 3. Create IAM Roles
```bash
# Create execution role
aws iam create-role --role-name ecsTaskExecutionRole --assume-role-policy-document file://aws/trust-policy.json
aws iam attach-role-policy --role-name ecsTaskExecutionRole --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
aws iam put-role-policy --role-name ecsTaskExecutionRole --policy-name SecretsManagerAccess --policy-document file://aws/iam-policies.json

# Create task role
aws iam create-role --role-name ecsTaskRole --assume-role-policy-document file://aws/trust-policy.json
```

### 4. Configuration (Automatic)
```bash
# AWS account ID and region are automatically detected from:
# - AWS CLI configuration (aws configure)
# - Environment variables (AWS_DEFAULT_REGION)
# - STS API calls (aws sts get-caller-identity)
```

### 5. Deploy
```bash
chmod +x aws/deploy.sh
./aws/deploy.sh

# Note: Update network configuration in deploy.sh with your VPC subnet/security group IDs
```

## 🛡️ Security Best Practices

1. **API Keys**: Never hardcode in containers
2. **Network**: Use private subnets + ALB
3. **Monitoring**: Enable CloudWatch + CloudTrail
4. **Updates**: Regular security patches
5. **Access**: Least privilege IAM policies

## 📊 Monitoring

```bash
# View logs
aws logs tail /ecs/auto-form-filler --follow

# Check service status
aws ecs describe-services --cluster auto-form-filler-cluster --services auto-form-filler-service
```