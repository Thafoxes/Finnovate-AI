"""
API layer for the AI Payment Intelligence system.

This module provides REST API endpoints using FastAPI for:
- AI chatbot interactions
- Payment campaign management  
- Customer and invoice operations
- Dashboard integration
- Real-time WebSocket communication

The API layer serves as the entry point for external clients
and integrates with the application layer using CQRS patterns.
"""

from .endpoints import app

__all__ = ['app']