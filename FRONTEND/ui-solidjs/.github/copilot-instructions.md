<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Omnitide Control Panel: Advanced Development Instructions

> **Next-Generation Cyberpunk Control Interface Specifications**  
> From: The Architect's Nexus  
> To: Development AI Agents  
> Classification: **BLEEDING-EDGE IMPLEMENTATION GUIDE**

---

## 🎯 **CORE MANDATE**

Implement a **state-of-the-art cyberpunk control interface** that transcends traditional web development boundaries. Every component must embody:

- **⚡ Performance**: 120fps WebGL rendering with sub-16ms interaction latency
- **🧠 Intelligence**: AI-powered features with explainable decision-making
- **🎮 Gaming DNA**: Immersive RTS/RPG interaction patterns
- **🛡️ Enterprise Grade**: Zero-trust security with WCAG 2.2 AAA compliance
- **🚀 Future-Ready**: WebGPU, WebTransport, and emerging web standards

---

## I. **ARCHITECTURAL FOUNDATIONS**

### 🏗️ **Technology Stack (Bleeding-Edge)**

```typescript
// Primary Framework Stack
- Solid.js 1.9+           // Fine-grained reactivity, 10x faster than React
- TypeScript 5.8+         // Latest language features, strict mode
- Vite 6.3+              // Sub-100ms HMR, ES2024 features
- Tailwind CSS 4.1+      // JIT compilation, CSS-in-JS engine

// Graphics & Visualization
- PixiJS 8.11+           // WebGL 2.0 rendering, 120fps performance
- Three.js 0.164+        // 3D graphics, spatial computing
- D3.js 7.9+             // Data visualization, WebGPU acceleration
- WebGPU API             // Compute shaders, next-gen graphics

// Communication & Data
- WebTransport           // HTTP/3 bidirectional streaming
- WebSocket              // Fallback real-time protocol
- Protobuf 3.21+         // Schema evolution, binary serialization
- GraphQL Subscriptions  // Type-safe real-time queries

// AI & Machine Learning
- TensorFlow.js          // Browser ML inference
- Transformers.js        // Natural language processing
- ONNX Runtime          // Cross-platform model execution
- Web Workers           // Background AI processing

// Advanced Web APIs
- Web Audio API         // Spatial audio processing
- Web Speech API        // Voice recognition/synthesis
- Gamepad API          // Controller input, haptic feedback
- Intersection Observer // Viewport optimization
- Web Locks API        // Resource exclusivity
- Broadcast Channel    // Cross-tab communication
```

### 🎨 **Design Philosophy**

```typescript
// Component Architecture: Atomic Design + Domain-Driven
interface ComponentHierarchy {
  atoms: 'Button' | 'Input' | 'Icon'; // Basic building blocks
  molecules: 'SearchBox' | 'NodeCard'; // Simple combinations
  organisms: 'FabricMap' | 'ContextPanel'; // Complex components
  templates: 'ControlPanel' | 'AgentPage'; // Layout structures
  pages: 'MainDashboard' | 'SettingsPage'; // Route components
}

// State Management: Signal-Based Reactivity
const [state, setState] = createStore({
  ui: { selectedNodes: new Set(), camera: { x: 0, y: 0, zoom: 1 } },
  data: { nodes: [], edges: [], agents: [] },
  realtime: { connected: false, latency: 0 },
  ai: { anomalies: [], predictions: [], insights: [] },
});

// Performance: Zero-Cost Abstractions
const selectedNodeData = createMemo(() =>
  state.data.nodes.filter((node) => state.ui.selectedNodes.has(node.id)),
);
```

---

## II. **GAME METAPHOR IMPLEMENTATION**

### 🏢 **Fallout Shelter: "The Apartment Complex"**

```typescript
// Multi-level facility rendering with spatial indexing
interface FacilityView {
  levels: ComputeLevel[]; // Vertical layers (basement to penthouse)
  rooms: ComputeNode[]; // Individual processing units
  infrastructure: Pipeline[]; // Resource distribution systems
  atmosphere: AmbientEffect[]; // Environmental effects

  // Zoom levels: Building → Floor → Room → Process
  lodStrategy: 'geometric' | 'semantic' | 'adaptive';
  cullingDistance: number; // Frustum culling for performance
}

// Visual Design Language
const shelterAesthetics = {
  lighting: 'atmospheric-industrial', // Moody industrial lighting
  materials: 'concrete-steel-glass', // Brutalist architecture
  colors: 'muted-earth-neon-accents', // Earthy base with neon highlights
  animations: 'mechanical-precision', // Precise, mechanical movements
};
```

### 🚀 **FTL: "The Starship"**

