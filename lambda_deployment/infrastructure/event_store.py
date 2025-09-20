"""Event Store Interface"""

from abc import ABC, abstractmethod
from domain.events import DomainEvent

class IEventPublisher(ABC):
    """Interface for event publisher"""
    
    @abstractmethod
    def publish(self, event: DomainEvent) -> None:
        """Publish domain event"""
        pass
    
    @abstractmethod
    def subscribe(self, event_type: str, handler) -> None:
        """Subscribe to event type"""
        pass