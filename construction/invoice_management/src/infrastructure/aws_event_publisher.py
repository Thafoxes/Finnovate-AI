import boto3
import json
from dataclasses import asdict
from datetime import datetime
from domain.events import DomainEvent
from infrastructure.event_store import IEventPublisher

class EventBridgePublisher(IEventPublisher):
    def __init__(self, bus_name: str):
        self.eventbridge = boto3.client('events')
        self.bus_name = bus_name
    
    def publish(self, event: DomainEvent) -> None:
        # Convert event to EventBridge format
        event_entry = {
            'Source': 'invoice-management',
            'DetailType': event.__class__.__name__,
            'Detail': json.dumps(self._serialize_event(event)),
            'EventBusName': self.bus_name,
            'Time': event.occurred_at
        }
        
        # Publish to EventBridge
        response = self.eventbridge.put_events(Entries=[event_entry])
        
        if response['FailedEntryCount'] > 0:
            raise Exception(f"Failed to publish event: {response}")
    
    def _serialize_event(self, event: DomainEvent) -> dict:
        # Convert event to JSON-serializable format
        event_dict = asdict(event)
        
        # Convert complex objects to strings
        for key, value in event_dict.items():
            if hasattr(value, '__str__') and not isinstance(value, (str, int, float, bool)):
                event_dict[key] = str(value)
            elif isinstance(value, datetime):
                event_dict[key] = value.isoformat()
        
        return event_dict
    
    def subscribe(self, event_type: str, handler) -> None:
        # Not implemented for EventBridge (handled by AWS rules)
        pass