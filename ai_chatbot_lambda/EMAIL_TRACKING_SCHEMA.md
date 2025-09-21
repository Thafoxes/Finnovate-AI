# Email Tracking DynamoDB Schema Design

## Table: EmailTrackingTable

### Purpose
Track email drafts, sending history, and prevent duplicate emails for the AI chatbot system.

### Schema Design

#### Primary Key
- **PK (Partition Key)**: `CUSTOMER#{customer_id}` - Groups all email activity by customer
- **SK (Sort Key)**: Various patterns for different item types:
  - `DRAFT#{timestamp}_{customer_id}` - Email drafts pending approval
  - `SENT#{timestamp}_{reminder_type}` - Sent email records
  - `TEMPLATE#{template_id}` - Email templates

#### Global Secondary Index (GSI1)
- **GSI1PK**: `STATUS#{status}` - Groups items by status (draft, sent, failed)
- **GSI1SK**: `{timestamp}` - Sort by timestamp for chronological ordering

### Item Types

#### 1. Email Draft Items
```json
{
  "PK": "CUSTOMER#cust_001",
  "SK": "DRAFT#20250921_143022_cust_001",
  "GSI1PK": "STATUS#draft",
  "GSI1SK": "2025-09-21T14:30:22Z",
  "customer_id": "cust_001",
  "customer_name": "John Doe",
  "customer_email": "john@example.com",
  "reminder_type": "first",
  "email_subject": "Payment Reminder from Innovate AI",
  "email_content": "Dear John...",
  "status": "draft",
  "created_date": "2025-09-21T14:30:22Z",
  "created_by": "ai_system",
  "overdue_amount": 1500.00,
  "overdue_invoices": ["INV-001", "INV-002"]
}
```

#### 2. Sent Email Records
```json
{
  "PK": "CUSTOMER#cust_001",
  "SK": "SENT#20250921_150000_first",
  "GSI1PK": "STATUS#sent",
  "GSI1SK": "2025-09-21T15:00:00Z",
  "customer_id": "cust_001",
  "reminder_type": "first",
  "email_subject": "Payment Reminder from Innovate AI",
  "email_content": "Dear John...",
  "status": "sent",
  "sent_date": "2025-09-21T15:00:00Z",
  "approved_by": "user_123",
  "ses_message_id": "0000014a-f4d4-4f41-9d83-8c0a6df0c5a1-000000",
  "delivery_status": "delivered"
}
```

#### 3. Email Template Items
```json
{
  "PK": "TEMPLATE#reminder_first",
  "SK": "VERSION#1",
  "GSI1PK": "STATUS#active",
  "GSI1SK": "2025-09-21T12:00:00Z",
  "template_id": "reminder_first",
  "template_name": "First Reminder Template",
  "template_type": "first_reminder",
  "subject_template": "Payment Reminder: Invoice {{invoice_id}} - Innovate AI",
  "body_template": "Dear {{customer_name}}...",
  "status": "active",
  "created_date": "2025-09-21T12:00:00Z",
  "version": 1,
  "branding": "innovate_ai"
}
```

### Duplicate Prevention Logic

#### Query Pattern for Recent Emails
To check if a customer received a specific reminder type recently:
```python
response = email_tracking_table.query(
    KeyConditionExpression='PK = :pk',
    FilterExpression='reminder_type = :reminder_type AND sent_date > :cutoff_date',
    ExpressionAttributeValues={
        ':pk': f'CUSTOMER#{customer_id}',
        ':reminder_type': reminder_type,
        ':cutoff_date': cutoff_date.isoformat()
    }
)
```

#### Business Rules
- **First Reminder**: No duplicate within 7 days
- **Second Reminder**: No duplicate within 5 days, must be at least 7 days after first
- **Final Reminder**: No duplicate within 3 days, must be at least 5 days after second

### Access Patterns

1. **Get all drafts pending approval**
   ```python
   # Query GSI1
   GSI1PK = "STATUS#draft"
   ```

2. **Get email history for a customer**
   ```python
   # Query main table
   PK = "CUSTOMER#{customer_id}"
   SK begins_with "SENT#"
   ```

3. **Get recent emails by type**
   ```python
   # Query main table with filter
   PK = "CUSTOMER#{customer_id}"
   FilterExpression: reminder_type = "first" AND sent_date > cutoff
   ```

4. **Get all sent emails in date range**
   ```python
   # Query GSI1
   GSI1PK = "STATUS#sent"
   GSI1SK between start_date AND end_date
   ```

### Capacity Planning
- **Billing Mode**: PAY_PER_REQUEST (suitable for MVP/hackathon)
- **Expected Volume**: 
  - ~1000 customers
  - ~3 email types per customer per month
  - ~100 drafts stored at any time
  - Total items: ~5000-10000

### Security Considerations
- Customer PII is stored (names, emails)
- Email content may contain sensitive invoice information
- Access should be restricted to authorized Lambda functions only

### Backup Strategy
- Point-in-time recovery enabled
- Daily backups to S3 (for production)
- Retention: 30 days for drafts, 1 year for sent emails