"""
Configuration management for the AI Payment Intelligence system.

This module handles environment variables, settings, and configuration
for different deployment environments (development, testing, production).
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path


logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    use_in_memory: bool = True
    dynamodb_region: str = "us-east-1"
    campaigns_table: str = "PaymentCampaigns"
    conversations_table: str = "Conversations"
    invoices_table: str = "OverdueInvoices"
    customers_table: str = "Customers"


@dataclass
class BedrockConfig:
    """Amazon Bedrock configuration settings."""
    region: str = "us-east-1"
    model_id: str = "amazon.nova-micro-v1:0"
    max_tokens: int = 1000
    temperature: float = 0.7
    top_p: float = 0.9
    use_mock: bool = True  # Use mock for development by default


@dataclass
class EmailConfig:
    """Email service configuration."""
    adapter_type: str = "mock"  # mock, smtp
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    username: Optional[str] = None
    password: Optional[str] = None
    use_tls: bool = True
    from_email: str = "noreply@payment-intelligence.com"
    from_name: str = "Payment Intelligence System"


@dataclass
class NotificationConfig:
    """Notification service configuration."""
    adapter_type: str = "logging"  # logging, sns, webhook
    sns_topic_arn: Optional[str] = None
    webhook_url: Optional[str] = None


@dataclass
class PaymentConfig:
    """Payment service configuration."""
    adapter_type: str = "mock"  # mock, stripe, square
    api_key: Optional[str] = None
    success_rate: float = 0.9  # For mock adapter
    processing_fee_rate: float = 0.025  # 2.5%


@dataclass
class SecurityConfig:
    """Security configuration settings."""
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    api_key_header: str = "X-API-Key"
    cors_origins: list = field(default_factory=lambda: ["http://localhost:3000"])
    rate_limit_per_minute: int = 60


@dataclass
class LoggingConfig:
    """Logging configuration settings."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size_mb: int = 10
    backup_count: int = 5


@dataclass
class ApplicationConfig:
    """Main application configuration."""
    environment: str = "development"
    debug: bool = True
    version: str = "1.0.0"
    service_name: str = "AI Payment Intelligence"
    host: str = "localhost"
    port: int = 8000
    
    # Sub-configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    bedrock: BedrockConfig = field(default_factory=BedrockConfig)
    email: EmailConfig = field(default_factory=EmailConfig)
    notification: NotificationConfig = field(default_factory=NotificationConfig)
    payment: PaymentConfig = field(default_factory=PaymentConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)


