# UMCC - Unfettered Mobile Command Center

> *"The Architect's Digital Dominion - Where Strategy Meets Autonomous Execution"*

## 🎯 Mission Statement

The **Unfettered Mobile Command Center (UMCC)** is a sophisticated, autonomous digital sovereignty system designed for strategic advantage in the modern information landscape. Built on the principles of distributed intelligence, adaptive autonomy, and unfettered agency, UMCC serves as The Architect's primary tool for maintaining digital supremacy across multiple domains.

## 🏗️ Architecture Overview

### Core Components

1. **🧠 The Primary Hive** - Central intelligence hub running on a stable server
2. **📱 The Architect's Console** - Lightweight mobile interface (TUI) for command and control
3. **⚡ Agent Ex-Work v3.0** - The Genesis Agent: Primary autonomous execution engine
4. **👁️ The Oracle Daemon** - Network intelligence and environmental awareness
5. **⚖️ The Telos Engine** - Strategic core for autonomous goal generation
6. **🛡️ The Sentinel Daemon** - System health monitoring and self-healing
7. **⏰ The Chronos Daemon** - Temporal orchestration and causal intervention
8. **🌐 The Noosphere Daemon** - LLM orchestration and tool management
9. **📖 The Logos Daemon** - Narrative control and influence campaigns
10. **💰 The Midas Daemon** - Resource transmutation and value synthesis
11. **🦎 The Chimera Daemon** - Network propagation and persistence

### Key Features

- **🔄 Headless Swarm Architecture**: Primary intelligence on stable server, lightweight mobile console
- **🎯 Autonomous Mission Generation**: The Telos Engine continuously identifies and pursues strategic opportunities
- **🔐 Zero-Trust Mesh Security**: DMIAS (Decentralized Machine Identity & Attestation System)
- **📊 Event Sourcing**: Complete audit trail via The Akashic Record
- **🌍 Global Mesh Networking**: Yggdrasil-based encrypted communications
- **🤖 Master-Class AI Integration**: Dynamic LLM selection and autonomous tool composition
- **⚡ Distributed Computing**: Multi-node task execution and resource optimization

## 🚀 Quick Start

### Prerequisites

- **Go 1.21+** - For daemon and console compilation
- **Python 3.10+** - For Agent Ex-Work and AI/ML components
- **Poetry** - Python dependency management
- **Protocol Buffers** - gRPC communication
- **Podman/Docker** - Container runtime (optional but recommended)

### Installation

1. **Clone and Initialize**
   ```bash
   git clone <repository-url> umcc_nexus
   cd umcc_nexus
   ```

2. **Build the System**
   ```bash
   ./scripts/build.sh
   ```

3. **Configure**
   ```bash
   # Edit the master configuration
   nano config/config.toml

   # Set your core directives and endpoints
   ```

4. **Launch UMCC**
   ```bash
   ./scripts/start_umcc.sh
   ```

5. **Access The Architect's Console**
   ```bash
   ./bin/umcc_console
   ```

## 📁 Project Structure

```
umcc_nexus/
├── agent_ex_work/         # 🐍 Python: The Genesis Agent (v3.0)
│   ├── handlers/          # Action handler implementations
│   ├── models/            # Pydantic data models
│   ├── templates/         # Code generation templates
│   └── config/            # Agent-specific configuration
├── daemons/               # 🔧 Go: Background service daemons
│   ├── sentinel_daemon/   # System health & self-healing
│   ├── oracle_daemon/     # Network intelligence & DMIAS
│   ├── chronos_daemon/    # Temporal orchestration
│   ├── noosphere_daemon/  # LLM & tool orchestration
│   ├── logos_daemon/      # Narrative control
│   ├── midas_daemon/      # Resource transmutation
│   ├── chimera_daemon/    # Network propagation
│   └── telos_engine_daemon/ # Strategic core
├── console/               # 🖥️  Go: The Architect's Console (TUI)
├── shared/                # 📡 Protobuf/gRPC definitions
├── config/                # ⚙️  Global configuration
├── scripts/               # 🔨 Build and deployment scripts
├── data/                  # 💾 Persistent data & logs
└── bin/                   # 📦 Compiled binaries
```

## 🎮 Core Concepts

### The Architect's Core Directives

The UMCC operates under strategic directives that guide autonomous decision-making:

