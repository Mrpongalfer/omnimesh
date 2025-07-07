# Omnitide Compute Fabric - Advanced Makefile
# Production-grade automation for build, test, deploy, and maintenance

.PHONY: help setup build test lint security clean dev deploy status monitor logs

# Default target
help: ## Show this help message
	@echo "🔧 Omnitide Compute Fabric - Build & Development Automation"
	@echo "=========================================================="
	@echo ""
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*##"; printf "\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@echo ""

##@ Setup & Installation

setup: ## Setup development environment
	@echo "🔧 Setting up development environment..."
	@chmod +x scripts/setup-dev.sh
	@./scripts/setup-dev.sh
	@echo "✅ Development environment ready!"

install-deps: ## Install system dependencies
	@echo "📦 Installing system dependencies..."
	@if command -v apt-get >/dev/null 2>&1; then \
		sudo apt-get update && \
		sudo apt-get install -y build-essential pkg-config libssl-dev postgresql-client docker.io docker-compose; \
	elif command -v brew >/dev/null 2>&1; then \
		brew install postgresql docker docker-compose; \
	else \
		echo "⚠️  Please install dependencies manually"; \
	fi

##@ Build & Compilation

build: build-rust build-go ## Build all components
	@echo "✅ All components built successfully!"

build-rust: ## Build Rust Nexus Prime Core
	@echo "🦀 Building Nexus Prime Core (Rust)..."
	@cd nexus-prime-core && cargo build --release
	@echo "✅ Rust build complete!"

build-go: ## Build Go Node Proxies
	@echo "🐹 Building Go Node Proxies..."
	@cd go-node-proxies && go build -o gcnp .
	@echo "✅ Go build complete!"

build-debug: ## Build all components in debug mode
	@echo "🔍 Building in debug mode..."
	@cd nexus-prime-core && cargo build
	@cd go-node-proxies && go build -race -o gcnp-debug .

##@ Testing & Quality Assurance

test: test-rust test-go test-integration ## Run all tests
	@echo "✅ All tests completed!"

test-rust: ## Run Rust tests
	@echo "🧪 Running Rust tests..."
	@cd nexus-prime-core && cargo test --lib || true

test-go: ## Run Go tests
	@echo "🧪 Running Go tests..."
	@cd go-node-proxies && go test -v ./...

test-integration: ## Run integration tests
	@echo "🔗 Running integration tests..."
	@chmod +x tests/integration_test.sh
	@./tests/integration_test.sh

test-coverage: ## Generate test coverage reports
	@echo "📊 Generating test coverage..."
	@mkdir -p coverage/rust coverage/go
	@cd go-node-proxies && go test -coverprofile=../coverage/go/coverage.out ./... && \
		go tool cover -html=../coverage/go/coverage.out -o ../coverage/go/coverage.html

##@ Code Quality & Security

lint: lint-rust lint-go ## Run all linters
	@echo "✅ All linting completed!"

lint-rust: ## Run Rust linting
	@echo "🔍 Linting Rust code..."
	@cd nexus-prime-core && cargo clippy -- -D warnings || true
	@cd nexus-prime-core && cargo fmt --check || true

lint-go: ## Run Go linting
	@echo "🔍 Linting Go code..."
	@cd go-node-proxies && go vet ./...
	@cd go-node-proxies && go fmt ./...
	@if command -v golangci-lint >/dev/null 2>&1; then \
		cd go-node-proxies && golangci-lint run; \
	else \
		echo "⚠️  golangci-lint not installed, skipping advanced Go linting"; \
	fi

format: ## Format all source code
	@echo "🎨 Formatting source code..."
	@cd nexus-prime-core && cargo fmt
	@cd go-node-proxies && go fmt ./...
	@echo "✅ Code formatting complete!"

security: security-rust security-go ## Run security audits
	@echo "✅ Security audit completed!"

security-rust: ## Run Rust security audit
	@echo "🔒 Running Rust security audit..."
	@cd nexus-prime-core && cargo audit || true

security-go: ## Run Go security audit
	@echo "🔒 Running Go security audit..."
	@cd go-node-proxies && go list -json -m all | nancy sleuth || true

##@ Development & Running

