"""
Domain Services for Payment Intelligence

This module provides domain services that contain business logic
that doesn't naturally fit within a single aggregate.

Domain services coordinate operations across multiple aggregates
and provide complex business capabilities.
"""

from .overdue_payment_service import OverduePaymentService
from .reminder_escalation_service import ReminderEscalationService
from .alternative_payment_service import AlternativePaymentService
from .email_generation_service import EmailGenerationService

__all__ = [
    "OverduePaymentService",
    "ReminderEscalationService", 
    "AlternativePaymentService",
    "EmailGenerationService"
]

# Domain Service Descriptions:
#
# OverduePaymentService:
#   - Identifies and prioritizes overdue invoices
#   - Provides collection recommendations and urgency scoring
#   - Calculates collection probability and strategies
#
# ReminderEscalationService:
#   - Manages escalation logic for payment campaigns
#   - Evaluates escalation criteria and determines actions
#   - Coordinates handoff to collections and management review
#
# AlternativePaymentService:
#   - Generates payment options (installments, settlements, discounts)
#   - Creates payment plans and alternative arrangements
#   - Optimizes payment strategies for maximum collection success
#
# EmailGenerationService:
#   - Generates AI-powered email content using Amazon Bedrock Nova Micro
#   - Personalizes communication based on customer profiles
#   - Creates settlement offers, payment plans, and escalation notices