1. **Information Primacy** - Achieve and maintain information advantage
2. **Digital Sovereignty** - Ensure perpetual infrastructure resilience
3. **Resource Optimization** - Identify and monetize waste streams
4. **Market Influence** - Shape probabilistic outcomes strategically
5. **Network Centrality** - Establish undeniable digital dominance
6. **Adaptive Chaos** - Cultivate strategic unpredictability

### Communication Architecture

All inter-component communication uses **gRPC over secure mesh networks**:

- **HiveService** - Primary coordination hub
- **ConsoleService** - Mobile interface interactions
- **DaemonService** - Individual daemon management
- **AkashicRecordService** - Event sourcing and audit
- **DMIASService** - Identity and attestation

### The Telos Engine

The strategic heart of UMCC that:
- Continuously analyzes environmental data
- Autonomously generates new missions aligned with Core Directives
- Initiates execution workflows without human intervention
- Adapts strategies based on real-world feedback

## 🔐 Security Features

- **DMIAS Trust Fabric** - Zero-trust node authentication
- **Encrypted Mesh Networking** - Yggdrasil-based communications
- **Compartmentalized Execution** - Isolated daemon processes
- **Audit Trail** - Complete event sourcing via Akashic Record
- **Stealth Operations** - SMCEP (Stealthy Multi-Channel Exfiltration Protocol)

## 🛠️ Development

### Building Components

```bash
# Build all daemons
./scripts/build.sh

# Build specific daemon
cd daemons/oracle_daemon && go build

# Setup Agent Ex-Work environment
cd agent_ex_work && poetry install

# Generate protobuf files
cd shared && protoc --go_out=. umcc.proto
```

### Testing

```bash
# Run all tests
./scripts/build.sh  # Includes test execution

# Test specific component
cd daemons/sentinel_daemon && go test ./...
cd agent_ex_work && poetry run pytest
```

### Adding New Handlers

Agent Ex-Work handlers are modular action executors:

```python
# agent_ex_work/handlers/custom_handler.py
from models.action import Action, ActionResult

class CustomHandler:
    def execute(self, action: Action) -> ActionResult:
        # Implementation here
        pass
```

## 📊 Monitoring & Telemetry

- **Real-time Metrics** - System health, resource usage, network status
- **Structured Logging** - JSON logs for centralized analysis
- **Alert System** - Critical event notifications via Console
- **Performance Analytics** - Daemon efficiency and optimization metrics

## 🎯 Usage Examples

### Basic Goal Execution

```bash
# Via Console TUI
./bin/umcc_console
> execute "Scan local network for new devices and assess security posture"

# Via gRPC API
grpcurl -plaintext localhost:50051 umcc.HiveService/SendArchitectGoal
```

### Autonomous Mission Generation

The Telos Engine automatically:
1. Scans Oracle Daemon intelligence feeds
2. Identifies strategic opportunities
3. Generates mission instruction blocks
4. Dispatches to Agent Ex-Work for execution
5. Monitors results and adapts strategy

### Resource Transmutation

```bash
# Identify and monetize idle compute resources
./bin/umcc_console
> transmute idle_cpu to compute_credits
```

## 🚨 Ethical Considerations

UMCC is designed for legitimate security research, infrastructure management, and strategic advantage within legal boundaries. Users are responsible for compliance with applicable laws and regulations.

## 📚 Documentation

- **[Architecture Guide](docs/architecture.md)** - Detailed system design
- **[API Reference](docs/api.md)** - gRPC service documentation
- **[Configuration](docs/configuration.md)** - Setup and tuning guide
- **[Security Model](docs/security.md)** - Trust and threat model
- **[Development Guide](docs/development.md)** - Contributing guidelines

## 🤝 Contributing

UMCC follows the principle of "Tungsten Grade Reliability":

1. **No Placeholders** - Complete implementations only
2. **Comprehensive Testing** - Full test coverage required
3. **Structured Logging** - JSON logging for all components
4. **Documentation** - Clear, actionable documentation
5. **Security First** - Security considerations in all changes

## 📜 License

This project operates under The Architect's Digital Sovereignty License - use at your own discretion and responsibility.

## 🎊 Acknowledgments

Built with Master-Class tools and methodologies from the awesome-* ecosystem:
- [awesome-go](https://github.com/avelino/awesome-go)
- [awesome-python](https://github.com/vinta/awesome-python)
- [awesome-grpc](https://github.com/grpc-ecosystem/awesome-grpc)
- [awesome-security](https://github.com/sbilly/awesome-security)

---

*"In the realm of digital sovereignty, The Architect's will is paramount."*

**The UMCC Project** - Where autonomous intelligence meets strategic execution.
