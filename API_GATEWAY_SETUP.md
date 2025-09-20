# API Gateway Setup Guide for Invoice Management

## Step-by-Step Setup

### 1. Create API Gateway
1. Go to **AWS Console** → **API Gateway**
2. Click **Create API**
3. Choose **REST API** (not private)
4. Click **Build**
5. **Settings:**
   - API name: `InvoiceManagementAPI`
   - Description: `Invoice Management CRUD Operations`
   - Endpoint Type: `Regional`
6. Click **Create API**

### 2. Create Resources and Methods

#### A. Create `/invoices` Resource
1. Select the root `/` resource
2. Click **Actions** → **Create Resource**
3. **Settings:**
   - Resource Name: `invoices`
   - Resource Path: `/invoices`
   - ✅ Enable API Gateway CORS
4. Click **Create Resource**

#### B. Create `/invoices/{invoice_id}` Resource
1. Select `/invoices` resource
2. Click **Actions** → **Create Resource**
3. **Settings:**
   - Resource Name: `invoice_id`
   - Resource Path: `/{invoice_id}`
   - ✅ Enable API Gateway CORS
4. Click **Create Resource**

#### C. Create `/payments` Resource
1. Select the root `/` resource
2. Click **Actions** → **Create Resource**
3. **Settings:**
   - Resource Name: `payments`
   - Resource Path: `/payments`
   - ✅ Enable API Gateway CORS
4. Click **Create Resource**

#### D. Create `/overdue-check` Resource
1. Select the root `/` resource
2. Click **Actions** → **Create Resource**
3. **Settings:**
   - Resource Name: `overdue-check`
   - Resource Path: `/overdue-check`
   - ✅ Enable API Gateway CORS
4. Click **Create Resource**

### 3. Create Methods for Each Resource

#### A. `/invoices` Methods

**POST Method (Create Invoice):**
1. Select `/invoices` resource
2. Click **Actions** → **Create Method**
3. Select **POST** from dropdown → Click ✓
4. **Integration Settings:**
   - Integration type: `Lambda Function`
   - ✅ Use Lambda Proxy integration
   - Lambda Region: `your-region`
   - Lambda Function: `your-lambda-function-name`
5. Click **Save** → **OK** (grant permission)

**GET Method (Get All Invoices):**
1. Select `/invoices` resource
2. Click **Actions** → **Create Method**
3. Select **GET** from dropdown → Click ✓
4. **Integration Settings:**
   - Integration type: `Lambda Function`
   - ✅ Use Lambda Proxy integration
   - Lambda Region: `your-region`
   - Lambda Function: `your-lambda-function-name`
5. Click **Save** → **OK**

#### B. `/invoices/{invoice_id}` Methods

**GET Method (Get Specific Invoice):**
1. Select `/invoices/{invoice_id}` resource
2. Click **Actions** → **Create Method**
3. Select **GET** from dropdown → Click ✓
4. **Integration Settings:**
   - Integration type: `Lambda Function`
   - ✅ Use Lambda Proxy integration
   - Lambda Region: `your-region`
   - Lambda Function: `your-lambda-function-name`
5. Click **Save** → **OK**

**PUT Method (Update Invoice):**
1. Select `/invoices/{invoice_id}` resource
2. Click **Actions** → **Create Method**
3. Select **PUT** from dropdown → Click ✓
4. **Integration Settings:**
   - Integration type: `Lambda Function`
   - ✅ Use Lambda Proxy integration
   - Lambda Region: `your-region`
   - Lambda Function: `your-lambda-function-name`
5. Click **Save** → **OK**

**DELETE Method (Delete Invoice):**
1. Select `/invoices/{invoice_id}` resource
2. Click **Actions** → **Create Method**
3. Select **DELETE** from dropdown → Click ✓
4. **Integration Settings:**
   - Integration type: `Lambda Function`
   - ✅ Use Lambda Proxy integration
   - Lambda Region: `your-region`
   - Lambda Function: `your-lambda-function-name`
5. Click **Save** → **OK**

#### C. `/payments` Method

