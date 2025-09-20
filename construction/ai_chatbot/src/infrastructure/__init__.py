"""
Infrastructure layer for the AI Payment Intelligence system.

This layer provides concrete implementations of interfaces defined in the domain
and application layers, including:
- Repository implementations (in-memory for MVP, DynamoDB ready)
- External service adapters (email, notifications, payments)
- AWS Bedrock integration for AI capabilities
- Configuration management
- Logging and monitoring setup

The infrastructure layer follows the Dependency Inversion Principle,
implementing interfaces defined in higher layers.
"""

from .repositories import (
    InMemoryCustomerRepository,
    InMemoryInvoiceRepository,
    InMemoryPaymentCampaignRepository,
    InMemoryConversationRepository,
    RepositoryFactory,
    get_customer_repository,
    get_invoice_repository,
    get_payment_campaign_repository,
    get_conversation_repository
)

from .bedrock_service import (
    BedrockEmailGenerator,
    MockBedrockEmailGenerator,
    EmailGenerationRequest,
    EmailGenerationResponse,
    BedrockServiceError,
    create_email_generator,
    get_email_generator
)

from .external_services import (
    EmailMessage,
    NotificationMessage,
    PaymentRequest,
    EmailServiceAdapter,
    NotificationServiceAdapter,
    PaymentServiceAdapter,
    SMTPEmailAdapter,
    MockEmailAdapter,
    LoggingNotificationAdapter,
    MockPaymentAdapter,
    ServiceAdapterFactory,
    get_email_adapter,
    get_notification_adapter,
    get_payment_adapter,
    ServiceConfiguration,
    service_config
)

from .config import (
    ApplicationConfig,
    DatabaseConfig,
    BedrockConfig,
    EmailConfig,
    NotificationConfig,
    PaymentConfig,
    SecurityConfig,
    LoggingConfig,
    ConfigurationManager,
    config_manager,
    get_config,
    load_config_from_file,
    validate_configuration,
    get_development_config,
    get_production_config,
    setup_logging
)


# Infrastructure layer facade for easy dependency injection
class InfrastructureContainer:
    """
    Infrastructure container providing access to all infrastructure services.
    
    This container implements the Service Locator pattern and provides
    a single point of access to all infrastructure dependencies.
    """
    
    def __init__(self, config: ApplicationConfig = None):
        """
        Initialize infrastructure container.
        
        Args:
            config: Application configuration (uses default if None)
        """
        self._config = config or get_config()
        self._repositories = {}
        self._services = {}
        self._adapters = {}
    
    # Repository access methods
    def get_customer_repository(self):
        """Get customer repository instance."""
        if 'customer' not in self._repositories:
            self._repositories['customer'] = get_customer_repository()
        return self._repositories['customer']
    
    def get_invoice_repository(self):
        """Get invoice repository instance."""
        if 'invoice' not in self._repositories:
            self._repositories['invoice'] = get_invoice_repository()
        return self._repositories['invoice']
    
    def get_payment_campaign_repository(self):
        """Get payment campaign repository instance."""
        if 'campaign' not in self._repositories:
            self._repositories['campaign'] = get_payment_campaign_repository()
        return self._repositories['campaign']
    
    def get_conversation_repository(self):
        """Get conversation repository instance."""
        if 'conversation' not in self._repositories:
            self._repositories['conversation'] = get_conversation_repository()
        return self._repositories['conversation']
    
    # Service access methods
    def get_email_generator(self):
        """Get AI email generator service."""
        if 'email_generator' not in self._services:
            self._services['email_generator'] = get_email_generator(
                use_mock=self._config.bedrock.use_mock
            )
        return self._services['email_generator']
    
    # Adapter access methods
    def get_email_adapter(self):
        """Get email service adapter."""
        if 'email' not in self._adapters:
            if self._config.email.adapter_type == "smtp":
                self._adapters['email'] = get_email_adapter(
                    adapter_type="smtp",
                    smtp_server=self._config.email.smtp_server,
                    smtp_port=self._config.email.smtp_port,
                    username=self._config.email.username,
                    password=self._config.email.password,
                    use_tls=self._config.email.use_tls
                )
            else:
                self._adapters['email'] = get_email_adapter(adapter_type="mock")
        return self._adapters['email']
    
    def get_notification_adapter(self):
        """Get notification service adapter."""
        if 'notification' not in self._adapters:
            self._adapters['notification'] = get_notification_adapter(
                adapter_type=self._config.notification.adapter_type
            )
        return self._adapters['notification']
    
    def get_payment_adapter(self):
        """Get payment service adapter."""
        if 'payment' not in self._adapters:
            self._adapters['payment'] = get_payment_adapter(
                adapter_type=self._config.payment.adapter_type
            )
        return self._adapters['payment']
    
    # Configuration access
    def get_config(self) -> ApplicationConfig:
        """Get application configuration."""
        return self._config
    
    # Health check methods
    def health_check(self) -> dict:
        """Perform infrastructure health check."""
        results = {
            "status": "healthy",
            "checks": {},
            "timestamp": None
        }
        
        try:
            from datetime import datetime
            results["timestamp"] = datetime.now().isoformat()
            
            # Check repositories
            try:
                customer_repo = self.get_customer_repository()
                results["checks"]["customer_repository"] = "healthy"
            except Exception as e:
                results["checks"]["customer_repository"] = f"error: {e}"
                results["status"] = "unhealthy"
            
            # Check AI service
            try:
                email_generator = self.get_email_generator()
                results["checks"]["email_generator"] = "healthy"
            except Exception as e:
                results["checks"]["email_generator"] = f"error: {e}"
                results["status"] = "degraded"
            
            # Check adapters
            try:
                email_adapter = self.get_email_adapter()
                results["checks"]["email_adapter"] = "healthy"
            except Exception as e:
                results["checks"]["email_adapter"] = f"error: {e}"
                results["status"] = "degraded"
            
            # Check configuration
            validation = validate_configuration()
            if validation["valid"]:
                results["checks"]["configuration"] = "valid"
            else:
                results["checks"]["configuration"] = f"issues: {validation['issues']}"
                results["status"] = "unhealthy"
            
        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
        
        return results


