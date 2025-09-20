# Invoice Management Domain Model

## Overview
The Invoice Management bounded context handles invoice lifecycle, status management, and payment tracking. It maintains invoice state consistency and integrates with other contexts through domain events.

## Bounded Context Definition

### Context Responsibilities
- Invoice lifecycle management (creation, status transitions, completion)
- Invoice data operations (CRUD, filtering, searching, sorting)
- Manual reminder request handling
- Invoice-payment relationship tracking
- Invoice state consistency enforcement

### Context Boundaries
**Owns:**
- Invoice aggregate and its lifecycle
- Invoice operations and queries
- Manual reminder requests
- Invoice-payment allocations

**References:**
- Customer data (minimal cache from Customer Management)
- Payment data (via events from Payment context)

**Integrates With:**
- AI Email Automation (publishes reminder events)
- Dashboard Analytics (publishes status events)
- Customer Management (caches customer data)
- Payment Processing (receives payment events)

## Aggregates

### 1. Invoice Aggregate
**Aggregate Root:** Invoice
**Boundary:** Single invoice with line items and status history
**Consistency Rules:**
- State transitions must follow business rules
- Amount calculations must be consistent
- Due date must be after issue date

**Entities:**
- **Invoice** (Root): InvoiceId, InvoiceNumber, CustomerId, IssueDate, DueDate, TotalAmount, Status
- **InvoiceLineItem**: LineItemId, Description, Quantity, UnitPrice, LineTotal
- **InvoiceStatusHistory**: HistoryId, PreviousStatus, NewStatus, ChangedAt, ChangedBy, Reason

### 2. Payment Aggregate
**Aggregate Root:** Payment
**Boundary:** Payment transaction with allocation details
**Consistency Rules:**
- Payment amount must be positive
- Allocation cannot exceed payment amount
- Payment status must be valid

**Entities:**
- **Payment** (Root): PaymentId, Amount, Currency, PaymentDate, PaymentMethod, Status
- **PaymentAllocation**: AllocationId, InvoiceId, AllocatedAmount, AllocationDate

## Value Objects

### Core Value Objects
- **InvoiceNumber**: Unique business identifier (INV-YYYY-NNNNNN format)
- **Money**: Amount with currency validation
- **InvoiceStatus**: Enum (Draft, Sent, Overdue, Paid, Cancelled, Disputed)
- **CustomerReference**: CustomerId with cached name and email
- **DateRange**: Start and end dates for filtering
- **PaymentMethod**: Type and details for payment processing

### Supporting Value Objects
- **InvoiceId**: UUID-based identity
- **PaymentId**: UUID-based identity
- **ExternalReference**: External system references (Stripe, bank)
- **AuditInfo**: Creation and update tracking

## Domain Events

### Invoice Lifecycle Events
- **InvoiceCreated**: New invoice created
- **InvoiceStatusChanged**: Status transition occurred
- **InvoiceBecameOverdue**: Invoice passed due date
- **InvoicePaid**: Invoice fully paid

### Integration Events
- **PaymentReceived**: Payment allocated to invoice
- **ManualReminderRequested**: User requested manual reminder
- **InvoiceViewed**: Invoice details accessed

## Domain Services

### 1. InvoiceStatusTransitionService
Manages complex business rules for invoice status transitions.
- `CanTransition(currentStatus, newStatus): bool`
- `ValidateTransition(invoice, newStatus): ValidationResult`
- `ExecuteTransition(invoice, newStatus, reason): void`

### 2. OverdueInvoiceDetectionService
Identifies invoices that have become overdue.
- `DetectOverdueInvoices(asOfDate): List<Invoice>`
- `CalculateDaysOverdue(invoice, asOfDate): int`
- `ShouldTriggerReminder(invoice): bool`

### 3. PaymentAllocationService
Handles payment allocation across invoices.
- `AllocatePayment(payment, invoices): AllocationResult`
- `CalculateRemainingBalance(invoice): Money`
- `ValidateAllocation(payment, allocations): ValidationResult`

### 4. InvoiceNumberGenerationService
Generates unique invoice numbers.
- `GenerateNextNumber(): InvoiceNumber`
- `ValidateNumber(invoiceNumber): bool`
- `ReserveNumber(invoiceNumber): bool`

