# 🤝 Contributing to OMNIMESH

**Welcome to the Trinity Convergence Platform contribution guide!**

Thank you for your interest in contributing to OMNIMESH. This guide will help you get started with contributing to our revolutionary Trinity Convergence Platform.

## 🎯 Quick Start for Contributors

### Prerequisites
- **Git**: Version control system
- **Docker**: Container runtime (v20.0+)
- **Make**: Build automation tool
- **Go**: v1.21+ (for proxy development)
- **Rust**: v1.70+ (for core engine development)
- **Python**: v3.10+ (for orchestrator development)
- **Node.js**: v18+ (for frontend development)

### Development Environment Setup

1. **Fork and Clone**
```bash
# Fork the repository on GitHub
git clone https://github.com/YOUR_USERNAME/omnimesh.git
cd omnimesh

# Add upstream remote
git remote add upstream https://github.com/mrpongalfer/omnimesh.git
```

2. **Environment Setup**
```bash
# Run the complete development setup
make dev-setup

# Verify installation
make health
```

3. **Start Development Environment**
```bash
# Start all services in development mode
make dev

# Check all services are running
make status
```

## 📋 Development Workflow

### 1. Issue Tracking
Before starting work, please:
- Check existing issues on GitHub
- Create a new issue if needed
- Comment on the issue to claim it
- Wait for maintainer approval for significant changes

### 2. Branch Naming Convention
```bash
# Feature branches
git checkout -b feature/add-natural-language-support

# Bug fix branches
git checkout -b fix/rust-engine-memory-leak

# Documentation branches
git checkout -b docs/update-api-reference

# Refactoring branches
git checkout -b refactor/optimize-message-bus
```

### 3. Commit Message Format
We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```bash
feat(nlp): add support for French language commands

fix(rust-engine): resolve memory leak in SIMD processor

docs(api): update authentication examples

test(integration): add end-to-end deployment tests
```

### 4. Pull Request Process

1. **Create Feature Branch**
```bash
git checkout -b feature/your-feature-name
```

2. **Make Changes**
```bash
# Make your changes
# Add tests
# Update documentation
```

3. **Test Your Changes**
```bash
# Run all tests
make test

# Run specific component tests
make test-rust
make test-go
make test-python

# Run integration tests
make test-integration

# Check code quality
make lint
make security-scan
```

4. **Commit Changes**
```bash
git add .
git commit -m "feat(component): add your feature description"
```

5. **Push and Create PR**
```bash
git push origin feature/your-feature-name
# Create PR on GitHub
```

## 🏗️ Architecture Guidelines

### Trinity Component Guidelines

#### PONGEX Core (Rust)
- **Performance First**: Optimize for zero-allocation patterns
- **Memory Safety**: Use Rust's ownership system effectively
- **Concurrency**: Prefer async/await over threads where possible
- **Testing**: Include benchmarks for performance-critical code

```rust
// Good: Zero-allocation string processing
fn process_command_zero_alloc(input: &str) -> Result<CommandType, ParseError> {
    match input.trim() {
        "health" | "status" => Ok(CommandType::Health),
        "deploy" => Ok(CommandType::Deploy),
        _ => Err(ParseError::UnknownCommand)
    }
}

// Bad: Unnecessary allocations
fn process_command_with_allocs(input: &str) -> Result<CommandType, ParseError> {
    let cleaned = input.to_lowercase().trim().to_string(); // Unnecessary allocation
    if cleaned == "health".to_string() { // Another unnecessary allocation
        Ok(CommandType::Health)
    } else {
        Err(ParseError::UnknownCommand)
    }
}
```

#### OMNITERM Interface (Python)
- **Async First**: Use asyncio for all I/O operations
- **Type Hints**: Always include comprehensive type hints
- **Error Handling**: Use proper exception hierarchies
- **Documentation**: Include docstrings for all public functions

```python
# Good: Proper async function with type hints
async def process_natural_language(
    command: str,
    context: CommandContext
) -> CommandResult:
    """
    Process natural language command with context.
    
    Args:
        command: Raw user input string
        context: Execution context with user info and settings
        
    Returns:
        CommandResult with action and parameters
        
    Raises:
        CommandParseError: If command cannot be interpreted
        AuthenticationError: If user lacks permissions
    """
    try:
        parsed = await self.nlp_engine.parse(command)
        return await self.execute_command(parsed, context)
    except ParseError as e:
        raise CommandParseError(f"Could not parse command: {e}")

# Bad: Blocking function without type hints
def process_command(command, context):
    parsed = nlp_parse(command)  # Blocking call
    return execute(parsed, context)
```