# Global infrastructure container instance
_infrastructure_container = None


def get_infrastructure_container(config: ApplicationConfig = None) -> InfrastructureContainer:
    """
    Get the global infrastructure container instance.
    
    Args:
        config: Optional configuration override
        
    Returns:
        InfrastructureContainer instance
    """
    global _infrastructure_container
    if _infrastructure_container is None or config is not None:
        _infrastructure_container = InfrastructureContainer(config)
    return _infrastructure_container


def reset_infrastructure_container():
    """Reset the global infrastructure container (useful for testing)."""
    global _infrastructure_container
    _infrastructure_container = None


# Infrastructure initialization
def initialize_infrastructure(config: ApplicationConfig = None) -> InfrastructureContainer:
    """
    Initialize the infrastructure layer with the given configuration.
    
    Args:
        config: Application configuration
        
    Returns:
        Initialized infrastructure container
    """
    if config is None:
        config = get_config()
    
    # Setup logging
    setup_logging(config.logging)
    
    # Create and configure infrastructure container
    container = InfrastructureContainer(config)
    
    # Validate configuration
    validation = validate_configuration()
    if not validation["valid"]:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Configuration issues detected: {validation['issues']}")
        if validation["warnings"]:
            logger.warning(f"Configuration warnings: {validation['warnings']}")
    
    return container


# Module-level exports for easy access
__all__ = [
    # Repository implementations
    'InMemoryCustomerRepository',
    'InMemoryInvoiceRepository', 
    'InMemoryPaymentCampaignRepository',
    'InMemoryConversationRepository',
    'RepositoryFactory',
    'get_customer_repository',
    'get_invoice_repository',
    'get_payment_campaign_repository',
    'get_conversation_repository',
    
    # Bedrock AI service
    'BedrockEmailGenerator',
    'MockBedrockEmailGenerator',
    'EmailGenerationRequest',
    'EmailGenerationResponse',
    'BedrockServiceError',
    'create_email_generator',
    'get_email_generator',
    
    # External service adapters
    'EmailMessage',
    'NotificationMessage',
    'PaymentRequest',
    'EmailServiceAdapter',
    'NotificationServiceAdapter',
    'PaymentServiceAdapter',
    'SMTPEmailAdapter',
    'MockEmailAdapter',
    'LoggingNotificationAdapter',
    'MockPaymentAdapter',
    'ServiceAdapterFactory',
    'get_email_adapter',
    'get_notification_adapter',
    'get_payment_adapter',
    'ServiceConfiguration',
    'service_config',
    
    # Configuration management
    'ApplicationConfig',
    'DatabaseConfig',
    'BedrockConfig',
    'EmailConfig',
    'NotificationConfig',
    'PaymentConfig',
    'SecurityConfig',
    'LoggingConfig',
    'ConfigurationManager',
    'config_manager',
    'get_config',
    'load_config_from_file',
    'validate_configuration',
    'get_development_config',
    'get_production_config',
    'setup_logging',
    
    # Infrastructure container
    'InfrastructureContainer',
    'get_infrastructure_container',
    'reset_infrastructure_container',
    'initialize_infrastructure'
]