```typescript
// Bridge-style command interface
interface StarshipBridge {
  stations: {
    helm: NavigationControls; // System navigation
    tactical: WeaponsControls; // Security operations
    engineering: PowerManagement; // Resource allocation
    science: DataAnalysis; // AI insights
    communications: NetworkComms; // External connections
  };

  // Power distribution with real-time constraints
  powerGrid: {
    total: 100;
    allocation: Record<SystemType, number>;
    constraints: { minimum: Record<SystemType, number> };
  };

  // Spatial audio for immersive bridge environment
  ambientAudio: {
    engineHum: SpatialAudioSource;
    computerChatter: RandomAudioEvents;
    alertSystems: PriorityAudioQueue;
  };
}
```

### ⚔️ **StarCraft II: "RTS Command Center"**

```typescript
// Real-time strategy interface patterns
interface RTSInterface {
  viewport: {
    camera: Camera3D; // Main tactical view
    selection: SelectionManager; // Multi-unit selection
    commands: CommandQueue; // Queued actions
  };

  controls: {
    hotkeys: HotkeySystem; // Customizable shortcuts
    gestures: GestureRecognition; // Touch/mouse gestures
    voice: VoiceCommands; // Speech recognition
  };

  // Command card with context-sensitive actions
  commandCard: {
    actions: ContextAction[]; // Available operations
    macros: SavedMacroSet[]; // Recorded command sequences
    suggestions: AIRecommendation[]; // ML-powered suggestions
  };
}
```

---

## III. **COMPONENT SPECIFICATIONS**

### 🗺️ **FabricMap (Primary Interface)**

```typescript
// WebGL-accelerated network visualization
interface FabricMapFeatures {
  rendering: {
    engine: 'PixiJS 8.11+';
    performance: '120fps sustained';
    capacity: '10,000+ nodes';
    effects: 'particle systems, shaders, instancing';
  };

  interaction: {
    selection: 'box, lasso, intelligent clustering';
    navigation: 'infinite zoom, smooth pan, bookmarks';
    manipulation: 'drag-drop, multi-select, bulk operations';
  };

  visualization: {
    layouts: 'force-directed, hierarchical, circular, custom';
    clustering: 'automatic grouping, manual categories';
    animation: 'smooth transitions, physics simulation';
    highlighting: 'search results, paths, relationships';
  };

  ai_features: {
    anomaly_detection: 'real-time pattern recognition';
    prediction: 'resource usage forecasting';
    optimization: 'layout suggestions, performance hints';
  };
}

// Implementation requirements
const fabricMapImplementation = {
  // Spatial indexing for O(log n) collision detection
  spatialIndex: new Octree({ maxObjects: 10, maxLevels: 8 }),

  // WebGL 2.0 with instanced rendering
  renderer: new PIXI.Renderer({
    powerPreference: 'high-performance',
    antialias: true,
    resolution: devicePixelRatio,
  }),

  // Physics simulation for dynamic layouts
  physicsEngine: new ForceSimulation({
    nodes: nodeArray,
    forces: ['center', 'charge', 'link', 'collision'],
  }),
};
```

### 📊 **ContextPanel (AI-Enhanced Information Display)**

```typescript
interface ContextPanelFeatures {
  content: {
    realtime_metrics: 'CPU, memory, network, custom KPIs';
    ai_insights: 'anomaly explanations, recommendations';
    predictive_analytics: 'capacity planning, performance trends';
    natural_language: 'plain English summaries, voice synthesis';
  };

  interaction: {
    drill_down: 'hierarchical data exploration';
    time_travel: 'historical data comparison';
    collaboration: 'shared annotations, team insights';
    export: 'PDF reports, CSV data, API endpoints';
  };

  visualization: {
    charts: 'real-time line, bar, scatter, heatmap';
    sparklines: 'micro-visualizations, trend indicators';
    gauges: 'circular progress, linear meters';
    alerts: 'threshold breaches, visual warnings';
  };
}
```

### 🔔 **NotificationFeed (Intelligent Alert System)**

```typescript
interface NotificationFeatures {
  intelligence: {
    classification: 'ML-powered severity scoring';
    filtering: 'smart noise reduction, user preferences';
    clustering: 'related event grouping';
    summarization: 'natural language event summaries';
  };

  interaction: {
    keyboard_nav: 'arrow keys, vim bindings, custom shortcuts';
    bulk_actions: 'mark all read, batch dismiss, archive';
    voice_synthesis: 'accessibility, hands-free operation';
    contextual_actions: 'quick fixes, investigation tools';
  };

  performance: {
    virtualization: 'only render visible items';
    pagination: 'infinite scroll, smart batching';
    caching: 'LRU cache with TTL expiration';
    compression: 'efficient data structures';
  };
}
```

### 💬 **UniversalCommandLine (NLP Interface)**

```typescript
interface CommandLineFeatures {
  nlp: {
    intent_recognition: 'transformer-based parsing';
    auto_completion: 'context-aware suggestions';
    error_correction: 'fuzzy matching, spell check';
    syntax_highlighting: 'real-time command validation';
  };

  capabilities: {
    system_control: 'agent management, resource allocation';
    data_queries: 'natural language to GraphQL/SQL';
    workflow_automation: 'macro recording, scheduling';
    help_system: 'contextual documentation, examples';
  };

  advanced: {
    voice_input: 'speech-to-text with noise cancellation';
    gesture_shortcuts: 'mouse/touch gesture recognition';
    collaborative_editing: 'shared command sessions';
    history_intelligence: 'smart command history search';
  };
}
```

---

## IV. **PERFORMANCE REQUIREMENTS**

### ⚡ **Core Web Vitals Targets**

```typescript
const performanceTargets = {
  FCP: '<1.5s', // First Contentful Paint
  LCP: '<2.5s', // Largest Contentful Paint
  FID: '<100ms', // First Input Delay
  CLS: '<0.1', // Cumulative Layout Shift
  TTFB: '<600ms', // Time to First Byte

  // Custom metrics
  interactionLatency: '<16ms', // UI response time
  frameRate: '120fps', // Rendering performance
  memoryUsage: '<128MB', // Heap size limit
  bundleSize: '<200KB', // Initial bundle gzipped
};
```

### 🚀 **Optimization Strategies**

```typescript
// Code splitting with intelligent chunking
const chunkingStrategy = {
  vendor: ['solid-js', 'solid-router'],
  visualization: ['pixi.js', 'd3', 'three'],
  ai: ['@tensorflow/tfjs', '@huggingface/transformers'],
  utils: ['protobufjs', 'date-fns', 'lodash-es'],
};

// WebGL performance optimization
const webglOptimizations = {
  // Instanced rendering for repeated geometry
  instancedRendering: true,

  // Frustum culling for off-screen objects
  frustumCulling: true,

  // Level-of-detail for distant objects
  lodRendering: { near: 'high', medium: 'mid', far: 'low' },

  // Texture atlasing for reduced draw calls
  textureAtlasing: { maxSize: 2048, padding: 2 },
};
```

---

## V. **ACCESSIBILITY & INCLUSION**

### ♿ **WCAG 2.2 AAA Compliance**

```typescript
interface AccessibilityFeatures {
  visual: {
    high_contrast: 'automatic detection, manual toggle';
    color_blind: 'protanopia, deuteranopia, tritanopia support';
    zoom: '500% zoom without horizontal scrolling';
    fonts: 'dyslexia-friendly typefaces, size adjustment';
  };

  motor: {
    keyboard_only: 'full navigation without mouse';
    voice_control: 'speech recognition for all actions';
    eye_tracking: 'gaze-based interaction (future)';
    switch_access: 'single/dual switch compatibility';
  };

  cognitive: {
    simplified_ui: 'reduced complexity mode';
    help_system: 'contextual assistance, tutorials';
    error_prevention: 'confirmation dialogs, undo actions';
    consistent_navigation: 'predictable interaction patterns';
  };

  auditory: {
    captions: 'visual representation of audio feedback';
    sign_language: 'ASL/BSL video interpretation (future)';
    haptic_feedback: 'tactile alternatives to audio cues';
    visual_alerts: 'screen flash, color changes for alerts';
  };
}
```

### 🌐 **Internationalization (i18n)**

```typescript
const i18nSupport = {
  languages: ['en', 'es', 'fr', 'de', 'ja', 'zh', 'ar', 'hi'],
  rtl_support: true, // Right-to-left languages
  locale_aware: {
    numbers: 'currency, decimal formats',
    dates: 'timezone, calendar systems',
    sorting: 'locale-specific collation',
  },
  dynamic_loading: 'lazy load translation bundles',
  fallback_strategy: 'graceful degradation to English',
};
```

---

## VI. **SECURITY & COMPLIANCE**

### 🛡️ **Zero-Trust Architecture**

```typescript
interface SecurityRequirements {
  authentication: {
    multi_factor: 'TOTP, WebAuthn, biometrics';
    session_management: 'JWT with refresh rotation';
    device_binding: 'hardware fingerprinting';
  };

  encryption: {
    in_transit: 'TLS 1.3, certificate pinning';
    at_rest: 'AES-256, key rotation';
    end_to_end: 'WebRTC for peer communications';
  };

  content_security: {
    csp_level_3: 'nonce-based script execution';
    sri: 'subresource integrity for all assets';
    cors: 'strict origin policies';
    headers: 'security headers for all responses';
  };

  monitoring: {
    intrusion_detection: 'behavioral analysis';
    audit_logging: 'immutable event records';
    vulnerability_scanning: 'automated dependency checks';
    penetration_testing: 'regular security assessments';
  };
}
```

---

## VII. **DEVELOPMENT STANDARDS**

### 📝 **Code Quality Requirements**

```typescript
const qualityStandards = {
  typescript: {
    strict: true,                    // Strict mode enabled
    noImplicitAny: true,            // No implicit any types
    exactOptionalPropertyTypes: true, // Exact optional properties
    noUncheckedIndexedAccess: true   // Safe index access
  },

  testing: {
    coverage: '>95%',               // Minimum test coverage
    unit: 'Vitest with jsdom',      // Fast unit testing
    integration: 'Testing Library', // Component testing
    e2e: 'Playwright cross-browser', // End-to-end testing
    visual: 'Percy/Chromatic'       // Visual regression
  },

  linting: {
    eslint: 'flat config, accessibility rules',
    prettier: 'consistent formatting',
    commitlint: 'conventional commits',
    husky: 'pre-commit hooks'
  },

  documentation: {
    inline: 'TSDoc comments for all public APIs',
    architecture: 'ADR (Architecture Decision Records)',
    api: 'OpenAPI/GraphQL schemas',
    user: 'Interactive tutorials, video guides'
  };
};
```

### 🚀 **CI/CD Pipeline**

```yaml
# .github/workflows/ci.yml
name: Continuous Integration
on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - name: Type check
        run: pnpm type-check

      - name: Lint check
        run: pnpm lint:check

      - name: Format check
        run: pnpm format:check

      - name: Unit tests
        run: pnpm test:coverage

      - name: E2E tests
        run: pnpm e2e

      - name: Performance audit
        run: pnpm perf:ci

      - name: Security scan
        run: pnpm audit && npx snyk test

      - name: Visual regression
        run: pnpm test:visual
```

---

## VIII. **FUTURE-PROOFING**

### 🔮 **Emerging Technologies**

```typescript
interface FutureTechnologies {
  webgpu: {
    compute_shaders: 'physics simulation, ML inference';
    advanced_graphics: 'ray tracing, global illumination';
    parallel_processing: 'massive data computations';
  };

  ai_integration: {
    local_models: 'on-device inference, privacy-first';
    federated_learning: 'collaborative model training';
    neural_interfaces: 'brain-computer interaction (future)';
  };

  spatial_computing: {
    webxr: 'AR/VR interfaces with hand tracking';
    holographic: 'hologram projection support';
    spatial_audio: '3D positional audio rendering';
  };

  quantum_computing: {
    visualization: 'quantum state representation';
    algorithms: 'quantum-inspired optimization';
    networking: 'quantum key distribution';
  };
}
```

---

## 🎯 **IMPLEMENTATION CHECKLIST**

### ✅ **Must-Have Features**

- [ ] WebGL 2.0 rendering with 120fps performance
- [ ] Signal-based reactive state management
- [ ] Real-time WebTransport/WebSocket communication
- [ ] AI-powered anomaly detection and insights
- [ ] Natural language command interface
- [ ] WCAG 2.2 AAA accessibility compliance
- [ ] Zero-trust security architecture
- [ ] Cross-browser E2E testing suite
- [ ] Performance monitoring and optimization
- [ ] Progressive Web App capabilities

### 🚀 **Nice-to-Have Features**

- [ ] WebGPU compute shader acceleration
- [ ] Voice command recognition
- [ ] Haptic feedback for controllers
- [ ] Spatial audio positioning
- [ ] AR/VR interface extensions
- [ ] Collaborative real-time editing
- [ ] Machine learning model training
- [ ] Quantum computing visualization

---

## 📚 **REFERENCE ARCHITECTURE**

See detailed implementation guides:

- [OMNITIDE_CODEX.md](./OMNITIDE_CODEX.md) - Comprehensive design specification
- [docs/ADR.md](./docs/ADR.md) - Architecture decision records
- [docs/PERFORMANCE.md](./docs/PERFORMANCE.md) - Performance optimization guide
- [PROJECT_STATUS.md](./PROJECT_STATUS.md) - Current implementation status

---

**REMEMBER: Every component must feel like it belongs in a cyberpunk future while delivering enterprise-grade reliability and performance. We're not just building a control panel—we're crafting the command center for the next generation of distributed computing.**

<p align="center">
  <strong>🎮 Gaming DNA | 🧠 AI-Enhanced | ⚡ Performance-First | 🛡️ Security-Hardened</strong>
</p>
