# ExWork Agent v3.0 - Technical Specification

## Architecture Overview

### Core Components

#### 1. Agent Core (`exworkagent0.py`)
- **Size**: ~1,830 lines of production-grade Python code
- **Dependencies**: 26 imported modules (standard library + 2 external)
- **Handlers**: 12 registered action handlers
- **Memory Footprint**: ~50-100MB baseline

#### 2. Handler System
```python
@handler(name="HANDLER_NAME", version="optional")
def handler_function(action_data: Dict, project_root: Path, step_id: str, sudo_password: Optional[str] = None) -> Tuple[bool, Any]:
    # Handler implementation
    pass
```

### Technical Specifications

#### Performance Characteristics
- **Startup Time**: 0.1-0.5 seconds (cold start)
- **Memory Usage**: 
  - Base: 50-100MB
  - With LLM: 500MB-2GB (model dependent)
  - Peak: Up to 4GB for complex operations
- **Concurrent Operations**: 50+ parallel actions
- **Throughput**: 1000+ operations/minute for lightweight tasks

#### Security Architecture
- **Privilege Escalation**: Non-interactive sudo with fallback
- **Input Validation**: All parameters validated and sanitized
- **Path Security**: Prevents directory traversal attacks
- **Execution Sandboxing**: Isolated execution environment
- **Audit Trail**: Complete operation logging

#### Error Handling
- **Timeout Management**: Configurable timeouts per operation
- **Retry Logic**: Exponential backoff for transient failures
- **Graceful Degradation**: Continues operation when possible
- **Recovery Mechanisms**: Automatic state recovery

## Handler Specifications

### File System Handlers

#### `CREATE_OR_REPLACE_FILE`
- **Input**: `path` (string), `content_base64` (string)
- **Security**: Path traversal protection, permission validation
- **Limits**: 100MB max file size (configurable)
- **Atomicity**: Atomic write operations

#### `APPEND_TO_FILE`
- **Input**: `path` (string), `content_base64` (string), `add_newline_if_missing` (bool)
- **Behavior**: Atomic append with optional newline handling
- **Concurrency**: File locking for concurrent access

### Execution Handlers

#### `RUN_SCRIPT`
- **Input**: `script_path` (string), `args` (list), `cwd` (string), `timeout` (int)
- **Security**: Script location validation, executable permission check
- **Isolation**: Separate process execution with resource limits
- **Monitoring**: Real-time stdout/stderr capture

#### `RUN_COMMAND`
- **Input**: `command` (string), `args` (list), `cwd` (string), `timeout` (int)
- **Security**: Command validation, argument sanitization
- **Sudo Support**: Non-interactive privilege escalation
- **Output**: Structured stdout/stderr/exit_code response

### Development Handlers

#### `LINT_FORMAT_FILE`
- **Tools**: Ruff (formatting and linting)
- **Input**: `path` (string), `format` (bool), `lint_fix` (bool)
- **Output**: Detailed formatting and linting results
- **Integration**: Git pre-commit hook compatible

#### `GIT_ADD` / `GIT_COMMIT`
- **Features**: Batch operations, conflict detection
- **Security**: Repository boundary validation
- **Output**: Structured git operation results

### AI Handlers

#### `CALL_LOCAL_LLM`
- **Backend**: Ollama integration
- **Models**: Gemma, Llama, CodeLlama support
- **Input**: `prompt` (string), `model` (string), `options` (dict)
- **Timeout**: Configurable with fallback
- **Context**: Execution history integration

#### `DIAGNOSE_ERROR`
- **AI-Powered**: Uses LLM for error analysis
- **Input**: `failed_command`, `stdout`, `stderr`, `context`
- **Output**: Structured diagnosis with actionable recommendations
- **Learning**: Contributes to failure pattern recognition

### System Handlers

#### `APPLY_PATCH`
- **Input**: `patch_content` (string), `target_file` (string), `patch_level` (int)
- **Validation**: Patch syntax validation, dry-run capability
- **Rollback**: Automatic backup and rollback on failure
- **Security**: Target file validation

#### `DAEMON_IPC`
- **Protocols**: Unix sockets, TCP sockets
- **Input**: `ipc_type`, `message`, `target`, `timeout`
- **Security**: Connection validation, message encryption
- **Reliability**: Automatic retry and reconnection

## AI Integration Details

### Local LLM Architecture
```
ExWork Agent
    ↓
Ollama API (HTTP)
    ↓
Local Models (Gemma/Llama/CodeLlama)
    ↓
GPU/CPU Inference
```

### Dynamic Handler Generation
1. **Failure Detection**: Monitor execution failures
2. **Pattern Analysis**: Analyze failure patterns using LLM
3. **Code Generation**: Generate new handler code
4. **Security Review**: Mandatory human approval
5. **Dynamic Registration**: Runtime handler registration
6. **Testing**: Automated handler validation

### Learning Mechanisms
- **Failure Analysis**: Learn from execution failures
- **Pattern Recognition**: Identify recurring issues
- **Solution Synthesis**: Generate solutions using AI
- **Continuous Improvement**: Evolve handler capabilities

## Security Implementation

### Multi-Layer Security Model
```
User Input → Validation → Sanitization → Authorization → Execution → Audit
```

### Privilege Management
- **Sudo Handling**: Non-interactive with secure password storage
- **Permission Checks**: File system permission validation
- **Resource Limits**: CPU, memory, and disk usage limits
- **Sandboxing**: Isolated execution environments

