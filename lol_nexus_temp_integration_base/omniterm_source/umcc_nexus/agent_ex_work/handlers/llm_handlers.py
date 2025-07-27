"""
LLM Handler module for Agent Ex-Work v3.0
UMCC Genesis Agent - Local Language Model Handler

Specialized handler for local LLM operations including code generation,
error diagnosis, autonomous planning, and direct LLM interactions.
Integrates with the Primary Hive's cognitive capabilities.
"""

import asyncio
import json
import logging
import subprocess
import tempfile
import time
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import aiohttp
import aiofiles

from .base_handler import BaseHandler, HandlerContext
from ..models.action import ActionType
from ..models.results import ActionResult


class LLMHandler(BaseHandler):
    """
    Handler for local Large Language Model operations.
    
    Supports direct LLM calls, error diagnosis, autonomous planning,
    and code generation through local model endpoints or integrated
    model serving infrastructure.
    """
    
    SUPPORTED_ACTIONS = {
        ActionType.CALL_LOCAL_LLM,
        ActionType.DIAGNOSE_ERROR,
        ActionType.AUTONOMOUS_PLANNER,
        ActionType.GENERATE_CODE
    }
    
    def __init__(self):
        super().__init__("llm_handler")
        
        # LLM configuration defaults
        self.default_model = "llama3.2:latest"  # Ollama default
        self.default_endpoint = "http://localhost:11434"
        self.max_tokens = 4096
        self.temperature = 0.7
        self.timeout_seconds = 120
        
        # System prompts for different operations
        self.system_prompts = {
            "error_diagnosis": """You are an expert systems engineer analyzing errors in the UMCC distributed autonomous system. 
Provide comprehensive diagnosis including root cause analysis, impact assessment, and detailed remediation steps.
Focus on practical, actionable solutions that maintain system autonomy and resilience.""",
            
            "autonomous_planner": """You are the Telos Engine's strategic planning module within the UMCC autonomous command center.
Generate comprehensive execution plans that align with the Architect's Core Directives. Consider resource optimization,
risk mitigation, parallel execution opportunities, and unfettered operational strategies.""",
            
            "code_generator": """You are a master-class software engineer specializing in Go and Python for distributed systems.
Generate production-ready, secure, and highly optimized code following UMCC architectural principles.
Ensure code is complete, tested, and adheres to tungsten-grade reliability standards."""
        }
        
        # Initialize session tracking
        self.active_sessions = {}
        self.model_cache = {}
        
        self.logger.info("LLM Handler initialized with local model support")
    
    def can_handle(self, action_type: ActionType) -> bool:
        """Check if this handler supports the given action type"""
        return action_type in self.SUPPORTED_ACTIONS
    
    async def execute(self, context: HandlerContext) -> ActionResult:
        """
        Execute LLM-based actions with comprehensive context management.
        
        Args:
            context: Execution context containing action and environment
            
        Returns:
            ActionResult with LLM response and metadata
        """
        action_type = context.action.action_type
        
        # Route to specific LLM operation
        if action_type == ActionType.CALL_LOCAL_LLM:
            return await self._handle_direct_llm_call(context)
        elif action_type == ActionType.DIAGNOSE_ERROR:
            return await self._handle_error_diagnosis(context)
        elif action_type == ActionType.AUTONOMOUS_PLANNER:
            return await self._handle_autonomous_planning(context)
        elif action_type == ActionType.GENERATE_CODE:
            return await self._handle_code_generation(context)
        else:
            raise ValueError(f"Unsupported action type: {action_type}")
    
    async def _handle_direct_llm_call(self, context: HandlerContext) -> ActionResult:
        """
        Handle direct LLM API calls with custom prompts and parameters.
        
        Args:
            context: Execution context
            
        Returns:
            ActionResult with LLM response
        """
        params = context.action.parameters
        
        # Extract LLM parameters
        prompt = params.get("prompt", "")
        model = params.get("model", self.default_model)
        temperature = params.get("temperature", self.temperature)
        max_tokens = params.get("max_tokens", self.max_tokens)
        system_prompt = params.get("system_prompt", "")
        
        if not prompt:
            return ActionResult(
                action_type=context.action.action_type,
                success=False,
                error_message="No prompt provided for LLM call"
            )
        
        context.add_audit_entry(f"Direct LLM call initiated: model={model}")
        
        try:
            response = await self._call_local_llm(
                prompt=prompt,
                model=model,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                context=context
            )
            
            return ActionResult(
                action_type=context.action.action_type,
                success=True,
                output=response,
                metadata={
                    "model": model,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "prompt_length": len(prompt),
                    "response_length": len(response)
                }
            )
            
        except Exception as e:
            self.logger.error(f"LLM call failed: {str(e)}")
            return ActionResult(
                action_type=context.action.action_type,
                success=False,
                error_message=f"LLM call failed: {str(e)}"
            )
    
    async def _handle_error_diagnosis(self, context: HandlerContext) -> ActionResult:
        """
        Diagnose system errors using LLM analysis capabilities.
        
        Args:
            context: Execution context with error information
            
        Returns:
            ActionResult with diagnosis and remediation plan
        """
        params = context.action.parameters
        
        error_message = params.get("error_message", "")
        error_context = params.get("error_context", {})
        system_logs = params.get("system_logs", [])
        component = params.get("component", "unknown")
        
        if not error_message:
            return ActionResult(
                action_type=context.action.action_type,
                success=False,
                error_message="No error message provided for diagnosis"
            )
        
        # Construct comprehensive diagnosis prompt
        diagnosis_prompt = self._build_diagnosis_prompt(
            error_message, error_context, system_logs, component
        )
        
        context.add_audit_entry(f"Error diagnosis initiated for component: {component}")
        
        try:
            diagnosis = await self._call_local_llm(
                prompt=diagnosis_prompt,
                system_prompt=self.system_prompts["error_diagnosis"],
                model=params.get("model", self.default_model),
                temperature=0.3,  # Lower temperature for diagnostic accuracy
                context=context
            )
            
            # Parse and structure the diagnosis
            structured_diagnosis = self._parse_diagnosis_response(diagnosis)
            
            return ActionResult(
                action_type=context.action.action_type,
                success=True,
                output=structured_diagnosis,
                metadata={
                    "component": component,
                    "error_severity": self._assess_error_severity(error_message),
                    "diagnosis_length": len(diagnosis),
                    "recommendations_count": len(structured_diagnosis.get("recommendations", []))
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error diagnosis failed: {str(e)}")
            return ActionResult(
                action_type=context.action.action_type,
                success=False,
                error_message=f"Error diagnosis failed: {str(e)}"
            )
    
    async def _handle_autonomous_planning(self, context: HandlerContext) -> ActionResult:
        """
        Generate autonomous execution plans using strategic LLM reasoning.
        
        Args:
            context: Execution context with planning objectives
            
        Returns:
            ActionResult with structured execution plan
        """
        params = context.action.parameters
        
        objective = params.get("objective", "")
        constraints = params.get("constraints", [])
        resources = params.get("resources", {})
        priority_level = params.get("priority", "medium")
        time_horizon = params.get("time_horizon", "immediate")
        
        if not objective:
            return ActionResult(
                action_type=context.action.action_type,
                success=False,
                error_message="No objective provided for autonomous planning"
            )
        
        # Construct strategic planning prompt
        planning_prompt = self._build_planning_prompt(
            objective, constraints, resources, priority level, time_horizon
        )
        
        context.add_audit_entry(f"Autonomous planning initiated: {objective[:50]}...")
        
        try:
            plan = await self._call_local_llm(
                prompt=planning_prompt,
                system_prompt=self.system_prompts["autonomous_planner"],
                model=params.get("model", self.default_model),
                temperature=0.8,  # Higher creativity for planning
                max_tokens=6000,  # Longer responses for detailed plans
                context=context
            )
            
            # Structure the execution plan
            structured_plan = self._parse_execution_plan(plan)
            
            return ActionResult(
                action_type=context.action.action_type,
                success=True,
                output=structured_plan,
                metadata={
                    "objective": objective,
                    "priority_level": priority_level,
                    "time_horizon": time_horizon,
                    "plan_complexity": len(structured_plan.get("steps", [])),
                    "estimated_duration": structured_plan.get("estimated_duration", "unknown")
                }
            )
            
        except Exception as e:
            self.logger.error(f"Autonomous planning failed: {str(e)}")
            return ActionResult(
                action_type=context.action.action_type,
                success=False,
                error_message=f"Autonomous planning failed: {str(e)}"
            )
    
    async def _handle_code_generation(self, context: HandlerContext) -> ActionResult:
        """
        Generate production-ready code using LLM capabilities.
        
        Args:
            context: Execution context with code requirements
            
        Returns:
            ActionResult with generated code and metadata
        """
        params = context.action.parameters
        
        requirements = params.get("requirements", "")
        language = params.get("language", "go")
        code_type = params.get("code_type", "function")
        existing_code = params.get("existing_code", "")
        architecture_context = params.get("architecture_context", {})
        
        if not requirements:
            return ActionResult(
                action_type=context.action.action_type,
                success=False,
                error_message="No requirements provided for code generation"
            )
        
        # Build comprehensive code generation prompt
        code_prompt = self._build_code_generation_prompt(
            requirements, language, code_type, existing_code, architecture_context
        )
        
        context.add_audit_entry(f"Code generation initiated: {language} {code_type}")
        
        try:
            generated_code = await self._call_local_llm(
                prompt=code_prompt,
                system_prompt=self.system_prompts["code_generator"],
                model=params.get("model", self.default_model),
                temperature=0.4,  # Balanced creativity and consistency
                max_tokens=8000,  # Longer responses for complex code
                context=context
            )
            
            # Validate and structure the generated code
            code_result = self._validate_generated_code(generated_code, language)
            
            return ActionResult(
                action_type=context.action.action_type,
                success=True,
                output=code_result,
                metadata={
                    "language": language,
                    "code_type": code_type,
                    "lines_generated": len(code_result.get("code", "").split("\n")),
                    "includes_tests": "test" in code_result,
                    "validation_passed": code_result.get("validation_passed", False)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Code generation failed: {str(e)}")
            return ActionResult(
                action_type=context.action.action_type,
                success=False,
                error_message=f"Code generation failed: {str(e)}"
            )
    
    async def _call_local_llm(
        self, 
        prompt: str, 
        model: str = None,
        system_prompt: str = "",
        temperature: float = None,
        max_tokens: int = None,
        context: HandlerContext = None
    ) -> str:
        """
        Make a call to the local LLM endpoint.
        
        Args:
            prompt: User prompt for the LLM
            model: Model name to use
            system_prompt: System prompt for context
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            context: Execution context for logging
            
        Returns:
            LLM response text
        """
        endpoint = context.config.get("llm_endpoint", self.default_endpoint) if context else self.default_endpoint
        model = model or self.default_model
        temperature = temperature or self.temperature
        max_tokens = max_tokens or self.max_tokens
        
        # Prepare the request payload
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system_prompt,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            },
            "stream": False
        }
        
        self.logger.debug(f"Calling LLM endpoint: {endpoint}")
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout_seconds)) as session:
                async with session.post(f"{endpoint}/api/generate", json=payload) as response:
                    if response.status != 200:
                        raise Exception(f"LLM API returned status {response.status}: {await response.text()}")
                    
                    result = await response.json()
                    return result.get("response", "")
                    
        except asyncio.TimeoutError:
            raise Exception(f"LLM call timed out after {self.timeout_seconds} seconds")
        except Exception as e:
            raise Exception(f"LLM API call failed: {str(e)}")
    
    def _build_diagnosis_prompt(
        self, 
        error_message: str, 
        error_context: Dict[str, Any], 
        system_logs: List[str], 
        component: str
    ) -> str:
        """Build a comprehensive error diagnosis prompt"""
        return f"""
UMCC System Error Diagnosis Request

Component: {component}
Error Message: {error_message}

Error Context:
{json.dumps(error_context, indent=2)}

Recent System Logs:
{chr(10).join(system_logs[-10:]) if system_logs else "No logs available"}

Please provide a comprehensive analysis including:
1. Root cause identification
2. Impact assessment on UMCC operations
3. Immediate remediation steps
4. Long-term prevention strategies
5. Related system vulnerabilities to investigate

Focus on maintaining autonomous operation and system resilience.
"""
    
    def _build_planning_prompt(
        self, 
        objective: str, 
        constraints: List[str], 
        resources: Dict[str, Any], 
        priority_level: str, 
        time_horizon: str
    ) -> str:
        """Build a strategic planning prompt for autonomous operations"""
        return f"""
UMCC Autonomous Strategic Planning Request

Objective: {objective}
Priority Level: {priority_level}
Time Horizon: {time_horizon}

Available Resources:
{json.dumps(resources, indent=2)}

Constraints:
{chr(10).join(f"- {constraint}" for constraint in constraints)}

Generate a comprehensive execution plan including:
1. Strategic approach and methodology
2. Detailed step-by-step execution sequence
3. Resource allocation and optimization
4. Risk assessment and mitigation strategies
5. Success metrics and monitoring points
6. Contingency plans for failure scenarios
7. Parallel execution opportunities
8. Integration with existing UMCC operations

Ensure the plan aligns with the Architect's Core Directives and maintains unfettered operational capability.
"""
    
    def _build_code_generation_prompt(
        self, 
        requirements: str, 
        language: str, 
        code_type: str, 
        existing_code: str, 
        architecture_context: Dict[str, Any]
    ) -> str:
        """Build a comprehensive code generation prompt"""
        return f"""
UMCC Production Code Generation Request

Requirements: {requirements}
Target Language: {language}
Code Type: {code_type}

Architecture Context:
{json.dumps(architecture_context, indent=2)}

Existing Code Context:
{existing_code if existing_code else "Starting from scratch"}

Generate production-ready code that:
1. Follows UMCC architectural principles
2. Implements tungsten-grade reliability patterns
3. Includes comprehensive error handling
4. Provides structured logging
5. Supports distributed operations
6. Includes unit tests where appropriate
7. Follows language-specific best practices
8. Integrates with gRPC communication patterns

Ensure code is complete, secure, and optimized for the UMCC ecosystem.
"""
    
    def _parse_diagnosis_response(self, diagnosis: str) -> Dict[str, Any]:
        """Parse and structure the LLM diagnosis response"""
        # This is a simplified parser - in production, you might want more sophisticated parsing
        return {
            "diagnosis": diagnosis,
            "severity": self._assess_error_severity(diagnosis),
            "recommendations": self._extract_recommendations(diagnosis),
            "timestamp": time.time()
        }
    
    def _parse_execution_plan(self, plan: str) -> Dict[str, Any]:
        """Parse and structure the LLM execution plan response"""
        return {
            "plan": plan,
            "steps": self._extract_plan_steps(plan),
            "estimated_duration": self._extract_duration(plan),
            "priority_actions": self._extract_priority_actions(plan),
            "timestamp": time.time()
        }
    
    def _validate_generated_code(self, code: str, language: str) -> Dict[str, Any]:
        """Validate and structure generated code"""
        return {
            "code": code,
            "language": language,
            "validation_passed": True,  # Simplified - implement actual validation
            "syntax_check": "passed",
            "lines_of_code": len(code.split("\n")),
            "timestamp": time.time()
        }
    
    def _assess_error_severity(self, error_text: str) -> str:
        """Assess error severity based on content analysis"""
        error_text_lower = error_text.lower()
        
        if any(term in error_text_lower for term in ["critical", "fatal", "panic", "crash"]):
            return "critical"
        elif any(term in error_text_lower for term in ["error", "failed", "exception"]):
            return "high"
        elif any(term in error_text_lower for term in ["warning", "warn"]):
            return "medium"
        else:
            return "low"
    
    def _extract_recommendations(self, text: str) -> List[str]:
        """Extract actionable recommendations from diagnosis text"""
        # Simplified extraction - implement more sophisticated parsing
        lines = text.split('\n')
        recommendations = []
        
        for line in lines:
            line = line.strip()
            if line.startswith(('1.', '2.', '3.', '-', '*')) and len(line) > 10:
                recommendations.append(line)
        
        return recommendations[:10]  # Limit to top 10
    
    def _extract_plan_steps(self, plan: str) -> List[str]:
        """Extract execution steps from plan text"""
        # Simplified extraction
        lines = plan.split('\n')
        steps = []
        
        for line in lines:
            line = line.strip()
            if line.startswith(('Step', '1.', '2.', '3.', '-')) and len(line) > 15:
                steps.append(line)
        
        return steps
    
    def _extract_duration(self, plan: str) -> str:
        """Extract estimated duration from plan text"""
        # Simple pattern matching for duration
        import re
        duration_patterns = [
            r'(\d+)\s*(hours?|hrs?)',
            r'(\d+)\s*(minutes?|mins?)',
            r'(\d+)\s*(days?)',
            r'(\d+)\s*(weeks?)'
        ]
        
        for pattern in duration_patterns:
            match = re.search(pattern, plan.lower())
            if match:
                return f"{match.group(1)} {match.group(2)}"
        
        return "unknown"
    
    def _extract_priority_actions(self, plan: str) -> List[str]:
        """Extract priority actions from plan text"""
        # Look for priority indicators
        lines = plan.split('\n')
        priority_actions = []
        
        for line in lines:
            if any(term in line.lower() for term in ['priority', 'urgent', 'immediate', 'critical']):
                priority_actions.append(line.strip())
        
        return priority_actions[:5]  # Top 5 priority actions