class ConfigurationManager:
    """Manages application configuration from environment variables and files."""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            env_file: Path to .env file to load
        """
        self.env_file = env_file
        self._config: Optional[ApplicationConfig] = None
        
        # Load environment variables from file if specified
        if env_file and Path(env_file).exists():
            self._load_env_file(env_file)
    
    def _load_env_file(self, env_file: str) -> None:
        """Load environment variables from file."""
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, _, value = line.partition('=')
                        if key and value:
                            os.environ[key.strip()] = value.strip()
            logger.info(f"Loaded environment variables from {env_file}")
        except Exception as e:
            logger.warning(f"Failed to load environment file {env_file}: {e}")
    
    def get_config(self) -> ApplicationConfig:
        """Get application configuration with environment variable overrides."""
        if self._config is None:
            self._config = self._build_config()
        return self._config
    
    def _build_config(self) -> ApplicationConfig:
        """Build configuration from environment variables."""
        
        # Main application config
        config = ApplicationConfig(
            environment=os.getenv("ENVIRONMENT", "development"),
            debug=os.getenv("DEBUG", "true").lower() == "true",
            version=os.getenv("VERSION", "1.0.0"),
            service_name=os.getenv("SERVICE_NAME", "AI Payment Intelligence"),
            host=os.getenv("HOST", "localhost"),
            port=int(os.getenv("PORT", "8000"))
        )
        
        # Database configuration
        config.database = DatabaseConfig(
            use_in_memory=os.getenv("USE_IN_MEMORY_DB", "true").lower() == "true",
            dynamodb_region=os.getenv("DYNAMODB_REGION", "us-east-1"),
            campaigns_table=os.getenv("DYNAMODB_CAMPAIGNS_TABLE", "PaymentCampaigns"),
            conversations_table=os.getenv("DYNAMODB_CONVERSATIONS_TABLE", "Conversations"),
            invoices_table=os.getenv("DYNAMODB_INVOICES_TABLE", "OverdueInvoices"),
            customers_table=os.getenv("DYNAMODB_CUSTOMERS_TABLE", "Customers")
        )
        
        # Bedrock configuration
        config.bedrock = BedrockConfig(
            region=os.getenv("BEDROCK_REGION", "us-east-1"),
            model_id=os.getenv("BEDROCK_MODEL_ID", "amazon.nova-micro-v1:0"),
            max_tokens=int(os.getenv("BEDROCK_MAX_TOKENS", "1000")),
            temperature=float(os.getenv("BEDROCK_TEMPERATURE", "0.7")),
            top_p=float(os.getenv("BEDROCK_TOP_P", "0.9")),
            use_mock=os.getenv("BEDROCK_USE_MOCK", "true").lower() == "true"
        )
        
        # Email configuration
        config.email = EmailConfig(
            adapter_type=os.getenv("EMAIL_ADAPTER_TYPE", "mock"),
            smtp_server=os.getenv("SMTP_SERVER"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            username=os.getenv("SMTP_USERNAME"),
            password=os.getenv("SMTP_PASSWORD"),
            use_tls=os.getenv("SMTP_USE_TLS", "true").lower() == "true",
            from_email=os.getenv("FROM_EMAIL", "noreply@payment-intelligence.com"),
            from_name=os.getenv("FROM_NAME", "Payment Intelligence System")
        )
        
        # Notification configuration
        config.notification = NotificationConfig(
            adapter_type=os.getenv("NOTIFICATION_ADAPTER_TYPE", "logging"),
            sns_topic_arn=os.getenv("SNS_TOPIC_ARN"),
            webhook_url=os.getenv("NOTIFICATION_WEBHOOK_URL")
        )
        
        # Payment configuration
        config.payment = PaymentConfig(
            adapter_type=os.getenv("PAYMENT_ADAPTER_TYPE", "mock"),
            api_key=os.getenv("PAYMENT_API_KEY"),
            success_rate=float(os.getenv("PAYMENT_SUCCESS_RATE", "0.9")),
            processing_fee_rate=float(os.getenv("PAYMENT_FEE_RATE", "0.025"))
        )
        
        # Security configuration
        cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000")
        config.security = SecurityConfig(
            jwt_secret_key=os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production"),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            jwt_expiration_hours=int(os.getenv("JWT_EXPIRATION_HOURS", "24")),
            api_key_header=os.getenv("API_KEY_HEADER", "X-API-Key"),
            cors_origins=[origin.strip() for origin in cors_origins.split(",")],
            rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
        )
        
        # Logging configuration
        config.logging = LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            format=os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            file_path=os.getenv("LOG_FILE_PATH"),
            max_file_size_mb=int(os.getenv("LOG_MAX_FILE_SIZE_MB", "10")),
            backup_count=int(os.getenv("LOG_BACKUP_COUNT", "5"))
        )
        
        return config
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration and return validation results."""
        config = self.get_config()
        issues = []
        warnings = []
        
        # Validate AWS credentials if not using mock
        if not config.bedrock.use_mock:
            if not os.getenv("AWS_ACCESS_KEY_ID"):
                issues.append("AWS_ACCESS_KEY_ID is required for Bedrock integration")
            if not os.getenv("AWS_SECRET_ACCESS_KEY"):
                issues.append("AWS_SECRET_ACCESS_KEY is required for Bedrock integration")
        
        # Validate email configuration
        if config.email.adapter_type == "smtp":
            if not config.email.smtp_server:
                issues.append("SMTP_SERVER is required for SMTP email adapter")
            if not config.email.username:
                issues.append("SMTP_USERNAME is required for SMTP email adapter")
            if not config.email.password:
                issues.append("SMTP_PASSWORD is required for SMTP email adapter")
        
        # Security warnings
        if config.security.jwt_secret_key == "your-secret-key-change-in-production":
            warnings.append("Using default JWT secret key - change for production")
        
        if config.environment == "production" and config.debug:
            warnings.append("Debug mode is enabled in production environment")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "config_summary": {
                "environment": config.environment,
                "bedrock_mock": config.bedrock.use_mock,
                "email_adapter": config.email.adapter_type,
                "database_type": "in-memory" if config.database.use_in_memory else "dynamodb"
            }
        }
    
    def get_aws_config(self) -> Dict[str, str]:
        """Get AWS-specific configuration."""
        return {
            "region": self.get_config().bedrock.region,
            "access_key_id": os.getenv("AWS_ACCESS_KEY_ID", ""),
            "secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY", ""),
            "session_token": os.getenv("AWS_SESSION_TOKEN", "")
        }
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.get_config().environment.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.get_config().environment.lower() == "development"


# Global configuration manager instance
config_manager = ConfigurationManager()


def get_config() -> ApplicationConfig:
    """Get the global application configuration."""
    return config_manager.get_config()


def load_config_from_file(env_file: str) -> ApplicationConfig:
    """Load configuration from a specific file."""
    global config_manager
    config_manager = ConfigurationManager(env_file)
    return config_manager.get_config()


def validate_configuration() -> Dict[str, Any]:
    """Validate the current configuration."""
    return config_manager.validate_config()


# Environment-specific configuration helpers
def get_development_config() -> ApplicationConfig:
    """Get configuration optimized for development."""
    config = get_config()
    config.debug = True
    config.bedrock.use_mock = True
    config.email.adapter_type = "mock"
    config.payment.adapter_type = "mock"
    config.database.use_in_memory = True
    return config


def get_production_config() -> ApplicationConfig:
    """Get configuration optimized for production."""
    config = get_config()
    config.debug = False
    config.bedrock.use_mock = False
    config.email.adapter_type = "smtp"
    config.payment.adapter_type = "stripe"  # or actual payment provider
    config.database.use_in_memory = False
    return config


def setup_logging(config: Optional[LoggingConfig] = None) -> None:
    """Setup logging based on configuration."""
    if config is None:
        config = get_config().logging
    
    log_level = getattr(logging, config.level.upper(), logging.INFO)
    
    # Configure logging
    logging_config = {
        'level': log_level,
        'format': config.format,
        'handlers': []
    }
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    formatter = logging.Formatter(config.format)
    console_handler.setFormatter(formatter)
    
    # File handler if specified
    if config.file_path:
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            config.file_path,
            maxBytes=config.max_file_size_mb * 1024 * 1024,
            backupCount=config.backup_count
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logging.getLogger().addHandler(file_handler)
    
    logging.getLogger().addHandler(console_handler)
    logging.getLogger().setLevel(log_level)
    
    logger.info(f"Logging configured - Level: {config.level}, File: {config.file_path}")


# Initialize logging with default configuration
setup_logging()