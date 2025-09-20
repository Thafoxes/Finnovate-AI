"""In-Memory Event Store and Event Publisher"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from dataclasses import asdict
from domain.events import DomainEvent
from domain.value_objects import InvoiceId, EventId


# Event Store Interface

class IEventStore(ABC):
    """Interface for event store"""
    
    @abstractmethod
    def save_event(self, event: DomainEvent) -> None:
        """Save domain event"""
        pass
    
    @abstractmethod
    def get_events_by_aggregate(self, aggregate_id: str) -> List[DomainEvent]:
        """Get all events for specific aggregate"""
        pass
    
    @abstractmethod
    def get_all_events(self) -> List[DomainEvent]:
        """Get all events"""
        pass


# Event Publisher Interface

class IEventPublisher(ABC):
    """Interface for event publisher"""
    
    @abstractmethod
    def publish(self, event: DomainEvent) -> None:
        """Publish domain event"""
        pass
    
    @abstractmethod
    def subscribe(self, event_type: str, handler: Callable[[DomainEvent], None]) -> None:
        """Subscribe to event type"""
        pass


# In-Memory Implementations

class InMemoryEventStore(IEventStore):
    """In-memory implementation of event store"""
    
    def __init__(self):
        self._events: List[DomainEvent] = []
        self._events_by_aggregate: Dict[str, List[DomainEvent]] = {}
    
    def save_event(self, event: DomainEvent) -> None:
        """Save domain event"""
        self._events.append(event)
        
        # Extract aggregate ID from event (simplified approach)
        aggregate_id = self._extract_aggregate_id(event)
        if aggregate_id:
            if aggregate_id not in self._events_by_aggregate:
                self._events_by_aggregate[aggregate_id] = []
            self._events_by_aggregate[aggregate_id].append(event)
    
    def get_events_by_aggregate(self, aggregate_id: str) -> List[DomainEvent]:
        """Get all events for specific aggregate"""
        return self._events_by_aggregate.get(aggregate_id, [])
    
    def get_all_events(self) -> List[DomainEvent]:
        """Get all events"""
        return self._events.copy()
    
    def _extract_aggregate_id(self, event: DomainEvent) -> Optional[str]:
        """Extract aggregate ID from event"""
        # Check for invoice_id in event
        if hasattr(event, 'invoice_id') and event.invoice_id:
            return str(event.invoice_id)
        # Check for payment_id in event
        if hasattr(event, 'payment_id') and event.payment_id:
            return str(event.payment_id)
        return None
    
    def clear(self) -> None:
        """Clear all events (for testing)"""
        self._events.clear()
        self._events_by_aggregate.clear()
    
    def count(self) -> int:
        """Get count of events"""
        return len(self._events)


class InMemoryEventPublisher(IEventPublisher):
    """In-memory implementation of event publisher"""
    
    def __init__(self, event_store: IEventStore):
        self._event_store = event_store
        self._subscribers: Dict[str, List[Callable[[DomainEvent], None]]] = {}
        self._published_events: List[DomainEvent] = []
    
    def publish(self, event: DomainEvent) -> None:
        """Publish domain event"""
        # Save to event store
        self._event_store.save_event(event)
        
        # Add to published events list
        self._published_events.append(event)
        
        # Notify subscribers
        event_type = event.__class__.__name__
        subscribers = self._subscribers.get(event_type, [])
        
        for handler in subscribers:
            try:
                handler(event)
            except Exception as e:
                # In real implementation, this would be logged
                print(f"Error handling event {event_type}: {e}")
    
    def subscribe(self, event_type: str, handler: Callable[[DomainEvent], None]) -> None:
        """Subscribe to event type"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
    
    def get_published_events(self) -> List[DomainEvent]:
        """Get all published events (for testing)"""
        return self._published_events.copy()
    
    def get_published_events_by_type(self, event_type: str) -> List[DomainEvent]:
        """Get published events by type (for testing)"""
        return [event for event in self._published_events 
                if event.__class__.__name__ == event_type]
    
    def clear_published_events(self) -> None:
        """Clear published events (for testing)"""
        self._published_events.clear()
    
    def get_subscriber_count(self, event_type: str) -> int:
        """Get number of subscribers for event type"""
        return len(self._subscribers.get(event_type, []))


