"""
UMCC Agent Ex-Work v3.0 - Handlers Package
Genesis Agent Handler Modules

This package contains all specialized handlers for the UMCC Agent Ex-Work
autonomous execution engine. Each handler implements the BaseHandler
interface and provides specialized capabilities for different action types.

Handler Architecture:
- BaseHandler: Abstract base class defining the handler contract
- LLMHandler: Local language model operations and AI reasoning
- APIHandler: External API calls and data fetching operations

All handlers operate under the Architect's Core Directives and maintain
tungsten-grade reliability standards for autonomous operation.
"""

from .base_handler import BaseHandler, HandlerContext
from .llm_handlers import LLMHandler
from .api_handlers import APIHandler

# Handler registry for dynamic discovery
HANDLER_REGISTRY = {
    "llm_handler": LLMHandler,
    "api_handler": APIHandler,
}

# Export all handler classes and utilities
__all__ = [
    "BaseHandler",
    "HandlerContext", 
    "LLMHandler",
    "APIHandler",
    "HANDLER_REGISTRY"
]

# Version information
__version__ = "3.0.0"
__author__ = "UMCC Genesis Agent"
__description__ = "Autonomous action handlers for the Unfettered Mobile Command Center"
