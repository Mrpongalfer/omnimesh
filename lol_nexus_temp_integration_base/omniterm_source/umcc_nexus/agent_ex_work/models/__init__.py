# agent_ex_work/models/__init__.py
"""
UMCC Agent Ex-Work v3.0 - Models Package
Genesis Agent Data Models

This package contains all Pydantic models used by the UMCC Agent Ex-Work
autonomous execution engine for type safety, validation, and serialization.
"""

from .action import Action, ActionType, InstructionBlock, AgentConfig
from .results import ActionResult, OverallResult

# Export all model classes
__all__ = [
    "Action",
    "ActionType", 
    "InstructionBlock",
    "AgentConfig",
    "ActionResult",
    "OverallResult"
]

# Version information
__version__ = "3.0.0"
__author__ = "UMCC Genesis Agent"
__description__ = "Data models for the Unfettered Mobile Command Center"
