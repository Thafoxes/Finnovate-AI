# Local Development and Testing Guide

## 🏠 Testing AI Bot Locally Before AWS Deployment

This guide shows you how to run and test your AI Payment Intelligence system locally before deploying to AWS.

## 📋 Prerequisites

1. **Python 3.8+** installed
2. **AWS credentials** configured in `.env` file
3. **Bedrock model access** approved (Nova Micro)

## 🚀 Quick Start

### Step 1: Install Dependencies
```bash
cd lambda_deployment
pip install -r requirements-local.txt
```

### Step 2: Start Local Server
```bash
# Windows
start_local.bat

# Or manually
python local_server.py
```

### Step 3: Test the System
```bash
# In another terminal
python test_local.py
```

## 🔧 Configuration

### Environment Variables (.env file)
Make sure your `lambda_deployment/.env` file contains:

```env
# AWS Configuration
AWS_REGION=ap-southeast-1
AWS_ACCESS_KEY_ID=AKIAV3R5T3IAV6HESI3U
AWS_SECRET_ACCESS_KEY=/h01kVFw05ReD0JuhuI4ofhl03NNVWTvFk+oy7zy

# Bedrock Configuration
BEDROCK_MODEL_ID=amazon.nova-micro-v1:0
BEDROCK_REGION=ap-southeast-1

# Application Configuration
ENVIRONMENT=development
DEBUG=true
USE_IN_MEMORY_DB=true
```

### Frontend Configuration
Update `finnovate-dashboard/.env` for local testing:

```env
REACT_APP_API_BASE_URL=http://localhost:5000
```

## 📡 Available Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Server health check |
| GET | `/test-bedrock` | Test AWS Bedrock connection |
| GET | `/test-data` | Get sample test data |
| GET | `/invoices` | Get all invoices |
| GET | `/invoices/overdue` | Get overdue invoices |
| GET | `/customers` | Get all customers |
| POST | `/ai/chat` | AI chatbot conversation |
| POST | `/ai/generate-email` | Generate payment emails |
| GET/POST | `/campaigns` | Payment campaign management |

## 🧪 Testing Scenarios

### 1. Basic Connectivity Test
```bash
curl http://localhost:5000/health
```

### 2. Bedrock Connection Test
```bash
curl http://localhost:5000/test-bedrock
```

### 3. AI Chat Test
```bash
curl -X POST http://localhost:5000/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What overdue invoices do we have?", "context": "payment_management"}'
```

### 4. Email Generation Test
```bash
curl -X POST http://localhost:5000/ai/generate-email \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_id": "test-001",
    "customer_name": "Test Customer",
    "amount": 1500.00,
    "days_overdue": 15,
    "tone": "professional"
  }'
```

## 🔍 Frontend Integration Testing

### Update Frontend URL
1. Open `finnovate-dashboard/.env`
2. Change: `REACT_APP_API_BASE_URL=http://localhost:5000`
3. Restart React dev server: `npm start`

### Test Frontend Features
1. **Dashboard**: Check if data loads
2. **AI Assistant**: Test chat functionality
3. **Invoice Management**: Test CRUD operations
4. **Email Generation**: Test AI email features

## 🐛 Troubleshooting

### Common Issues:

#### 1. "Import flask could not be resolved"
```bash
pip install flask flask-cors boto3 python-dotenv
```

#### 2. "Access denied" for Bedrock
- Check AWS credentials in `.env`
- Verify Bedrock model access is approved
- Test with: `curl http://localhost:5000/test-bedrock`

#### 3. "CORS errors" in browser
- Ensure local server is running on port 5000
- Check frontend `.env` has correct API URL
- Verify CORS is enabled in `local_server.py`

#### 4. "No invoices found"
- Check if using real DynamoDB data or in-memory
- For real data: set `USE_IN_MEMORY_DB=false` in `.env`
- For test data: ensure sample data is generated

### Debug Mode
Enable detailed logging:
```env
DEBUG=true
```

## 📊 Test Results Interpretation

### Automated Test Suite Results:
- ✅ **Health Check**: Server is running properly
- ✅ **Bedrock Connection**: AWS credentials and model access working
- ✅ **Invoice Data**: Data retrieval working
- ✅ **AI Chat**: AI conversation functionality working
- ✅ **Email Generation**: AI email creation working
- ✅ **Campaign Management**: Campaign CRUD operations working

### Performance Benchmarks:
- Health check: < 100ms
- Bedrock responses: 1-3 seconds
- Invoice queries: < 500ms
- Email generation: 2-5 seconds

## 🚀 Ready for AWS Deployment?

If all local tests pass:

1. ✅ **Local functionality confirmed**
2. ✅ **AWS services accessible**
3. ✅ **AI responses generating correctly**
4. ✅ **Frontend integration working**

**Next Steps:**
1. Deploy Lambda functions to AWS
2. Update frontend to use AWS API Gateway URL
3. Run production tests
4. Monitor CloudWatch logs

## 💡 Development Tips

### Hot Reloading
The local server supports hot reloading when `DEBUG=true`. Changes to code will automatically restart the server.

### Data Testing
- Use real DynamoDB data: `USE_IN_MEMORY_DB=false`
- Use sample data: `USE_IN_MEMORY_DB=true`

### Performance Testing
Monitor response times for:
- AI chat responses (target: < 5 seconds)
- Data queries (target: < 1 second)
- Email generation (target: < 3 seconds)

### Cost Monitoring
Local testing uses actual Bedrock API calls, so:
- Monitor token usage
- Use shorter test messages
- Implement request caching if needed

---

**Happy Testing! 🎉**

Your AI bot should be fully functional locally before AWS deployment.