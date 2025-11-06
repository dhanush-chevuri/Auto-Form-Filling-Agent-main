#!/bin/bash

# AWS Infrastructure Setup
# Creates ECR repo, ECS cluster, secrets, and task definition
set -e

# Get AWS region and account ID
AWS_REGION=${AWS_DEFAULT_REGION:-$(aws configure get region)}
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "🏗️ Setting up AWS Infrastructure..."
echo "📍 Region: $AWS_REGION"
echo "🏢 Account ID: $AWS_ACCOUNT_ID"

# Check if environment variables are set
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "❌ Error: OPENROUTER_API_KEY environment variable not set"
    exit 1
fi

if [ -z "$LLAMA_CLOUD_API_KEY" ]; then
    echo "❌ Error: LLAMA_CLOUD_API_KEY environment variable not set"
    exit 1
fi

# Create secrets for API keys
echo "Creating OpenRouter API key secret..."
aws secretsmanager create-secret \
  --name "auto-form-filler/openrouter-key" \
  --description "OpenRouter API key for auto form filler" \
  --secret-string "$OPENROUTER_API_KEY" \
  --region $AWS_REGION

echo "Creating Llama Cloud API key secret..."
aws secretsmanager create-secret \
  --name "auto-form-filler/llama-key" \
  --description "Llama Cloud API key for auto form filler" \
  --secret-string "$LLAMA_CLOUD_API_KEY" \
  --region $AWS_REGION

# Generate task definition with actual AWS values
echo "📝 Generating task-definition.json..."
cat > aws/task-definition.json << EOF
{
  "family": "auto-form-filler-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::${AWS_ACCOUNT_ID}:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::${AWS_ACCOUNT_ID}:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/auto-form-filler:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "essential": true,
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/auto-form-filler",
          "awslogs-region": "${AWS_REGION}",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "secrets": [
        {
          "name": "OPENROUTER_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:secret:auto-form-filler/openrouter-key"
        },
        {
          "name": "LLAMA_CLOUD_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:secret:auto-form-filler/llama-key"
        }
      ],
      "environment": [
        {
          "name": "ENV",
          "value": "production"
        }
      ]
    }
  ]
}
EOF

# Create ECR repository
echo "📦 Creating ECR repository..."
aws ecr create-repository --repository-name auto-form-filler --region $AWS_REGION || echo "ECR repo already exists"

# Create ECS cluster
echo "🏗️ Creating ECS cluster..."
aws ecs create-cluster --cluster-name auto-form-filler-cluster --region $AWS_REGION || echo "Cluster already exists"

# Create CloudWatch log group
echo "📊 Creating CloudWatch log group..."
aws logs create-log-group --log-group-name /ecs/auto-form-filler --region $AWS_REGION || echo "Log group already exists"

# Setup IAM roles and permissions
echo "🔐 Setting up IAM roles..."
./aws/fix-iam-permissions.sh

echo "✅ Infrastructure setup completed!"
echo "📝 Task definition generated with your AWS account details"
echo "🚀 Run './aws/deploy-demo.sh' to deploy the application"