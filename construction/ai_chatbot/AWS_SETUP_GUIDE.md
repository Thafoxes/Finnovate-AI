# AWS Setup Instructions for AI Payment Intelligence System

This guide will walk you through setting up the AWS services required for the AI-powered payment collection chatbot system.

## Prerequisites

- AWS Account with administrative access
- AWS CLI installed and configured
- Basic familiarity with AWS Console

## Required AWS Services

1. **Amazon Bedrock** - For AI-powered email generation using Nova Micro
2. **AWS Lambda** - For serverless API endpoints
3. **Amazon DynamoDB** - For data storage (optional, using in-memory for MVP)
4. **Amazon S3** - For static assets and file storage
5. **AWS IAM** - For permissions and security
6. **Amazon API Gateway** - For REST API management
7. **Amazon CloudWatch** - For logging and monitoring

---

## Step 1: Enable Amazon Bedrock and Request Model Access

### 1.1 Enable Bedrock Service
1. Open AWS Console and navigate to **Amazon Bedrock**
2. If this is your first time, click **"Get started"**
3. Select your preferred region (recommend `us-east-1` or `us-west-2` for best model availability)

### 1.2 Request Access to Nova Micro Model
1. In Bedrock console, go to **"Model access"** in the left sidebar
2. Click **"Request model access"**
3. Find **"Amazon Nova Micro"** in the list
4. Click **"Request access"** next to Nova Micro
5. Fill out the use case form:
   - **Use case**: "AI-powered customer service for payment collection"
   - **Description**: "Generating personalized email content for overdue payment reminders and customer communication"
6. Submit the request

> **Note**: Model access approval can take 1-24 hours. You'll receive an email when approved.

### 1.3 Verify Model Access
Once approved:
1. Go back to **"Model access"** 
2. Verify **"Amazon Nova Micro"** shows **"Access granted"** status
3. Note the model ID: `amazon.nova-micro-v1:0`

---

## Step 2: Create IAM Roles and Policies

### 2.1 Create Bedrock Service Role
1. Navigate to **IAM** > **Roles**
2. Click **"Create role"**
3. Select **"AWS service"** > **"Lambda"**
4. Click **"Next"**
5. Create a custom policy with the following JSON:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream",
                "bedrock:GetModel",
                "bedrock:ListModels"
            ],
            "Resource": [
                "arn:aws:bedrock:*:*:model/amazon.nova-micro-v1:0",
                "arn:aws:bedrock:*:*:model/amazon.nova-micro-v1"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        }
    ]
}
```

6. Name the policy: `BedrockNovaAccessPolicy`
7. Click **"Create policy"**
8. Attach this policy to the role
9. Name the role: `PaymentIntelligenceLambdaRole`

### 2.2 Create API User for Local Development
1. Navigate to **IAM** > **Users**
2. Click **"Create user"**
3. Username: `payment-ai-dev-user`
4. Select **"Attach policies directly"**
5. Attach the `BedrockNovaAccessPolicy` created above
6. Click **"Create user"**
7. Go to the user details page
8. Click **"Security credentials"** tab
9. Click **"Create access key"**
10. Select **"Local code"**
11. **Save the Access Key ID and Secret Access Key** - you'll need these for your application

---

## Step 3: Configure Amazon S3 for File Storage

### 3.1 Create S3 Bucket
1. Navigate to **Amazon S3**
2. Click **"Create bucket"**
3. Bucket name: `payment-intelligence-assets-[random-suffix]` (must be globally unique)
4. Region: Same as your Bedrock region
5. Keep default settings for now
6. Click **"Create bucket"**

### 3.2 Configure CORS for Web Access
1. Select your bucket
2. Go to **"Permissions"** tab
3. Scroll to **"Cross-origin resource sharing (CORS)"**
4. Click **"Edit"** and add:

```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "POST", "PUT", "DELETE"],
        "AllowedOrigins": ["http://localhost:3000", "https://your-domain.com"],
        "ExposeHeaders": ["ETag"]
    }
]
```

---

## Step 4: Create DynamoDB Tables (Optional for MVP)

If you want to use DynamoDB instead of in-memory storage:

### 4.1 Create Payment Campaigns Table
1. Navigate to **DynamoDB**
2. Click **"Create table"**
3. Table name: `PaymentCampaigns`
4. Partition key: `campaign_id` (String)
5. Sort key: `customer_id` (String)
6. Use default settings
7. Click **"Create table"**

### 4.2 Create Conversations Table
1. Click **"Create table"**
2. Table name: `Conversations`
3. Partition key: `conversation_id` (String)
4. Sort key: `timestamp` (Number)
5. Click **"Create table"**

### 4.3 Create Overdue Invoices Table
1. Click **"Create table"**
2. Table name: `OverdueInvoices`
3. Partition key: `invoice_id` (String)
4. Sort key: `customer_id` (String)
5. Click **"Create table"**

---

## Step 5: Set Up API Gateway (for Production)

### 5.1 Create REST API
1. Navigate to **API Gateway**
2. Click **"Create API"**
3. Select **"REST API"** > **"Build"**
4. API name: `PaymentIntelligenceAPI`
5. Description: `API for AI payment collection system`
6. Click **"Create API"**

### 5.2 Configure CORS
1. Select your API
2. Click **"Actions"** > **"Enable CORS"**
3. Allow origins: `*` (or specify your domain)
4. Allow headers: `Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token`
5. Allow methods: `GET,POST,PUT,DELETE,OPTIONS`
6. Click **"Enable CORS and replace existing CORS headers"**

---

## Step 6: Environment Configuration

### 6.1 Create AWS Credentials File
On your local machine, create `~/.aws/credentials`:

```ini
[default]
aws_access_key_id = YOUR_ACCESS_KEY_ID
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
region = us-east-1
```

### 6.2 Create Environment Variables File
Create `.env` file in your project root:

```env
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here

