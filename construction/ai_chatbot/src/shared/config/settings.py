"""
Configuration settings for AI Chatbot Payment Intelligence System
"""
import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class BedrockConfig:
    """Configuration for Amazon Bedrock Nova Micro"""
    region: str = "us-east-1"
    model_id: str = "amazon.nova-micro-v1:0"
    max_tokens: int = 500
    temperature: float = 0.7
    top_p: float = 0.9
    
    # Credentials (will be set from environment variables)
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None


@dataclass
class AppConfig:
    """Main application configuration"""
    debug: bool = True
    log_level: str = "INFO"
    api_host: str = "localhost"
    api_port: int = 8000
    
    # Business rules
    max_reminder_attempts: int = 3
    escalation_delay_days: int = 7
    
    # Mock data settings
    enable_mock_services: bool = True
    mock_invoice_count: int = 50
    mock_customer_count: int = 20


def get_bedrock_config() -> BedrockConfig:
    """Get Bedrock configuration from environment variables"""
    return BedrockConfig(
        region=os.getenv("AWS_REGION", "us-east-1"),
        model_id=os.getenv("BEDROCK_MODEL_ID", "amazon.nova-micro-v1:0"),
        max_tokens=int(os.getenv("BEDROCK_MAX_TOKENS", "500")),
        temperature=float(os.getenv("BEDROCK_TEMPERATURE", "0.7")),
        top_p=float(os.getenv("BEDROCK_TOP_P", "0.9")),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        aws_session_token=os.getenv("AWS_SESSION_TOKEN")
    )


def get_app_config() -> AppConfig:
    """Get application configuration from environment variables"""
    return AppConfig(
        debug=os.getenv("DEBUG", "true").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        api_host=os.getenv("API_HOST", "localhost"),
        api_port=int(os.getenv("API_PORT", "8000")),
        max_reminder_attempts=int(os.getenv("MAX_REMINDER_ATTEMPTS", "3")),
        escalation_delay_days=int(os.getenv("ESCALATION_DELAY_DAYS", "7")),
        enable_mock_services=os.getenv("ENABLE_MOCK_SERVICES", "true").lower() == "true",
        mock_invoice_count=int(os.getenv("MOCK_INVOICE_COUNT", "50")),
        mock_customer_count=int(os.getenv("MOCK_CUSTOMER_COUNT", "20"))
    )