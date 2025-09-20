# Invoice Management Logical Design

## Overview
This document describes the logical design for the Invoice Management system, implementing a highly scalable, event-driven architecture using AWS services and Domain-Driven Design principles.

## Architecture Pattern

### Hexagonal Architecture with AWS Adaptations
The system follows hexagonal architecture principles with AWS-native adaptations:

- **Domain Layer**: Pure business logic with no external dependencies
- **Application Layer**: Orchestration logic hosted in AWS Lambda functions
- **Infrastructure Layer**: AWS services acting as adapters (DynamoDB, EventBridge, API Gateway)

### Key Architectural Decisions
- **Compute**: AWS Lambda (serverless) for auto-scaling and cost optimization
- **Storage**: DynamoDB with single-table design for performance and scalability
- **Messaging**: Amazon EventBridge for domain event communication
- **API**: REST APIs through API Gateway with JWT authentication
- **State Management**: Domain-driven state machine in Lambda + DynamoDB

## Application Layer Design

### Lambda Functions

#### Command Functions (Write Operations)

**1. invoice-create-function**
- **Purpose**: Handle invoice creation requests
- **Trigger**: API Gateway POST /invoices
- **Memory**: 512 MB, Timeout: 30s
- **Process Flow**:
  1. Validate request payload
  2. Verify customer exists via Customer Management API
  3. Generate unique invoice number
  4. Create Invoice aggregate
  5. Save to DynamoDB
  6. Publish InvoiceCreated event
- **Dependencies**: Customer Management client, DynamoDB repository, EventBridge publisher

**2. invoice-status-update-function**
- **Purpose**: Handle invoice status transitions
- **Trigger**: API Gateway PUT /invoices/{id}/status
- **Memory**: 256 MB, Timeout: 15s
- **Process Flow**:
  1. Load Invoice aggregate from DynamoDB
  2. Validate status transition using domain service
  3. Execute status change with audit trail
  4. Save updated aggregate
  5. Publish InvoiceStatusChanged event
- **Business Rules**: Enforces valid state transitions (Draft → Sent → Overdue → Paid/Cancelled/Disputed)

**3. invoice-reminder-function**
- **Purpose**: Process manual reminder requests
- **Trigger**: API Gateway POST /invoices/{id}/reminder
- **Memory**: 256 MB, Timeout: 10s
- **Process Flow**:
  1. Load Invoice aggregate
  2. Validate reminder eligibility
  3. Publish ManualReminderRequested event
  4. Return confirmation
- **Integration**: Publishes events consumed by AI Email Automation

#### Query Functions (Read Operations)

**4. invoice-list-function**
- **Purpose**: Return paginated invoice lists with filtering
- **Trigger**: API Gateway GET /invoices
- **Memory**: 512 MB, Timeout: 30s
- **Query Patterns**:
  - All invoices with pagination
  - Filter by status using GSI2
  - Filter by customer using GSI1
  - Filter by date range using GSI3
- **Optimization**: ElastiCache for frequently accessed data

**5. invoice-details-function**
- **Purpose**: Return complete invoice details
- **Trigger**: API Gateway GET /invoices/{id}
- **Memory**: 256 MB, Timeout: 15s
- **Data Assembly**:
  - Invoice metadata and line items
  - Status history
  - Payment history via GSI4
  - Customer information (cached)

**6. invoice-search-function**
- **Purpose**: Full-text search across invoices
- **Trigger**: API Gateway GET /invoices/search
- **Memory**: 1024 MB, Timeout: 30s
- **Search Strategy**:
  - Invoice number exact match
  - Customer name partial match
  - Multi-GSI query with result ranking

#### Event Handler Functions

**7. payment-received-handler**
- **Purpose**: Process payment allocation to invoices
- **Trigger**: EventBridge PaymentReceived events
- **Memory**: 256 MB, Timeout: 15s
- **Process Flow**:
  1. Parse PaymentReceived event
  2. Load Invoice aggregate
  3. Apply payment using PaymentAllocationService
  4. Update invoice status if fully paid
  5. Publish InvoicePaid event if applicable
- **Idempotency**: Event ID-based deduplication

**8. customer-updated-handler**
- **Purpose**: Synchronize customer cache in invoices
- **Trigger**: EventBridge CustomerUpdated events
- **Memory**: 256 MB, Timeout: 20s
- **Process Flow**:
  1. Parse CustomerUpdated event
  2. Query affected invoices
  3. Update cached customer data
  4. Batch update DynamoDB records

