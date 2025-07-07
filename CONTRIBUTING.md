# Contributing to OmniTide Compute Fabric

Welcome to the OmniTide Compute Fabric project! We're excited to have you contribute to the future of distributed AI orchestration.

## 🎯 Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## 🚀 Quick Start

### Development Environment Setup

```bash
# Clone the repository
git clone https://github.com/omnimesh/omnitide.git
cd omnitide

# Install development tools
./scripts/setup-dev.sh

# Install pre-commit hooks
pre-commit install

# Verify setup
make verify-setup
```

### Required Tools

- **Rust**: 1.70+ with `clippy`, `rustfmt`, `cargo-audit`
- **Go**: 1.23+ with `golangci-lint`, `gosec`
- **Docker**: 24.0+ with `buildx`
- **Node.js**: 18+ with `pnpm`
- **Protocol Buffers**: 3.21+
- **Git**: 2.40+ with signed commits enabled

## 📋 Development Workflow

### 1. Issue Creation

Before starting work:

1. **Search existing issues** to avoid duplicates
2. **Create a detailed issue** with:
   - Clear problem description
   - Expected vs actual behavior
   - Reproduction steps
   - Environment details
   - Acceptance criteria

### 2. Branch Strategy

We follow **GitFlow** with semantic branch naming:

```bash
# Feature branches
feature/ISSUE-123-add-agent-migration

# Bug fix branches
bugfix/ISSUE-456-fix-memory-leak

# Hot fix branches (for production)
hotfix/ISSUE-789-critical-security-fix

# Release branches
release/v1.2.0
```

### 3. Development Process

```bash
# 1. Create and switch to feature branch
git checkout -b feature/ISSUE-123-your-feature

# 2. Make changes following coding standards
# 3. Write/update tests
# 4. Run quality checks
make check-all

# 5. Commit with conventional commits
git commit -m "feat(nexus): add agent migration capability

- Implement migration protocol
- Add state transfer logic
- Update API documentation

Closes #123"

# 6. Push and create PR
git push origin feature/ISSUE-123-your-feature
```

### 4. Pull Request Requirements

All PRs must include:

- [ ] **Descriptive title** following conventional commits
- [ ] **Detailed description** explaining changes
- [ ] **Issue reference** (e.g., "Closes #123")
- [ ] **Breaking changes** clearly documented
- [ ] **Tests** covering new functionality
- [ ] **Documentation** updates
- [ ] **Changelog** entry (if user-facing)

### 5. Review Process

1. **Automated Checks**: All CI checks must pass
2. **Code Review**: At least 2 approvals required
3. **Security Review**: For security-sensitive changes
4. **Performance Review**: For performance-critical code
5. **Documentation Review**: For user-facing changes

## 💻 Coding Standards

### Rust Code Standards

```rust
// Use explicit error handling
fn process_agent() -> Result<Agent, AgentError> {
    // Avoid unwrap() in production code
    let config = load_config().map_err(AgentError::ConfigLoad)?;
    
    // Use structured logging
    tracing::info!(
        agent_id = %agent.id,
        node_id = %node.id,
        "Processing agent deployment"
    );
    
    Ok(agent)
}

// Use type-driven design
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct AgentConfig {
    pub id: AgentId,
    pub name: String,
    pub resources: ResourceRequirements,
}

// Document public APIs thoroughly
/// Deploys an AI agent to the specified compute node.
///
/// # Arguments
///
/// * `agent_config` - Configuration for the agent to deploy
/// * `node_id` - Target node identifier
///
/// # Returns
///
/// Returns the deployed agent instance or an error if deployment fails.
///
/// # Errors
///
/// - `AgentError::NodeNotFound` if the target node doesn't exist
/// - `AgentError::InsufficientResources` if the node lacks resources
/// - `AgentError::DeploymentFailed` if the deployment process fails
///
/// # Example
///
/// ```rust
/// let config = AgentConfig::new("synthesizer", "node-1");
/// let agent = deploy_agent(config, "node-123").await?;
/// ```
pub async fn deploy_agent(
    agent_config: AgentConfig,
    node_id: NodeId,
) -> Result<Agent, AgentError> {
    // Implementation
}
```

### Go Code Standards

```go
// Use structured logging
import "log/slog"

func ProcessContainer(ctx context.Context, containerID string) error {
    logger := slog.With(
        "container_id", containerID,
        "operation", "process",
    )
    
    logger.Info("Processing container")
    
    // Use context for cancellation
    select {
    case <-ctx.Done():
        return ctx.Err()
    default:
        // Continue processing
    }
    
    return nil
}

// Use interfaces for testability
type ContainerManager interface {
    Deploy(ctx context.Context, config DeploymentConfig) (*Container, error)
    Stop(ctx context.Context, id string) error
    List(ctx context.Context) ([]*Container, error)
}

// Document public APIs
// DeploymentConfig represents the configuration for deploying a container.
type DeploymentConfig struct {
    // AgentID is the unique identifier for the AI agent
    AgentID string `json:"agent_id" validate:"required"`
    
    // Image is the Docker image to deploy
    Image string `json:"image" validate:"required"`
    
    // Resources defines the resource requirements
    Resources ResourceRequirements `json:"resources"`
}