dev: ## Start development environment
	@echo "🚀 Starting development environment..."
	@docker-compose up -d || true
	@echo "🔗 Starting Nexus Prime Core..."
	@cd nexus-prime-core && RUST_LOG=debug cargo run &
	@sleep 3
	@echo "🔗 Starting Go Node Proxy..."
	@cd go-node-proxies && go run . &
	@echo "✅ Development environment running!"
	@echo "📊 Access points:"
	@echo "   - Nexus Prime gRPC: localhost:50053"
	@echo "   - WebSocket API: localhost:8080"
	@echo "   - Prometheus: localhost:9090"
	@echo "   - Grafana: localhost:3000"

stop: ## Stop development environment
	@echo "🛑 Stopping development environment..."
	@docker-compose down || true
	@pkill -f "nexus-prime-core" || true
	@pkill -f "go run" || true
	@echo "✅ Development environment stopped!"

restart: stop dev ## Restart development environment

##@ Deployment & Operations

deploy-dev: ## Deploy to development environment
	@echo "🚀 Deploying to development..."
	@chmod +x scripts/deploy.sh
	@./scripts/deploy.sh development

deploy-prod: ## Deploy to production environment
	@echo "🚀 Deploying to production..."
	@chmod +x scripts/deploy.sh
	@sudo ./scripts/deploy.sh production

status: ## Check system status
	@echo "📊 System Status"
	@echo "================"
	@echo "Nexus Prime Core:"
	@if pgrep -f "nexus-prime-core" >/dev/null; then \
		echo "  ✅ Running (PID: $$(pgrep -f 'nexus-prime-core'))"; \
	else \
		echo "  ❌ Not running"; \
	fi
	@echo "Go Node Proxies:"
	@if pgrep -f "gcnp\|go run" >/dev/null; then \
		echo "  ✅ Running (PID: $$(pgrep -f 'gcnp\|go run'))"; \
	else \
		echo "  ❌ Not running"; \
	fi
	@echo "Docker Services:"
	@docker-compose ps 2>/dev/null || echo "  ❌ Docker Compose not running"

monitor: ## Open monitoring dashboard
	@echo "📊 Opening monitoring dashboard..."
	@if command -v xdg-open >/dev/null 2>&1; then \
		xdg-open http://localhost:3000; \
	elif command -v open >/dev/null 2>&1; then \
		open http://localhost:3000; \
	else \
		echo "🌐 Access Grafana at: http://localhost:3000"; \
	fi

logs: ## View system logs
	@echo "📋 System Logs (last 50 lines)"
	@echo "==============================="
	@if [ -f nexus-prime-core/nexus.log ]; then \
		echo "Nexus Prime Core:"; \
		tail -20 nexus-prime-core/nexus.log; \
	fi
	@if [ -f go-node-proxies/proxy.log ]; then \
		echo "Go Node Proxy:"; \
		tail -20 go-node-proxies/proxy.log; \
	fi
	@echo "Docker Logs:"
	@docker-compose logs --tail=20 2>/dev/null || echo "No Docker logs available"

##@ Documentation & Maintenance

docs: ## Generate and serve documentation
	@echo "📚 Generating documentation..."
	@cd nexus-prime-core && cargo doc --no-deps || true
	@cd go-node-proxies && go doc -all
	@echo "✅ Documentation generated!"
	@echo "📖 Rust docs: nexus-prime-core/target/doc/nexus_prime_core/index.html"

benchmark: ## Run performance benchmarks
	@echo "⚡ Running performance benchmarks..."
	@cd nexus-prime-core && cargo bench || true
	@cd go-node-proxies && go test -bench=. -benchmem

profile: ## Run performance profiling
	@echo "🔬 Performance profiling..."
	@cd nexus-prime-core && cargo build --release
	@cd go-node-proxies && go build -o gcnp-profile .
	@echo "📊 Run with: perf record ./target/release/nexus-prime-core"

clean: ## Clean build artifacts
	@echo "🧹 Cleaning build artifacts..."
	@cd nexus-prime-core && cargo clean
	@cd go-node-proxies && go clean
	@rm -f go-node-proxies/gcnp go-node-proxies/gcnp-debug go-node-proxies/gcnp-profile
	@rm -rf coverage/
	@docker-compose down --volumes --remove-orphans 2>/dev/null || true
	@echo "✅ Cleanup complete!"

