#!/usr/bin/env python3
"""
LoL Nexus Core Orchestrator v3.0
Trinity Convergence: PONGEX + OMNITERM + OMNIMESH Unified Architecture

The central orchestration engine for the LoL Nexus Compute Fabric.
Integrates high-performance computing, natural language interfaces,
and distributed system orchestration.
"""

import asyncio
import json
import logging
import os
import sys
import toml
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import subprocess
import signal
import time

# Core imports for Trinity Convergence
try:
    from .agents.exwork_agent import ExWorkAgent
    from .agents.noa_module import NOAModule
    from .fabric_proxies.rust_bridge import RustBridge
    from .fabric_proxies.go_proxy import GoProxyManager
except ImportError:
    # Fallback for development/testing
    class ExWorkAgent:
        def __init__(self, *args, **kwargs): pass
        async def initialize(self): return True
        async def shutdown(self): pass
        async def health_check(self): return True
        async def handle_operation(self, op): return {"status": "completed"}
    
    class NOAModule:
        def __init__(self, *args, **kwargs): pass
        async def initialize(self): return True
        async def shutdown(self): pass
        async def health_check(self): return True
        async def handle_operation(self, op): return {"status": "completed"}
    
    class RustBridge:
        def __init__(self, *args, **kwargs): pass
        async def initialize(self): return True
        async def shutdown(self): pass
        async def health_check(self): return True
        async def handle_operation(self, op): return {"status": "completed"}
    
    class GoProxyManager:
        def __init__(self, *args, **kwargs): pass
        async def initialize(self): return True
        async def shutdown(self): pass
        async def health_check(self): return True
        async def handle_operation(self, op): return {"status": "completed"}

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.agents.models.action import (
    Action, ActionResult, ActionType, AgentConfig,
    InstructionBlock, OverallResult, ExecutionContext
)


