"""
Amazon Bedrock service adapter for AI-powered email generation.

This module provides integration with Amazon Bedrock Nova Micro model
for generating personalized payment reminder emails and customer communications.
"""

import json
import boto3
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from ..domain.value_objects import CustomerId, InvoiceId
from ..domain.entities import Customer, OverdueInvoice


logger = logging.getLogger(__name__)


@dataclass
class EmailGenerationRequest:
    """Request for generating an email using AI."""
    customer_name: str
    company_name: Optional[str]
    invoice_amount: float
    currency: str
    days_overdue: int
    invoice_number: str
    due_date: datetime
    escalation_level: int  # 1, 2, or 3
    payment_history: Optional[str] = None
    custom_context: Optional[str] = None
    tone: str = "professional"  # professional, friendly, firm, urgent


@dataclass
class EmailGenerationResponse:
    """Response from AI email generation."""
    subject: str
    body: str
    tone_analysis: str
    suggested_next_action: str
    escalation_recommendation: Optional[str] = None


class BedrockServiceError(Exception):
    """Custom exception for Bedrock service errors."""
    pass


class BedrockEmailGenerator:
    """Service for generating AI-powered payment emails using Amazon Bedrock."""
    
    def __init__(self, region_name: str = "us-east-1", model_id: str = "amazon.nova-micro-v1:0"):
        """
        Initialize Bedrock email generator.
        
        Args:
            region_name: AWS region for Bedrock service
            model_id: Bedrock model identifier
        """
        self.model_id = model_id
        self.region_name = region_name
        self._client = None
    
    @property
    def client(self):
        """Lazy initialization of Bedrock client."""
        if self._client is None:
            try:
                self._client = boto3.client(
                    'bedrock-runtime',
                    region_name=self.region_name
                )
            except Exception as e:
                logger.error(f"Failed to initialize Bedrock client: {e}")
                raise BedrockServiceError(f"Failed to connect to Bedrock: {e}")
        return self._client
    
    async def generate_payment_reminder_email(
        self, 
        request: EmailGenerationRequest
    ) -> EmailGenerationResponse:
        """
        Generate a personalized payment reminder email.
        
        Args:
            request: Email generation request with customer and invoice details
            
        Returns:
            EmailGenerationResponse with generated email content
        """
        try:
            prompt = self._build_email_prompt(request)
            
            # Prepare the request body for Nova Micro
            request_body = {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": 1000,
                    "temperature": 0.7,
                    "topP": 0.9,
                    "stopSequences": ["</email>"]
                }
            }
            
            # Invoke the model
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType='application/json',
                accept='application/json'
            )
            
            # Parse the response
            response_body = json.loads(response['body'].read())
            generated_text = response_body.get('results', [{}])[0].get('outputText', '')
            
            return self._parse_email_response(generated_text, request)
            
        except Exception as e:
            logger.error(f"Failed to generate email: {e}")
            raise BedrockServiceError(f"Email generation failed: {e}")
    
    def _build_email_prompt(self, request: EmailGenerationRequest) -> str:
        """Build the prompt for email generation."""
        
        escalation_context = {
            1: "first friendly reminder",
            2: "second follow-up with urgency", 
            3: "final notice before escalation"
        }
        
        tone_guidance = {
            "professional": "formal, respectful, and business-like",
            "friendly": "warm, approachable, and understanding",
            "firm": "assertive, direct, but still respectful",
            "urgent": "pressing, serious, but not aggressive"
        }
        
        prompt = f"""
You are an AI assistant specialized in generating professional payment reminder emails for B2B collections. 
Generate a personalized email for the following scenario:

CUSTOMER INFORMATION:
- Customer Name: {request.customer_name}
- Company: {request.company_name or 'N/A'}

INVOICE DETAILS:
- Invoice Number: {request.invoice_number}
- Amount Due: {request.currency} {request.invoice_amount:,.2f}
- Original Due Date: {request.due_date.strftime('%B %d, %Y')}
- Days Overdue: {request.days_overdue} days

CONTEXT:
- Escalation Level: {request.escalation_level} ({escalation_context.get(request.escalation_level, 'unknown')})
- Desired Tone: {request.tone} ({tone_guidance.get(request.tone, 'professional')})
- Payment History: {request.payment_history or 'No specific history provided'}
- Additional Context: {request.custom_context or 'None'}

REQUIREMENTS:
1. Generate a subject line that is clear and professional
2. Create an email body that is {tone_guidance.get(request.tone, 'professional')}
3. Include specific payment options and next steps
4. For escalation level 3, mention potential consequences professionally
5. Always include a call to action
6. Keep the tone appropriate for B2B communication
7. Be empathetic but firm about payment expectations

FORMAT YOUR RESPONSE AS:
<email>
<subject>Your generated subject line</subject>
<body>
Your complete email body here...
</body>
<tone_analysis>Brief analysis of the tone used</tone_analysis>
<next_action>Suggested next action if no response</next_action>
<escalation_note>Optional escalation recommendation if applicable</escalation_note>
</email>

Generate the email now:
"""
        return prompt
    
    def _parse_email_response(
        self, 
        generated_text: str, 
        request: EmailGenerationRequest
    ) -> EmailGenerationResponse:
        """Parse the AI-generated email response."""
        
        try:
            # Extract content between tags
            subject = self._extract_tag_content(generated_text, 'subject')
            body = self._extract_tag_content(generated_text, 'body')
            tone_analysis = self._extract_tag_content(generated_text, 'tone_analysis')
            next_action = self._extract_tag_content(generated_text, 'next_action')
            escalation_note = self._extract_tag_content(generated_text, 'escalation_note')
            
            # Fallback parsing if tags aren't found
            if not subject or not body:
                lines = generated_text.strip().split('\n')
                subject = subject or f"Payment Reminder - Invoice {request.invoice_number}"
                body = body or generated_text
            
            return EmailGenerationResponse(
                subject=subject or f"Payment Reminder - Invoice {request.invoice_number}",
                body=body or "Payment reminder email content could not be generated.",
                tone_analysis=tone_analysis or f"Generated with {request.tone} tone",
                suggested_next_action=next_action or "Follow up in 3-5 business days",
                escalation_recommendation=escalation_note
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse AI response, using fallback: {e}")
            
            # Fallback response
            return EmailGenerationResponse(
                subject=f"Payment Reminder - Invoice {request.invoice_number}",
                body=generated_text,
                tone_analysis=f"Generated with {request.tone} tone",
                suggested_next_action="Follow up in 3-5 business days"
            )
    
    def _extract_tag_content(self, text: str, tag: str) -> Optional[str]:
        """Extract content between XML-like tags."""
        try:
            start_tag = f"<{tag}>"
            end_tag = f"</{tag}>"
            
            start_index = text.find(start_tag)
            if start_index == -1:
                return None
            
            start_index += len(start_tag)
            end_index = text.find(end_tag, start_index)
            
            if end_index == -1:
                return None
            
            return text[start_index:end_index].strip()
        except Exception:
            return None
    
    async def generate_conversation_response(
        self,
        customer_message: str,
        conversation_context: str,
        customer_info: Dict[str, Any]
    ) -> str:
        """
        Generate a response for customer conversation.
        
        Args:
            customer_message: The customer's message
            conversation_context: Previous conversation context
            customer_info: Customer information for personalization
            
        Returns:
            AI-generated response
        """
        try:
            prompt = f"""
You are a professional customer service AI assistant handling payment collection conversations.

CUSTOMER INFORMATION:
- Name: {customer_info.get('name', 'Customer')}
- Company: {customer_info.get('company', 'N/A')}

CONVERSATION CONTEXT:
{conversation_context}

CUSTOMER'S LATEST MESSAGE:
"{customer_message}"

GUIDELINES:
1. Be professional, empathetic, and solution-oriented
2. Focus on resolving payment issues collaboratively
3. Offer specific next steps and payment options
4. Acknowledge concerns while maintaining payment expectations
5. Provide clear timelines and consequences when appropriate
6. Keep responses concise but thorough

Generate a helpful response:
"""
            
            request_body = {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": 500,
                    "temperature": 0.6,
                    "topP": 0.8
                }
            }
            
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType='application/json',
                accept='application/json'
            )
            
            response_body = json.loads(response['body'].read())
            generated_text = response_body.get('results', [{}])[0].get('outputText', '')
            
            return generated_text.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate conversation response: {e}")
            return "Thank you for your message. We'll review your situation and get back to you shortly with payment options."


