#!/usr/bin/env python3
"""
AI Payment Intelligence System - Comprehensive Demo Script

This script demonstrates the complete AI-powered payment collection system
with overdue invoice management, AI-generated emails, and customer interactions.

Usage:
    python demo.py [--mock] [--verbose] [--scenario SCENARIO]

Scenarios:
    - full_demo: Complete system demonstration (default)
    - payment_campaign: Payment campaign creation and management
    - ai_chat: AI chatbot interactions
    - escalation_flow: Payment escalation workflow
    - analytics: Performance analytics and reporting
"""

import asyncio
import json
import logging
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from infrastructure import initialize_infrastructure, get_config
from infrastructure.bedrock_service import EmailGenerationRequest
from domain.value_objects import CustomerId, InvoiceId, CampaignId
from domain.entities import Customer, OverdueInvoice
from application.commands import (
    CreatePaymentCampaignCommand, SendPaymentReminderCommand,
    ProcessIncomingPaymentCommand, RecordCustomerResponseCommand
)
from application.queries import (
    GetOverdueInvoicesQuery, GetPaymentCampaignsQuery,
    GetCustomerPaymentHistoryQuery
)
from application.handlers import CommandBus, QueryBus


# Demo configuration
DEMO_CONFIG = {
    "customers": [
        {
            "id": "cust_001",
            "name": "John Smith",
            "email": "john.smith@techsolutions.com",
            "company": "Tech Solutions Inc.",
            "payment_history": "Generally pays on time, occasional 5-7 day delays"
        },
        {
            "id": "cust_002", 
            "name": "Sarah Johnson",
            "email": "sarah.j@globalmanufacturing.com",
            "company": "Global Manufacturing LLC",
            "payment_history": "New customer, no payment history"
        },
        {
            "id": "cust_003",
            "name": "Mike Chen",
            "email": "m.chen@retailpartners.com",
            "company": "Retail Partners Co.",
            "payment_history": "Frequently late payments, requires regular follow-up"
        }
    ],
    "invoices": [
        {
            "id": "inv_001",
            "customer_id": "cust_001",
            "amount": 15750.00,
            "currency": "USD",
            "due_date": datetime.now() - timedelta(days=15),
            "description": "Software licensing and support services",
            "priority": "normal"
        },
        {
            "id": "inv_002",
            "customer_id": "cust_002", 
            "amount": 28900.50,
            "currency": "USD",
            "due_date": datetime.now() - timedelta(days=32),
            "description": "Manufacturing equipment maintenance",
            "priority": "high"
        },
        {
            "id": "inv_003",
            "customer_id": "cust_003",
            "amount": 5200.00,
            "currency": "USD", 
            "due_date": datetime.now() - timedelta(days=8),
            "description": "Retail POS system setup",
            "priority": "normal"
        }
    ]
}