# Event Bus (combines store and publisher)

class InMemoryEventBus:
    """In-memory event bus combining store and publisher"""
    
    def __init__(self):
        self._event_store = InMemoryEventStore()
        self._event_publisher = InMemoryEventPublisher(self._event_store)
    
    @property
    def event_store(self) -> IEventStore:
        return self._event_store
    
    @property
    def event_publisher(self) -> IEventPublisher:
        return self._event_publisher
    
    def publish_event(self, event: DomainEvent) -> None:
        """Publish event (convenience method)"""
        self._event_publisher.publish(event)
    
    def subscribe_to_event(self, event_type: str, handler: Callable[[DomainEvent], None]) -> None:
        """Subscribe to event (convenience method)"""
        self._event_publisher.subscribe(event_type, handler)
    
    def get_event_history(self, aggregate_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get event history for debugging/monitoring"""
        if aggregate_id:
            events = self._event_store.get_events_by_aggregate(aggregate_id)
        else:
            events = self._event_store.get_all_events()
        
        history = []
        for event in events:
            event_data = {
                'event_id': str(event.event_id),
                'event_type': event.__class__.__name__,
                'occurred_at': event.occurred_at.isoformat(),
                'data': self._serialize_event(event)
            }
            history.append(event_data)
        
        return history
    
    def _serialize_event(self, event: DomainEvent) -> Dict[str, Any]:
        """Serialize event to dictionary"""
        try:
            # Convert dataclass to dict
            event_dict = asdict(event)
            
            # Convert complex objects to strings
            for key, value in event_dict.items():
                if hasattr(value, '__str__') and not isinstance(value, (str, int, float, bool)):
                    event_dict[key] = str(value)
                elif isinstance(value, datetime):
                    event_dict[key] = value.isoformat()
            
            return event_dict
        except Exception:
            # Fallback to basic representation
            return {'event_type': event.__class__.__name__, 'timestamp': event.occurred_at.isoformat()}
    
    def reset(self) -> None:
        """Reset event bus (for testing)"""
        self._event_store.clear()
        self._event_publisher.clear_published_events()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics"""
        return {
            'total_events': self._event_store.count(),
            'published_events': len(self._event_publisher.get_published_events()),
            'event_types': list(set(event.__class__.__name__ 
                                  for event in self._event_store.get_all_events()))
        }


# Event Handler Registry

class EventHandlerRegistry:
    """Registry for event handlers"""
    
    def __init__(self, event_bus: InMemoryEventBus):
        self._event_bus = event_bus
        self._handlers: Dict[str, List[str]] = {}
    
    def register_handler(self, event_type: str, handler_name: str, 
                        handler_func: Callable[[DomainEvent], None]) -> None:
        """Register event handler"""
        self._event_bus.subscribe_to_event(event_type, handler_func)
        
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler_name)
    
    def get_registered_handlers(self) -> Dict[str, List[str]]:
        """Get all registered handlers"""
        return self._handlers.copy()


# Event Bus Factory

class EventBusFactory:
    """Factory for creating event bus instances"""
    
    @staticmethod
    def create_event_bus() -> InMemoryEventBus:
        """Create event bus instance"""
        return InMemoryEventBus()
    
    @staticmethod
    def create_event_store() -> IEventStore:
        """Create event store instance"""
        return InMemoryEventStore()
    
    @staticmethod
    def create_event_publisher(event_store: IEventStore) -> IEventPublisher:
        """Create event publisher instance"""
        return InMemoryEventPublisher(event_store)


# Global Event Bus (singleton for demo)

class GlobalEventBus:
    """Global event bus singleton for demo purposes"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._event_bus = InMemoryEventBus()
            self._initialized = True
    
    @property
    def event_bus(self) -> InMemoryEventBus:
        return self._event_bus
    
    def reset(self) -> None:
        """Reset global event bus"""
        self._event_bus.reset()