// Deploy deploys a new container with the given configuration.
//
// It returns the deployed container information or an error if deployment fails.
// The context can be used to cancel the deployment operation.
func (m *Manager) Deploy(ctx context.Context, config DeploymentConfig) (*Container, error) {
    // Implementation
}
```

### Performance Standards

#### Rust Performance Guidelines

```rust
// Use appropriate data structures
use std::collections::HashMap; // O(1) lookup
use dashmap::DashMap; // Concurrent HashMap

// Minimize allocations
fn process_events(events: &[Event]) -> Vec<ProcessedEvent> {
    // Pre-allocate with known capacity
    let mut processed = Vec::with_capacity(events.len());
    
    for event in events {
        // Avoid unnecessary clones
        processed.push(process_event(event));
    }
    
    processed
}

// Use async efficiently
async fn handle_requests(requests: Vec<Request>) -> Vec<Response> {
    // Process concurrently
    let futures: Vec<_> = requests.into_iter()
        .map(|req| handle_request(req))
        .collect();
    
    // Await all at once
    futures_util::future::join_all(futures).await
}

// Benchmark critical paths
#[cfg(test)]
mod benches {
    use super::*;
    use criterion::{black_box, criterion_group, criterion_main, Criterion};
    
    fn bench_agent_deployment(c: &mut Criterion) {
        c.bench_function("agent_deployment", |b| {
            b.iter(|| {
                deploy_agent(black_box(test_config()))
            })
        });
    }
    
    criterion_group!(benches, bench_agent_deployment);
    criterion_main!(benches);
}
```

#### Go Performance Guidelines

```go
// Use appropriate data structures
var agentCache sync.Map // Concurrent map

// Minimize allocations
func ProcessEvents(events []Event) []ProcessedEvent {
    // Pre-allocate with known capacity
    processed := make([]ProcessedEvent, 0, len(events))
    
    for _, event := range events {
        processed = append(processed, processEvent(event))
    }
    
    return processed
}

// Use pools for frequent allocations
var bufferPool = sync.Pool{
    New: func() interface{} {
        return make([]byte, 0, 1024)
    },
}

func ProcessData(data []byte) []byte {
    buf := bufferPool.Get().([]byte)
    defer bufferPool.Put(buf[:0])
    
    // Process data using buf
    return result
}

// Benchmark critical functions
func BenchmarkAgentDeployment(b *testing.B) {
    config := testConfig()
    
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        deployAgent(config)
    }
}
```

### Security Standards

#### Input Validation

```rust
use validator::{Validate, ValidationError};

#[derive(Debug, Validate, serde::Deserialize)]
pub struct AgentRequest {
    #[validate(length(min = 1, max = 255))]
    pub name: String,
    
    #[validate(regex = "RE_AGENT_ID")]
    pub agent_id: String,
    
    #[validate(range(min = 1, max = 100))]
    pub cpu_cores: u32,
    
    #[validate(email)]
    pub owner_email: String,
}

// Validate all inputs
pub fn create_agent(request: AgentRequest) -> Result<Agent, ValidationError> {
    request.validate()?;
    // Process validated request
}
```

#### Secure Defaults

```rust
// Always use secure defaults
#[derive(Debug)]
pub struct SecurityConfig {
    pub tls_enabled: bool, // Default: true in production
    pub min_tls_version: String, // Default: "1.3"
    pub require_client_auth: bool, // Default: true
    pub session_timeout: Duration, // Default: 15 minutes
}

impl Default for SecurityConfig {
    fn default() -> Self {
        Self {
            tls_enabled: true,
            min_tls_version: "1.3".to_string(),
            require_client_auth: true,
            session_timeout: Duration::from_secs(900), // 15 minutes
        }
    }
}
```

## 🧪 Testing Standards

### Test Categories

1. **Unit Tests**: Test individual functions/methods
2. **Integration Tests**: Test component interactions
3. **End-to-End Tests**: Test complete workflows
4. **Performance Tests**: Benchmark critical paths
5. **Security Tests**: Test security controls
6. **Chaos Tests**: Test failure scenarios

### Test Structure

```rust
// Unit test example
#[cfg(test)]
mod tests {
    use super::*;
    use test_case::test_case;
    
    #[test_case("valid-agent-id", true; "valid agent ID")]
    #[test_case("", false; "empty agent ID")]
    #[test_case("invalid@id", false; "invalid characters")]
    fn test_validate_agent_id(agent_id: &str, expected: bool) {
        assert_eq!(validate_agent_id(agent_id), expected);
    }
    
