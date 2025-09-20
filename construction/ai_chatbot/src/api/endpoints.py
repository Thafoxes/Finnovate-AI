"""
FastAPI endpoints for the AI Payment Intelligence system.

This module provides REST API endpoints for:
- AI chatbot interactions
- Payment campaign management
- Customer and invoice operations
- Dashboard integration with finnovate-dashboard

The API follows RESTful principles and integrates with the application layer
using CQRS pattern with commands and queries.
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import logging
import uuid

from ..application.commands import (
    CreatePaymentCampaignCommand, SendPaymentReminderCommand,
    ProcessIncomingPaymentCommand, RecordCustomerResponseCommand,
    EscalatePaymentCampaignCommand, SchedulePaymentReminderCommand
)
from ..application.queries import (
    GetOverdueInvoicesQuery, GetPaymentCampaignsQuery,
    GetCustomerPaymentHistoryQuery, GetConversationHistoryQuery,
    GetCampaignPerformanceQuery, GetCustomerInsightsQuery
)
from ..application.handlers import CommandBus, QueryBus
from ..infrastructure import get_infrastructure_container, get_config
from ..domain.value_objects import CustomerId, InvoiceId, CampaignId, ConversationId


logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Payment Intelligence API",
    description="REST API for AI-powered payment collection system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
config = get_config()
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.security.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency injection setup
def get_infrastructure():
    """Dependency injection for infrastructure container."""
    return get_infrastructure_container()

def get_command_bus() -> CommandBus:
    """Get command bus instance."""
    infrastructure = get_infrastructure_container()
    return CommandBus(infrastructure)

def get_query_bus() -> QueryBus:
    """Get query bus instance."""
    infrastructure = get_infrastructure_container()
    return QueryBus(infrastructure)


# Request/Response Models
class ChatMessageRequest(BaseModel):
    """Request model for chat messages."""
    message: str = Field(..., description="Customer message content")
    customer_id: Optional[str] = Field(None, description="Customer ID if known")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID")
    invoice_id: Optional[str] = Field(None, description="Related invoice ID")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")


class ChatMessageResponse(BaseModel):
    """Response model for chat messages."""
    response: str = Field(..., description="AI-generated response")
    conversation_id: str = Field(..., description="Conversation ID")
    suggested_actions: List[str] = Field(default_factory=list, description="Suggested next actions")
    payment_options: Optional[List[Dict[str, Any]]] = Field(None, description="Available payment options")
    escalation_needed: bool = Field(False, description="Whether escalation is recommended")


class CreateCampaignRequest(BaseModel):
    """Request model for creating payment campaigns."""
    customer_id: str = Field(..., description="Customer ID")
    invoice_ids: List[str] = Field(..., description="List of overdue invoice IDs")
    campaign_type: str = Field("automated", description="Campaign type")
    escalation_strategy: str = Field("standard", description="Escalation strategy")
    priority: str = Field("normal", description="Campaign priority")


class SendReminderRequest(BaseModel):
    """Request model for sending payment reminders."""
    campaign_id: str = Field(..., description="Campaign ID")
    reminder_type: str = Field("email", description="Reminder type")
    custom_message: Optional[str] = Field(None, description="Custom message content")
    schedule_time: Optional[datetime] = Field(None, description="Scheduled send time")


class ProcessPaymentRequest(BaseModel):
    """Request model for processing payments."""
    invoice_id: str = Field(..., description="Invoice ID")
    customer_id: str = Field(..., description="Customer ID")
    amount: float = Field(..., gt=0, description="Payment amount")
    currency: str = Field("USD", description="Payment currency")
    payment_method: str = Field(..., description="Payment method")
    reference_number: Optional[str] = Field(None, description="Payment reference")


class CustomerResponseRequest(BaseModel):
    """Request model for recording customer responses."""
    conversation_id: str = Field(..., description="Conversation ID")
    customer_id: str = Field(..., description="Customer ID")
    message_content: str = Field(..., description="Customer message")
    response_type: str = Field("general", description="Response type")
    intent: Optional[str] = Field(None, description="Detected intent")


# API Routes

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "AI Payment Intelligence API",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/health")
async def health_check(infrastructure=Depends(get_infrastructure)):
    """Health check endpoint."""
    try:
        health_status = infrastructure.health_check()
        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


# Chat/Conversation Endpoints
@app.post("/api/v1/chat/message", response_model=ChatMessageResponse)
async def send_chat_message(
    request: ChatMessageRequest,
    background_tasks: BackgroundTasks,
    command_bus: CommandBus = Depends(get_command_bus),
    query_bus: QueryBus = Depends(get_query_bus)
):
    """
    Send a message to the AI chatbot.
    
    This endpoint handles customer interactions, generates AI responses,
    and manages conversation state.
    """
    try:
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Record customer message
        if request.customer_id:
            record_command = RecordCustomerResponseCommand(
                conversation_id=conversation_id,
                customer_id=request.customer_id,
                message_content=request.message,
                response_type="chat_message",
                intent=request.context.get("intent"),
                metadata=request.context
            )
            await command_bus.execute(record_command)
        
        # Generate AI response (this would integrate with Bedrock service)
        infrastructure = get_infrastructure_container()
        email_generator = infrastructure.get_email_generator()
        
        # Build conversation context
        customer_info = {
            "name": request.context.get("customer_name", "Customer"),
            "company": request.context.get("company_name"),
            "id": request.customer_id
        }
        
        # Get conversation history for context
        conversation_context = ""
        if request.conversation_id:
            try:
                history_query = GetConversationHistoryQuery(
                    conversation_id=ConversationId(conversation_id),
                    limit=10
                )
                history_result = await query_bus.execute(history_query)
                # Build context from history
                conversation_context = "\n".join([
                    f"Customer: {msg.get('content', '')}" 
                    for msg in history_result.messages[-5:]  # Last 5 messages
                ])
            except Exception as e:
                logger.warning(f"Could not retrieve conversation history: {e}")
        
        # Generate AI response
        ai_response = await email_generator.generate_conversation_response(
            customer_message=request.message,
            conversation_context=conversation_context,
            customer_info=customer_info
        )
        
        # Analyze response for suggested actions
        suggested_actions = []
        payment_options = None
        escalation_needed = False
        
        # Simple keyword analysis for suggestions
        message_lower = request.message.lower()
        if any(word in message_lower for word in ["pay", "payment", "settle"]):
            suggested_actions.append("Provide payment options")
            payment_options = [
                {"method": "bank_transfer", "description": "Direct bank transfer"},
                {"method": "credit_card", "description": "Credit card payment"},
                {"method": "payment_plan", "description": "Set up payment plan"}
            ]
        
        if any(word in message_lower for word in ["problem", "issue", "cannot", "unable"]):
            suggested_actions.append("Escalate to human agent")
            escalation_needed = True
        
        if any(word in message_lower for word in ["dispute", "disagree", "wrong"]):
            suggested_actions.append("Review invoice details")
            escalation_needed = True
        
        return ChatMessageResponse(
            response=ai_response,
            conversation_id=conversation_id,
            suggested_actions=suggested_actions,
            payment_options=payment_options,
            escalation_needed=escalation_needed
        )
        
    except Exception as e:
        logger.error(f"Chat message processing failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to process chat message")


# Campaign Management Endpoints
@app.post("/api/v1/campaigns")
async def create_payment_campaign(
    request: CreateCampaignRequest,
    command_bus: CommandBus = Depends(get_command_bus)
):
    """Create a new payment campaign."""
    try:
        command = CreatePaymentCampaignCommand(
            customer_id=request.customer_id,
            invoice_ids=request.invoice_ids,
            campaign_type=request.campaign_type,
            escalation_strategy=request.escalation_strategy,
            priority=request.priority
        )
        
        result = await command_bus.execute(command)
        
        return {
            "campaign_id": result.campaign_id,
            "status": "created",
            "message": "Payment campaign created successfully"
        }
        
    except Exception as e:
        logger.error(f"Campaign creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create campaign")


@app.get("/api/v1/campaigns")
async def get_payment_campaigns(
    customer_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    query_bus: QueryBus = Depends(get_query_bus)
):
    """Get payment campaigns with optional filtering."""
    try:
        query = GetPaymentCampaignsQuery(
            customer_id=CustomerId(customer_id) if customer_id else None,
            status=status,
            limit=limit
        )
        
        result = await query_bus.execute(query)
        
        return {
            "campaigns": result.campaigns,
            "total_count": result.total_count,
            "page_info": result.page_info
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch campaigns: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch campaigns")


@app.post("/api/v1/campaigns/{campaign_id}/reminders")
async def send_payment_reminder(
    campaign_id: str,
    request: SendReminderRequest,
    background_tasks: BackgroundTasks,
    command_bus: CommandBus = Depends(get_command_bus)
):
    """Send a payment reminder for a campaign."""
    try:
        command = SendPaymentReminderCommand(
            campaign_id=campaign_id,
            reminder_type=request.reminder_type,
            custom_message=request.custom_message,
            schedule_time=request.schedule_time
        )
        
        if request.schedule_time:
            # Schedule for later
            background_tasks.add_task(
                lambda: command_bus.execute(command)
            )
            return {"status": "scheduled", "message": "Reminder scheduled successfully"}
        else:
            # Send immediately
            result = await command_bus.execute(command)
            return {
                "status": "sent",
                "reminder_id": result.reminder_id,
                "message": "Reminder sent successfully"
            }
        
    except Exception as e:
        logger.error(f"Failed to send reminder: {e}")
        raise HTTPException(status_code=500, detail="Failed to send reminder")


# Payment Processing Endpoints
@app.post("/api/v1/payments")
async def process_payment(
    request: ProcessPaymentRequest,
    command_bus: CommandBus = Depends(get_command_bus)
):
    """Process a payment."""
    try:
        command = ProcessIncomingPaymentCommand(
            invoice_id=request.invoice_id,
            customer_id=request.customer_id,
            amount=request.amount,
            currency=request.currency,
            payment_method=request.payment_method,
            reference_number=request.reference_number
        )
        
        result = await command_bus.execute(command)
        
        return {
            "transaction_id": result.transaction_id,
            "status": result.status,
            "amount_processed": result.amount_processed,
            "message": "Payment processed successfully"
        }
        
    except Exception as e:
        logger.error(f"Payment processing failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to process payment")


# Data Query Endpoints
@app.get("/api/v1/invoices/overdue")
async def get_overdue_invoices(
    customer_id: Optional[str] = None,
    days_overdue: Optional[int] = None,
    min_amount: Optional[float] = None,
    limit: int = 50,
    query_bus: QueryBus = Depends(get_query_bus)
):
    """Get overdue invoices with optional filtering."""
    try:
        query = GetOverdueInvoicesQuery(
            customer_id=CustomerId(customer_id) if customer_id else None,
            days_overdue=days_overdue,
            min_amount=min_amount,
            limit=limit
        )
        
        result = await query_bus.execute(query)
        
        return {
            "invoices": result.invoices,
            "total_amount": result.total_amount,
            "total_count": result.total_count,
            "summary": result.summary
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch overdue invoices: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch overdue invoices")


@app.get("/api/v1/customers/{customer_id}/payment-history")
async def get_customer_payment_history(
    customer_id: str,
    limit: int = 50,
    query_bus: QueryBus = Depends(get_query_bus)
):
    """Get payment history for a specific customer."""
    try:
        query = GetCustomerPaymentHistoryQuery(
            customer_id=CustomerId(customer_id),
            limit=limit
        )
        
        result = await query_bus.execute(query)
        
        return {
            "customer_id": customer_id,
            "payment_history": result.payments,
            "total_paid": result.total_paid,
            "average_days_to_pay": result.average_days_to_pay,
            "payment_patterns": result.payment_patterns
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch payment history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch payment history")


@app.get("/api/v1/analytics/campaign-performance")
async def get_campaign_performance(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    query_bus: QueryBus = Depends(get_query_bus)
):
    """Get campaign performance analytics."""
    try:
        query = GetCampaignPerformanceQuery(
            start_date=start_date,
            end_date=end_date
        )
        
        result = await query_bus.execute(query)
        
        return {
            "performance_metrics": result.metrics,
            "success_rates": result.success_rates,
            "response_times": result.response_times,
            "escalation_rates": result.escalation_rates,
            "recommendations": result.recommendations
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch campaign performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch performance data")


# WebSocket endpoint for real-time chat (optional enhancement)
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/api/v1/chat/ws/{conversation_id}")
async def websocket_chat(websocket: WebSocket, conversation_id: str):
    """WebSocket endpoint for real-time chat."""
    await websocket.accept()
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            # Process message (similar to POST endpoint)
            # For now, just echo back
            response = f"Echo: {data}"
            
            # Send response back to client
            await websocket.send_text(response)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for conversation {conversation_id}")


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.now().isoformat()
        }
    )


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("AI Payment Intelligence API starting up...")
    
    # Initialize infrastructure
    from ..infrastructure import initialize_infrastructure
    container = initialize_infrastructure()
    
    # Validate configuration
    validation = container.health_check()
    if validation["status"] != "healthy":
        logger.warning(f"Startup validation issues: {validation}")
    
    logger.info("API startup completed")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("AI Payment Intelligence API shutting down...")
    # Cleanup tasks would go here
    logger.info("API shutdown completed")


if __name__ == "__main__":
    import uvicorn
    
    config = get_config()
    uvicorn.run(
        "api:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level=config.logging.level.lower()
    )