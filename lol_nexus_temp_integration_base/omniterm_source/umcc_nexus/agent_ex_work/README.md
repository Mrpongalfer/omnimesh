# Agent Ex-Work v3.0 - The Genesis Agent

The primary autonomous execution engine of the UMCC system. Agent Ex-Work is designed to:

- Execute instruction blocks with full autonomy
- Interface with LLMs for planning and decision-making
- Handle complex multi-step workflows
- Provide self-healing and error recovery
- Maintain comprehensive audit trails

## Core Components

- **models/** - Pydantic data models for actions, results, and configurations
- **handlers/** - Pluggable action handlers for different task types
- **templates/** - Code generation templates for autonomous composition
- **config/** - Agent-specific configuration files

## Usage

```bash
# Install dependencies
poetry install

# Run the agent
poetry run python agent_ex_work.py

# Run tests
poetry run pytest tests/
```

## Configuration

Agent Ex-Work reads its configuration from:
1. `config/agent_config.toml` - Agent-specific settings
2. `../../config/config.toml` - Global UMCC configuration

## Action Handlers

Action handlers are modular components that execute specific types of actions:

- `RUN_SCRIPT` - Execute shell scripts and commands
- `CALL_LOCAL_LLM` - Interface with local LLM inference
- `FILE_OPERATION` - File system operations
- `NETWORK_SCAN` - Network reconnaissance
- `SYSTEM_INFO` - System information gathering
- `CRYPTO_OPERATION` - Cryptographic operations

## Autonomous Planning

The agent includes an autonomous planner that can:
- Decompose high-level goals into executable actions
- Select appropriate tools and methods
- Handle error recovery and retry logic
- Adapt strategies based on execution results
