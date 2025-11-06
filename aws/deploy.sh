#!/bin/bash

# AWS ECS Deployment Script
set -e

# Get AWS configuration
AWS_REGION=${AWS_DEFAULT_REGION:-$(aws configure get region)}
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO="auto-form-filler"
CLUSTER_NAME="auto-form-filler-cluster"
SERVICE_NAME="auto-form-filler-service"

echo "📍 Region: $AWS_REGION"
echo "🏢 Account ID: $AWS_ACCOUNT_ID"

echo "🚀 Starting AWS ECS Deployment..."

# 1. Build and push Docker image for linux/amd64
echo "📦 Building Docker image for linux/amd64..."
docker build --platform linux/amd64 -f backend/Dockerfile.prod -t $ECR_REPO:latest ./backend

echo "🔐 Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

echo "🏷️ Tagging image..."
docker tag $ECR_REPO:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest

echo "⬆️ Pushing to ECR..."
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest

# 2. Update task definition
echo "📝 Registering new task definition..."
aws ecs register-task-definition --cli-input-json file://aws/task-definition.json

# 3. Create or update service
echo "🔄 Creating/updating ECS service..."

# Check if service exists
if aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $AWS_REGION --query 'services[0].serviceName' --output text 2>/dev/null | grep -q $SERVICE_NAME; then
    echo "Service exists, updating..."
    aws ecs update-service \
        --cluster $CLUSTER_NAME \
        --service $SERVICE_NAME \
        --task-definition auto-form-filler-backend \
        --force-new-deployment \
        --region $AWS_REGION
else
    echo "Creating new service..."
    aws ecs create-service \
        --cluster $CLUSTER_NAME \
        --service-name $SERVICE_NAME \
        --task-definition auto-form-filler-backend \
        --desired-count 1 \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}" \
        --region $AWS_REGION
    echo "⚠️ Update network configuration in deploy.sh with your VPC details"
fi

echo "✅ Deployment completed!"
echo "🔍 Check status: aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME"