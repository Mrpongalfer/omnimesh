# Contributing to Omnitide Control Panel

> **Welcome to the future of distributed system interfaces!** 🚀  
> Thank you for your interest in contributing to the next-generation cyberpunk control panel.

---

## 🎯 **Getting Started**

### Prerequisites

- **Node.js 20.11.0+** (LTS with Corepack support)
- **npm 10+** or **pnpm 9.4+** (recommended for performance)
- **Git 2.40+** with LFS support
- **VS Code** with recommended extensions (optional but encouraged)

### Development Environment Setup

```bash
# Clone the repository
git clone https://github.com/omnitide/control-panel.git
cd control-panel

# Install dependencies (pnpm recommended)
pnpm install

# Setup development environment
pnpm run setup

# Verify installation
pnpm run doctor

# Start development server
pnpm run dev
```

### Recommended VS Code Extensions

```bash
# Install all recommended extensions
code --install-extension bradlc.vscode-tailwindcss
code --install-extension ms-playwright.playwright
code --install-extension vitest.explorer
code --install-extension esbenp.prettier-vscode
code --install-extension dbaeumer.vscode-eslint
code --install-extension ms-vscode.vscode-typescript-next
```

---

## 🏗️ **Project Architecture**

### Technology Stack

- **Framework**: Solid.js 1.9+ (fine-grained reactivity)
- **Language**: TypeScript 5.8+ (strict mode, latest features)
- **Build**: Vite 6.3+ (sub-100ms HMR)
- **Styling**: Tailwind CSS 4.1+ (JIT compilation)
- **Graphics**: PixiJS 8.11+ (WebGL 2.0, 120fps)
- **State**: Signal-based reactive store
- **Testing**: Vitest + Playwright (>95% coverage)

### Code Organization

```
src/
├── components/     # Atomic design components (atoms, molecules, organisms)
├── pages/         # Route-level components with lazy loading
├── services/      # Business logic with dependency injection
├── store/         # Signal-based state management
├── proto/         # Protocol Buffers definitions
├── workers/       # Web Workers for background processing
└── utils/         # Pure utility functions
```

---

## 📝 **Development Workflow**

### 1. Issue Creation

- **Use Templates**: Bug reports, feature requests, or enhancement proposals
- **Provide Context**: Include screenshots, code snippets, and environment details
- **Label Appropriately**: Use labels for priority, type, and affected components

### 2. Branch Strategy

```bash
# Create feature branch from main
git checkout main
git pull origin main
git checkout -b feature/amazing-feature

# Create hotfix branch for urgent fixes
git checkout -b hotfix/critical-security-fix

# Create documentation branch
git checkout -b docs/update-api-documentation
```

### 3. Development Process

```bash
# Make your changes following the coding standards
# Run tests frequently during development
pnpm run test:watch

# Type-check your changes
pnpm run type-check

# Lint and format code
pnpm run lint
pnpm run format

# Run comprehensive quality check
pnpm run doctor

# Commit with conventional commit format
git add .
git commit -m "feat: add WebGL spatial indexing for 10K+ nodes"
```

### 4. Testing Requirements

```bash
# Unit tests (>95% coverage required)
pnpm run test:coverage

# E2E tests (critical paths must pass)
pnpm run e2e

# Visual regression tests
pnpm run test:visual

# Performance benchmarks
pnpm run perf

# Accessibility validation
pnpm run test:a11y
```

### 5. Pull Request Process

- **Fill Template**: Use the PR template with all sections completed
- **Link Issues**: Reference related issues with "Closes #123" or "Fixes #456"
- **Add Screenshots**: Visual changes require before/after screenshots
- **Performance Impact**: Include bundle size changes and performance metrics
- **Breaking Changes**: Document any breaking changes in detail

---

## 🎨 **Coding Standards**

### TypeScript Guidelines

```typescript
// Use strict type definitions
interface NodeMetrics {
  readonly id: string;
  readonly timestamp: number;
  readonly cpu: number;
  readonly memory: number;
  readonly network: NetworkMetrics;
}

// Prefer branded types for domain concepts
type NodeId = string & { readonly brand: unique symbol };
type Timestamp = number & { readonly brand: unique symbol };

// Use exhaustive switch statements
function handleNodeStatus(status: NodeStatus): string {
  switch (status) {
    case 'active':
      return 'Node is operational';
    case 'degraded':
      return 'Node experiencing issues';
    case 'failed':
      return 'Node is down';
    default:
      // TypeScript ensures this is unreachable
      const _exhaustive: never = status;
      throw new Error(`Unhandled status: ${status}`);
  }
}

// Use proper async/await patterns
async function fetchNodeMetrics(nodeId: NodeId): Promise<NodeMetrics> {
  try {
    const response = await fetch(`/api/nodes/${nodeId}/metrics`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch node metrics:', error);
    throw error;
  }
}
```