#### OMNIMESH Platform (Go)
- **Goroutine Safety**: Always consider concurrent access
- **Context Propagation**: Use context.Context for cancellation
- **Error Wrapping**: Use fmt.Errorf with %w verb
- **Interface Design**: Prefer small, focused interfaces

```go
// Good: Proper interface and error handling
type ServiceManager interface {
    Deploy(ctx context.Context, service Service) error
    Scale(ctx context.Context, serviceID string, replicas int) error
    Health(ctx context.Context, serviceID string) (HealthStatus, error)
}

func (sm *DefaultServiceManager) Deploy(ctx context.Context, service Service) error {
    if err := sm.validateService(service); err != nil {
        return fmt.Errorf("service validation failed: %w", err)
    }
    
    select {
    case <-ctx.Done():
        return ctx.Err()
    default:
        return sm.executeDeployment(ctx, service)
    }
}

// Bad: No context, poor error handling
func (sm *DefaultServiceManager) Deploy(service Service) error {
    sm.executeDeployment(service) // No error handling
    return nil
}
```

## 🧪 Testing Guidelines

### Test Structure
Each component should have comprehensive tests:

```
tests/
├── unit/           # Fast, isolated tests
├── integration/    # Multi-component tests
├── e2e/           # End-to-end tests
└── performance/   # Benchmark tests
```

### Test Coverage Requirements
- **Unit Tests**: >90% coverage
- **Integration Tests**: All major workflows
- **E2E Tests**: Critical user journeys
- **Performance Tests**: All performance-critical paths

### Writing Good Tests

#### Rust Tests
```rust
#[cfg(test)]
mod tests {
    use super::*;
    use tokio_test;

    #[tokio::test]
    async fn test_command_processing_health_check() {
        // Arrange
        let engine = RustEngine::new_for_testing();
        let request = Request::new("health_check", vec![]);

        // Act
        let result = engine.process_request(request).await;

        // Assert
        assert!(result.is_ok());
        assert_eq!(result.unwrap().status, ResponseStatus::Success);
    }

    #[tokio::test]
    async fn test_command_processing_invalid_input() {
        let engine = RustEngine::new_for_testing();
        let request = Request::new("invalid_command", vec![]);

        let result = engine.process_request(request).await;

        assert!(result.is_err());
        assert_eq!(result.unwrap_err().kind(), ErrorKind::InvalidCommand);
    }
}
```

#### Python Tests
```python
import pytest
import asyncio
from unittest.mock import AsyncMock, patch

class TestNaturalLanguageProcessor:
    @pytest.fixture
    async def nlp_processor(self):
        return NaturalLanguageProcessor()

    @pytest.mark.asyncio
    async def test_health_command_recognition(self, nlp_processor):
        # Arrange
        command = "check system health please"
        
        # Act
        result = await nlp_processor.process_command(command)
        
        # Assert
        assert result.action == "health_check"
        assert result.confidence > 0.9

    @pytest.mark.asyncio
    async def test_deploy_command_with_parameters(self, nlp_processor):
        command = "deploy to production with 5 replicas"
        
        result = await nlp_processor.process_command(command)
        
        assert result.action == "deploy"
        assert result.parameters["environment"] == "production"
        assert result.parameters["replicas"] == 5

    @pytest.mark.asyncio
    async def test_unknown_command_handling(self, nlp_processor):
        command = "do something completely unknown"
        
        with pytest.raises(CommandParseError):
            await nlp_processor.process_command(command)
```

#### Go Tests
```go
func TestServiceManager_Deploy(t *testing.T) {
    tests := []struct {
        name        string
        service     Service
        expectError bool
        errorType   error
    }{
        {
            name: "successful deployment",
            service: Service{
                Name: "test-service",
                Image: "nginx:latest",
                Replicas: 3,
            },
            expectError: false,
        },
        {
            name: "invalid service name",
            service: Service{
                Name: "", // Invalid
                Image: "nginx:latest",
            },
            expectError: true,
            errorType: ValidationError{},
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            sm := NewServiceManager()
            ctx := context.Background()

            err := sm.Deploy(ctx, tt.service)

            if tt.expectError {
                assert.Error(t, err)
                if tt.errorType != nil {
                    assert.IsType(t, tt.errorType, err)
                }
            } else {
                assert.NoError(t, err)
            }
        })
    }
}
```