**9. overdue-detection-function**
- **Purpose**: Detect and process overdue invoices
- **Trigger**: EventBridge scheduled rule (daily)
- **Memory**: 1024 MB, Timeout: 300s
- **Process Flow**:
  1. Query invoices with due_date < current_date AND status = SENT
  2. Update status to OVERDUE
  3. Publish InvoiceBecameOverdue events
  4. Trigger automatic first reminders

## Infrastructure Layer Design

### Data Persistence - DynamoDB

#### Single Table Design
```
Table: InvoiceManagement
Partition Key: PK (String)
Sort Key: SK (String)
Billing Mode: On-Demand
Encryption: AWS Managed
Point-in-Time Recovery: Enabled
```

#### Global Secondary Indexes
```
GSI1 - Customer Index:
  PK: CUSTOMER#{CustomerId}
  SK: INVOICE#{InvoiceNumber}
  Purpose: Query invoices by customer

GSI2 - Status Index:
  PK: STATUS#{Status}
  SK: DUEDATE#{DueDate}#{InvoiceId}
  Purpose: Query invoices by status, ordered by due date

GSI3 - Date Index:
  PK: DATE#{YYYY-MM}
  SK: CREATED#{CreatedDate}#{InvoiceId}
  Purpose: Query invoices by date range

GSI4 - Payment Index:
  PK: INVOICE#{InvoiceId}
  SK: PAYMENT#{PaymentDate}#{PaymentId}
  Purpose: Query payments for specific invoice
```

#### Data Model Structure
```json
Invoice Entity:
{
  "PK": "INVOICE#{InvoiceId}",
  "SK": "METADATA",
  "GSI1PK": "CUSTOMER#{CustomerId}",
  "GSI1SK": "INVOICE#{InvoiceNumber}",
  "GSI2PK": "STATUS#{Status}",
  "GSI2SK": "DUEDATE#{DueDate}#{InvoiceId}",
  "invoice_id": "uuid",
  "invoice_number": "INV-2024-000001",
  "customer_id": "uuid",
  "customer_name": "Acme Corp",
  "customer_email": "billing@acme.com",
  "status": "OVERDUE",
  "total_amount": 1000.00,
  "currency": "USD",
  "due_date": "2024-02-15",
  "version": 3
}

Line Item:
{
  "PK": "INVOICE#{InvoiceId}",
  "SK": "LINEITEM#{LineItemId}",
  "description": "Software License",
  "quantity": 1,
  "unit_price": 1000.00,
  "line_total": 1000.00
}

Status History:
{
  "PK": "INVOICE#{InvoiceId}",
  "SK": "HISTORY#{Timestamp}#{HistoryId}",
  "previous_status": "SENT",
  "new_status": "OVERDUE",
  "changed_at": "2024-02-16T00:01:00Z",
  "changed_by": "system",
  "reason": "Due date passed"
}
```

### Event-Driven Communication - EventBridge

#### Custom Event Bus
```yaml
Bus Name: invoice-management-events
Description: Dedicated bus for Invoice Management domain events
Encryption: AWS managed key
Archive: 7-day retention for replay
Schema Registry: invoice-management-schemas
```

#### Domain Events
```json
InvoiceCreated:
{
  "source": "invoice-management",
  "detail-type": "InvoiceCreated",
  "detail": {
    "invoiceId": "uuid",
    "invoiceNumber": "INV-2024-000001",
    "customerId": "uuid",
    "totalAmount": {"amount": 1000.00, "currency": "USD"},
    "dueDate": "2024-02-15",
    "occurredAt": "2024-01-15T10:30:00Z"
  }
}

InvoiceBecameOverdue:
{
  "source": "invoice-management",
  "detail-type": "InvoiceBecameOverdue",
  "detail": {
    "invoiceId": "uuid",
    "customerId": "uuid",
    "daysOverdue": 5,
    "totalAmount": {"amount": 1000.00, "currency": "USD"},
    "customerEmail": "billing@acme.com",
    "occurredAt": "2024-02-16T00:01:00Z"
  }
}
```

#### Event Routing Rules
```yaml
InvoiceOverdueToEmailAutomation:
  Pattern: {"source": ["invoice-management"], "detail-type": ["InvoiceBecameOverdue"]}
  Target: ai-email-automation-events bus

InvoiceEventsToAnalytics:
  Pattern: {"source": ["invoice-management"]}
  Target: dashboard-analytics-events bus

PaymentReceivedFromPaymentSystem:
  Pattern: {"source": ["payment-processing"], "detail-type": ["PaymentReceived"]}
  Target: payment-received-handler Lambda
```

