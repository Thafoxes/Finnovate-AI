"""AWS EventBridge Publisher Implementation"""

import boto3
import json
from dataclasses import asdict
from datetime import datetime
from ..domain.events import DomainEvent
from ..infrastructure.event_store import IEventPublisher

class EventBridgePublisher(IEventPublisher):
    """EventBridge implementation of event publisher"""
    
    def __init__(self, bus_name: str):
        self.eventbridge = boto3.client('events')
        self.bus_name = bus_name
    
    def publish(self, event: DomainEvent) -> None:
        """Publish domain event to EventBridge"""
        try:
            # Convert event to EventBridge format
            event_entry = {
                'Source': 'invoice-management',
                'DetailType': event.__class__.__name__,
                'Detail': json.dumps(self._serialize_event(event)),
                'EventBusName': self.bus_name
            }
            
            # Publish to EventBridge
            response = self.eventbridge.put_events(Entries=[event_entry])
            
            if response['FailedEntryCount'] > 0:
                print(f"Failed to publish event: {response}")
                
        except Exception as e:
            print(f"Error publishing event: {e}")
    
    def subscribe(self, event_type: str, handler) -> None:
        """Subscribe to event - not used in EventBridge (handled by AWS rules)"""
        pass
    
    def _serialize_event(self, event: DomainEvent) -> dict:
        """Convert event to JSON-serializable format"""
        try:
            event_dict = asdict(event)
            
            # Convert complex objects to strings
            for key, value in event_dict.items():
                if hasattr(value, '__str__') and not isinstance(value, (str, int, float, bool)):
                    event_dict[key] = str(value)
                elif isinstance(value, datetime):
                    event_dict[key] = value.isoformat()
            
            return event_dict
            
        except Exception as e:
            print(f"Error serializing event: {e}")
            return {'event_type': event.__class__.__name__}