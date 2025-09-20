"""
External service adapters for email, notifications, and payment processing.

This module provides adapters for integrating with external services
following the Adapter pattern for clean separation of concerns.
"""

import logging
import smtplib
from abc import ABC, abstractmethod
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

from ..domain.value_objects import CustomerId, InvoiceId


logger = logging.getLogger(__name__)


@dataclass
class EmailMessage:
    """Email message data structure."""
    to_email: str
    subject: str
    body: str
    from_email: str
    from_name: str
    is_html: bool = True
    attachments: Optional[List[str]] = None


@dataclass
class NotificationMessage:
    """Notification message data structure."""
    recipient_id: str
    title: str
    message: str
    notification_type: str  # email, sms, push, webhook
    priority: str = "normal"  # low, normal, high, urgent
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class PaymentRequest:
    """Payment processing request."""
    invoice_id: str
    customer_id: str
    amount: float
    currency: str
    payment_method: str
    description: str
    reference_number: Optional[str] = None


class EmailServiceAdapter(ABC):
    """Abstract adapter for email services."""
    
    @abstractmethod
    async def send_email(self, message: EmailMessage) -> bool:
        """Send an email message."""
        pass
    
    @abstractmethod
    async def send_bulk_emails(self, messages: List[EmailMessage]) -> Dict[str, bool]:
        """Send multiple emails."""
        pass


class NotificationServiceAdapter(ABC):
    """Abstract adapter for notification services."""
    
    @abstractmethod
    async def send_notification(self, notification: NotificationMessage) -> bool:
        """Send a notification."""
        pass
    
    @abstractmethod
    async def send_bulk_notifications(self, notifications: List[NotificationMessage]) -> Dict[str, bool]:
        """Send multiple notifications."""
        pass


class PaymentServiceAdapter(ABC):
    """Abstract adapter for payment processing services."""
    
    @abstractmethod
    async def process_payment(self, payment_request: PaymentRequest) -> Dict[str, Any]:
        """Process a payment."""
        pass
    
    @abstractmethod
    async def validate_payment_method(self, payment_method: str, customer_id: str) -> bool:
        """Validate a payment method."""
        pass


# Concrete implementations

