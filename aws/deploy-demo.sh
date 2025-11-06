#!/bin/bash

# ECS Demo Deployment (No Load Balancer)
set -e

# Get AWS configuration
AWS_REGION=${AWS_DEFAULT_REGION:-$(aws configure get region)}
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO="auto-form-filler"
CLUSTER_NAME="auto-form-filler-cluster"
SERVICE_NAME="auto-form-filler-demo"

echo "🚀 Starting ECS Demo Deployment (No ALB)..."
echo "📍 Region: $AWS_REGION"
echo "🏢 Account ID: $AWS_ACCOUNT_ID"

# 1. Build and push Docker image for linux/amd64
echo "📦 Building Docker image for linux/amd64..."
docker build --platform linux/amd64 -f backend/Dockerfile.prod -t $ECR_REPO:latest ./backend

echo "🔐 Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

echo "🏷️ Tagging image..."
docker tag $ECR_REPO:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest

echo "⬆️ Pushing to ECR..."
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest

# 2. Generate demo task definition
echo "📝 Generating demo task definition..."
cat > aws/task-definition-demo-generated.json << EOF
{
  "family": "auto-form-filler-demo",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::${AWS_ACCOUNT_ID}:role/ecsTaskExecutionRole",
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
      ]
    }
  ]
}
EOF

# 3. Register task definition
echo "📝 Registering demo task definition..."
aws ecs register-task-definition --cli-input-json file://aws/task-definition-demo-generated.json

# 4. Create service with public IP (no ALB)
echo "🌐 Creating ECS service with public IP..."

# Get default VPC and subnet
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query 'Vpcs[0].VpcId' --output text)
SUBNET_ID=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[0].SubnetId' --output text)

# Create security group for demo
SG_ID=$(aws ec2 create-security-group \
  --group-name auto-form-filler-demo-sg \
  --description "Demo security group for auto form filler" \
  --vpc-id $VPC_ID \
  --query 'GroupId' --output text 2>/dev/null || \
  aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=auto-form-filler-demo-sg" \
  --query 'SecurityGroups[0].GroupId' --output text)

# Allow HTTP traffic
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 8000 \
  --cidr 0.0.0.0/0 2>/dev/null || echo "Security group rule already exists"

# Create or update service
if aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $AWS_REGION --query 'services[0].serviceName' --output text 2>/dev/null | grep -q $SERVICE_NAME; then
    echo "Service exists, updating..."
    aws ecs update-service \
        --cluster $CLUSTER_NAME \
        --service $SERVICE_NAME \
        --task-definition auto-form-filler-demo \
        --force-new-deployment \
        --region $AWS_REGION
else
    echo "Creating new demo service..."
    aws ecs create-service \
        --cluster $CLUSTER_NAME \
        --service-name $SERVICE_NAME \
        --task-definition auto-form-filler-demo \
        --desired-count 1 \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_ID],securityGroups=[$SG_ID],assignPublicIp=ENABLED}" \
        --region $AWS_REGION
fi

echo "✅ Demo deployment completed!"
echo "🌐 Your app will be available at: http://[TASK-PUBLIC-IP]:8000"
echo "🔍 Get public IP: aws ecs describe-tasks --cluster $CLUSTER_NAME --tasks \$(aws ecs list-tasks --cluster $CLUSTER_NAME --service-name $SERVICE_NAME --query 'taskArns[0]' --output text) --query 'tasks[0].attachments[0].details[?name==\`networkInterfaceId\`].value' --output text | xargs -I {} aws ec2 describe-network-interfaces --network-interface-ids {} --query 'NetworkInterfaces[0].Association.PublicIp' --output text"