## 📝 Documentation Standards

### Code Documentation

#### Rust Documentation
```rust
/// Processes high-performance computational requests using SIMD optimization.
/// 
/// This function takes advantage of hardware SIMD instructions to parallelize
/// mathematical operations across multiple data elements simultaneously.
/// 
/// # Arguments
/// 
/// * `data` - Input data vector to process
/// * `operation` - The mathematical operation to perform
/// 
/// # Returns
/// 
/// Returns a `Result` containing the processed data vector or a `ProcessingError`
/// if the operation fails.
/// 
/// # Examples
/// 
/// ```rust
/// use trinity_core::{SIMDProcessor, Operation};
/// 
/// let processor = SIMDProcessor::new();
/// let data = vec![1.0, 2.0, 3.0, 4.0];
/// let result = processor.process_simd(&data, Operation::Multiply(2.0))?;
/// assert_eq!(result, vec![2.0, 4.0, 6.0, 8.0]);
/// ```
/// 
/// # Performance
/// 
/// This function is optimized for large data sets (>1000 elements) and provides
/// significant performance improvements over scalar operations.
pub fn process_simd(&self, data: &[f32], operation: Operation) -> Result<Vec<f32>, ProcessingError> {
    // Implementation here
}
```

#### Python Documentation
```python
async def process_natural_language(
    self,
    command: str,
    context: Optional[CommandContext] = None
) -> CommandResult:
    """
    Process natural language input and convert to executable commands.
    
    This method uses advanced NLP techniques including tokenization, POS tagging,
    named entity recognition, and intent classification to understand user commands
    and convert them into structured actions.
    
    Args:
        command: Raw natural language input from the user
        context: Optional execution context containing user preferences,
                authentication info, and session state
    
    Returns:
        CommandResult containing the interpreted action, parameters,
        and confidence score
    
    Raises:
        CommandParseError: When the command cannot be interpreted
        AuthenticationError: When the user lacks required permissions
        ValueError: When the command parameter is empty or invalid
    
    Examples:
        >>> processor = NaturalLanguageProcessor()
        >>> result = await processor.process_natural_language("check system health")
        >>> print(result.action)  # "health_check"
        >>> print(result.confidence)  # 0.95
        
        >>> result = await processor.process_natural_language(
        ...     "deploy to production",
        ...     context=CommandContext(user="admin")
        ... )
        >>> print(result.parameters)  # {"environment": "production"}
    
    Note:
        This method is async and should be awaited. It may perform I/O operations
        such as database lookups for context enrichment.
    """
```

### README Files
Each component should have its own README:

```markdown
# Component Name

Brief description of what this component does.

## Quick Start

```bash
# Basic usage
./component-cli --help
```

## Architecture

Brief architecture overview with diagrams if needed.

## Configuration

Configuration options and examples.

## Development

How to build, test, and contribute to this component.

## API Reference

Link to detailed API documentation.
```

## 🔒 Security Guidelines

### Security Best Practices

1. **Input Validation**
```python
def validate_user_input(command: str) -> str:
    """Validate and sanitize user input."""
    if not command or len(command.strip()) == 0:
        raise ValueError("Command cannot be empty")
    
    if len(command) > MAX_COMMAND_LENGTH:
        raise ValueError(f"Command too long (max {MAX_COMMAND_LENGTH} chars)")
    
    # Sanitize dangerous characters
    sanitized = re.sub(r'[;<>&|`$]', '', command)
    
    return sanitized.strip()
