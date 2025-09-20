"""
Base Entity class for Payment Intelligence Domain

This module provides the base entity class that all domain entities inherit from.
Entities have identity and lifecycle, unlike value objects.
"""
from abc import ABC
from typing import Any, List
from datetime import datetime
import uuid


class DomainEvent:
    """Base class for domain events"""
    def __init__(self, event_id: str = None, occurred_at: datetime = None):
        self.event_id = event_id or str(uuid.uuid4())
        self.occurred_at = occurred_at or datetime.utcnow()
        self.event_type = self.__class__.__name__


class Entity(ABC):
    """
    Base class for all domain entities.
    
    Entities are objects that have identity and lifecycle.
    They are compared by their identity, not their attributes.
    """
    
    def __init__(self, entity_id: str):
        if not entity_id:
            raise ValueError("Entity ID cannot be empty")
        
        self._id = entity_id
        self._domain_events: List[DomainEvent] = []
        self._created_at = datetime.utcnow()
        self._updated_at = datetime.utcnow()
    
    @property
    def id(self) -> str:
        """Get the entity identifier"""
        return self._id
    
    @property
    def created_at(self) -> datetime:
        """Get the creation timestamp"""
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        """Get the last update timestamp"""
        return self._updated_at
    
    def mark_as_modified(self) -> None:
        """Mark entity as modified (updates timestamp)"""
        self._updated_at = datetime.utcnow()
    
    def add_domain_event(self, event: DomainEvent) -> None:
        """Add a domain event to be published"""
        self._domain_events.append(event)
    
    def get_domain_events(self) -> List[DomainEvent]:
        """Get all domain events for this entity"""
        return self._domain_events.copy()
    
    def clear_domain_events(self) -> None:
        """Clear all domain events after publishing"""
        self._domain_events.clear()
    
    def __eq__(self, other: Any) -> bool:
        """Compare entities by their identity"""
        if not isinstance(other, Entity):
            return False
        return self._id == other._id
    
    def __hash__(self) -> int:
        """Hash entities by their identity"""
        return hash(self._id)
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(id={self._id})"
    
    def __repr__(self) -> str:
        return self.__str__()