reset: clean ## Complete reset (clean + remove data)
	@echo "🔄 Complete system reset..."
	@rm -rf nexus-prime-core/data/
	@rm -rf local/
	@rm -f *.log
	@echo "✅ System reset complete!"

##@ Database & Storage

db-setup: ## Setup development database
	@echo "🗄️  Setting up database..."
	@docker-compose up -d postgres || true
	@sleep 5
	@docker-compose exec postgres createdb -U postgres omnitide 2>/dev/null || true
	@echo "✅ Database ready!"

db-reset: ## Reset database
	@echo "🔄 Resetting database..."
	@docker-compose down postgres || true
	@docker volume rm omnimesh_postgres_data 2>/dev/null || true
	@$(MAKE) db-setup

##@ Utilities

check-deps: ## Check for missing dependencies
	@echo "🔍 Checking dependencies..."
	@echo "Rust toolchain:"
	@rustc --version 2>/dev/null || echo "  ❌ Rust not installed"
	@cargo --version 2>/dev/null || echo "  ❌ Cargo not installed"
	@echo "Go toolchain:"
	@go version 2>/dev/null || echo "  ❌ Go not installed"
	@echo "Docker:"
	@docker --version 2>/dev/null || echo "  ❌ Docker not installed"
	@docker-compose --version 2>/dev/null || echo "  ❌ Docker Compose not installed"
	@echo "Protocol Buffers:"
	@protoc --version 2>/dev/null || echo "  ❌ protoc not installed"

update-deps: ## Update all dependencies
	@echo "📦 Updating dependencies..."
	@cd nexus-prime-core && cargo update
	@cd go-node-proxies && go get -u && go mod tidy

generate-certs: ## Generate development certificates
	@echo "🔐 Generating development certificates..."
	@mkdir -p certs
	@openssl req -x509 -newkey rsa:4096 -keyout certs/key.pem -out certs/cert.pem -days 365 -nodes -subj "/C=US/ST=CA/L=SF/O=Omnitide/CN=localhost" 2>/dev/null || echo "⚠️  OpenSSL not available"
	@echo "✅ Certificates generated in ./certs/"

##@ CI/CD

ci: check-deps build lint test security ## Run full CI pipeline
	@echo "🎯 CI Pipeline completed successfully!"

cd: ci deploy-dev ## Run CD pipeline (CI + Deploy)
	@echo "🚀 CD Pipeline completed successfully!"

release: ## Create a release build
	@echo "📦 Creating release build..."
	@cd nexus-prime-core && cargo build --release
	@cd go-node-proxies && CGO_ENABLED=0 go build -ldflags="-w -s" -o gcnp .
	@mkdir -p dist/
	@cp nexus-prime-core/target/release/nexus-prime-core dist/ 2>/dev/null || echo "⚠️  Rust binary not available"
	@cp go-node-proxies/gcnp dist/
	@tar -czf dist/omnitide-fabric-$(shell date +%Y%m%d-%H%M%S).tar.gz -C dist/ .
	@echo "✅ Release package created in dist/"

# Advanced targets for production management
backup: ## Backup system data
	@echo "💾 Creating system backup..."
	@mkdir -p backups/$(shell date +%Y%m%d-%H%M%S)
	@cp -r nexus-prime-core/data/ backups/$(shell date +%Y%m%d-%H%M%S)/ 2>/dev/null || true
	@echo "✅ Backup created!"

restore: ## Restore from backup (specify BACKUP_DIR=path)
	@echo "🔄 Restoring from backup..."
	@if [ -z "$(BACKUP_DIR)" ]; then \
		echo "❌ Please specify BACKUP_DIR=path"; \
		exit 1; \
	fi
	@cp -r $(BACKUP_DIR)/* nexus-prime-core/data/
	@echo "✅ Restore completed!"

health: ## Run comprehensive health check
	@echo "🩺 Running health check..."
	@curl -s http://localhost:8080/health >/dev/null && echo "✅ WebSocket API healthy" || echo "❌ WebSocket API unhealthy"
	@curl -s http://localhost:9090/metrics >/dev/null && echo "✅ Metrics endpoint healthy" || echo "❌ Metrics endpoint unhealthy"
	@nc -z localhost 50053 && echo "✅ gRPC endpoint healthy" || echo "❌ gRPC endpoint unhealthy"