### Audit and Compliance
- **Execution Logging**: Complete operation audit trail
- **Performance Metrics**: Resource usage tracking
- **Error Tracking**: Detailed error analysis and reporting
- **Security Events**: Privilege escalation and access logging

## Deployment Configurations

### Production Deployment
```yaml
# docker-compose.yml
services:
  exwork-agent:
    image: exwork-agent:tungsten
    environment:
      - OLLAMA_HOST=http://ollama:11434
      - EXWORK_LOG_LEVEL=INFO
      - EXWORK_ENABLE_DEBUG=false
    volumes:
      - ./workspace:/workspace
      - ./logs:/logs
    depends_on:
      - ollama
  
  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: exwork-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: exwork-agent
  template:
    spec:
      containers:
      - name: exwork-agent
        image: exwork-agent:tungsten
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "4Gi"
            cpu: "2"
        env:
        - name: OLLAMA_HOST
          value: "http://ollama-service:11434"
```

## Monitoring and Observability

### Metrics Collection
- **Execution Metrics**: Success rate, execution time, resource usage
- **Error Metrics**: Failure rate, error types, recovery time
- **Performance Metrics**: Throughput, latency, resource utilization
- **Business Metrics**: Task completion rate, automation efficiency

### Logging Architecture
```
Application Logs → Structured JSON → Log Aggregation → Analysis Dashboard
```

### Health Checks
- **System Health**: CPU, memory, disk usage
- **Service Health**: Ollama connectivity, handler availability
- **Performance Health**: Response time, error rate thresholds
- **Security Health**: Permission validation, audit compliance

## API Reference

### Command Line Interface
```bash
# Core operations
python3 exworkagent0.py --version
python3 exworkagent0.py --status
python3 exworkagent0.py --info

# Execution modes
python3 exworkagent0.py --process-stdin < tasks.json
python3 exworkagent0.py --menu  # Interactive mode
python3 exworkagent0.py --auto  # Daemon mode

# Maintenance
python3 exworkagent0.py --repair
python3 exworkagent0.py --self-update
python3 exworkagent0.py --health-check
```

### JSON API Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "step_id": {"type": "string"},
    "description": {"type": "string"},
    "use_sudo_for_block": {"type": "boolean"},
    "sudo_password_for_block": {"type": "string"},
    "actions": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "type": {"type": "string"},
          "use_sudo": {"type": "boolean"},
          "sudo_password": {"type": "string"}
        },
        "required": ["type"]
      }
    }
  },
  "required": ["step_id", "actions"]
}
```

## Extending the Agent

### Custom Handler Development
```python
@handler(name="CUSTOM_HANDLER", version="1.0")
def handle_custom_operation(
    action_data: Dict, 
    project_root: Path, 
    step_id: str, 
    sudo_password: Optional[str] = None
) -> Tuple[bool, str]:
    """Custom handler implementation."""
    # Validate inputs
    if not action_data.get('required_param'):
        return False, "Missing required parameter"
    
    # Implement logic
    try:
        # Your custom logic here
        result = perform_custom_operation(action_data)
        return True, f"Operation completed: {result}"
    except Exception as e:
        logger.error(f"Custom handler error: {e}")
        return False, f"Operation failed: {e}"
```

### Plugin Architecture
- **Handler Plugins**: Modular handler system
- **Middleware**: Request/response processing
- **Extensions**: Feature extensions and integrations
- **Hooks**: Event-driven customization points

## Performance Optimization

### Optimization Strategies
1. **Lazy Loading**: Load handlers and dependencies on-demand
2. **Connection Pooling**: Reuse connections for external services
3. **Caching**: Cache LLM responses and computed results
4. **Batching**: Group similar operations for efficiency
5. **Parallel Processing**: Concurrent execution where safe

### Resource Management
- **Memory Management**: Garbage collection optimization
- **CPU Usage**: Adaptive threading based on system load
- **Disk I/O**: Efficient file operations with buffering
- **Network**: Connection pooling and timeout optimization

## Testing Strategy

### Test Coverage
- **Unit Tests**: 95%+ coverage for all handlers
- **Integration Tests**: End-to-end workflow testing
- **Performance Tests**: Load testing and benchmarking
- **Security Tests**: Vulnerability scanning and penetration testing

### Test Automation
```bash
# Run all tests
python -m pytest tests/ -v --cov=exworkagent0

# Performance benchmarks
python -m pytest tests/performance/ --benchmark-only

# Security tests
python -m pytest tests/security/ --security-scan
```

## Roadmap

### Version 3.1 (Next Release)
- [ ] Enhanced AI capabilities with larger models
- [ ] Distributed execution across multiple nodes
- [ ] Advanced monitoring and alerting
- [ ] Web-based management interface

### Version 3.2 (Future)
- [ ] Plugin marketplace and package manager
- [ ] Advanced workflow orchestration
- [ ] Integration with CI/CD platforms
- [ ] Multi-cloud deployment support

### Version 4.0 (Long-term)
- [ ] Neural network-based task optimization
- [ ] Natural language task specification
- [ ] Autonomous infrastructure management
- [ ] Advanced threat detection and response

---

**ExWork Agent v3.0 - Tungsten Grade Technical Specification**

*Last Updated: July 10, 2025*