# Bedrock Configuration
BEDROCK_MODEL_ID=amazon.nova-micro-v1:0
BEDROCK_REGION=us-east-1

# S3 Configuration
S3_BUCKET_NAME=payment-intelligence-assets-your-suffix

# DynamoDB Configuration (optional)
DYNAMODB_CAMPAIGNS_TABLE=PaymentCampaigns
DYNAMODB_CONVERSATIONS_TABLE=Conversations
DYNAMODB_INVOICES_TABLE=OverdueInvoices

# Application Configuration
ENVIRONMENT=development
DEBUG=true
```

---

## Step 7: Test Bedrock Access

### 7.1 Test with AWS CLI
```bash
# Test Bedrock access
aws bedrock list-foundation-models --region us-east-1

# Test Nova Micro specifically
aws bedrock get-foundation-model --model-identifier amazon.nova-micro-v1:0 --region us-east-1
```

### 7.2 Test with Python (once infrastructure is built)
```python
import boto3

# Initialize Bedrock client
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

# Test model invocation
response = bedrock.invoke_model(
    modelId='amazon.nova-micro-v1:0',
    body='{"inputText":"Hello, this is a test","textGenerationConfig":{"maxTokenCount":100,"temperature":0.7}}'
)

print("Bedrock test successful!")
```

---

## Step 8: Cost Management Setup

### 8.1 Set Up Billing Alerts
1. Navigate to **AWS Billing and Cost Management**
2. Go to **"Budgets"**
3. Click **"Create budget"**
4. Select **"Cost budget"**
5. Set monthly budget: `$50` (adjust as needed)
6. Set alert at 80% of budget
7. Add your email for notifications

### 8.2 Monitor Bedrock Usage
1. Navigate to **CloudWatch**
2. Go to **"Metrics"**
3. Look for **"AWS/Bedrock"** namespace
4. Set up alarms for:
   - Model invocation count
   - Token usage
   - Error rates

---

## Security Checklist

- [ ] Model access approved for Nova Micro
- [ ] IAM roles with minimal required permissions
- [ ] Access keys stored securely (never in code)
- [ ] S3 bucket not publicly accessible
- [ ] API Gateway CORS properly configured
- [ ] CloudWatch logging enabled
- [ ] Billing alerts configured

---

## Troubleshooting

### Common Issues:

1. **"Access denied" errors with Bedrock**
   - Verify model access is approved
   - Check IAM permissions include `bedrock:InvokeModel`
   - Ensure correct model ID: `amazon.nova-micro-v1:0`

2. **"Model not found" errors**
   - Verify you're using the correct region
   - Check model access status in Bedrock console
   - Wait for model access approval if still pending

3. **High costs**
   - Monitor token usage in CloudWatch
   - Implement request caching
   - Set appropriate token limits in requests

4. **CORS issues**
   - Verify API Gateway CORS configuration
   - Check S3 bucket CORS settings
   - Ensure frontend origin is whitelisted

---

## Next Steps

After completing this setup:

1. **Test all services** using the verification steps above
2. **Configure monitoring** in CloudWatch for production readiness
3. **Implement the infrastructure layer** in your application code
4. **Deploy and test** the complete system

## Estimated Costs

For development/testing:
- **Bedrock Nova Micro**: ~$0.00025 per 1K input tokens, ~$0.001 per 1K output tokens
- **DynamoDB**: ~$1.25/month for light usage (free tier: 25GB storage, 200M requests)
- **S3**: ~$0.023/GB/month (free tier: 5GB for 12 months)
- **API Gateway**: ~$3.50 per million requests (free tier: 1M requests for 12 months)
- **Lambda**: ~$0.20 per 1M requests (free tier: 1M requests/month)

**Estimated monthly cost for development: $5-15**

Let me know when you've completed these steps and I'll continue with implementing the infrastructure layer code!