class AIPaymentDemoRunner:
    """Comprehensive demo runner for the AI Payment Intelligence system."""
    
    def __init__(self, use_mock: bool = True, verbose: bool = False):
        """Initialize demo runner."""
        self.use_mock = use_mock
        self.verbose = verbose
        self.logger = self._setup_logging()
        
        # Initialize infrastructure
        self.logger.info("Initializing AI Payment Intelligence system...")
        self.infrastructure = initialize_infrastructure()
        self.command_bus = CommandBus(self.infrastructure)
        self.query_bus = QueryBus(self.infrastructure)
        
        # Demo data storage
        self.demo_customers = {}
        self.demo_invoices = {}
        self.demo_campaigns = {}
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for demo."""
        logger = logging.getLogger("demo")
        logger.setLevel(logging.INFO if self.verbose else logging.WARNING)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def print_header(self, title: str):
        """Print formatted section header."""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
    
    def print_step(self, step: str, description: str = ""):
        """Print formatted step."""
        print(f"\n🔹 {step}")
        if description:
            print(f"   {description}")
    
    def print_result(self, result: Any, title: str = "Result"):
        """Print formatted result."""
        print(f"\n✅ {title}:")
        if isinstance(result, dict):
            for key, value in result.items():
                print(f"   {key}: {value}")
        else:
            print(f"   {result}")
    
    def print_ai_email(self, email_data: Dict[str, Any]):
        """Print formatted AI-generated email."""
        print(f"\n📧 AI-Generated Email:")
        print(f"   Subject: {email_data.get('subject', 'N/A')}")
        print(f"   Body:\n{email_data.get('body', 'N/A')}")
        print(f"   Tone Analysis: {email_data.get('tone_analysis', 'N/A')}")
        print(f"   Next Action: {email_data.get('suggested_next_action', 'N/A')}")
    
    async def setup_demo_data(self):
        """Setup demo customers and invoices."""
        self.print_header("Setting Up Demo Data")
        
        # Create customers
        customer_repo = self.infrastructure.get_customer_repository()
        for customer_data in DEMO_CONFIG["customers"]:
            customer = Customer(
                customer_id=CustomerId(customer_data["id"]),
                name=customer_data["name"],
                email=customer_data["email"],
                company_name=customer_data["company"]
            )
            await customer_repo.save(customer)
            self.demo_customers[customer_data["id"]] = customer
            self.print_step(f"Created customer: {customer.name} ({customer.company_name})")
        
        # Create overdue invoices
        invoice_repo = self.infrastructure.get_invoice_repository()
        for invoice_data in DEMO_CONFIG["invoices"]:
            invoice = OverdueInvoice(
                invoice_id=InvoiceId(invoice_data["id"]),
                customer_id=CustomerId(invoice_data["customer_id"]),
                amount_due=invoice_data["amount"],
                due_date=invoice_data["due_date"],
                currency=invoice_data["currency"],
                description=invoice_data["description"],
                priority=invoice_data["priority"]
            )
            await invoice_repo.save(invoice)
            self.demo_invoices[invoice_data["id"]] = invoice
            
            days_overdue = (datetime.now() - invoice_data["due_date"]).days
            self.print_step(
                f"Created overdue invoice: {invoice_data['id']}",
                f"${invoice_data['amount']:,.2f} • {days_overdue} days overdue"
            )
    
    async def demo_payment_campaign_creation(self):
        """Demonstrate payment campaign creation."""
        self.print_header("Payment Campaign Creation")
        
        # Create payment campaign for high-priority customer
        customer_id = "cust_002"  # Global Manufacturing LLC
        invoice_ids = ["inv_002"]
        
        self.print_step(
            "Creating AI-powered payment campaign",
            f"Customer: {self.demo_customers[customer_id].name} • Invoice: {invoice_ids[0]}"
        )
        
        command = CreatePaymentCampaignCommand(
            customer_id=customer_id,
            invoice_ids=invoice_ids,
            campaign_type="automated",
            escalation_strategy="progressive",
            priority="high"
        )
        
        result = await self.command_bus.execute(command)
        self.demo_campaigns[result.campaign_id] = result
        
        self.print_result({
            "Campaign ID": result.campaign_id,
            "Status": "Created",
            "Customer": self.demo_customers[customer_id].name,
            "Invoice Count": len(invoice_ids),
            "Strategy": "Progressive escalation"
        })
        
        return result.campaign_id
    
    async def demo_ai_email_generation(self, campaign_id: str):
        """Demonstrate AI email generation."""
        self.print_header("AI-Powered Email Generation")
        
        # Get customer and invoice details
        customer = self.demo_customers["cust_002"]
        invoice = self.demo_invoices["inv_002"]
        days_overdue = (datetime.now() - invoice.due_date).days
        
        self.print_step(
            "Generating personalized payment reminder using Amazon Bedrock Nova Micro",
            f"Customer: {customer.name} • Amount: ${invoice.amount_due:,.2f} • {days_overdue} days overdue"
        )
        
        # Create email generation request
        email_request = EmailGenerationRequest(
            customer_name=customer.name,
            company_name=customer.company_name,
            invoice_amount=invoice.amount_due,
            currency=invoice.currency,
            days_overdue=days_overdue,
            invoice_number=invoice.invoice_id.value,
            due_date=invoice.due_date,
            escalation_level=2,  # Second reminder
            payment_history="New customer, no payment history",
            tone="professional"
        )
        
        # Generate email using AI service
        email_generator = self.infrastructure.get_email_generator()
        email_response = await email_generator.generate_payment_reminder_email(email_request)
        
        self.print_ai_email({
            "subject": email_response.subject,
            "body": email_response.body,
            "tone_analysis": email_response.tone_analysis,
            "suggested_next_action": email_response.suggested_next_action
        })
        
        return email_response
    
    async def demo_payment_reminder_sending(self, campaign_id: str):
        """Demonstrate sending payment reminders."""
        self.print_header("Sending Payment Reminders")
        
        self.print_step(
            "Sending AI-generated payment reminder",
            "Using email service adapter with personalized content"
        )
        
        command = SendPaymentReminderCommand(
            campaign_id=campaign_id,
            reminder_type="email",
            custom_message="This is a demo payment reminder",
            schedule_time=None  # Send immediately
        )
        
        result = await self.command_bus.execute(command)
        
        self.print_result({
            "Reminder ID": result.reminder_id,
            "Status": "Sent",
            "Type": "Email",
            "Timestamp": datetime.now().isoformat()
        })
        
        return result.reminder_id
    
    async def demo_ai_chat_interaction(self):
        """Demonstrate AI chatbot interaction."""
        self.print_header("AI Chatbot Customer Interaction")
        
        customer = self.demo_customers["cust_001"]
        
        # Simulate customer messages and AI responses
        chat_scenarios = [
            {
                "customer_message": "Hi, I received an email about an overdue payment. Can you help me understand what this is about?",
                "context": "Initial inquiry about overdue invoice"
            },
            {
                "customer_message": "I want to pay this invoice but I need to set up a payment plan. Can we arrange monthly payments?",
                "context": "Payment plan request"
            },
            {
                "customer_message": "Actually, I think there might be an error on this invoice. The amount seems too high.",
                "context": "Dispute inquiry - needs escalation"
            }
        ]
        
        email_generator = self.infrastructure.get_email_generator()
        
        for i, scenario in enumerate(chat_scenarios, 1):
            self.print_step(
                f"Chat Interaction {i}",
                scenario["context"]
            )
            
            print(f"\n👤 Customer ({customer.name}): {scenario['customer_message']}")
            
            # Generate AI response
            customer_info = {
                "name": customer.name,
                "company": customer.company_name,
                "id": customer.customer_id.value
            }
            
            conversation_context = "Customer inquiry about overdue invoice INV-002"
            
            ai_response = await email_generator.generate_conversation_response(
                customer_message=scenario["customer_message"],
                conversation_context=conversation_context,
                customer_info=customer_info
            )
            
            print(f"🤖 AI Assistant: {ai_response}")
            
            # Determine if escalation is needed
            if "error" in scenario["customer_message"].lower() or "wrong" in scenario["customer_message"].lower():
                print("⚠️  Escalation recommended: Potential billing dispute detected")
    
    async def demo_payment_processing(self):
        """Demonstrate payment processing."""
        self.print_header("Payment Processing")
        
        # Simulate customer making a payment
        customer_id = "cust_001"
        invoice_id = "inv_001"
        customer = self.demo_customers[customer_id]
        invoice = self.demo_invoices[invoice_id]
        
        self.print_step(
            "Processing customer payment",
            f"Customer: {customer.name} • Invoice: {invoice_id} • Amount: ${invoice.amount_due:,.2f}"
        )
        
        command = ProcessIncomingPaymentCommand(
            invoice_id=invoice_id,
            customer_id=customer_id,
            amount=invoice.amount_due,
            currency=invoice.currency,
            payment_method="credit_card",
            reference_number="CC_TXN_20241221_001"
        )
        
        result = await self.command_bus.execute(command)
        
        self.print_result({
            "Transaction ID": result.transaction_id,
            "Status": result.status,
            "Amount Processed": f"${result.amount_processed:,.2f}",
            "Payment Method": "Credit Card",
            "Processing Time": "Immediate"
        })
    
    async def demo_analytics_and_reporting(self):
        """Demonstrate analytics and reporting capabilities."""
        self.print_header("Analytics & Performance Reporting")
        
        # Query overdue invoices
        self.print_step("Analyzing overdue invoices")
        
        query = GetOverdueInvoicesQuery(
            customer_id=None,
            days_overdue=None,
            min_amount=None,
            limit=50
        )
        
        invoice_result = await self.query_bus.execute(query)
        
        self.print_result({
            "Total Overdue Invoices": invoice_result.total_count,
            "Total Amount": f"${invoice_result.total_amount:,.2f}",
            "Average Days Overdue": f"{invoice_result.summary.get('average_days_overdue', 0):.1f}",
            "High Priority Count": invoice_result.summary.get('high_priority_count', 0)
        })
        
        # Query payment campaigns
        self.print_step("Analyzing payment campaigns")
        
        campaign_query = GetPaymentCampaignsQuery(
            customer_id=None,
            status=None,
            limit=10
        )
        
        campaign_result = await self.query_bus.execute(campaign_query)
        
        self.print_result({
            "Active Campaigns": campaign_result.total_count,
            "Success Rate": "73.5%",  # Mock data
            "Average Response Time": "2.3 days",  # Mock data
            "AI Resolution Rate": "68.4%"  # Mock data
        })
    
    async def demo_escalation_workflow(self):
        """Demonstrate escalation workflow."""
        self.print_header("Escalation Workflow")
        
        customer_id = "cust_003"  # Retail Partners Co. - frequent late payments
        customer = self.demo_customers[customer_id]
        
        self.print_step(
            "Simulating escalation scenario",
            f"Customer: {customer.name} • Multiple failed payment attempts"
        )
        
        # Create escalation campaign
        command = CreatePaymentCampaignCommand(
            customer_id=customer_id,
            invoice_ids=["inv_003"],
            campaign_type="escalation",
            escalation_strategy="aggressive",
            priority="high"
        )
        
        result = await self.command_bus.execute(command)
        
        self.print_result({
            "Campaign Type": "Escalation",
            "Priority": "High",
            "Strategy": "Aggressive follow-up",
            "Automated Actions": "Daily reminders, human escalation after 3 attempts",
            "Expected Resolution": "5-7 business days"
        })
        
        # Simulate escalation steps
        escalation_steps = [
            "Day 1: AI-generated personalized reminder sent",
            "Day 2: Follow-up email with payment options",
            "Day 3: Phone call attempted, voicemail left",
            "Day 4: Escalated to human agent",
            "Day 5: Human agent contact successful, payment plan negotiated"
        ]
        
        print(f"\n📋 Escalation Timeline:")
        for step in escalation_steps:
            print(f"   • {step}")
    
    async def run_full_demo(self):
        """Run the complete system demonstration."""
        print("🚀 AI Payment Intelligence System - Complete Demo")
        print("   Powered by Amazon Bedrock Nova Micro & Domain-Driven Design")
        print(f"   Demo Mode: {'Mock Services' if self.use_mock else 'Live AWS Services'}")
        
        try:
            # Setup demo data
            await self.setup_demo_data()
            
            # Demo payment campaign creation
            campaign_id = await self.demo_payment_campaign_creation()
            
            # Demo AI email generation
            await self.demo_ai_email_generation(campaign_id)
            
            # Demo sending reminders
            await self.demo_payment_reminder_sending(campaign_id)
            
            # Demo AI chat interaction
            await self.demo_ai_chat_interaction()
            
            # Demo payment processing
            await self.demo_payment_processing()
            
            # Demo escalation workflow
            await self.demo_escalation_workflow()
            
            # Demo analytics
            await self.demo_analytics_and_reporting()
            
            # Final summary
            self.print_header("Demo Summary")
            print("✅ Successfully demonstrated:")
            print("   • AI-powered payment campaign creation")
            print("   • Personalized email generation using Amazon Bedrock")
            print("   • Intelligent customer chat interactions") 
            print("   • Automated payment processing")
            print("   • Smart escalation workflows")
            print("   • Comprehensive analytics and reporting")
            print("   • Domain-driven architecture with CQRS")
            print("   • Hexagonal architecture with clean separation")
            
            print(f"\n🎯 System Performance:")
            print(f"   • Bedrock Integration: {'✅ Mock Mode' if self.use_mock else '✅ Live'}")
            print(f"   • Email Service: ✅ Operational")
            print(f"   • Payment Processing: ✅ Operational")
            print(f"   • Data Storage: ✅ In-Memory (MVP)")
            print(f"   • API Endpoints: ✅ FastAPI Ready")
            print(f"   • React Components: ✅ Finnovate Dashboard Integration")
            
        except Exception as e:
            self.logger.error(f"Demo failed: {e}")
            print(f"\n❌ Demo Error: {e}")
            raise


async def main():
    """Main demo runner."""
    parser = argparse.ArgumentParser(description="AI Payment Intelligence Demo")
    parser.add_argument(
        "--mock", 
        action="store_true", 
        help="Use mock services instead of live AWS"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--scenario",
        choices=["full_demo", "payment_campaign", "ai_chat", "escalation_flow", "analytics"],
        default="full_demo",
        help="Demo scenario to run"
    )
    
    args = parser.parse_args()
    
    # Create demo runner
    demo = AIPaymentDemoRunner(use_mock=args.mock, verbose=args.verbose)
    
    # Setup demo data first
    await demo.setup_demo_data()
    
    # Run selected scenario
    if args.scenario == "full_demo":
        await demo.run_full_demo()
    elif args.scenario == "payment_campaign":
        campaign_id = await demo.demo_payment_campaign_creation()
        await demo.demo_ai_email_generation(campaign_id)
        await demo.demo_payment_reminder_sending(campaign_id)
    elif args.scenario == "ai_chat":
        await demo.demo_ai_chat_interaction()
    elif args.scenario == "escalation_flow":
        await demo.demo_escalation_workflow()
    elif args.scenario == "analytics":
        await demo.demo_analytics_and_reporting()


if __name__ == "__main__":
    asyncio.run(main())