    #[tokio::test]
    async fn test_agent_deployment_success() {
        // Arrange
        let config = test_agent_config();
        let mock_node = mock_compute_node();
        
        // Act
        let result = deploy_agent(config, mock_node).await;
        
        // Assert
        assert!(result.is_ok());
        let agent = result.unwrap();
        assert_eq!(agent.status, AgentStatus::Running);
    }
}
```

### Integration Tests

```rust
// Integration test example
#[tokio::test]
async fn test_full_deployment_workflow() {
    // Setup test environment
    let test_env = TestEnvironment::new().await;
    
    // Deploy nexus core
    let nexus = test_env.start_nexus().await?;
    
    // Deploy node proxy
    let proxy = test_env.start_proxy().await?;
    
    // Test agent deployment
    let agent_config = AgentConfig::new("test-agent");
    let deployment_result = nexus.deploy_agent(agent_config).await?;
    
    // Verify deployment
    assert!(deployment_result.is_success());
    
    // Cleanup
    test_env.cleanup().await;
}
```

### Test Coverage Requirements

- **Rust**: Minimum 90% line coverage
- **Go**: Minimum 85% line coverage
- **Critical paths**: 100% coverage required
- **Error paths**: All error conditions tested
- **Edge cases**: Boundary conditions covered

## 📊 Performance Requirements

### Latency Targets

- **gRPC API calls**: < 10ms p95
- **WebSocket messages**: < 5ms p95
- **Agent deployment**: < 30s p95
- **Database operations**: < 1ms p95

### Throughput Targets

- **Concurrent connections**: 10,000+
- **Requests per second**: 10,000+
- **Agent deployments**: 100+ per minute
- **Event processing**: 1,000,000+ per second

### Resource Limits

- **Memory usage**: < 512MB per service
- **CPU usage**: < 50% under normal load
- **Disk I/O**: < 100MB/s sustained
- **Network I/O**: < 1GB/s sustained

## 🔐 Security Requirements

### Security Checklist

- [ ] **Input validation** on all external inputs
- [ ] **Output encoding** to prevent injection
- [ ] **Authentication** for all API endpoints
- [ ] **Authorization** with least privilege
- [ ] **Audit logging** for security events
- [ ] **Encryption** in transit and at rest
- [ ] **Secrets management** with rotation
- [ ] **Dependency scanning** for vulnerabilities

### Security Testing

```bash
# Static analysis
cargo audit                    # Rust vulnerability scanning
gosec ./...                   # Go security analysis
semgrep --config=auto         # Multi-language security scanning

# Dynamic analysis
docker run --rm -v "$(pwd):/src" securecodewarrior/docker-clair
trivy fs .                    # Container vulnerability scanning

# Penetration testing
nuclei -u http://localhost:8080
nmap -A localhost             # Network scanning
```

## 📚 Documentation Standards

### Documentation Types

1. **Code Documentation**: Inline comments and docstrings
2. **API Documentation**: OpenAPI/Swagger specs
3. **User Documentation**: Getting started, tutorials
4. **Architecture Documentation**: Design docs, ADRs
5. **Operational Documentation**: Deployment, monitoring

### Writing Guidelines

- **Clear and concise**: Use simple, direct language
- **Comprehensive**: Cover all use cases and edge cases
- **Examples**: Provide working code examples
- **Up-to-date**: Keep documentation in sync with code
- **Searchable**: Use consistent terminology

### Documentation Tools

- **Rust**: `rustdoc` with comprehensive examples
- **Go**: `godoc` with package documentation
- **API**: OpenAPI 3.0 specifications
- **Books**: mdBook for comprehensive guides
- **Diagrams**: Mermaid for architecture diagrams

## 🚀 Release Process

### Version Strategy

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking API changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

- [ ] **Version bump** in all relevant files
- [ ] **Changelog** updated with all changes
- [ ] **Documentation** updated
- [ ] **Tests** passing on all platforms
- [ ] **Security scan** completed
- [ ] **Performance benchmarks** within targets
- [ ] **Migration guide** for breaking changes
- [ ] **Release notes** prepared

### Automated Releases

```yaml
# .github/workflows/release.yml
name: Release
on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build Release
        run: make build-release
        
      - name: Run Tests
        run: make test-all
        
      - name: Security Scan
        run: make security-scan
        
      - name: Create Release
        uses: actions/create-release@v1
        with:
          tag_name: ${{ github.ref }}
          release_name: Release ${{ github.ref }}
          draft: false
          prerelease: false
```

## 🏆 Recognition

We recognize contributions through:

- **Hall of Fame**: Top contributors featured in README
- **Contributor badges**: GitHub profile badges
- **Conference speaking**: Opportunities to present work
- **Mentorship programs**: Senior contributor mentoring
- **Swag and rewards**: OmniTide merchandise

## 📞 Getting Help

### Community Channels

- **Discord**: [OmniTide Community](https://discord.gg/omnitide)
- **GitHub Discussions**: For design discussions
- **Stack Overflow**: Tag questions with `omnitide`
- **Office Hours**: Weekly developer office hours

### Maintainer Contact

- **Technical Questions**: Create a GitHub issue
- **Security Issues**: security@omnitide.dev
- **General Inquiries**: hello@omnitide.dev

## 📄 License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

Thank you for contributing to OmniTide! Together, we're building the future of distributed AI orchestration. 🚀
