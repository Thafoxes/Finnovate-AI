# AI Chatbot System Implementation Plan

This plan outlines the steps to implement a Python-based AI chatbot system following the Domain-Driven Design logical design. The implementation will use in-memory repositories and event stores, and integrate with Amazon Bedrock Nova Micro model for AI capabilities.

## Implementation Steps

- [ ] **Step 1: Analyze Logical Design**
  - [x] Review the logical design document to understand domain model
  - [x] Identify core aggregates, entities, value objects, and domain services
  - [x] Understand the bounded context structure

- [ ] **Step 2: Create Project Structure**
  - [ ] Create the /construction/ai_chatbot/src/ directory structure
  - [ ] Set up domain, application, and infrastructure layers
  - [ ] Create package initialization files
  - [ ] Set up configuration for Nova Micro model

- [ ] **Step 3: Implement Domain Layer**
  - [ ] Create value objects (Intent, EntityMention, ConversationContext, PaymentStatus, ReminderLevel, etc.)
  - [ ] Implement entities (Message, ConversationAction, OverdueInvoice, PaymentReminder, etc.)
  - [ ] Implement aggregates (Conversation, ChatbotProfile, PaymentCampaign, EmailTemplate)
  - [ ] Create domain events (PaymentReminderSent, AlternativePaymentOffered, etc.)
  - [ ] Implement domain services (OverduePaymentService, EmailGenerationService, PaymentEscalationService)

- [ ] **Step 4: Implement Application Layer**
  - [ ] Create command and query handlers
  - [ ] Implement application services
  - [ ] Create DTOs for data transfer
  - [ ] Implement event handlers

- [ ] **Step 5: Implement Infrastructure Layer**
  - [ ] Create in-memory repositories
  - [ ] Implement in-memory event store
  - [ ] Create mock AWS service adapters (Bedrock Nova Micro, Comprehend, etc.)
  - [ ] Implement conversation persistence

- [ ] **Step 6: Create Integration Layer**
  - [ ] Implement Bedrock Nova Micro integration for email generation
  - [ ] Create mock services for invoice and customer data access
  - [ ] Implement overdue payment detection service
  - [ ] Create payment reminder escalation logic
  - [ ] Implement alternative payment options service

- [ ] **Step 7: Create React Integration**
  - [ ] Create dedicated chatbot page component for finnovate-dashboard
  - [ ] Implement chat interface UI with Material-UI (full page layout)
  - [ ] Add navigation route for "/chatbot" or "/ai-assistant"
  - [ ] Integrate with existing Redux store for user session and invoice/customer data
  - [ ] Create API service for chatbot communication

- [ ] **Step 8: Create Demo Script**
  - [ ] Implement conversation flow demo for backend testing
  - [ ] Create sample scenarios (overdue invoice queries, email generation, etc.)
  - [ ] Add test data setup for development

- [ ] **Step 8: Add Error Handling and Logging**
  - [ ] Implement comprehensive error handling
  - [ ] Add logging throughout the system
  - [ ] Create validation mechanisms
  - [ ] Add retry logic for AI service calls

- [ ] **Step 9: Create Configuration and Dependencies**
  - [ ] Create requirements.txt file for Python backend
  - [ ] Update package.json for React frontend dependencies
  - [ ] Set up configuration management for both frontend and backend
  - [ ] Create environment variable handling
  - [ ] Add dependency injection setup

- [ ] **Step 10: Deploy and Integration Testing**
  - [ ] Test chatbot integration within React dashboard
  - [ ] Validate conversation flows in web interface
  - [ ] Test error scenarios in production-like environment
  - [ ] Verify API communication between frontend and backend

## Technical Decisions

### Model Configuration
- **AI Model**: Amazon Bedrock Nova Micro (as specified)
- **Fallback**: Mock responses for development/testing
- **Prompt Engineering**: Optimized for financial domain with Nova Micro limitations

### File Structure
```
/construction/ai_chatbot/src/
├── domain/
│   ├── aggregates/
│   ├── entities/
│   ├── value_objects/
│   ├── events/
│   ├── services/
│   └── repositories/
├── application/
│   ├── handlers/
│   ├── services/
│   └── dtos/
├── infrastructure/
│   ├── repositories/
│   ├── event_store/
│   ├── aws_adapters/
│   └── mocks/
├── api/
│   ├── endpoints/
│   ├── middleware/
│   └── websockets/
├── shared/
│   ├── config/
│   └── utils/
├── demo.py
└── requirements.txt

/finnovate-dashboard/src/
├── components/
│   ├── chatbot/
│   │   ├── ChatInterface.tsx
│   │   ├── ChatMessage.tsx
│   │   ├── ChatInput.tsx
│   │   ├── OverdueInvoiceCard.tsx
│   │   └── PaymentReminderPanel.tsx
│   └── ...existing components
├── pages/
│   ├── ChatbotPage.tsx
│   └── ...existing pages
├── services/
│   ├── chatbotApi.ts
│   ├── overduePaymentApi.ts
│   └── ...existing services
├── store/
│   ├── chatbot/
│   │   ├── chatbotSlice.ts
│   │   └── chatbotTypes.ts
│   └── ...existing store
└── types/
    ├── chatbot.ts
    ├── overduePayment.ts
    └── ...existing types
```