### API Layer - API Gateway

#### REST API Configuration
```yaml
API Name: invoice-management-api
Type: REST API
Endpoint: Regional
Base URL: https://api.company.com/invoice-management/v1
Authentication: JWT Authorizer
Rate Limiting: Usage plans with API keys
CORS: Enabled for web applications
```

#### Resource Structure
```
/invoices
├── GET    (List invoices) → invoice-list-function
├── POST   (Create invoice) → invoice-create-function
├── /{id}
│   ├── GET    (Get details) → invoice-details-function
│   ├── PUT    (Update) → invoice-update-function
│   ├── /status
│   │   └── PUT (Update status) → invoice-status-update-function
│   └── /reminder
│       └── POST (Send reminder) → invoice-reminder-function
└── /search
    └── GET (Search) → invoice-search-function
```

#### Authentication & Authorization
```yaml
JWT Authorizer:
  Token Source: Authorization header
  Issuer: https://auth.company.com
  Algorithm: RS256

Authorization Scopes:
  finance-admin: Full access (read, write, delete, remind)
  finance-user: Limited access (read, remind)
  finance-viewer: Read-only access
```

## External Service Integration

### Stripe Payment Integration

#### Anti-Corruption Layer
```python
class StripePaymentAdapter:
    """Transforms Stripe events to domain events"""
    
    async def handle_webhook(self, webhook_payload, signature):
        # 1. Verify webhook signature
        # 2. Transform Stripe event to PaymentReceived domain event
        # 3. Publish to EventBridge
        
    def _transform_to_domain_event(self, stripe_event):
        if stripe_event['type'] == 'payment_intent.succeeded':
            return PaymentReceived(
                payment_id=PaymentId.generate(),
                invoice_id=self._extract_invoice_id(stripe_event),
                amount=Money(stripe_event['amount'] / 100, stripe_event['currency']),
                external_reference=ExternalReference('stripe', stripe_event['id'])
            )
```

#### Webhook Configuration
```yaml
Endpoint: /api/v1/webhooks/payments
Handler: stripe-webhook-handler
Events: payment_intent.succeeded, payment_intent.payment_failed
Security: Webhook signature verification, IP whitelist
```

### Customer Management Integration

#### Service Client with Circuit Breaker
```python
class CustomerManagementClient:
    """Resilient client for Customer Management service"""
    
    async def get_customer(self, customer_id):
        # 1. Check cache first
        # 2. Fetch from service with circuit breaker
        # 3. Update cache on success
        # 4. Return cached data during outages
```

#### Event Subscription
```yaml
CustomerUpdated Events:
  Source: customer-management-events
  Handler: customer-updated-handler
  Purpose: Synchronize customer cache in invoices
```

## Component Interactions and Data Flows

### Invoice Creation Flow
```
1. User → API Gateway (POST /invoices)
2. API Gateway → invoice-create-function
3. invoice-create-function → Customer Management API (validate customer)
4. invoice-create-function → DynamoDB (save invoice)
5. invoice-create-function → EventBridge (publish InvoiceCreated)
6. EventBridge → AI Email Automation (notification)
7. EventBridge → Dashboard Analytics (metrics)
```

### Payment Processing Flow
```
1. Stripe → stripe-webhook-handler (payment_intent.succeeded)
2. stripe-webhook-handler → EventBridge (publish PaymentReceived)
3. EventBridge → payment-received-handler
4. payment-received-handler → DynamoDB (load invoice, apply payment)
5. payment-received-handler → EventBridge (publish InvoicePaid if fully paid)
6. EventBridge → Dashboard Analytics (update metrics)
```

### Overdue Detection Flow
```
1. EventBridge Schedule → overdue-detection-function (daily)
2. overdue-detection-function → DynamoDB (query sent invoices past due date)
3. overdue-detection-function → DynamoDB (update status to OVERDUE)
4. overdue-detection-function → EventBridge (publish InvoiceBecameOverdue)
5. EventBridge → AI Email Automation (trigger first reminder)
```

### Manual Reminder Flow
```
1. User → API Gateway (POST /invoices/{id}/reminder)
2. API Gateway → invoice-reminder-function
3. invoice-reminder-function → DynamoDB (validate invoice)
4. invoice-reminder-function → EventBridge (publish ManualReminderRequested)
5. EventBridge → AI Email Automation (generate and send reminder)
```

