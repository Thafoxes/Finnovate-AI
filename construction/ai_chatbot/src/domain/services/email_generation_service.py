"""
Email Generation Service for Payment Intelligence Domain

Domain service responsible for generating AI-powered, personalized
email content for payment reminders and collection communications.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from abc import ABC, abstractmethod

from ..entities.overdue_invoice import OverdueInvoice
from ..entities.payment_reminder import PaymentReminder
from ..aggregates.conversation import Conversation
from ..value_objects.payment_value_objects import (
    ReminderLevel, MessageIntent, ConversationContext, EmailTemplate
)


class EmailTone(Enum):
    """Tone options for generated emails"""
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"
    URGENT = "urgent"
    EMPATHETIC = "empathetic"
    ASSERTIVE = "assertive"
    DIPLOMATIC = "diplomatic"


class EmailPersonalization(Enum):
    """Personalization levels for emails"""
    BASIC = "basic"
    MODERATE = "moderate"
    ADVANCED = "advanced"
    HYPER_PERSONALIZED = "hyper_personalized"


class IBedrockService(ABC):
    """Interface for Amazon Bedrock integration"""
    
    @abstractmethod
    def generate_email_content(
        self,
        prompt: str,
        model_id: str = "nova-micro",
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> str:
        pass
    
    @abstractmethod
    def analyze_customer_sentiment(self, text: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def generate_subject_line(self, email_content: str, tone: EmailTone) -> str:
        pass


class ICustomerInsightsService(ABC):
    """Interface for customer insights and data"""
    
    @abstractmethod
    def get_customer_communication_preferences(self, customer_id: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def get_customer_relationship_history(self, customer_id: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def get_customer_business_context(self, customer_id: str) -> Dict[str, Any]:
        pass


class EmailGenerationService:
    """
    Domain service for generating AI-powered email content for payment collection.
    
    Leverages Amazon Bedrock Nova Micro for intelligent, contextual email
    generation that adapts to customer profiles and payment situations.
    """
    
    def __init__(
        self,
        bedrock_service: IBedrockService,
        customer_insights: ICustomerInsightsService
    ):
        self._bedrock_service = bedrock_service
        self._customer_insights = customer_insights
        
        # Email generation configuration
        self._default_model = "nova-micro"
        self._max_email_length = 500
        self._temperature_settings = {
            EmailTone.FRIENDLY: 0.8,
            EmailTone.PROFESSIONAL: 0.3,
            EmailTone.URGENT: 0.5,
            EmailTone.EMPATHETIC: 0.7,
            EmailTone.ASSERTIVE: 0.4,
            EmailTone.DIPLOMATIC: 0.6
        }
    
    def generate_payment_reminder_email(
        self,
        invoice: OverdueInvoice,
        reminder_level: ReminderLevel,
        customer_profile: Dict[str, Any],
        personalization_level: EmailPersonalization = EmailPersonalization.MODERATE
    ) -> EmailTemplate:
        """Generate a payment reminder email using AI"""
        
        # Get customer communication preferences
        comm_prefs = self._customer_insights.get_customer_communication_preferences(invoice.customer_id)
        
        # Determine appropriate tone based on reminder level and customer profile
        tone = self._determine_email_tone(reminder_level, customer_profile, comm_prefs)
        
        # Build context for AI generation
        email_context = self._build_email_context(
            invoice, reminder_level, customer_profile, personalization_level
        )
        
        # Generate email content using Bedrock
        email_content = self._generate_email_content(email_context, tone)
        
        # Generate subject line
        subject_line = self._bedrock_service.generate_subject_line(email_content, tone)
        
        # Create email template
        email_template = EmailTemplate(
            template_id=f"reminder_{reminder_level.value}_{invoice.invoice_id}",
            subject=subject_line,
            body=email_content,
            sender_name=comm_prefs.get("preferred_sender_name", "Accounts Receivable Team"),
            sender_email=comm_prefs.get("sender_email", "ar@company.com"),
            template_variables=email_context.get("variables", {}),
            personalization_data=self._extract_personalization_data(email_context)
        )
        
        return email_template
    
    def generate_settlement_offer_email(
        self,
        invoice: OverdueInvoice,
        settlement_details: Dict[str, Any],
        customer_profile: Dict[str, Any]
    ) -> EmailTemplate:
        """Generate a settlement offer email"""
        
        # Build settlement-specific context
        settlement_context = self._build_settlement_context(
            invoice, settlement_details, customer_profile
        )
        
        # Use diplomatic tone for settlement offers
        tone = EmailTone.DIPLOMATIC
        
        # Generate content
        email_content = self._generate_email_content(settlement_context, tone)
        subject_line = f"Settlement Offer - Invoice #{invoice.invoice_number}"
        
        # Get communication preferences
        comm_prefs = self._customer_insights.get_customer_communication_preferences(invoice.customer_id)
        
        return EmailTemplate(
            template_id=f"settlement_{invoice.invoice_id}",
            subject=subject_line,
            body=email_content,
            sender_name=comm_prefs.get("preferred_sender_name", "Collections Manager"),
            sender_email=comm_prefs.get("sender_email", "collections@company.com"),
            template_variables=settlement_context.get("variables", {}),
            personalization_data=self._extract_personalization_data(settlement_context)
        )
    
    def generate_payment_plan_offer_email(
        self,
        invoice: OverdueInvoice,
        payment_plan_details: Dict[str, Any],
        customer_profile: Dict[str, Any]
    ) -> EmailTemplate:
        """Generate a payment plan offer email"""
        
        # Build payment plan context
        plan_context = self._build_payment_plan_context(
            invoice, payment_plan_details, customer_profile
        )
        
        # Use friendly but professional tone
        tone = EmailTone.FRIENDLY
        
        # Generate content
        email_content = self._generate_email_content(plan_context, tone)
        subject_line = f"Flexible Payment Options - Invoice #{invoice.invoice_number}"
        
        comm_prefs = self._customer_insights.get_customer_communication_preferences(invoice.customer_id)
        
        return EmailTemplate(
            template_id=f"payment_plan_{invoice.invoice_id}",
            subject=subject_line,
            body=email_content,
            sender_name=comm_prefs.get("preferred_sender_name", "Customer Success Team"),
            sender_email=comm_prefs.get("sender_email", "success@company.com"),
            template_variables=plan_context.get("variables", {}),
            personalization_data=self._extract_personalization_data(plan_context)
        )
    
    def generate_escalation_notice_email(
        self,
        invoice: OverdueInvoice,
        escalation_details: Dict[str, Any],
        customer_profile: Dict[str, Any]
    ) -> EmailTemplate:
        """Generate an escalation notice email"""
        
        # Build escalation context
        escalation_context = self._build_escalation_context(
            invoice, escalation_details, customer_profile
        )
        
        # Use assertive but professional tone
        tone = EmailTone.ASSERTIVE
        
        # Generate content
        email_content = self._generate_email_content(escalation_context, tone)
        subject_line = f"URGENT: Account Escalation Notice - Invoice #{invoice.invoice_number}"
        
        comm_prefs = self._customer_insights.get_customer_communication_preferences(invoice.customer_id)
        
        return EmailTemplate(
            template_id=f"escalation_{invoice.invoice_id}",
            subject=subject_line,
            body=email_content,
            sender_name=comm_prefs.get("escalation_sender_name", "Collections Manager"),
            sender_email=comm_prefs.get("escalation_email", "collections@company.com"),
            template_variables=escalation_context.get("variables", {}),
            personalization_data=self._extract_personalization_data(escalation_context)
        )
    
    def generate_thank_you_email(
        self,
        invoice: OverdueInvoice,
        payment_details: Dict[str, Any],
        customer_profile: Dict[str, Any]
    ) -> EmailTemplate:
        """Generate a thank you email after payment received"""
        
        # Build thank you context
        thank_you_context = self._build_thank_you_context(
            invoice, payment_details, customer_profile
        )
        
        # Use friendly and appreciative tone
        tone = EmailTone.FRIENDLY
        
        # Generate content
        email_content = self._generate_email_content(thank_you_context, tone)
        subject_line = f"Thank You - Payment Received for Invoice #{invoice.invoice_number}"
        
        comm_prefs = self._customer_insights.get_customer_communication_preferences(invoice.customer_id)
        
        return EmailTemplate(
            template_id=f"thank_you_{invoice.invoice_id}",
            subject=subject_line,
            body=email_content,
            sender_name=comm_prefs.get("preferred_sender_name", "Accounts Receivable Team"),
            sender_email=comm_prefs.get("sender_email", "ar@company.com"),
            template_variables=thank_you_context.get("variables", {}),
            personalization_data=self._extract_personalization_data(thank_you_context)
        )
    
    def optimize_email_for_customer(
        self,
        base_template: EmailTemplate,
        customer_profile: Dict[str, Any],
        conversation_history: Optional[Conversation] = None
    ) -> EmailTemplate:
        """Optimize an existing email template for a specific customer"""
        
        # Analyze customer communication patterns
        comm_preferences = self._customer_insights.get_customer_communication_preferences(
            customer_profile["customer_id"]
        )
        
        # Build optimization context
        optimization_context = {
            "original_email": base_template.body,
            "customer_preferences": comm_preferences,
            "customer_profile": customer_profile,
            "conversation_history": self._extract_conversation_context(conversation_history) if conversation_history else None
        }
        
        # Create optimization prompt
        optimization_prompt = self._build_optimization_prompt(optimization_context)
        
        # Generate optimized content
        temperature = 0.6  # Moderate creativity for optimization
        optimized_content = self._bedrock_service.generate_email_content(
            optimization_prompt,
            self._default_model,
            self._max_email_length,
            temperature
        )
        
        # Create optimized template
        optimized_template = EmailTemplate(
            template_id=f"{base_template.template_id}_optimized",
            subject=base_template.subject,
            body=optimized_content,
            sender_name=base_template.sender_name,
            sender_email=base_template.sender_email,
            template_variables=base_template.template_variables,
            personalization_data=base_template.personalization_data
        )
        
        return optimized_template
    
    def analyze_email_effectiveness(
        self,
        email_template: EmailTemplate,
        customer_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze the effectiveness of an email template"""
        
        # Use Bedrock to analyze sentiment and tone
        sentiment_analysis = self._bedrock_service.analyze_customer_sentiment(email_template.body)
        
        # Calculate readability and engagement metrics
        readability_score = self._calculate_readability_score(email_template.body)
        engagement_score = self._predict_engagement_score(email_template, customer_profile)
        
        return {
            "sentiment_analysis": sentiment_analysis,
            "readability_score": readability_score,
            "engagement_score": engagement_score,
            "length_analysis": {
                "word_count": len(email_template.body.split()),
                "character_count": len(email_template.body),
                "paragraph_count": email_template.body.count('\n\n') + 1,
                "optimal_length": 150 <= len(email_template.body.split()) <= 300
            },
            "tone_consistency": self._analyze_tone_consistency(email_template.body),
            "personalization_level": self._assess_personalization_level(email_template),
            "call_to_action_strength": self._assess_cta_strength(email_template.body),
            "improvement_suggestions": self._generate_improvement_suggestions(
                email_template, customer_profile
            )
        }
    
    def generate_a_b_test_variants(
        self,
        base_template: EmailTemplate,
        customer_profile: Dict[str, Any],
        variant_count: int = 3
    ) -> List[EmailTemplate]:
        """Generate A/B test variants of an email template"""
        
        variants = []
        tones = [EmailTone.FRIENDLY, EmailTone.PROFESSIONAL, EmailTone.URGENT]
        
        for i, tone in enumerate(tones[:variant_count]):
            # Build variant context
            variant_context = {
                "base_content": base_template.body,
                "target_tone": tone.value,
                "customer_profile": customer_profile,
                "variant_number": i + 1
            }
            
            # Generate variant
            variant_prompt = self._build_variant_prompt(variant_context)
            variant_content = self._generate_email_content(variant_context, tone)
            
            # Create variant template
            variant = EmailTemplate(
                template_id=f"{base_template.template_id}_variant_{i+1}",
                subject=f"{base_template.subject} - Variant {i+1}",
                body=variant_content,
                sender_name=base_template.sender_name,
                sender_email=base_template.sender_email,
                template_variables=base_template.template_variables,
                personalization_data=base_template.personalization_data
            )
            
            variants.append(variant)
        
        return variants
    
    # Private helper methods
    
    def _determine_email_tone(
        self,
        reminder_level: ReminderLevel,
        customer_profile: Dict[str, Any],
        comm_prefs: Dict[str, Any]
    ) -> EmailTone:
        """Determine appropriate email tone"""
        
        # Customer preference override
        preferred_tone = comm_prefs.get("preferred_communication_tone")
        if preferred_tone and preferred_tone in [tone.value for tone in EmailTone]:
            return EmailTone(preferred_tone)
        
        # Tone based on reminder level
        if reminder_level == ReminderLevel.FIRST:
            return EmailTone.FRIENDLY
        elif reminder_level == ReminderLevel.SECOND:
            return EmailTone.PROFESSIONAL
        elif reminder_level == ReminderLevel.THIRD:
            return EmailTone.URGENT
        elif reminder_level == ReminderLevel.ESCALATED:
            return EmailTone.ASSERTIVE
        
        # Adjust based on customer characteristics
        if customer_profile.get("financial_hardship", False):
            return EmailTone.EMPATHETIC
        
        if customer_profile.get("high_value_customer", False):
            return EmailTone.DIPLOMATIC
        
        return EmailTone.PROFESSIONAL
    
    def _build_email_context(
        self,
        invoice: OverdueInvoice,
        reminder_level: ReminderLevel,
        customer_profile: Dict[str, Any],
        personalization_level: EmailPersonalization
    ) -> Dict[str, Any]:
        """Build context for email generation"""
        
        # Get customer business context
        business_context = self._customer_insights.get_customer_business_context(invoice.customer_id)
        relationship_history = self._customer_insights.get_customer_relationship_history(invoice.customer_id)
        
        context = {
            "invoice_details": {
                "invoice_number": invoice.invoice_number,
                "amount": invoice.current_balance.amount,
                "currency": invoice.current_balance.currency,
                "due_date": invoice.due_date.strftime("%B %d, %Y"),
                "days_overdue": invoice.days_overdue,
                "original_amount": invoice.original_amount.amount
            },
            "customer_info": {
                "name": customer_profile.get("name", "Valued Customer"),
                "company": customer_profile.get("company_name", ""),
                "contact_person": customer_profile.get("contact_person", ""),
                "relationship_length": relationship_history.get("relationship_years", 0),
                "payment_history": customer_profile.get("payment_history_summary", "good")
            },
            "reminder_context": {
                "level": reminder_level.value,
                "previous_reminders": invoice.reminder_count,
                "urgency": "high" if invoice.days_overdue > 30 else "medium"
            },
            "business_context": business_context,
            "personalization_level": personalization_level.value,
            "variables": {
                "customer_name": customer_profile.get("name", "Valued Customer"),
                "invoice_number": invoice.invoice_number,
                "amount_due": f"{invoice.current_balance.currency} {invoice.current_balance.amount:,.2f}",
                "due_date": invoice.due_date.strftime("%B %d, %Y"),
                "days_overdue": invoice.days_overdue,
                "company_name": customer_profile.get("company_name", ""),
                "payment_portal_url": "https://payments.company.com/pay",
                "contact_phone": "1-800-COLLECT",
                "contact_email": "ar@company.com"
            }
        }
        
        return context
    
    def _build_settlement_context(
        self,
        invoice: OverdueInvoice,
        settlement_details: Dict[str, Any],
        customer_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build context for settlement offer emails"""
        
        base_context = self._build_email_context(
            invoice, ReminderLevel.THIRD, customer_profile, EmailPersonalization.ADVANCED
        )
        
        # Add settlement-specific information
        base_context.update({
            "settlement_details": settlement_details,
            "offer_type": "settlement",
            "variables": {
                **base_context["variables"],
                "settlement_amount": f"{settlement_details['settlement_amount'].currency} {settlement_details['settlement_amount'].amount:,.2f}",
                "discount_amount": f"{settlement_details['discount_amount'].currency} {settlement_details['discount_amount'].amount:,.2f}",
                "discount_percentage": f"{settlement_details['discount_percentage']:.1f}%",
                "payment_deadline": settlement_details['payment_deadline'].strftime("%B %d, %Y"),
                "savings": f"{settlement_details['discount_amount'].currency} {settlement_details['discount_amount'].amount:,.2f}"
            }
        })
        
        return base_context
    
    def _build_payment_plan_context(
        self,
        invoice: OverdueInvoice,
        payment_plan_details: Dict[str, Any],
        customer_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build context for payment plan emails"""
        
        base_context = self._build_email_context(
            invoice, ReminderLevel.SECOND, customer_profile, EmailPersonalization.ADVANCED
        )
        
        # Add payment plan information
        base_context.update({
            "payment_plan_details": payment_plan_details,
            "offer_type": "payment_plan",
            "variables": {
                **base_context["variables"],
                "monthly_payment": f"{payment_plan_details['monthly_payment'].currency} {payment_plan_details['monthly_payment'].amount:,.2f}",
                "plan_duration": f"{len(payment_plan_details['payment_schedule'])} months",
                "first_payment_due": payment_plan_details['payment_schedule'][0]['due_date'].strftime("%B %d, %Y"),
                "total_plan_cost": f"{payment_plan_details['total_cost'].currency} {payment_plan_details['total_cost'].amount:,.2f}",
                "setup_fee": f"{payment_plan_details.get('setup_fee', 0):.2f}"
            }
        })
        
        return base_context
    
    def _build_escalation_context(
        self,
        invoice: OverdueInvoice,
        escalation_details: Dict[str, Any],
        customer_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build context for escalation emails"""
        
        base_context = self._build_email_context(
            invoice, ReminderLevel.ESCALATED, customer_profile, EmailPersonalization.BASIC
        )
        
        # Add escalation information
        base_context.update({
            "escalation_details": escalation_details,
            "message_type": "escalation_notice",
            "variables": {
                **base_context["variables"],
                "escalation_reason": escalation_details.get("primary_reason", "non_payment"),
                "next_action": escalation_details.get("next_action", "collections_referral"),
                "deadline": (datetime.utcnow() + timedelta(days=7)).strftime("%B %d, %Y"),
                "collections_contact": escalation_details.get("collections_contact", "collections@company.com")
            }
        })
        
        return base_context
    
    def _build_thank_you_context(
        self,
        invoice: OverdueInvoice,
        payment_details: Dict[str, Any],
        customer_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build context for thank you emails"""
        
        base_context = self._build_email_context(
            invoice, ReminderLevel.FIRST, customer_profile, EmailPersonalization.MODERATE
        )
        
        # Add payment details
        base_context.update({
            "payment_details": payment_details,
            "message_type": "thank_you",
            "variables": {
                **base_context["variables"],
                "payment_amount": f"{payment_details['amount'].currency} {payment_details['amount'].amount:,.2f}",
                "payment_date": payment_details['payment_date'].strftime("%B %d, %Y"),
                "payment_method": payment_details.get("payment_method", ""),
                "confirmation_number": payment_details.get("confirmation_number", "")
            }
        })
        
        return base_context
    
    def _generate_email_content(
        self,
        context: Dict[str, Any],
        tone: EmailTone
    ) -> str:
        """Generate email content using Bedrock"""
        
        # Build AI prompt
        prompt = self._build_ai_prompt(context, tone)
        
        # Get temperature for tone
        temperature = self._temperature_settings.get(tone, 0.5)
        
        # Generate content
        email_content = self._bedrock_service.generate_email_content(
            prompt,
            self._default_model,
            self._max_email_length,
            temperature
        )
        
        return email_content
    
    def _build_ai_prompt(self, context: Dict[str, Any], tone: EmailTone) -> str:
        """Build AI prompt for email generation"""
        
        customer_name = context["variables"]["customer_name"]
        invoice_number = context["variables"]["invoice_number"]
        amount_due = context["variables"]["amount_due"]
        days_overdue = context["variables"]["days_overdue"]
        
        # Base prompt structure
        prompt = f"""
        Generate a professional payment reminder email with the following specifications:
        
        TONE: {tone.value}
        RECIPIENT: {customer_name}
        INVOICE: #{invoice_number}
        AMOUNT: {amount_due}
        DAYS OVERDUE: {days_overdue}
        
        EMAIL REQUIREMENTS:
        - Professional but {tone.value} tone
        - Clear call to action
        - Include payment options
        - Maintain customer relationship
        - 150-300 words
        - Include contact information
        
        CONTEXT:
        """
        
        # Add specific context based on message type
        if context.get("message_type") == "settlement":
            prompt += f"""
            - This is a settlement offer email
            - Settlement amount: {context['variables'].get('settlement_amount', 'N/A')}
            - Discount offered: {context['variables'].get('discount_percentage', 'N/A')}
            - Payment deadline: {context['variables'].get('payment_deadline', 'N/A')}
            """
        elif context.get("message_type") == "payment_plan":
            prompt += f"""
            - This is a payment plan offer email
            - Monthly payment: {context['variables'].get('monthly_payment', 'N/A')}
            - Plan duration: {context['variables'].get('plan_duration', 'N/A')}
            """
        elif context.get("message_type") == "escalation_notice":
            prompt += f"""
            - This is an escalation notice
            - Account will be escalated if no response
            - Final opportunity to resolve
            """
        elif context.get("message_type") == "thank_you":
            prompt += f"""
            - This is a thank you email for payment received
            - Payment amount: {context['variables'].get('payment_amount', 'N/A')}
            - Payment date: {context['variables'].get('payment_date', 'N/A')}
            """
        
        # Add personalization context
        personalization_level = context.get("personalization_level", "moderate")
        if personalization_level == "advanced":
            company_name = context["variables"].get("company_name", "")
            if company_name:
                prompt += f"""
                - Customer company: {company_name}
                - Reference business relationship
                """
        
        prompt += """
        
        Generate the email body only (no subject line). Use proper business email formatting with appropriate greetings and closing.
        """
        
        return prompt
    
    def _build_optimization_prompt(self, optimization_context: Dict[str, Any]) -> str:
        """Build prompt for email optimization"""
        
        return f"""
        Optimize the following email for better customer engagement and response rates:
        
        ORIGINAL EMAIL:
        {optimization_context['original_email']}
        
        CUSTOMER PREFERENCES:
        {optimization_context['customer_preferences']}
        
        OPTIMIZATION GOALS:
        - Improve clarity and readability
        - Enhance personalization
        - Strengthen call to action
        - Maintain professional tone
        - Increase likelihood of payment
        
        Generate an improved version of the email that addresses these goals while maintaining the core message.
        """
    
    def _build_variant_prompt(self, variant_context: Dict[str, Any]) -> str:
        """Build prompt for A/B test variants"""
        
        return f"""
        Create a variant of the following email with a {variant_context['target_tone']} tone:
        
        BASE EMAIL:
        {variant_context['base_content']}
        
        VARIANT REQUIREMENTS:
        - Change tone to {variant_context['target_tone']}
        - Keep the same core message and information
        - Maintain professional standards
        - Adjust language and phrasing accordingly
        - Keep similar length
        
        Generate variant #{variant_context['variant_number']} with the specified tone changes.
        """
    
    def _extract_personalization_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract personalization data from context"""
        return {
            "customer_name": context["variables"].get("customer_name"),
            "company_name": context["variables"].get("company_name"),
            "relationship_length": context.get("customer_info", {}).get("relationship_length"),
            "payment_history": context.get("customer_info", {}).get("payment_history"),
            "personalization_level": context.get("personalization_level")
        }
    
    def _extract_conversation_context(self, conversation: Conversation) -> Dict[str, Any]:
        """Extract relevant context from conversation history"""
        if not conversation or not conversation.messages:
            return {}
        
        recent_messages = conversation.messages[-5:]  # Last 5 messages
        
        return {
            "recent_interactions": len(recent_messages),
            "customer_sentiment": "positive",  # Would analyze actual messages
            "common_concerns": [],  # Would extract from message analysis
            "preferred_communication_style": "formal"  # Would derive from patterns
        }
    
    def _calculate_readability_score(self, text: str) -> float:
        """Calculate readability score (simplified)"""
        # Simplified readability calculation
        words = text.split()
        sentences = text.count('.') + text.count('!') + text.count('?')
        
        if sentences == 0:
            return 0.0
        
        avg_words_per_sentence = len(words) / sentences
        
        # Simple scoring (lower is better for business communication)
        if avg_words_per_sentence <= 15:
            return 0.9  # Excellent
        elif avg_words_per_sentence <= 20:
            return 0.7  # Good
        elif avg_words_per_sentence <= 25:
            return 0.5  # Fair
        else:
            return 0.3  # Poor
    
    def _predict_engagement_score(
        self,
        email_template: EmailTemplate,
        customer_profile: Dict[str, Any]
    ) -> float:
        """Predict engagement score based on email characteristics"""
        
        base_score = 0.5
        
        # Length optimization
        word_count = len(email_template.body.split())
        if 150 <= word_count <= 300:
            base_score += 0.2
        elif word_count > 500:
            base_score -= 0.2
        
        # Personalization bonus
        if email_template.personalization_data.get("company_name"):
            base_score += 0.1
        
        if email_template.personalization_data.get("relationship_length", 0) > 2:
            base_score += 0.1
        
        # Customer preference alignment
        if customer_profile.get("prefers_brief_communication", False) and word_count <= 200:
            base_score += 0.15
        
        return min(max(base_score, 0.0), 1.0)
    
    def _analyze_tone_consistency(self, email_body: str) -> Dict[str, Any]:
        """Analyze tone consistency in email"""
        # Simplified tone analysis
        return {
            "consistent": True,
            "dominant_tone": "professional",
            "tone_variations": [],
            "tone_score": 0.8
        }
    
    def _assess_personalization_level(self, email_template: EmailTemplate) -> str:
        """Assess the level of personalization in email"""
        personalization_elements = 0
        
        if email_template.personalization_data.get("customer_name"):
            personalization_elements += 1
        if email_template.personalization_data.get("company_name"):
            personalization_elements += 1
        if email_template.personalization_data.get("relationship_length"):
            personalization_elements += 1
        
        if personalization_elements >= 3:
            return "high"
        elif personalization_elements >= 2:
            return "medium"
        elif personalization_elements >= 1:
            return "low"
        else:
            return "none"
    
    def _assess_cta_strength(self, email_body: str) -> float:
        """Assess call-to-action strength"""
        cta_indicators = [
            "please pay", "make payment", "contact us", "click here",
            "call now", "pay online", "visit", "respond"
        ]
        
        cta_count = sum(1 for indicator in cta_indicators if indicator.lower() in email_body.lower())
        
        # Score based on CTA presence and clarity
        if cta_count >= 2:
            return 0.9
        elif cta_count == 1:
            return 0.7
        else:
            return 0.3
    
    def _generate_improvement_suggestions(
        self,
        email_template: EmailTemplate,
        customer_profile: Dict[str, Any]
    ) -> List[str]:
        """Generate suggestions for email improvement"""
        suggestions = []
        
        word_count = len(email_template.body.split())
        if word_count > 400:
            suggestions.append("Consider shortening the email for better readability")
        
        if not email_template.personalization_data.get("company_name"):
            suggestions.append("Add company name for better personalization")
        
        cta_strength = self._assess_cta_strength(email_template.body)
        if cta_strength < 0.7:
            suggestions.append("Strengthen call-to-action with clearer instructions")
        
        if customer_profile.get("prefers_brief_communication", False) and word_count > 250:
            suggestions.append("Customer prefers brief communication - consider shortening")
        
        return suggestions