### Implementation Assumptions
- In-memory storage for conversations and payment campaigns (MVP scope)
- Mock AWS service responses for local development
- User authentication via existing dashboard session
- Dedicated chatbot page in finnovate-dashboard navigation
- Material-UI components for consistent design with existing dashboard
- Redux integration for user session and invoice/customer data access
- REST API communication between frontend and backend
- No conversation history persistence (MVP/hackathon scope)
- Focus on overdue payment management workflow
- Domain-Driven Design principles with clear bounded contexts

## Requirements Clarification (Confirmed)

1. ✅ **Accessibility**: Specific navigation page only - dedicated chatbot page
2. ✅ **Authentication**: Current user session from dashboard
3. ✅ **Data Access**: Access to current user's invoice and customer data
4. ✅ **UI Pattern**: Dedicated page for chatbot (not floating button)
5. ✅ **Persistence**: No conversation history persistence (MVP/hackathon scope)
6. ✅ **Integration Scope**: Invoices and customers only for overdue payment management

## Domain-Driven Design Structure

### Bounded Context: Payment Intelligence
**Core Responsibility**: Automate and optimize overdue payment collection through AI-powered communication

### Domain Model Components

#### Aggregates (following DDD principles)
1. **PaymentCampaign** (Aggregate Root)
   - Manages the entire lifecycle of payment collection for an invoice
   - Contains payment reminders, escalation logic, and alternative payment offers
   - Enforces business rules around reminder frequency and escalation triggers

2. **Conversation** (Aggregate Root)
   - Handles AI chatbot interactions with users
   - Maintains conversation context and state
   - Coordinates with PaymentCampaign for payment-related actions

3. **ChatbotProfile** (Aggregate Root)
   - Defines AI assistant capabilities and personality
   - Contains prompt templates and response patterns
   - Manages domain-specific knowledge for financial communications

#### Entities
- **PaymentReminder**: Individual reminder instances with status and delivery info
- **OverdueInvoice**: Extended invoice entity with payment collection metadata
- **Message**: Chat messages with context and intent recognition
- **AlternativePaymentOption**: Different payment methods offered to customers

#### Value Objects
- **ReminderLevel**: (First, Second, Third, Escalated)
- **PaymentStatus**: (Pending, Overdue, PartiallyPaid, Paid, InDefault)
- **MessageIntent**: (PaymentInquiry, ReminderRequest, EscalationTrigger)
- **ConversationContext**: Current state and history for AI decision making

#### Domain Services
- **OverduePaymentService**: Identifies and prioritizes overdue invoices
- **ReminderEscalationService**: Manages the 3-step reminder process
- **AlternativePaymentService**: Offers payment plans and options
- **EmailGenerationService**: Creates personalized payment reminder emails
- **PaymentIntelligenceService**: AI-powered payment prediction and optimization

#### Domain Events
- **PaymentReminderSent**: When a reminder is successfully delivered
- **PaymentReminderFailed**: When reminder delivery fails
- **EscalationTriggered**: When moving to alternative payment options
- **PaymentReceived**: When payment is confirmed
- **ConversationStarted**: When user initiates chatbot interaction

## Core Business Use Case
**Primary Goal**: AI-powered overdue payment management system
- Send intelligent email reminders for overdue payments
- Escalate to alternative payment options after 3rd reminder
- Automate customer communication with personalized messaging
- Track payment follow-up campaigns

## Integration Strategy

### Frontend Integration
- **UI Pattern**: Dedicated chatbot page with full-screen chat interface
- **Navigation**: Add "/ai-assistant" route to existing dashboard navigation
- **Styling**: Material-UI components matching dashboard theme
- **State Management**: Redux slice for chatbot state, leveraging existing invoice/customer data
- **API Communication**: REST endpoints for chat and payment management operations
- **Authentication**: Leverage existing dashboard user session

### Backend Integration
- **API Layer**: FastAPI for REST endpoints focused on overdue payment management
- **Domain Model**: DDD approach with Payment Management bounded context
- **Data Access**: Integration with existing invoice/customer data via mock services
- **Business Logic**: Payment reminder escalation, alternative payment options
- **Deployment**: Separate microservice for payment intelligence

Please review this updated plan and confirm your approval before I proceed with the implementation.