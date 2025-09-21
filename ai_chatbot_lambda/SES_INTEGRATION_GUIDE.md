# Amazon SES Integration Guide - Sandbox Mode

## Current SES Configuration

### Sending Quota
- **Max 24-hour send**: 200 emails
- **Max send rate**: 1 email per second  
- **Sent last 24 hours**: 2 emails
- **Status**: Sandbox Mode (production access not requested)

### Verified Identities
- ✅ **wongjiasoon@gmail.com** - Verified (Success)
- ⏳ **innovateai.com** - Pending verification
- **Verification Token**: JthTLenMp/rB4QnYscsOc+DMqPzlfJ8zxf8tNd8rKZY=

### Sandbox Mode Limitations
In sandbox mode, SES can only send emails to:
1. Verified email addresses
2. The AWS account's verified domains
3. Amazon SES mailbox simulator addresses

## Email System Architecture

### 1. Email Template System
- Templates stored in DynamoDB EmailTrackingTable
- Status workflow: `drafted` → `approved` → `sent`
- Personalization data for customer/invoice details
- HTML and text versions generated automatically

### 2. Duplicate Prevention
- Customer email state tracking in DynamoDB
- Business rule: Only one reminder of each type per customer per period
- Tracking fields: `first_reminder_sent`, `second_reminder_sent`, `final_notice_sent`

### 3. Sandbox Mode Implementation
For the hackathon MVP, we implement "sandbox mode" which:
- ✅ Creates proper email templates with AI-generated content
- ✅ Shows email preview functionality  
- ✅ Tracks email "sending" status in DynamoDB
- ✅ Demonstrates workflow without actually sending emails
- ✅ Provides realistic demo data for presentation

## API Endpoints

### 1. Draft Email - `POST /ai/draft-email`
**Request:**
```json
{
  "customer_id": "cust_001",
  "reminder_type": "first"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "template_id": "template_20250921_140523_cust_001", 
    "customer_name": "John Doe",
    "reminder_type": "first",
    "email_subject": "Payment Reminder - Invoice #INV-001",
    "email_preview": "Dear John Doe, we hope this message finds you well...",
    "overdue_invoices_count": 2,
    "total_overdue_amount": 1500.00,
    "status": "drafted",
    "created_at": "2025-09-21T14:05:23Z"
  }
}
```

### 2. Get Email Drafts - `GET /ai/email-drafts`
**Response:**
```json
{
  "success": true,
  "data": {
    "drafts": [
      {
        "template_id": "template_20250921_140523_cust_001",
        "customer_id": "cust_001", 
        "customer_name": "John Doe",
        "reminder_type": "first",
        "subject": "Payment Reminder - Invoice #INV-001",
        "created_at": "2025-09-21T14:05:23Z",
        "preview": "Dear John Doe, we hope this message..."
      }
    ],
    "total_pending": 1
  }
}
```

### 3. Approve and Send - `POST /ai/approve-and-send`
**Request:**
```json
{
  "template_id": "template_20250921_140523_cust_001",
  "approver": "admin"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "message": "Email approved and sent successfully (sandbox mode)",
    "template_id": "template_20250921_140523_cust_001",
    "customer_id": "cust_001",
    "reminder_type": "first", 
    "sent_date": "2025-09-21T14:10:15Z",
    "sandbox_simulation": {
      "simulation": "sandbox_mode",
      "would_send_to": "cust_001",
      "subject": "Payment Reminder - Invoice #INV-001",
      "delivery_status": "simulated_success"
    }
  }
}
```

### 4. Email History - `GET /ai/email-history`
**Response:**
```json
{
  "success": true,
  "data": {
    "recent_emails": [
      {
        "template_id": "template_20250921_140523_cust_001",
        "customer_id": "cust_001",
        "customer_name": "John Doe", 
        "reminder_type": "first",
        "subject": "Payment Reminder - Invoice #INV-001",
        "sent_at": "2025-09-21T14:10:15Z",
        "delivery_status": "delivered"
      }
    ],
    "daily_analytics": {
      "date": "2025-09-21",
      "emails_sent": 5,
      "first_reminders": 3,
      "second_reminders": 2, 
      "templates_created": 8,
      "templates_approved": 5,
      "delivery_rate": 1.0
    }
  }
}
```

## DynamoDB Schema

### Email Template Entity
```
PK: "TEMPLATE#{template_id}"
SK: "v#{version_number}"
Type: "email_template"
customer_id: "cust_001"
reminder_type: "first_reminder"
status: "drafted" | "approved" | "sent"
subject: "Payment Reminder - Invoice #INV-001"
body_text: "Dear John Doe..."
body_html: "<html>..."
personalization_data: {
  customer_name: "John Doe",
  total_amount_due: 1500.00
}
created_by: "ai_system"
created_at: "2025-09-21T14:05:23Z"
GSI1PK: "TEMPLATE_STATUS#{status}"
GSI1SK: "created_at#{created_at}"
```

### Email Sending Record
```
PK: "SENT#{customer_id}"
SK: "#{reminder_type}#{sent_date}"
Type: "email_sent"
template_id: "template_001"
customer_id: "cust_001"
reminder_type: "first_reminder"
sent_at: "2025-09-21T14:10:15Z"
ses_message_id: "sandbox-template_001"
delivery_status: "sent"
GSI1PK: "REMINDER_TYPE#{reminder_type}"
GSI1SK: "sent_at#{sent_at}"
```

### Customer Email State
```
PK: "CUSTOMER#{customer_id}"
SK: "EMAIL_STATE"
Type: "customer_email_state"
customer_id: "cust_001"
first_reminder_sent: "2025-09-21T14:10:15Z"
second_reminder_sent: null
final_notice_sent: null
last_email_sent: "2025-09-21T14:10:15Z"
total_emails_sent: 1
```

## Testing the Email System

### Test Sequence
1. **Create Draft**: Call `/ai/draft-email` with customer_id
2. **Review Drafts**: Call `/ai/email-drafts` to see pending templates
3. **Approve & Send**: Call `/ai/approve-and-send` with template_id
4. **Check History**: Call `/ai/email-history` to see sent emails and analytics

### Sandbox Mode Benefits
- ✅ Full workflow demonstration without actual email sending
- ✅ Complete audit trail in DynamoDB
- ✅ Realistic analytics and reporting
- ✅ Template preview functionality
- ✅ Duplicate prevention testing
- ✅ AI-generated professional content with Innovate AI branding

## Production Considerations

For production deployment (not needed for hackathon):
1. **Request Production Access**: Submit AWS SES production access request
2. **Domain Verification**: Complete innovateai.com domain verification 
3. **Bounce/Complaint Handling**: Implement SES notification handling
4. **Email Authentication**: Set up SPF, DKIM, DMARC records
5. **Monitoring**: CloudWatch metrics for delivery rates, bounces
6. **Compliance**: GDPR, CAN-SPAM compliance features

## Current Status: Ready for Demo

✅ **SES Configuration**: Sandbox mode active with verified sender
✅ **Lambda Integration**: Email functions deployed and tested
✅ **DynamoDB Schema**: Complete email tracking system
✅ **API Endpoints**: All 4 email endpoints implemented
✅ **Workflow**: Draft → Approve → Send → Track cycle
✅ **Analytics**: Daily email statistics tracking
✅ **Duplicate Prevention**: Business rules implemented
✅ **AI Integration**: Nova Pro generating professional emails

The email management system is ready for hackathon demonstration with full functionality in sandbox mode.