class LoLNexusOrchestrator:
    """
    LoL Nexus Orchestrator - Trinity Convergence Architecture
    Primary autonomous execution engine combining:
    - PONGEX ExWork Agent v3.0 (Core Engine)
    - omniterm Genesis Agent (Interface Layer)  
    - OMNIMESH Infrastructure (Platform Layer)
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/nexus_config.toml"
        self.config: Optional[AgentConfig] = None
        self.is_running = False
        self.execution_context: Optional[ExecutionContext] = None
        self.active_instructions: Dict[str, InstructionBlock] = {}
        self.execution_history: List[OverallResult] = []

        # Setup logging
        self._setup_logging()

        logger.info("🚀 LoL Nexus Orchestrator v3.0 initializing (Trinity Convergence)...")

    def _setup_logging(self):
        """Configure structured logging for the agent"""
        # Remove default logger
        logger.remove()

        # Add structured JSON logging to file
        log_dir = Path("../logs")
        log_dir.mkdir(exist_ok=True)

        logger.add(
            log_dir / "agent_ex_work.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
            rotation="100 MB",
            retention="30 days",
            serialize=True,  # JSON format
            level="INFO"
        )

        # Add console logging
        logger.add(
            sys.stdout,
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level="INFO"
        )

    def load_config(self) -> None:
        """Load unified LoL Nexus configuration from master TOML file"""
        logger.info("📋 Loading LoL Nexus Trinity Convergence configuration...")

        # Load the master nexus configuration
        nexus_config_path = Path(self.config_path)
        agent_config_path = Path("core/agents/config/agent_config.toml")

        config_data = {}

        # Load master nexus config
        if nexus_config_path.exists():
            try:
                nexus_config = toml.load(nexus_config_path)
                logger.info(f"✅ Loaded master nexus config from {nexus_config_path}")

                # Extract core configuration
                if "core" in nexus_config:
                    config_data.update(nexus_config["core"])

                # Extract agent configuration
                if "agents" in nexus_config:
                    config_data.update(nexus_config["agents"])

                # Extract security configuration
                if "security" in nexus_config:
                    config_data.update(nexus_config["security"])

                # Extract performance configuration  
                if "performance" in nexus_config:
                    config_data.update(nexus_config["performance"])

            except Exception as e:
                logger.warning(f"⚠️  Failed to load master nexus config: {e}")

        # Load agent-specific config as fallback
        if agent_config_path.exists():
            try:
                agent_config = toml.load(agent_config_path)
                logger.info(f"✅ Loaded agent config from {agent_config_path}")

                # Merge agent config with lower priority
                for key, value in agent_config.items():
                    if key not in config_data:
                        config_data[key] = value

            except Exception as e:
                logger.warning(f"⚠️  Failed to load agent config: {e}")

        # Load agent-specific config if it exists
        if agent_config_path.exists():
            try:
                agent_config = toml.load(agent_config_path)
                config_data.update(agent_config.get("agent", {}))
                logger.info(f"✅ Loaded agent config from {agent_config_path}")
            except Exception as e:
                logger.warning(f"⚠️  Failed to load agent config: {e}")

        # Set defaults
        config_data.setdefault("agent_id", f"agent_ex_work_{int(time.time())}")
        config_data.setdefault("hive_address", "localhost:50051")
        config_data.setdefault("listen_port", 50053)
        config_data.setdefault("log_level", "INFO")
        config_data.setdefault("max_concurrent_actions", 5)
        config_data.setdefault("default_timeout_seconds", 300)
        config_data.setdefault("enable_autonomous_planning", True)
        config_data.setdefault("ollama_host", "http://localhost:11434")
        config_data.setdefault("template_cache_size", 100)

        try:
            self.config = AgentConfig(**config_data)
            logger.info(f"✅ Agent configuration loaded successfully (ID: {self.config.agent_id})")
        except ValidationError as e:
            logger.error(f"❌ Invalid agent configuration: {e}")
            raise

        # Setup execution context
        self.execution_context = ExecutionContext(
            working_directory=str(Path.cwd()),
            environment_variables=dict(os.environ),
            user_id=os.getenv("USER", "unknown"),
            node_id=self.config.agent_id,
            transaction_id="",
            debug_mode=os.getenv("DEBUG", "false").lower() == "true"
        )

    async def execute_instruction_block(self, instruction_block: InstructionBlock) -> OverallResult:
        """
        Execute a complete instruction block
        """
        logger.info(f"🎯 Executing instruction block: {instruction_block.step_id}")
        logger.info(f"📝 Description: {instruction_block.description}")

        start_time = time.time()
        action_results: List[ActionResult] = []
        overall_success = True

        # Update execution context with transaction ID
        if self.execution_context:
            self.execution_context.transaction_id = instruction_block.transaction_id

        # Store the active instruction
        self.active_instructions[instruction_block.step_id] = instruction_block

        try:
            # Handle high-level goals with autonomous planning
            if instruction_block.is_high_level_goal and instruction_block.goal:
                logger.info(f"🤖 Autonomous planning for goal: {instruction_block.goal}")
                # TODO: Implement autonomous planning logic
                # For now, create a simple diagnostic action
                diagnostic_action = Action(
                    step_id=f"diagnostic_{int(time.time())}",
                    type=ActionType.SYSTEM_INFO,
                    description=f"Autonomous diagnostic for goal: {instruction_block.goal}",
                    params={"info_type": "system_overview"},
                    timeout_seconds=30
                )
                instruction_block.actions = [diagnostic_action]

            # Execute each action in the instruction block
            for action in instruction_block.actions:
                logger.info(f"⚡ Executing action: {action.step_id} ({action.type})")

                try:
                    result = await self.execute_action(action)
                    action_results.append(result)

                    if not result.success:
                        overall_success = False
                        logger.error(f"❌ Action failed: {action.step_id} - {result.error}")

                        # TODO: Implement retry logic and error recovery

                except Exception as e:
                    logger.error(f"💥 Exception during action execution: {e}")
                    error_result = ActionResult(
                        success=False,
                        output="",
                        error=f"Exception during execution: {str(e)}",
                        action_type=action.type,
                        action_id=action.step_id,
                        duration_seconds=0.0,
                        timestamp=datetime.now()
                    )
                    action_results.append(error_result)
                    overall_success = False

        except Exception as e:
            logger.error(f"💥 Critical error during instruction block execution: {e}")
            overall_success = False

        finally:
            # Remove from active instructions
            self.active_instructions.pop(instruction_block.step_id, None)

        # Create overall result
        total_duration = time.time() - start_time
        overall_result = OverallResult(
            overall_success=overall_success,
            status_message=f"Executed {len(action_results)} actions, {sum(1 for r in action_results if r.success)} succeeded",
            total_duration_seconds=total_duration,
            action_results=action_results,
            timestamp=datetime.now(),
            instruction_block_id=instruction_block.step_id,
            transaction_id=instruction_block.transaction_id,
            source_actor=instruction_block.source_actor
        )

        # Store in execution history
        self.execution_history.append(overall_result)

        # Keep only last 100 results to prevent memory issues
        if len(self.execution_history) > 100:
            self.execution_history = self.execution_history[-100:]

        logger.info(f"✅ Instruction block completed: {instruction_block.step_id} (Success: {overall_success})")
        return overall_result

    async def execute_action(self, action: Action) -> ActionResult:
        """
        Execute a single action
        """
        start_time = time.time()

        try:
            # TODO: Implement action handlers
            # For now, create mock execution based on action type

            if action.type == ActionType.SYSTEM_INFO:
                return await self._mock_system_info_action(action)
            elif action.type == ActionType.RUN_SCRIPT:
                return await self._mock_run_script_action(action)
            elif action.type == ActionType.CALL_LOCAL_LLM:
                return await self._mock_llm_action(action)
            else:
                # Default mock action
                await asyncio.sleep(0.1)  # Simulate work
                return ActionResult(
                    success=True,
                    output=f"Mock execution of {action.type} action completed",
                    error="",
                    action_type=action.type,
                    action_id=action.step_id,
                    duration_seconds=time.time() - start_time,
                    timestamp=datetime.now(),
                    payload={"mock": True, "params": action.params}
                )

        except Exception as e:
            return ActionResult(
                success=False,
                output="",
                error=f"Action execution failed: {str(e)}",
                action_type=action.type,
                action_id=action.step_id,
                duration_seconds=time.time() - start_time,
                timestamp=datetime.now()
            )

    async def _mock_system_info_action(self, action: Action) -> ActionResult:
        """Mock system information gathering"""
        start_time = time.time()

        import platform
        import psutil

        try:
            system_info = {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "disk_usage": psutil.disk_usage('/').percent,
                "current_time": datetime.now().isoformat()
            }

            return ActionResult(
                success=True,
                output=json.dumps(system_info, indent=2),
                error="",
                action_type=action.type,
                action_id=action.step_id,
                duration_seconds=time.time() - start_time,
                timestamp=datetime.now(),
                payload=system_info
            )

        except Exception as e:
            return ActionResult(
                success=False,
                output="",
                error=f"System info gathering failed: {str(e)}",
                action_type=action.type,
                action_id=action.step_id,
                duration_seconds=time.time() - start_time,
                timestamp=datetime.now()
            )

    async def _mock_run_script_action(self, action: Action) -> ActionResult:
        """Mock script execution"""
        start_time = time.time()

        script = action.params.get("script", "echo 'Hello from Agent Ex-Work'")

        return ActionResult(
            success=True,
            output=f"Mock execution of script: {script}\nScript output would appear here",
            error="",
            action_type=action.type,
            action_id=action.step_id,
            duration_seconds=time.time() - start_time,
            timestamp=datetime.now(),
            payload={"script": script, "mock": True}
        )

    async def _mock_llm_action(self, action: Action) -> ActionResult:
        """Mock LLM interaction"""
        start_time = time.time()

        prompt = action.params.get("prompt", "System status check")

        # Simulate LLM processing time
        await asyncio.sleep(0.5)

        mock_response = f"AI Analysis for: {prompt}\n\nBased on current system parameters, the optimal approach would be to implement a structured diagnostic protocol. This would involve systematic evaluation of key performance indicators and strategic alignment with core directives."

        return ActionResult(
            success=True,
            output=mock_response,
            error="",
            action_type=action.type,
            action_id=action.step_id,
            duration_seconds=time.time() - start_time,
            timestamp=datetime.now(),
            payload={"prompt": prompt, "model": "mock_llm", "tokens_used": 150}
        )

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "agent_id": self.config.agent_id if self.config else "unknown",
            "is_running": self.is_running,
            "uptime_seconds": time.time() - self.start_time if hasattr(self, 'start_time') else 0,
            "active_instructions": len(self.active_instructions),
            "total_executions": len(self.execution_history),
            "recent_executions": [
                {
                    "id": r.instruction_block_id,
                    "success": r.overall_success,
                    "timestamp": r.timestamp.isoformat(),
                    "duration": r.total_duration_seconds
                }
                for r in self.execution_history[-5:]  # Last 5
            ],
            "execution_context": self.execution_context.dict() if self.execution_context else None,
            "timestamp": datetime.now().isoformat()
        }

    async def start(self):
        """Start the Agent Ex-Work daemon"""
        logger.info("🚀 Starting Agent Ex-Work v3.0...")

        self.load_config()
        self.is_running = True
        self.start_time = time.time()

        logger.info(f"✅ Agent Ex-Work started successfully")
        logger.info(f"🆔 Agent ID: {self.config.agent_id}")
        logger.info(f"🌐 Hive Address: {self.config.hive_address}")
        logger.info(f"🎧 Listen Port: {self.config.listen_port}")

        # Start the main agent loop
        await self.main_loop()

    async def main_loop(self):
        """Main agent execution loop"""
        logger.info("🔄 Agent Ex-Work main loop started")

        # Demonstration: Create and execute a self-diagnostic instruction block
        demo_instruction = InstructionBlock(
            step_id=f"demo_diagnostic_{int(time.time())}",
            description="Agent Ex-Work v3.0 self-diagnostic and capability demonstration",
            actions=[
                Action(
                    step_id="system_info",
                    type=ActionType.SYSTEM_INFO,
                    description="Gather system information",
                    params={"info_type": "comprehensive"}
                ),
                Action(
                    step_id="llm_test",
                    type=ActionType.CALL_LOCAL_LLM,
                    description="Test LLM integration",
                    params={"prompt": "Analyze system readiness for autonomous operations"}
                )
            ],
            transaction_id=f"demo_tx_{int(time.time())}",
            source_actor="self_diagnostic"
        )

        # Execute the demonstration
        result = await self.execute_instruction_block(demo_instruction)
        logger.info(f"🎯 Demo execution completed: {result.overall_success}")

        # Main loop - in a real implementation, this would listen for gRPC requests
        while self.is_running:
            # Status logging every 30 seconds
            status = self.get_status()
            logger.info(f"💓 Agent heartbeat: {status['active_instructions']} active, {status['total_executions']} total executions")

            await asyncio.sleep(30)

    async def stop(self):
        """Stop the Agent Ex-Work daemon"""
        logger.info("🛑 Stopping Agent Ex-Work...")
        self.is_running = False
        logger.info("✅ Agent Ex-Work stopped")


async def main():
    """Main entry point"""
    try:
        # Change to the agent directory
        agent_dir = Path(__file__).parent
        os.chdir(agent_dir)

        # Create and start the agent
        agent = AgentExWork()
        await agent.start()

    except KeyboardInterrupt:
        logger.info("🔴 Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        raise
    finally:
        logger.info("🏁 Agent Ex-Work shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