**POST Method (Process Payment):**
1. Select `/payments` resource
2. Click **Actions** → **Create Method**
3. Select **POST** from dropdown → Click ✓
4. **Integration Settings:**
   - Integration type: `Lambda Function`
   - ✅ Use Lambda Proxy integration
   - Lambda Region: `your-region`
   - Lambda Function: `your-lambda-function-name`
5. Click **Save** → **OK**

#### D. `/overdue-check` Method

**POST Method (Check Overdue):**
1. Select `/overdue-check` resource
2. Click **Actions** → **Create Method**
3. Select **POST** from dropdown → Click ✓
4. **Integration Settings:**
   - Integration type: `Lambda Function`
   - ✅ Use Lambda Proxy integration
   - Lambda Region: `your-region`
   - Lambda Function: `your-lambda-function-name`
5. Click **Save** → **OK**

### 4. Configure CORS (Important!)

For each resource (`/invoices`, `/invoices/{invoice_id}`, `/payments`, `/overdue-check`):

1. Select the resource
2. Click **Actions** → **Enable CORS**
3. **Settings:**
   - Access-Control-Allow-Origin: `*`
   - Access-Control-Allow-Headers: `Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token`
   - Access-Control-Allow-Methods: Select all methods you created
4. Click **Enable CORS and replace existing CORS headers**

### 5. Deploy API

1. Click **Actions** → **Deploy API**
2. **Settings:**
   - Deployment stage: `[New Stage]`
   - Stage name: `prod`
   - Stage description: `Production stage`
3. Click **Deploy**

### 6. Get Your API URLs

After deployment, you'll get a base URL like:
`https://1s15pejl1c.execute-api.ap-southeast-1.amazonaws.com/prod`
Your endpoints will be:
- `POST https://your-api-id.execute-api.your-region.amazonaws.com/prod/invoices`
- `GET https://your-api-id.execute-api.your-region.amazonaws.com/prod/invoices`
- `GET https://your-api-id.execute-api.your-region.amazonaws.com/prod/invoices/{invoice_id}`
- `PUT https://your-api-id.execute-api.your-region.amazonaws.com/prod/invoices/{invoice_id}`
- `DELETE https://your-api-id.execute-api.your-region.amazonaws.com/prod/invoices/{invoice_id}`
- `POST https://your-api-id.execute-api.your-region.amazonaws.com/prod/payments`
- `POST https://your-api-id.execute-api.your-region.amazonaws.com/prod/overdue-check`

## Testing Your Setup

### Test in API Gateway Console
1. Select any method
2. Click **TEST**
3. Add test data in **Request Body**
4. Click **Test**

### Sample Test Data

**Create Invoice (POST /invoices):**
```json
{
  "customer_id": "CUST-001",
  "customer_name": "Test Customer",
  "customer_email": "test@example.com",
  "line_items": [
    {
      "description": "Web Development",
      "quantity": 10,
      "unit_price": 150.00
    }
  ]
}
```

**Update Status (PUT /invoices/{id}):**
```json
{
  "status": "SENT",
  "reason": "Invoice sent to customer"
}
```

**Process Payment (POST /payments):**
```json
{
  "invoice_id": "your-invoice-id",
  "payment_amount": 1500.00
}
```

## Troubleshooting

### Common Issues:
1. **Lambda Permission Errors**: API Gateway needs permission to invoke Lambda
2. **CORS Errors**: Make sure CORS is enabled on all resources
3. **Path Parameter Issues**: Ensure `{invoice_id}` is correctly configured
4. **Method Not Allowed**: Check HTTP method routing in Lambda code

### Lambda Code Update Needed:
Your Lambda needs to handle path parameters. Update the routing logic:

```python
# In lambda_handler function
path = event.get('path', '')
path_params = event.get('pathParameters') or {}
invoice_id = path_params.get('invoice_id')

if 'invoices' in path and invoice_id:
    # Handle /invoices/{id} endpoints
    if http_method == 'GET':
        return handle_get_specific_invoice(invoice_id, invoice_service)
    elif http_method == 'PUT':
        return handle_update_invoice(event, invoice_service)
    elif http_method == 'DELETE':
        return handle_delete_invoice(event, invoice_service)
```

## Next Steps
1. Complete API Gateway setup
2. Test each endpoint
3. Update checklist with ✅ for completed items
4. Start systematic CRUD testing