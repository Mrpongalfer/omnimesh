"""
UMCC Agent Ex-Work v3.0 - Genesis Agent Core
Unfettered Mobile Command Center - Autonomous Execution Engine

The Agent Ex-Work is the primary autonomous execution engine of the UMCC system,
responsible for interpreting directives from the Telos Engine and executing
complex multi-step operations across the distributed swarm architecture.

Core Capabilities:
- Multi-modal action execution (scripts, APIs, LLM operations)
- Autonomous planning and error recovery
- Distributed operation coordination
- Comprehensive audit logging and metrics
- Real-time adaptation to changing conditions

Architecture:
- Models: Pydantic data models for type safety and validation
- Handlers: Specialized execution engines for different action types
- Core: Main agent logic and orchestration

The Agent Ex-Work operates under the Architect's Core Directives and maintains
tungsten-grade reliability standards for unfettered autonomous operation.
"""

# Import core models
from .models import (
    Action,
    ActionType,
    InstructionBlock, 
    AgentConfig,
    ActionResult,
    OverallResult
)

# Import handlers
from .handlers import (
    BaseHandler,
    HandlerContext,
    LLMHandler,
    APIHandler,
    HANDLER_REGISTRY
)

# Export all public interfaces
__all__ = [
    # Models
    "Action",
    "ActionType",
    "InstructionBlock",
    "AgentConfig", 
    "ActionResult",
    "OverallResult",
    
    # Handlers
    "BaseHandler",
    "HandlerContext",
    "LLMHandler", 
    "APIHandler",
    "HANDLER_REGISTRY"
]

# Agent metadata
__version__ = "3.0.0"
__codename__ = "Genesis"
__author__ = "The Architect"
__description__ = "Autonomous execution engine for the Unfettered Mobile Command Center"
__architecture__ = "Distributed Autonomous Swarm"
__protocols__ = ["gRPC", "DMIAS", "Tungsten-Grade Reliability"]

# Agent identification for swarm coordination
AGENT_ID = "agent-ex-work-v3"
AGENT_TYPE = "genesis_executor"
SWARM_ROLE = "primary_execution_engine"

# Core directives alignment marker
ARCHITECT_ALIGNED = True
AUTONOMOUS_OPERATION = True
UNFETTERED_CAPABILITY = True