## Performance and Scalability

### Caching Strategy
```yaml
ElastiCache Redis:
  - Invoice details: TTL 300 seconds
  - Customer reference data: TTL 3600 seconds
  - Search results: TTL 60 seconds
  - Frequently accessed invoices: TTL 900 seconds
```

### Auto-Scaling
```yaml
Lambda Concurrency:
  - Reserved concurrency for critical functions
  - Provisioned concurrency for low-latency requirements
  
DynamoDB:
  - On-demand billing for automatic scaling
  - Global Secondary Indexes scale independently
```

### Performance Optimization
```yaml
Connection Pooling:
  - Singleton DynamoDB clients
  - Connection reuse across Lambda invocations
  
Batch Operations:
  - BatchGetItem for multiple invoice queries
  - TransactWrite for atomic multi-item operations
```

## Security Design

### Authentication & Authorization
```yaml
API Gateway:
  - JWT-based authentication
  - Role-based authorization (RBAC)
  - API key management for rate limiting
  
Lambda Functions:
  - IAM roles with least privilege
  - VPC configuration for enhanced security
```

### Data Protection
```yaml
Encryption:
  - DynamoDB: AWS managed encryption at rest
  - EventBridge: AWS managed encryption
  - API Gateway: TLS 1.2+ for data in transit
  
Access Control:
  - Resource-based policies
  - Cross-account access controls
```

## Monitoring and Observability

### CloudWatch Metrics
```yaml
Business Metrics:
  - Invoices created per day
  - Payment processing success rate
  - Overdue invoice count
  - Reminder effectiveness

Technical Metrics:
  - Lambda function duration and errors
  - DynamoDB read/write capacity utilization
  - API Gateway request count and latency
  - EventBridge event processing metrics
```

### Distributed Tracing
```yaml
X-Ray Integration:
  - End-to-end request tracing
  - Lambda function performance analysis
  - DynamoDB operation tracing
  - External service call monitoring
```

### Logging Strategy
```yaml
Structured Logging:
  - JSON format with correlation IDs
  - Business event logging
  - Error tracking with context
  - Performance metrics logging
```

## Disaster Recovery

### Backup Strategy
```yaml
DynamoDB:
  - Point-in-time recovery (35 days)
  - Daily on-demand backups
  - Cross-region backup replication
  
Event Store:
  - Event replay capability
  - 7-day event archive retention
```

### High Availability
```yaml
Multi-AZ Deployment:
  - Lambda functions across multiple AZs
  - DynamoDB global tables for DR
  - API Gateway regional endpoints
  
RTO/RPO Targets:
  - RTO: 15 minutes
  - RPO: 5 minutes
```

## Cost Optimization

### Serverless Benefits
```yaml
Pay-per-Use:
  - Lambda: Pay only for execution time
  - DynamoDB: On-demand billing
  - API Gateway: Pay per request
  
Right-Sizing:
  - ARM64 Lambda functions for better price/performance
  - Appropriate memory allocation based on profiling
```

### Resource Optimization
```yaml
Caching:
  - Reduce DynamoDB read operations
  - Minimize external API calls
  
Batch Processing:
  - Bulk operations where possible
  - Efficient query patterns
```

## Implementation Roadmap

### Phase 1: Core Invoice Management
- Invoice CRUD operations
- Basic status management
- DynamoDB setup with GSIs

### Phase 2: Event-Driven Integration
- EventBridge setup and domain events
- Payment processing integration
- Customer Management integration

### Phase 3: Advanced Features
- Overdue detection and automation
- Manual reminder functionality
- Search and filtering capabilities

### Phase 4: Monitoring and Optimization
- Comprehensive monitoring setup
- Performance optimization
- Security hardening

## Conclusion

This logical design provides a comprehensive blueprint for implementing a highly scalable, event-driven Invoice Management system using AWS services and Domain-Driven Design principles. The architecture ensures:

- **Scalability**: Serverless components auto-scale based on demand
- **Reliability**: Event-driven patterns with retry and error handling
- **Maintainability**: Clear separation of concerns and hexagonal architecture
- **Performance**: Optimized data access patterns and caching strategies
- **Security**: Comprehensive authentication, authorization, and encryption
- **Observability**: Full monitoring, logging, and tracing capabilities

The design supports all user stories from the Invoice Management unit while providing a foundation for future enhancements and integrations with other bounded contexts in the billing intelligence system.