```

2. **Authentication & Authorization**
```python
async def require_permission(permission: str):
    """Decorator to require specific permission."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = get_current_user()
            if not await check_permission(user, permission):
                raise UnauthorizedError(f"Permission required: {permission}")
            return await func(*args, **kwargs)
        return wrapper
    return decorator

@require_permission("deploy.production")
async def deploy_to_production(service: Service):
    # Implementation
    pass
```

3. **Secrets Management**
```python
# Good: Use environment variables or secret management
api_key = os.getenv('TRINITY_API_KEY')
if not api_key:
    raise ConfigurationError("TRINITY_API_KEY not configured")

# Bad: Hardcoded secrets
api_key = "sk-1234567890abcdef"  # Never do this!
```

### Security Review Process
- All PRs with security implications require security team review
- Use `make security-scan` before submitting PRs
- Follow OWASP guidelines for web security
- Regular dependency vulnerability scanning

## 🚀 Performance Guidelines

### Performance Best Practices

1. **Async Programming**
```python
# Good: Concurrent execution
async def process_multiple_commands(commands: List[str]) -> List[CommandResult]:
    tasks = [process_command(cmd) for cmd in commands]
    return await asyncio.gather(*tasks)

# Bad: Sequential execution
async def process_multiple_commands_slow(commands: List[str]) -> List[CommandResult]:
    results = []
    for cmd in commands:
        result = await process_command(cmd)  # Blocking
        results.append(result)
    return results
```

2. **Memory Management**
```rust
// Good: Use references to avoid cloning
fn process_large_data(data: &[u8]) -> ProcessResult {
    // Process data without copying
    ProcessResult::new(data.len())
}

// Bad: Unnecessary cloning
fn process_large_data_slow(data: &[u8]) -> ProcessResult {
    let owned_data = data.to_vec();  // Expensive copy
    ProcessResult::new(owned_data.len())
}
```

3. **Caching Strategy**
```python
from functools import lru_cache
import asyncio

class CommandCache:
    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self.cache = TTLCache(maxsize=max_size, ttl=ttl)
    
    @lru_cache(maxsize=128)
    def get_command_pattern(self, command_type: str) -> Pattern:
        """Cache compiled regex patterns."""
        return re.compile(COMMAND_PATTERNS[command_type])
    
    async def get_with_fallback(self, key: str, fallback_fn):
        """Get from cache with async fallback."""
        if key in self.cache:
            return self.cache[key]
        
        result = await fallback_fn()
        self.cache[key] = result
        return result
```

## 📊 Code Quality Standards

### Linting and Formatting

#### Rust
```toml
# .rustfmt.toml
max_width = 100
tab_spaces = 4
newline_style = "Unix"
use_small_heuristics = "Default"
```

#### Python
```toml
# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py310']
include = '\.pyi?$'

[tool.isort]
profile = "black"
multi_line_output = 3

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

#### Go
```bash
# Use gofmt and goimports
gofmt -s -w .
goimports -w .

# Use golangci-lint for comprehensive linting
golangci-lint run
```

### Code Review Checklist

**General:**
- [ ] Code follows project conventions
- [ ] All tests pass
- [ ] Documentation is updated
- [ ] No hardcoded secrets or sensitive data
- [ ] Error handling is appropriate

**Performance:**
- [ ] No unnecessary allocations
- [ ] Async operations where appropriate
- [ ] Proper resource cleanup
- [ ] Caching used where beneficial

**Security:**
- [ ] Input validation implemented
- [ ] Authentication/authorization checks
- [ ] No SQL injection vulnerabilities
- [ ] Secrets properly managed

**Testing:**
- [ ] Unit tests cover new functionality
- [ ] Integration tests for API changes
- [ ] Edge cases are tested
- [ ] Performance tests for critical paths

## 🐛 Bug Report Guidelines

### Bug Report Template
```markdown
## Bug Description
A clear and concise description of the bug.

## Steps to Reproduce
1. Go to '...'
2. Click on '...'
3. Run command '...'
4. See error

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened.

## Environment
- OS: [e.g., Ubuntu 22.04]
- Trinity Version: [e.g., 3.0.0]
- Component: [e.g., PONGEX Core, OMNITERM Interface]

## Logs
```
Paste relevant logs here
```

## Additional Context
Add any other context about the problem here.
```

## 💡 Feature Request Guidelines

### Feature Request Template
```markdown
## Feature Description
A clear and concise description of the feature.

## Problem Statement
What problem does this feature solve?

## Proposed Solution
Describe your proposed solution.

## Alternatives Considered
Describe alternative solutions you've considered.

## Implementation Ideas
Any ideas about how this could be implemented.

## Additional Context
Add any other context or screenshots about the feature request.
```

## 🎖️ Recognition

We recognize contributions in several ways:

1. **Contributor List**: All contributors are listed in our README
2. **Release Notes**: Significant contributions are mentioned in release notes
3. **Special Recognition**: Outstanding contributors get special recognition
4. **Maintainer Status**: Active contributors may be invited as maintainers

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Discord**: Join our Discord server for real-time chat
- **Email**: Contact maintainers at omnimesh-dev@example.com

## 📜 License

By contributing to OMNIMESH, you agree that your contributions will be licensed under the same license as the project.

---

**Thank you for contributing to the Trinity Convergence Platform! Together, we're building the future of computational systems.**
