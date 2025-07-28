"""
Base handler module for Agent Ex-Work v3.0
UMCC Genesis Agent - Base Handler Implementation

Provides the foundational abstract base class and context management
for all specialized action handlers in the UMCC ecosystem.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path

from ..models.action import Action, ActionType
from ..models.results import ActionResult


@dataclass
class HandlerContext:
    """
    Context container for handler execution environment.
    Provides access to configuration, logging, metrics, and execution state.
    """
    # Core execution context
    action: Action
    config: Dict[str, Any]
    logger: logging.Logger
    execution_id: str
    timestamp: float = field(default_factory=time.time)
    
    # State management
    variables: Dict[str, Any] = field(default_factory=dict)
    working_directory: Path = field(default_factory=lambda: Path.cwd())
    timeout_seconds: int = 300
    
    # Security and audit context
    security_level: str = "standard"
    audit_trail: List[str] = field(default_factory=list)
    
    # Environment specifics
    environment: str = "production"
    user_context: Optional[str] = None
    
    def add_audit_entry(self, message: str) -> None:
        """Add an entry to the audit trail with timestamp"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        self.audit_trail.append(f"[{timestamp}] {message}")
    
    def get_variable(self, key: str, default: Any = None) -> Any:
        """Safely retrieve a context variable"""
        return self.variables.get(key, default)
    
    def set_variable(self, key: str, value: Any) -> None:
        """Set a context variable with audit logging"""
        self.variables[key] = value
        self.add_audit_entry(f"Variable set: {key} = {type(value).__name__}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for serialization"""
        return {
            "execution_id": self.execution_id,
            "timestamp": self.timestamp,
            "action_type": self.action.action_type.value,
            "security_level": self.security_level,
            "environment": self.environment,
            "working_directory": str(self.working_directory),
            "timeout_seconds": self.timeout_seconds,
            "variables": self.variables,
            "audit_trail": self.audit_trail
        }


class BaseHandler(ABC):
    """
    Abstract base class for all UMCC action handlers.
    
    Defines the contract that all specialized handlers must implement,
    providing common functionality for logging, error handling, and
    result generation in accordance with the Architect's protocols.
    """
    
    def __init__(self, handler_name: str):
        """
        Initialize the base handler with essential components.
        
        Args:
            handler_name: Unique identifier for this handler type
        """
        self.handler_name = handler_name
        self.logger = logging.getLogger(f"umcc.agent.handler.{handler_name}")
        self.execution_count = 0
        self.success_count = 0
        self.error_count = 0
        self.total_execution_time = 0.0
        
        # Initialize structured logging
        self.logger.setLevel(logging.INFO)
        
        # Handler-specific metrics
        self.metrics = {
            "handler_name": handler_name,
            "initialized_at": time.time(),
            "executions": 0,
            "successes": 0,
            "errors": 0,
            "average_execution_time": 0.0
        }
    
    @abstractmethod
    def can_handle(self, action_type: ActionType) -> bool:
        """
        Determine if this handler can process the given action type.
        
        Args:
            action_type: The type of action to be executed
            
        Returns:
            True if this handler can process the action, False otherwise
        """
        pass
    
    @abstractmethod
    async def execute(self, context: HandlerContext) -> ActionResult:
        """
        Execute the action with the provided context.
        
        This is the core method that each handler must implement to
        process their specific action types according to the UMCC
        protocols and Architect's directives.
        
        Args:
            context: Complete execution context including action and environment
            
        Returns:
            ActionResult containing execution outcome and artifacts
            
        Raises:
            Exception: Implementation-specific exceptions for error conditions
        """
        pass
    
    async def handle_action(self, context: HandlerContext) -> ActionResult:
        """
        Primary entry point for action execution with comprehensive
        logging, metrics collection, and error handling.
        
        Args:
            context: Complete execution context
            
        Returns:
            ActionResult with execution outcome
        """
        start_time = time.time()
        self.execution_count += 1
        
        # Pre-execution logging and validation
        self.logger.info(
            "Handler execution initiated",
            extra={
                "handler_name": self.handler_name,
                "action_type": context.action.action_type.value,
                "execution_id": context.execution_id,
                "security_level": context.security_level
            }
        )
        
        context.add_audit_entry(f"Handler {self.handler_name} initiated execution")
        
        try:
            # Validate handler capability
            if not self.can_handle(context.action.action_type):
                raise ValueError(f"Handler {self.handler_name} cannot process action type {context.action.action_type}")
            
            # Execute the action
            result = await self.execute(context)
            
            # Post-execution metrics and logging
            execution_time = time.time() - start_time
            self.total_execution_time += execution_time
            
            if result.success:
                self.success_count += 1
                self.logger.info(
                    "Handler execution completed successfully",
                    extra={
                        "handler_name": self.handler_name,
                        "execution_id": context.execution_id,
                        "execution_time": execution_time,
                        "output_size": len(str(result.output)) if result.output else 0
                    }
                )
            else:
                self.error_count += 1
                self.logger.warning(
                    "Handler execution completed with errors",
                    extra={
                        "handler_name": self.handler_name,
                        "execution_id": context.execution_id,
                        "execution_time": execution_time,
                        "error_message": result.error_message
                    }
                )
            
            context.add_audit_entry(f"Handler execution completed: success={result.success}")
            result.execution_time = execution_time
            
            return result
            
        except Exception as e:
            # Error handling and logging
            execution_time = time.time() - start_time
            self.error_count += 1
            self.total_execution_time += execution_time
            
            self.logger.error(
                "Handler execution failed with exception",
                extra={
                    "handler_name": self.handler_name,
                    "execution_id": context.execution_id,
                    "execution_time": execution_time,
                    "exception_type": type(e).__name__,
                    "exception_message": str(e)
                },
                exc_info=True
            )
            
            context.add_audit_entry(f"Handler execution failed: {type(e).__name__}: {str(e)}")
            
            # Return error result
            return ActionResult(
                action_type=context.action.action_type,
                success=False,
                output=None,
                error_message=f"Handler execution failed: {str(e)}",
                execution_time=execution_time,
                metadata={
                    "handler_name": self.handler_name,
                    "exception_type": type(e).__name__,
                    "context": context.to_dict()
                }
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current handler performance metrics.
        
        Returns:
            Dictionary containing handler performance statistics
        """
        avg_time = (self.total_execution_time / self.execution_count 
                   if self.execution_count > 0 else 0.0)
        
        return {
            "handler_name": self.handler_name,
            "executions": self.execution_count,
            "successes": self.success_count,
            "errors": self.error_count,
            "success_rate": (self.success_count / self.execution_count 
                           if self.execution_count > 0 else 0.0),
            "average_execution_time": avg_time,
            "total_execution_time": self.total_execution_time
        }
    
    def reset_metrics(self) -> None:
        """Reset all handler metrics to zero"""
        self.execution_count = 0
        self.success_count = 0
        self.error_count = 0
        self.total_execution_time = 0.0
        self.logger.info(f"Metrics reset for handler {self.handler_name}")
    
    def validate_action(self, action: Action) -> bool:
        """
        Validate that an action is properly formed for this handler.
        
        Args:
            action: Action to validate
            
        Returns:
            True if action is valid, False otherwise
        """
        if not action:
            return False
        
        if not isinstance(action.action_type, ActionType):
            return False
        
        if not self.can_handle(action.action_type):
            return False
        
        # Additional validation can be implemented by subclasses
        return True
    
    def __repr__(self) -> str:
        """String representation of the handler"""
        return (f"{self.__class__.__name__}(name={self.handler_name}, "
                f"executions={self.execution_count}, "
                f"success_rate={self.success_count/max(1, self.execution_count):.2%})")
