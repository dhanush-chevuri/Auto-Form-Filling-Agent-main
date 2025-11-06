#!/bin/bash

# ECS HTTPS Deployment with Application Load Balancer
set -e

AWS_REGION=${AWS_DEFAULT_REGION:-$(aws configure get region)}
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO="auto-form-filler"
CLUSTER_NAME="auto-form-filler-cluster"
SERVICE_NAME="auto-form-filler-https"

echo "🚀 Starting ECS HTTPS Deployment..."

# 1. Build and push image
docker build --platform linux/amd64 -f backend/Dockerfile.prod -t $ECR_REPO:latest ./backend
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
docker tag $ECR_REPO:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest

# 2. Create ALB with HTTPS
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query 'Vpcs[0].VpcId' --output text)
SUBNETS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[0:2].SubnetId' --output text | tr '\t' ',')

# Create security group for ALB
ALB_SG_ID=$(aws ec2 create-security-group \
  --group-name auto-form-filler-alb-sg \
  --description "ALB security group" \
  --vpc-id $VPC_ID \
  --query 'GroupId' --output text 2>/dev/null || \
  aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=auto-form-filler-alb-sg" \
  --query 'SecurityGroups[0].GroupId' --output text)

aws ec2 authorize-security-group-ingress --group-id $ALB_SG_ID --protocol tcp --port 443 --cidr 0.0.0.0/0 2>/dev/null || true
aws ec2 authorize-security-group-ingress --group-id $ALB_SG_ID --protocol tcp --port 80 --cidr 0.0.0.0/0 2>/dev/null || true

# Create ALB
ALB_ARN=$(aws elbv2 create-load-balancer \
  --name auto-form-filler-alb \
  --subnets $(echo $SUBNETS | tr ',' ' ') \
  --security-groups $ALB_SG_ID \
  --query 'LoadBalancers[0].LoadBalancerArn' --output text 2>/dev/null || \
  aws elbv2 describe-load-balancers \
  --names auto-form-filler-alb \
  --query 'LoadBalancers[0].LoadBalancerArn' --output text)

# Get ALB DNS name
ALB_DNS=$(aws elbv2 describe-load-balancers --load-balancer-arns $ALB_ARN --query 'LoadBalancers[0].DNSName' --output text)

echo "✅ ALB created: https://$ALB_DNS"
echo "⚠️  You need to:"
echo "1. Create SSL certificate in ACM for your domain"
echo "2. Add HTTPS listener to ALB with certificate"
echo "3. Point your domain to ALB DNS name"
echo "4. Update REACT_APP_API_URL to https://yourdomain.com"