### Component Guidelines

```typescript
// Use proper JSX patterns with TypeScript
interface ButtonProps {
  readonly variant: 'primary' | 'secondary' | 'danger';
  readonly size: 'small' | 'medium' | 'large';
  readonly disabled?: boolean;
  readonly loading?: boolean;
  readonly onClick?: () => void;
  readonly children: JSX.Element;
  readonly 'aria-label'?: string;
}

export const Button = (props: ButtonProps) => {
  const [isPressed, setIsPressed] = createSignal(false);

  return (
    <button
      class={`btn btn-${props.variant} btn-${props.size}`}
      disabled={props.disabled || props.loading}
      aria-label={props['aria-label']}
      aria-pressed={isPressed()}
      onMouseDown={() => setIsPressed(true)}
      onMouseUp={() => setIsPressed(false)}
      onClick={props.onClick}
    >
      <Show when={props.loading} fallback={props.children}>
        <LoadingSpinner />
      </Show>
    </button>
  );
};
```

### Performance Guidelines

```typescript
// Use createMemo for expensive computations
const expensiveComputation = createMemo(() => {
  return heavyCalculation(props.data);
});

// Use createResource for async data fetching
const [nodeData] = createResource(
  () => props.nodeId,
  (nodeId) => fetchNodeMetrics(nodeId),
);

// Avoid unnecessary re-renders with proper signal usage
const [nodes, setNodes] = createSignal<Node[]>([]);
const activeNodeCount = createMemo(
  () => nodes().filter((node) => node.status === 'active').length,
);

// Use lazy loading for large components
const LazyVisualization = lazy(() => import('./HeavyVisualization'));
```

### Accessibility Requirements

```typescript
// All interactive elements must be keyboard accessible
const KeyboardAccessibleButton = (props: ButtonProps) => {
  return (
    <button
      {...props}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          props.onClick?.();
        }
      }}
      role="button"
      tabIndex={0}
      aria-label={props['aria-label']}
    >
      {props.children}
    </button>
  );
};

// Provide screen reader announcements for dynamic content
const announceToScreenReader = (message: string) => {
  const announcer = document.getElementById('aria-live-announcer');
  if (announcer) {
    announcer.textContent = message;
  }
};
```

---

## 🧪 **Testing Guidelines**

### Unit Testing Best Practices

```typescript
// Test pure functions thoroughly
describe('nodeMetricsCalculator', () => {
  test('calculates CPU utilization correctly', () => {
    const metrics = { cpuUsed: 75, cpuTotal: 100 };
    expect(calculateCpuUtilization(metrics)).toBe(0.75);
  });

  test('handles edge cases gracefully', () => {
    expect(calculateCpuUtilization({ cpuUsed: 0, cpuTotal: 0 })).toBe(0);
  });
});

// Test component behavior, not implementation
describe('FabricMap', () => {
  test('renders network topology with correct node count', async () => {
    const nodes = [
      { id: '1', x: 0, y: 0, status: 'active' },
      { id: '2', x: 100, y: 100, status: 'failed' },
    ];

    render(() => <FabricMap nodes={nodes} />);

    expect(screen.getByRole('img', { name: /network topology/i })).toBeInTheDocument();
    expect(screen.getByText('2 nodes')).toBeInTheDocument();
  });
});
```

### E2E Testing Patterns

```typescript
// Test complete user workflows
test('user can select multiple nodes and perform bulk operations', async ({
  page,
}) => {
  await page.goto('/control-panel');

  // Select multiple nodes
  await page.click('[data-testid="node-1"]');
  await page.keyboard.press('Control+click');
  await page.click('[data-testid="node-2"]');

  // Verify selection
  expect(
    await page.locator('[data-testid="selected-count"]').textContent(),
  ).toBe('2 selected');

  // Perform bulk operation
  await page.click('[data-testid="bulk-restart"]');
  await page.click('[data-testid="confirm-action"]');

  // Verify result
  await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
});
```

---

## 🚀 **Performance Guidelines**

### Bundle Size Optimization

- Keep initial bundle < 200KB gzipped
- Use dynamic imports for heavy dependencies
- Implement proper code splitting strategies
- Monitor bundle analyzer reports

### Runtime Performance

- Maintain 120fps rendering in WebGL components
- Keep interaction latency < 16ms
- Use Web Workers for heavy computations
- Implement proper memory management

### Core Web Vitals Compliance