class MockBedrockEmailGenerator(BedrockEmailGenerator):
    """Mock implementation for testing without AWS dependencies."""
    
    def __init__(self, region_name: str = "us-east-1", model_id: str = "amazon.nova-micro-v1:0"):
        """Initialize mock generator."""
        self.model_id = model_id
        self.region_name = region_name
        # Don't initialize real client
    
    @property
    def client(self):
        """Return None for mock - we don't use real client."""
        return None
    
    async def generate_payment_reminder_email(
        self, 
        request: EmailGenerationRequest
    ) -> EmailGenerationResponse:
        """Generate mock email for testing."""
        
        escalation_messages = {
            1: "We hope this message finds you well.",
            2: "We previously reached out regarding this overdue payment.",
            3: "This is our final reminder before escalating this matter."
        }
        
        subject = f"Payment Reminder - Invoice {request.invoice_number} ({request.days_overdue} days overdue)"
        
        body = f"""Dear {request.customer_name},

{escalation_messages.get(request.escalation_level, '')}

We would like to remind you that invoice {request.invoice_number} for {request.currency} {request.invoice_amount:,.2f} remains outstanding. This payment was due on {request.due_date.strftime('%B %d, %Y')} and is now {request.days_overdue} days overdue.

To resolve this matter quickly, please:
1. Process payment immediately via bank transfer
2. Contact us to discuss payment arrangements
3. Provide updated payment timeline

If you have any questions or concerns, please don't hesitate to reach out.

Best regards,
Payment Collection Team"""
        
        return EmailGenerationResponse(
            subject=subject,
            body=body,
            tone_analysis=f"Generated with {request.tone} tone using mock service",
            suggested_next_action="Follow up in 3-5 business days if no response",
            escalation_recommendation="Consider phone call if level 3" if request.escalation_level == 3 else None
        )
    
    async def generate_conversation_response(
        self,
        customer_message: str,
        conversation_context: str,
        customer_info: Dict[str, Any]
    ) -> str:
        """Generate mock conversation response."""
        return f"Thank you for your message, {customer_info.get('name', 'Customer')}. We understand your situation and would like to work with you to resolve this payment matter. Please let us know what payment arrangement would work best for you."


# Factory function for creating email generator
def create_email_generator(use_mock: bool = False) -> BedrockEmailGenerator:
    """
    Create email generator instance.
    
    Args:
        use_mock: If True, returns mock implementation for testing
        
    Returns:
        BedrockEmailGenerator instance
    """
    if use_mock:
        return MockBedrockEmailGenerator()
    else:
        return BedrockEmailGenerator()


# Singleton instance
_email_generator = None


def get_email_generator(use_mock: bool = False) -> BedrockEmailGenerator:
    """Get singleton email generator instance."""
    global _email_generator
    if _email_generator is None:
        _email_generator = create_email_generator(use_mock=use_mock)
    return _email_generator