class SMTPEmailAdapter(EmailServiceAdapter):
    """SMTP email service adapter."""
    
    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        username: str,
        password: str,
        use_tls: bool = True
    ):
        """Initialize SMTP adapter."""
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls
    
    async def send_email(self, message: EmailMessage) -> bool:
        """Send email via SMTP."""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = message.subject
            msg['From'] = f"{message.from_name} <{message.from_email}>"
            msg['To'] = message.to_email
            
            # Add body
            if message.is_html:
                body_part = MIMEText(message.body, 'html')
            else:
                body_part = MIMEText(message.body, 'plain')
            
            msg.attach(body_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {message.to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {message.to_email}: {e}")
            return False
    
    async def send_bulk_emails(self, messages: List[EmailMessage]) -> Dict[str, bool]:
        """Send multiple emails."""
        results = {}
        for message in messages:
            results[message.to_email] = await self.send_email(message)
        return results


class MockEmailAdapter(EmailServiceAdapter):
    """Mock email adapter for testing."""
    
    def __init__(self):
        """Initialize mock adapter."""
        self.sent_emails: List[EmailMessage] = []
    
    async def send_email(self, message: EmailMessage) -> bool:
        """Mock send email."""
        self.sent_emails.append(message)
        logger.info(f"Mock email sent to {message.to_email}: {message.subject}")
        return True
    
    async def send_bulk_emails(self, messages: List[EmailMessage]) -> Dict[str, bool]:
        """Mock send bulk emails."""
        results = {}
        for message in messages:
            results[message.to_email] = await self.send_email(message)
        return results
    
    def get_sent_emails(self) -> List[EmailMessage]:
        """Get list of sent emails for testing."""
        return self.sent_emails.copy()
    
    def clear_sent_emails(self) -> None:
        """Clear sent emails list."""
        self.sent_emails.clear()


class LoggingNotificationAdapter(NotificationServiceAdapter):
    """Notification adapter that logs messages (for MVP)."""
    
    def __init__(self):
        """Initialize logging adapter."""
        self.sent_notifications: List[NotificationMessage] = []
    
    async def send_notification(self, notification: NotificationMessage) -> bool:
        """Log notification message."""
        try:
            self.sent_notifications.append(notification)
            logger.info(
                f"Notification sent - Type: {notification.notification_type}, "
                f"Recipient: {notification.recipient_id}, "
                f"Title: {notification.title}, "
                f"Priority: {notification.priority}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False
    
    async def send_bulk_notifications(self, notifications: List[NotificationMessage]) -> Dict[str, bool]:
        """Send multiple notifications."""
        results = {}
        for notification in notifications:
            results[notification.recipient_id] = await self.send_notification(notification)
        return results
    
    def get_sent_notifications(self) -> List[NotificationMessage]:
        """Get sent notifications for testing."""
        return self.sent_notifications.copy()


class MockPaymentAdapter(PaymentServiceAdapter):
    """Mock payment service adapter for testing."""
    
    def __init__(self):
        """Initialize mock payment adapter."""
        self.processed_payments: List[PaymentRequest] = []
        self.payment_success_rate = 0.9  # 90% success rate for testing
    
    async def process_payment(self, payment_request: PaymentRequest) -> Dict[str, Any]:
        """Mock payment processing."""
        try:
            self.processed_payments.append(payment_request)
            
            # Simulate payment processing
            import random
            success = random.random() < self.payment_success_rate
            
            if success:
                result = {
                    "status": "success",
                    "transaction_id": f"txn_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "amount_processed": payment_request.amount,
                    "currency": payment_request.currency,
                    "processing_fee": payment_request.amount * 0.025,  # 2.5% fee
                    "net_amount": payment_request.amount * 0.975,
                    "timestamp": datetime.now().isoformat()
                }
                logger.info(f"Mock payment processed successfully: {result['transaction_id']}")
            else:
                result = {
                    "status": "failed",
                    "error_code": "INSUFFICIENT_FUNDS",
                    "error_message": "Mock payment failure for testing",
                    "timestamp": datetime.now().isoformat()
                }
                logger.warning(f"Mock payment failed for invoice {payment_request.invoice_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Payment processing error: {e}")
            return {
                "status": "error",
                "error_message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def validate_payment_method(self, payment_method: str, customer_id: str) -> bool:
        """Mock payment method validation."""
        # Simple validation logic for testing
        valid_methods = ["credit_card", "bank_transfer", "ach", "wire_transfer"]
        is_valid = payment_method.lower() in valid_methods
        
        logger.info(f"Payment method validation - Method: {payment_method}, Valid: {is_valid}")
        return is_valid
    
    def get_processed_payments(self) -> List[PaymentRequest]:
        """Get processed payments for testing."""
        return self.processed_payments.copy()
    
    def set_success_rate(self, rate: float) -> None:
        """Set payment success rate for testing."""
        self.payment_success_rate = max(0.0, min(1.0, rate))


# Service adapters factory
class ServiceAdapterFactory:
    """Factory for creating service adapter instances."""
    
    @staticmethod
    def create_email_adapter(adapter_type: str = "mock", **kwargs) -> EmailServiceAdapter:
        """Create email adapter."""
        if adapter_type == "smtp":
            return SMTPEmailAdapter(**kwargs)
        elif adapter_type == "mock":
            return MockEmailAdapter()
        else:
            raise ValueError(f"Unknown email adapter type: {adapter_type}")
    
    @staticmethod
    def create_notification_adapter(adapter_type: str = "logging") -> NotificationServiceAdapter:
        """Create notification adapter."""
        if adapter_type == "logging":
            return LoggingNotificationAdapter()
        else:
            raise ValueError(f"Unknown notification adapter type: {adapter_type}")
    
    @staticmethod
    def create_payment_adapter(adapter_type: str = "mock") -> PaymentServiceAdapter:
        """Create payment adapter."""
        if adapter_type == "mock":
            return MockPaymentAdapter()
        else:
            raise ValueError(f"Unknown payment adapter type: {adapter_type}")


# Singleton instances for MVP
_email_adapter = None
_notification_adapter = None
_payment_adapter = None


def get_email_adapter(adapter_type: str = "mock", **kwargs) -> EmailServiceAdapter:
    """Get singleton email adapter instance."""
    global _email_adapter
    if _email_adapter is None:
        _email_adapter = ServiceAdapterFactory.create_email_adapter(adapter_type, **kwargs)
    return _email_adapter


def get_notification_adapter(adapter_type: str = "logging") -> NotificationServiceAdapter:
    """Get singleton notification adapter instance."""
    global _notification_adapter
    if _notification_adapter is None:
        _notification_adapter = ServiceAdapterFactory.create_notification_adapter(adapter_type)
    return _notification_adapter


def get_payment_adapter(adapter_type: str = "mock") -> PaymentServiceAdapter:
    """Get singleton payment adapter instance."""
    global _payment_adapter
    if _payment_adapter is None:
        _payment_adapter = ServiceAdapterFactory.create_payment_adapter(adapter_type)
    return _payment_adapter


# Configuration utilities
class ServiceConfiguration:
    """Configuration for external services."""
    
    def __init__(self):
        """Initialize configuration."""
        self.email_config = {
            "adapter_type": "mock",
            "smtp_server": None,
            "smtp_port": 587,
            "username": None,
            "password": None,
            "use_tls": True
        }
        
        self.notification_config = {
            "adapter_type": "logging"
        }
        
        self.payment_config = {
            "adapter_type": "mock",
            "success_rate": 0.9
        }
    
    def configure_email_service(self, **kwargs) -> None:
        """Configure email service."""
        self.email_config.update(kwargs)
    
    def configure_notification_service(self, **kwargs) -> None:
        """Configure notification service."""
        self.notification_config.update(kwargs)
    
    def configure_payment_service(self, **kwargs) -> None:
        """Configure payment service."""
        self.payment_config.update(kwargs)
    
    def get_email_adapter(self) -> EmailServiceAdapter:
        """Get configured email adapter."""
        return get_email_adapter(**self.email_config)
    
    def get_notification_adapter(self) -> NotificationServiceAdapter:
        """Get configured notification adapter."""
        return get_notification_adapter(**self.notification_config)
    
    def get_payment_adapter(self) -> PaymentServiceAdapter:
        """Get configured payment adapter."""
        return get_payment_adapter(**self.payment_config)


# Global configuration instance
service_config = ServiceConfiguration()