- First Contentful Paint (FCP) < 1.5s
- Largest Contentful Paint (LCP) < 2.5s
- First Input Delay (FID) < 100ms
- Cumulative Layout Shift (CLS) < 0.1

---

## 🛡️ **Security Guidelines**

### Code Security

- Never commit secrets or API keys
- Validate all user inputs
- Use Content Security Policy headers
- Implement proper error handling without information leakage

### Dependency Security

- Run `npm audit` before commits
- Keep dependencies updated
- Use Snyk for vulnerability scanning
- Review third-party packages carefully

---

## 📚 **Documentation Standards**

### Code Documentation

````typescript
/**
 * Calculates the network latency between two nodes using geographical distance
 * and network topology factors.
 *
 * @param sourceNode - The originating network node
 * @param targetNode - The destination network node
 * @param networkTopology - Current network configuration and routing rules
 * @returns Promise resolving to latency in milliseconds, or null if unreachable
 *
 * @example
 * ```typescript
 * const latency = await calculateNetworkLatency(nodeA, nodeB, topology);
 * if (latency !== null) {
 *   console.log(`Latency: ${latency}ms`);
 * }
 * ```
 */
async function calculateNetworkLatency(
  sourceNode: NetworkNode,
  targetNode: NetworkNode,
  networkTopology: NetworkTopology,
): Promise<number | null> {
  // Implementation...
}
````

### README Updates

- Keep README current with latest features
- Include performance benchmarks
- Update installation instructions
- Add troubleshooting guides

### Architecture Decisions

- Document significant technical decisions in ADRs
- Include rationale and trade-offs
- Update when decisions change
- Reference related decisions

---

## 🎯 **Review Process**

### Code Review Checklist

- [ ] **Functionality**: Does the code work as intended?
- [ ] **Performance**: No performance regressions introduced?
- [ ] **Security**: No security vulnerabilities added?
- [ ] **Accessibility**: WCAG 2.2 AAA compliance maintained?
- [ ] **Tests**: Comprehensive test coverage provided?
- [ ] **Documentation**: Adequate documentation included?
- [ ] **Type Safety**: Full TypeScript type coverage?
- [ ] **Style**: Follows project coding standards?

### Review Timeline

- **Small PRs**: 24-48 hours
- **Medium PRs**: 2-3 business days
- **Large PRs**: 1 week (consider breaking into smaller PRs)
- **Hotfixes**: Same day for critical issues

---

## 🏆 **Recognition**

### Contributor Levels

- **First-time Contributor**: Welcome package and mentorship
- **Regular Contributor**: Recognition in release notes
- **Core Contributor**: Direct commit access and decision influence
- **Maintainer**: Full project governance responsibilities

### Ways to Contribute

- 🐛 **Bug Reports**: High-quality issue reports with reproduction steps
- 💡 **Feature Requests**: Well-researched enhancement proposals
- 📝 **Documentation**: Improve guides, tutorials, and API docs
- 🧪 **Testing**: Add test coverage and improve test quality
- 🎨 **Design**: UI/UX improvements and accessibility enhancements
- ⚡ **Performance**: Optimization and benchmark improvements
- 🛡️ **Security**: Security audits and vulnerability fixes

---

## 🤝 **Community Guidelines**

### Code of Conduct

- **Be Respectful**: Treat all contributors with respect and kindness
- **Be Inclusive**: Welcome contributors from all backgrounds and skill levels
- **Be Collaborative**: Work together to build the best possible product
- **Be Professional**: Maintain professional standards in all interactions

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and project discussions
- **Discord**: Real-time chat and community building
- **Email**: Security issues and sensitive communications

---

## 📈 **Project Roadmap**

### Current Focus (v1.x)

- 🎮 Game-inspired interface refinements
- 🧠 AI feature enhancements
- ⚡ Performance optimizations
- 🛡️ Security hardening

### Near-term Goals (v2.x)

- 🌐 Multi-platform support
- 🔄 Real-time collaboration
- 📱 Mobile interface adaptation
- 🎯 Advanced analytics

### Long-term Vision (v3.x+)

- 🤖 Autonomous system management
- 🧬 Neural interface integration
- 🌌 Quantum computing support
- 🔮 Predictive system orchestration

---

**Ready to contribute? Start by exploring our [good first issues](https://github.com/omnitide/control-panel/labels/good%20first%20issue) and join our community!**

For questions, reach out through [GitHub Discussions](https://github.com/omnitide/control-panel/discussions) or join our [Discord community](https://discord.gg/omnitide).

---

<p align="center">
  <strong>🚀 Together, we're building the future of distributed system interfaces! 🚀</strong>
</p>
