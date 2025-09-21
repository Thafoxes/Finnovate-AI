# Email Management System - DynamoDB Schema Design

## Overview
This document defines the DynamoDB schema for the email management system that supports email template creation, approval workflow, sending tracking, and duplicate prevention.

## Table: EmailTrackingTable

### Primary Access Patterns

1. **Email Templates by Status**: Find all draft/approved email templates
2. **Customer Email History**: Get all emails sent to a specific customer
3. **Reminder Type Tracking**: Prevent duplicate reminders of same type to same customer
4. **Approval Workflow**: Track template approval process
5. **Email Analytics**: Analyze email sending patterns

### Schema Structure

#### Primary Key Design
- **PK (Partition Key)**: Entity identifier
- **SK (Sort Key)**: Entity type and timestamp/identifier

#### Global Secondary Index (GSI1)
- **GSI1PK**: Secondary access pattern
- **GSI1SK**: Secondary sort pattern

### Data Models

#### 1. Email Template Entity
```
PK: "TEMPLATE#{template_id}"
SK: "v#{version_number}"
Type: "email_template"
template_id: "template_001"
version: 1
customer_id: "cust_001"
reminder_type: "first_reminder" | "second_reminder" | "final_notice"
status: "drafted" | "approved" | "sent" | "cancelled"
subject: "Payment Reminder - Invoice #{invoice_id}"
body_text: "Dear {customer_name}, we wanted to..."
body_html: "<html>...</html>"
personalization_data: {
  customer_name: "John Doe",
  invoice_id: "INV-001",
  amount_due: 1500.00,
  due_date: "2025-09-30"
}
created_by: "ai_system"
created_at: "2025-09-21T10:00:00Z"
approved_by: null
approved_at: null
sent_at: null
ai_prompt_used: "PAYMENT_REMINDER_FIRST"

# GSI1 for querying by status
GSI1PK: "TEMPLATE_STATUS#{status}"
GSI1SK: "created_at#{created_at}"
```

#### 2. Email Sending Record Entity
```
PK: "SENT#{customer_id}"
SK: "#{reminder_type}#{sent_date}"
Type: "email_sent"
template_id: "template_001"
customer_id: "cust_001"
reminder_type: "first_reminder"
invoice_id: "INV-001"
subject: "Payment Reminder - Invoice #INV-001"
sent_at: "2025-09-21T10:30:00Z"
ses_message_id: "0000014a-f4d4-4f89-93b1-2f9c7d8e6a5b"
delivery_status: "sent" | "delivered" | "bounced" | "complained"
template_version: 1

# GSI1 for querying by reminder type
GSI1PK: "REMINDER_TYPE#{reminder_type}"
GSI1SK: "sent_at#{sent_at}"
```

#### 3. Customer Email State Entity
```
PK: "CUSTOMER#{customer_id}"
SK: "EMAIL_STATE"
Type: "customer_email_state"
customer_id: "cust_001"
first_reminder_sent: "2025-09-21T10:30:00Z"
second_reminder_sent: null
final_notice_sent: null
last_email_sent: "2025-09-21T10:30:00Z"
total_emails_sent: 1
opt_out_status: false
bounce_count: 0
complaint_count: 0

# GSI1 for analytics
GSI1PK: "CUSTOMER_STATE"
GSI1SK: "last_email_sent#{last_email_sent}"
```

#### 4. Email Analytics Entity
```
PK: "ANALYTICS#{date}"
SK: "DAILY_SUMMARY"
Type: "email_analytics"
date: "2025-09-21"
templates_created: 15
templates_approved: 12
emails_sent: 10
first_reminders: 6
second_reminders: 3
final_notices: 1
bounce_rate: 0.05
delivery_rate: 0.95

# GSI1 for time series analytics
GSI1PK: "ANALYTICS"
GSI1SK: "date#{date}"
```

## Business Logic Functions

### 1. Duplicate Prevention
```python
def can_send_reminder(customer_id: str, reminder_type: str) -> bool:
    """
    Check if a reminder can be sent to avoid duplicates
    Business Rule: Only one reminder of each type per customer per month
    """
    # Query customer email state
    # Check if reminder_type was already sent in current billing cycle
    # Return boolean
```

### 2. Template Approval Workflow
```python
def approve_template(template_id: str, approver: str) -> dict:
    """
    Approve an email template for sending
    Transition: drafted -> approved
    """
    # Update template status
    # Record approver and timestamp
    # Trigger sending process if auto-send enabled
```

### 3. Email Sending with Tracking
```python
def send_email_template(template_id: str) -> dict:
    """
    Send approved email template and track in DynamoDB
    Creates email_sent record and updates customer_email_state
    """
    # Validate template is approved
    # Send via SES
    # Record sending details
    # Update customer state
    # Create analytics record
```

## Query Patterns

### 1. Get Pending Templates for Approval
```python
# Query by GSI1
GSI1PK = "TEMPLATE_STATUS#drafted"
# Sort by creation time (oldest first)
```

### 2. Check if Customer Already Received Reminder Type
```python
# Query customer email state
PK = "CUSTOMER#{customer_id}"
SK = "EMAIL_STATE"
# Check reminder_type_sent field
```

### 3. Get Email History for Customer
```python
# Query by PK
PK = "SENT#{customer_id}"
# SK begins_with "#"
# Sort by sent_date descending
```

### 4. Analytics Dashboard Queries
```python
# Daily/Monthly analytics
PK = "ANALYTICS#{date_range}"
# GSI1 for time series: GSI1PK = "ANALYTICS"
```

## Integration Points

### 1. AI Lambda Function Integration
- Templates created by Nova Pro with AI-generated content
- Personalization data passed from invoice/customer analysis
- Template quality scoring and optimization

### 2. SES Integration
- Send emails through Amazon SES
- Handle delivery status callbacks
- Process bounce/complaint notifications

### 3. Invoice Management Integration
- Link templates to specific invoices
- Pull customer and invoice data for personalization
- Trigger reminders based on payment due dates

## Performance Considerations

1. **Hot Partitions**: Use customer_id distribution to avoid hot partitions
2. **Time-based Queries**: GSI1 supports efficient time-range queries
3. **Batch Operations**: Support bulk template creation and sending
4. **TTL**: Consider TTL for old analytics data (retention policy)

## Security & Compliance

1. **Data Encryption**: Enable encryption at rest and in transit
2. **Access Control**: IAM policies for Lambda functions only
3. **PII Handling**: Customer email addresses and names (minimal exposure)
4. **Audit Trail**: All template changes and sending actions logged

## Error Handling & Monitoring

1. **Failed Sends**: Retry logic with exponential backoff
2. **Bounce Handling**: Update customer state, prevent future sends
3. **Template Validation**: Ensure required fields before approval
4. **CloudWatch Metrics**: Track sending rates, failures, approval times

---

This schema supports the MVP hackathon version while being extensible for production features.