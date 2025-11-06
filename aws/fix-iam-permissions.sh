#!/bin/bash

# Fix IAM permissions for Secrets Manager access
set -e

AWS_REGION=${AWS_DEFAULT_REGION:-$(aws configure get region)}
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "🔐 Fixing IAM permissions for Secrets Manager..."

# Create trust policy for ECS tasks
cat > /tmp/ecs-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create secrets manager policy
cat > /tmp/secrets-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:secret:auto-form-filler/*"
      ]
    }
  ]
}
EOF

# Create or update execution role
echo "Creating/updating ecsTaskExecutionRole..."
aws iam create-role \
  --role-name ecsTaskExecutionRole \
  --assume-role-policy-document file:///tmp/ecs-trust-policy.json 2>/dev/null || \
  echo "Role already exists"

# Attach AWS managed policy
aws iam attach-role-policy \
  --role-name ecsTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Create and attach secrets manager policy
aws iam put-role-policy \
  --role-name ecsTaskExecutionRole \
  --policy-name SecretsManagerAccess \
  --policy-document file:///tmp/secrets-policy.json

echo "✅ IAM permissions fixed!"
echo "🔄 Redeploy your service: ./aws/deploy-demo.sh"

# Cleanup
rm -f /tmp/ecs-trust-policy.json /tmp/secrets-policy.json