### 5. CustomerCacheService
Manages customer data caching.
- `UpdateCustomerCache(customerId, customerData): void`
- `ValidateCustomerReference(customerReference): bool`
- `SyncCustomerData(customerId): CustomerReference`

### 6. InvoiceValidationService
Validates invoice business rules.
- `ValidateInvoiceCreation(invoiceData): ValidationResult`
- `ValidateLineItems(lineItems): ValidationResult`
- `ValidateBusinessRules(invoice): ValidationResult`

## Repositories

### IInvoiceRepository
Primary persistence interface for Invoice aggregate.
- `Save(invoice): Task<void>`
- `GetById(invoiceId): Task<Invoice>`
- `GetByNumber(invoiceNumber): Task<Invoice>`
- `GetByCustomerId(customerId): Task<List<Invoice>>`
- `GetOverdueInvoices(asOfDate): Task<List<Invoice>>`
- `SearchInvoices(criteria): Task<PagedResult<Invoice>>`

### IPaymentRepository
Persistence interface for Payment aggregate.
- `Save(payment): Task<void>`
- `GetById(paymentId): Task<Payment>`
- `GetByInvoiceId(invoiceId): Task<List<Payment>>`
- `GetUnallocatedPayments(): Task<List<Payment>>`

### IInvoiceQueryRepository
Optimized read operations for UI scenarios.
- `GetInvoiceList(filters, sorting, pagination): Task<PagedResult<InvoiceListItem>>`
- `GetInvoiceDetails(invoiceId): Task<InvoiceDetails>`
- `SearchInvoices(searchTerm): Task<List<InvoiceSearchResult>>`

## Domain Policies

### Status Transition Policies
1. **InvoiceStatusTransitionPolicy**: Enforces valid state transitions (Draft → Sent → Overdue → Paid/Cancelled/Disputed)
2. **OverdueDetectionPolicy**: Automatically marks invoices overdue after due date
3. **InvoicePaymentCompletionPolicy**: Marks invoice as paid when fully allocated

### Payment Policies
4. **PaymentAllocationPolicy**: Allocates payments to oldest invoices first (FIFO)
5. **AutomaticReminderPolicy**: Sends first reminder automatically when overdue

### Validation Policies
6. **InvoiceCreationPolicy**: Validates invoice creation requirements
7. **LineItemValidationPolicy**: Validates line item business rules
8. **ManualReminderPolicy**: Requires confirmation for manual reminders

### Data Integrity Policies
9. **CustomerReferencePolicy**: Synchronizes customer cache
10. **AuditTrailPolicy**: Logs all invoice operations
11. **DataRetentionPolicy**: Maintains 7-year retention requirement
12. **NumberingPolicy**: Ensures sequential, unique invoice numbers

## Integration Patterns

### Event-Driven Integration
- **Outbound Events**: Published to EventBridge for loose coupling
- **Inbound Events**: Subscribed from Payment and Customer contexts
- **Event Sourcing**: Status history maintained for audit trail

### Anti-Corruption Layer
- **Customer Integration**: Minimal cached data with sync events
- **Payment Integration**: Separate aggregate with event coordination
- **External Systems**: Stripe integration through Payment aggregate

## Business Rules Summary

### Invoice State Machine
```
Draft → Sent → Overdue → (Paid | Cancelled | Disputed)
```

### Key Invariants
- Invoice amount must be positive
- Due date must be after issue date
- Status transitions must be valid
- Payment allocations cannot exceed payment amount
- Invoice numbers must be unique and sequential

### Automation Rules
- Invoices automatically become overdue after due date
- First reminders sent automatically for overdue invoices
- Invoice status updates to paid when fully allocated
- Customer cache synchronized via events

## Design Rationale

### Aggregate Design
- **Separate Payment Aggregate**: Different lifecycles and external integration needs
- **Customer Reference**: Avoids large aggregate, maintains performance
- **Status History Entity**: Provides audit trail within aggregate boundary

### Event-Driven Architecture
- **Loose Coupling**: Units can evolve independently
- **Scalability**: Asynchronous processing of non-critical operations
- **Audit Trail**: Complete history of domain events
- **Integration**: Clean boundaries between contexts

### Domain Service Usage
- **Complex Business Logic**: Rules spanning multiple entities
- **External Coordination**: Cross-aggregate operations
- **Stateless Operations**: Pure business logic without side effects