#!/bin/bash

# AWS CLI commands to set up AI Chatbot infrastructure

echo "Creating EmailTrackingTable for AI Chatbot..."

# Create DynamoDB table using CloudFormation
aws cloudformation create-stack \
  --stack-name innovate-ai-email-tracking \
  --template-body file://email-tracking-table.json \
  --region us-east-1

echo "Waiting for stack creation to complete..."
aws cloudformation wait stack-create-complete \
  --stack-name innovate-ai-email-tracking \
  --region us-east-1

echo "Stack creation completed!"

# Get the table name from the stack output
TABLE_NAME=$(aws cloudformation describe-stacks \
  --stack-name innovate-ai-email-tracking \
  --region us-east-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`EmailTrackingTableName`].OutputValue' \
  --output text)

echo "Created table: $TABLE_NAME"

# Verify table is active
aws dynamodb describe-table \
  --table-name $TABLE_NAME \
  --region us-east-1 \
  --query 'Table.TableStatus'

echo "EmailTrackingTable setup complete!"

# Note: For Lambda deployment, you'll need to:
# 1. Create a deployment package (zip file)
# 2. Create IAM role with appropriate permissions
# 3. Create Lambda function
# 4. Set environment variables
# 5. Configure API Gateway integration

echo ""
echo "Next steps:"
echo "1. Create Lambda deployment package"
echo "2. Set up IAM permissions for Bedrock and DynamoDB access"
echo "3. Deploy Lambda function"
echo "4. Configure API Gateway integration"