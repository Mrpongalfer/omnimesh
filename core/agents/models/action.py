"""
Pydantic data models for Agent Ex-Work v3.0
Aligns with the protobuf definitions in shared/umcc.proto
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """Enumeration of supported action types"""
    RUN_SCRIPT = "RUN_SCRIPT"
    CALL_LOCAL_LLM = "CALL_LOCAL_LLM"
    FILE_OPERATION = "FILE_OPERATION"
    NETWORK_SCAN = "NETWORK_SCAN"
    SYSTEM_INFO = "SYSTEM_INFO"
    CRYPTO_OPERATION = "CRYPTO_OPERATION"
    DATABASE_QUERY = "DATABASE_QUERY"
    HTTP_REQUEST = "HTTP_REQUEST"
    DOCKER_OPERATION = "DOCKER_OPERATION"
    GIT_OPERATION = "GIT_OPERATION"
    # LLM Handler actions
    DIAGNOSE_ERROR = "DIAGNOSE_ERROR"
    AUTONOMOUS_PLANNER = "AUTONOMOUS_PLANNER"
    GENERATE_CODE = "GENERATE_CODE"
    # API Handler actions
    CALL_EXTERNAL_API = "CALL_EXTERNAL_API"
    FETCH_DATA = "FETCH_DATA"
    # Container/deployment actions
    DEPLOY_CONTAINER = "DEPLOY_CONTAINER"


class Action(BaseModel):
    """Represents a single executable action within an instruction block"""
    step_id: str = Field(..., description="Unique identifier for this action step")
    type: ActionType = Field(..., description="Type of action to execute")
    description: str = Field(..., description="Human-readable description of the action")
    params: Dict[str, Any] = Field(default_factory=dict, description="Action-specific parameters")
    timeout_seconds: int = Field(default=300, description="Timeout for action execution")
    autonomous_signoff_bypass: bool = Field(default=False, description="Skip human approval for low-risk actions")
    target_node_yggdrasil_ip: Optional[str] = Field(None, description="Target node for remote execution")
    remote_cwd: Optional[str] = Field(None, description="Working directory on remote target")
    credential_id: Optional[str] = Field(None, description="Credentials ID for authentication")


class InstructionBlock(BaseModel):
    """A sequence of actions for Agent Ex-Work to execute"""
    step_id: str = Field(..., description="Unique identifier for this instruction block")
    description: str = Field(..., description="Human-readable description of the block")
    actions: List[Action] = Field(default_factory=list, description="List of actions to execute")
    is_high_level_goal: bool = Field(default=False, description="Whether this requires autonomous planning")
    goal: Optional[str] = Field(None, description="High-level natural language goal")
    transaction_id: str = Field(..., description="Transaction ID for DATCS")
    source_actor: str = Field(..., description="Source of the instruction block")
    core_directive_id: Optional[str] = Field(None, description="Associated core directive ID")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ActionResult(BaseModel):
    """Represents the result of a single executed action"""
    success: bool = Field(..., description="Whether the action succeeded")
    output: str = Field(default="", description="Action output/stdout")
    error: str = Field(default="", description="Error message if action failed")
    action_type: ActionType = Field(..., description="Type of action that was executed")
    action_id: str = Field(..., description="ID of the action that was executed")
    duration_seconds: float = Field(..., description="Time taken to execute the action")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the action completed")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Additional result data")


class OverallResult(BaseModel):
    """Represents the overall result of executing an entire InstructionBlock"""
    overall_success: bool = Field(..., description="Whether all actions succeeded")
    status_message: str = Field(..., description="Summary status message")
    total_duration_seconds: float = Field(..., description="Total execution time")
    action_results: List[ActionResult] = Field(default_factory=list, description="Results from individual actions")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the block completed")
    instruction_block_id: str = Field(..., description="ID of the executed instruction block")
    transaction_id: str = Field(..., description="Transaction ID from the instruction block")
    source_actor: str = Field(..., description="Actor that initiated the instruction block")


class AgentConfig(BaseModel):
    """Configuration model for Agent Ex-Work"""
    agent_id: str = Field(..., description="Unique identifier for this agent instance")
    hive_address: str = Field(default="localhost:50051", description="Primary Hive gRPC address")
    listen_port: int = Field(default=50053, description="Port for agent's gRPC server")
    log_level: str = Field(default="INFO", description="Logging level")
    max_concurrent_actions: int = Field(default=5, description="Maximum concurrent action executions")
    default_timeout_seconds: int = Field(default=300, description="Default action timeout")
    enable_autonomous_planning: bool = Field(default=True, description="Enable autonomous goal decomposition")
    ollama_host: str = Field(default="http://localhost:11434", description="Ollama LLM server address")
    template_cache_size: int = Field(default=100, description="Number of templates to cache in memory")

    class Config:
        env_prefix = "AGENT_EX_WORK_"


class TemplateInfo(BaseModel):
    """Information about a code template"""
    file: str = Field(..., description="Path to template file")
    description: str = Field(..., description="Template description")
    keywords: List[str] = Field(default_factory=list, description="Search keywords")
    language: str = Field(..., description="Programming language")
    parameters: List[str] = Field(default_factory=list, description="Required parameters")


class TemplateIndex(BaseModel):
    """Index of available code templates"""
    version: str = Field(..., description="Template index version")
    last_updated: datetime = Field(..., description="Last update timestamp")
    description: str = Field(..., description="Index description")
    templates: Dict[str, Dict[str, TemplateInfo]] = Field(..., description="Categorized templates")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Index metadata")


class ExecutionContext(BaseModel):
    """Context information for action execution"""
    working_directory: str = Field(..., description="Current working directory")
    environment_variables: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    user_id: str = Field(..., description="User executing the action")
    node_id: str = Field(..., description="Node where action is executing")
    transaction_id: str = Field(..., description="Current transaction ID")
    debug_mode: bool = Field(default=False, description="Whether debug mode is enabled")


class SystemMetrics(BaseModel):
    """System performance and health metrics"""
    cpu_usage_percent: float = Field(..., description="CPU usage percentage")
    memory_usage_percent: float = Field(..., description="Memory usage percentage")
    disk_usage_percent: float = Field(..., description="Disk usage percentage")
    network_io_bytes: Dict[str, int] = Field(default_factory=dict, description="Network I/O statistics")
    active_processes: int = Field(..., description="Number of active processes")
    load_average: List[float] = Field(default_factory=list, description="System load averages")
    timestamp: datetime = Field(default_factory=datetime.now, description="Metrics timestamp")


class NetworkScanResult(BaseModel):
    """Result of a network scan operation"""
    target: str = Field(..., description="Scan target (IP, hostname, range)")
    scan_type: str = Field(..., description="Type of scan performed")
    open_ports: List[int] = Field(default_factory=list, description="List of open ports found")
    services: Dict[int, str] = Field(default_factory=dict, description="Detected services by port")
    os_fingerprint: Optional[str] = Field(None, description="Detected operating system")
    scan_duration_seconds: float = Field(..., description="Time taken for scan")
    timestamp: datetime = Field(default_factory=datetime.now, description="Scan timestamp")


class CryptoOperation(BaseModel):
    """Cryptographic operation request/result"""
    operation: str = Field(..., description="Type of crypto operation")
    algorithm: str = Field(..., description="Cryptographic algorithm used")
    key_size: Optional[int] = Field(None, description="Key size in bits")
    input_data: Optional[str] = Field(None, description="Input data (base64 encoded)")
    output_data: Optional[str] = Field(None, description="Output data (base64 encoded)")
    success: bool = Field(default=False, description="Whether operation succeeded")
    error_message: Optional[str] = Field(None, description="Error message if failed")
