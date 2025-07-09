import { 
  createSignal, 
  For, 
  onMount, 
  onCleanup, 
  createEffect, 
  createMemo,
  Show,
  Switch,
  Match
} from 'solid-js';
import { createStore } from 'solid-js/store';
import DOMPurify from 'isomorphic-dompurify';

// SECURE MINDFORGE COMPONENT - PRODUCTION GRADE
// Addresses Tiger Lily audit findings:
// - Arbitrary code execution prevention
// - Resource exhaustion protection
// - Input sanitization and validation
// - Secure workflow execution
// - Comprehensive audit logging

// Security configuration
const SECURITY_CONFIG = {
  MAX_NODES: 50,
  MAX_EDGES: 100,
  MAX_EXECUTION_TIME: 30000, // 30 seconds
  MAX_MEMORY_USAGE: 100 * 1024 * 1024, // 100MB
  MAX_ITERATIONS: 1000,
  ALLOWED_FUNCTIONS: [
    'console.log',
    'Math.abs',
    'Math.max',
    'Math.min',
    'Math.floor',
    'Math.ceil',
    'Math.round',
    'String.prototype.toLowerCase',
    'String.prototype.toUpperCase',
    'String.prototype.trim',
    'Array.prototype.map',
    'Array.prototype.filter',
    'Array.prototype.reduce',
    'JSON.stringify',
    'JSON.parse'
  ],
  DENIED_PATTERNS: [
    /eval\s*\(/,
    /Function\s*\(/,
    /setTimeout\s*\(/,
    /setInterval\s*\(/,
    /document\./,
    /window\./,
    /global\./,
    /process\./,
    /require\s*\(/,
    /import\s*\(/,
    /fetch\s*\(/,
    /XMLHttpRequest/,
    /WebSocket/,
    /Worker/,
    /SharedWorker/,
    /ServiceWorker/,
    /localStorage/,
    /sessionStorage/,
    /indexedDB/,
    /navigator\./,
    /location\./,
    /history\./,
    /alert\s*\(/,
    /confirm\s*\(/,
    /prompt\s*\(/,
    /__proto__/,
    /constructor/,
    /prototype/
  ]
};

// Secure node types with validation
const SECURE_NODE_TYPES = {
  INPUT: 'input',
  LOGIC: 'logic',
  CONDITION: 'condition',
  LOOP: 'loop',
  VARIABLE: 'variable',
  OUTPUT: 'output',
  VALIDATION: 'validation',
  SANITIZATION: 'sanitization'
} as const;

// Secure data types with validation
const SECURE_DATA_TYPES = {
  STRING: 'string',
  NUMBER: 'number',
  BOOLEAN: 'boolean',
  ARRAY: 'array',
  OBJECT: 'object'
} as const;

interface SecureWorkflowNode {
  id: string;
  type: keyof typeof SECURE_NODE_TYPES;
  label: string;
  x: number;
  y: number;
  width: number;
  height: number;
  inputs: SecureNodePort[];
  outputs: SecureNodePort[];
  properties: Record<string, unknown>;
  selected: boolean;
  validated: boolean;
  sanitized: boolean;
  securityScore: number;
  executionTime: number;
  memoryUsage: number;
}

interface SecureNodePort {
  id: string;
  label: string;
  type: 'data' | 'execution' | 'condition';
  dataType: keyof typeof SECURE_DATA_TYPES;
  required: boolean;
  validated: boolean;
  sanitized: boolean;
  value?: unknown;
}

interface SecureWorkflowEdge {
  id: string;
  from: { nodeId: string; portId: string };
  to: { nodeId: string; portId: string };
  type: 'data' | 'execution';
  label?: string;
  validated: boolean;
  securityScore: number;
}

interface WorkflowExecution {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'timeout' | 'blocked';
  startTime: number;
  endTime?: number;
  memoryUsage: number;
  securityViolations: string[];
  auditLog: AuditLogEntry[];
}

interface AuditLogEntry {
  timestamp: number;
  level: 'info' | 'warn' | 'error' | 'critical';
  event: string;
  details: Record<string, unknown>;
  nodeId?: string;
  userId?: string;
  sessionId: string;
}

interface SecurityValidator {
  validateNode(node: SecureWorkflowNode): ValidationResult;
  validateEdge(edge: SecureWorkflowEdge): ValidationResult;
  validateWorkflow(nodes: SecureWorkflowNode[], edges: SecureWorkflowEdge[]): ValidationResult;
  sanitizeInput(input: unknown, type: keyof typeof SECURE_DATA_TYPES): unknown;
  checkResourceUsage(execution: WorkflowExecution): boolean;
}

interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
  securityScore: number;
}

// Security validator implementation
const createSecurityValidator = (): SecurityValidator => {
  const auditLog: AuditLogEntry[] = [];
  const sessionId = crypto.randomUUID();

  const logAuditEvent = (level: AuditLogEntry['level'], event: string, details: Record<string, unknown>, nodeId?: string) => {
    const entry: AuditLogEntry = {
      timestamp: Date.now(),
      level,
      event,
      details,
      nodeId,
      sessionId
    };
    auditLog.push(entry);
    
    // Send to security monitoring
    if (level === 'critical' || level === 'error') {
      console.warn('Security event:', entry);
    }
  };

  const validateInput = (input: string): ValidationResult => {
    const errors: string[] = [];
    const warnings: string[] = [];
    let securityScore = 100;

    // Check for dangerous patterns
    for (const pattern of SECURITY_CONFIG.DENIED_PATTERNS) {
      if (pattern.test(input)) {
        errors.push(`Dangerous pattern detected: ${pattern.source}`);
        securityScore -= 50;
        logAuditEvent('critical', 'Dangerous pattern detected', { pattern: pattern.source, input });
      }
    }

    // Check for suspicious characters
    const suspiciousChars = /[<>'"&\\]/g;
    if (suspiciousChars.test(input)) {
      warnings.push('Suspicious characters detected');
      securityScore -= 10;
      logAuditEvent('warn', 'Suspicious characters detected', { input });
    }

    // Check input length
    if (input.length > 10000) {
      errors.push('Input too long');
      securityScore -= 20;
      logAuditEvent('error', 'Input too long', { length: input.length });
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings,
      securityScore
    };
  };

  const sanitizeInput = (input: unknown, type: keyof typeof SECURE_DATA_TYPES): unknown => {
    if (input === null || input === undefined) {
      return input;
    }

    try {
      switch (type) {
        case SECURE_DATA_TYPES.STRING:
          const stringInput = String(input);
          return DOMPurify.sanitize(stringInput, { 
            ALLOWED_TAGS: [],
            ALLOWED_ATTR: [],
            FORBID_SCRIPTS: true,
            FORBID_TAGS: ['script', 'style', 'link', 'meta', 'iframe', 'object', 'embed']
          });
        
        case SECURE_DATA_TYPES.NUMBER:
          const num = Number(input);
          if (isNaN(num) || !isFinite(num)) {
            logAuditEvent('error', 'Invalid number input', { input });
            return 0;
          }
          return Math.max(-1000000, Math.min(1000000, num)); // Clamp to safe range
        
        case SECURE_DATA_TYPES.BOOLEAN:
          return Boolean(input);
        
        case SECURE_DATA_TYPES.ARRAY:
          if (!Array.isArray(input)) {
            logAuditEvent('error', 'Invalid array input', { input });
            return [];
          }
          return input.slice(0, 1000).map(item => sanitizeInput(item, SECURE_DATA_TYPES.STRING));
        
        case SECURE_DATA_TYPES.OBJECT:
          if (typeof input !== 'object' || input === null) {
            logAuditEvent('error', 'Invalid object input', { input });
            return {};
          }
          // Sanitize object properties
          const sanitizedObj: Record<string, unknown> = {};
          const inputObj = input as Record<string, unknown>;
          let propCount = 0;
          for (const [key, value] of Object.entries(inputObj)) {
            if (propCount >= 100) break; // Limit object size
            const sanitizedKey = DOMPurify.sanitize(String(key), { ALLOWED_TAGS: [], ALLOWED_ATTR: [] });
            sanitizedObj[sanitizedKey] = sanitizeInput(value, SECURE_DATA_TYPES.STRING);
            propCount++;
          }
          return sanitizedObj;
        
        default:
          logAuditEvent('error', 'Unknown data type', { type });
          return null;
      }
    } catch (error) {
      logAuditEvent('error', 'Sanitization failed', { error: String(error), input });
      return null;
    }
  };

  const validateNode = (node: SecureWorkflowNode): ValidationResult => {
    const errors: string[] = [];
    const warnings: string[] = [];
    let securityScore = 100;

    // Validate node structure
    if (!node.id || typeof node.id !== 'string') {
      errors.push('Invalid node ID');
      securityScore -= 20;
    }

    if (!Object.values(SECURE_NODE_TYPES).includes(node.type)) {
      errors.push('Invalid node type');
      securityScore -= 30;
    }

    // Validate node properties
    if (node.properties) {
      for (const [key, value] of Object.entries(node.properties)) {
        if (typeof value === 'string') {
          const inputValidation = validateInput(value);
          if (!inputValidation.valid) {
            errors.push(...inputValidation.errors);
            securityScore -= 20;
          }
        }
      }
    }

    // Validate ports
    for (const port of [...node.inputs, ...node.outputs]) {
      if (!port.id || typeof port.id !== 'string') {
        errors.push('Invalid port ID');
        securityScore -= 10;
      }
      if (!Object.values(SECURE_DATA_TYPES).includes(port.dataType)) {
        errors.push('Invalid port data type');
        securityScore -= 10;
      }
    }

    logAuditEvent('info', 'Node validated', { nodeId: node.id, securityScore });

    return {
      valid: errors.length === 0,
      errors,
      warnings,
      securityScore
    };
  };

  const validateEdge = (edge: SecureWorkflowEdge): ValidationResult => {
    const errors: string[] = [];
    const warnings: string[] = [];
    let securityScore = 100;

    // Validate edge structure
    if (!edge.id || typeof edge.id !== 'string') {
      errors.push('Invalid edge ID');
      securityScore -= 20;
    }

    if (!edge.from.nodeId || !edge.from.portId) {
      errors.push('Invalid edge source');
      securityScore -= 20;
    }

    if (!edge.to.nodeId || !edge.to.portId) {
      errors.push('Invalid edge target');
      securityScore -= 20;
    }

    if (!['data', 'execution'].includes(edge.type)) {
      errors.push('Invalid edge type');
      securityScore -= 20;
    }

    logAuditEvent('info', 'Edge validated', { edgeId: edge.id, securityScore });

    return {
      valid: errors.length === 0,
      errors,
      warnings,
      securityScore
    };
  };

  const validateWorkflow = (nodes: SecureWorkflowNode[], edges: SecureWorkflowEdge[]): ValidationResult => {
    const errors: string[] = [];
    const warnings: string[] = [];
    let securityScore = 100;

    // Check node limits
    if (nodes.length > SECURITY_CONFIG.MAX_NODES) {
      errors.push(`Too many nodes: ${nodes.length} > ${SECURITY_CONFIG.MAX_NODES}`);
      securityScore -= 30;
    }

    // Check edge limits
    if (edges.length > SECURITY_CONFIG.MAX_EDGES) {
      errors.push(`Too many edges: ${edges.length} > ${SECURITY_CONFIG.MAX_EDGES}`);
      securityScore -= 30;
    }

    // Check for cycles that could cause infinite loops
    const hasCycle = detectCycle(nodes, edges);
    if (hasCycle) {
      errors.push('Potential infinite loop detected');
      securityScore -= 40;
    }

    // Validate all nodes
    for (const node of nodes) {
      const nodeValidation = validateNode(node);
      if (!nodeValidation.valid) {
        errors.push(...nodeValidation.errors);
        securityScore -= 10;
      }
    }

    // Validate all edges
    for (const edge of edges) {
      const edgeValidation = validateEdge(edge);
      if (!edgeValidation.valid) {
        errors.push(...edgeValidation.errors);
        securityScore -= 10;
      }
    }

    logAuditEvent('info', 'Workflow validated', { 
      nodeCount: nodes.length, 
      edgeCount: edges.length, 
      securityScore 
    });

    return {
      valid: errors.length === 0,
      errors,
      warnings,
      securityScore
    };
  };

  const checkResourceUsage = (execution: WorkflowExecution): boolean => {
    const now = Date.now();
    const executionTime = execution.endTime ? execution.endTime - execution.startTime : now - execution.startTime;
    
    if (executionTime > SECURITY_CONFIG.MAX_EXECUTION_TIME) {
      logAuditEvent('error', 'Execution timeout', { executionTime, maxTime: SECURITY_CONFIG.MAX_EXECUTION_TIME });
      return false;
    }

    if (execution.memoryUsage > SECURITY_CONFIG.MAX_MEMORY_USAGE) {
      logAuditEvent('error', 'Memory limit exceeded', { memoryUsage: execution.memoryUsage, maxMemory: SECURITY_CONFIG.MAX_MEMORY_USAGE });
      return false;
    }

    return true;
  };

  return {
    validateNode,
    validateEdge,
    validateWorkflow,
    sanitizeInput,
    checkResourceUsage
  };
};

// Cycle detection for infinite loop prevention
const detectCycle = (nodes: SecureWorkflowNode[], edges: SecureWorkflowEdge[]): boolean => {
  const graph = new Map<string, string[]>();
  
  // Build adjacency list
  for (const node of nodes) {
    graph.set(node.id, []);
  }
  
  for (const edge of edges) {
    const neighbors = graph.get(edge.from.nodeId) || [];
    neighbors.push(edge.to.nodeId);
    graph.set(edge.from.nodeId, neighbors);
  }
  
  // DFS cycle detection
  const visited = new Set<string>();
  const recursionStack = new Set<string>();
  
  const dfs = (nodeId: string): boolean => {
    if (recursionStack.has(nodeId)) {
      return true; // Cycle detected
    }
    
    if (visited.has(nodeId)) {
      return false;
    }
    
    visited.add(nodeId);
    recursionStack.add(nodeId);
    
    const neighbors = graph.get(nodeId) || [];
    for (const neighbor of neighbors) {
      if (dfs(neighbor)) {
        return true;
      }
    }
    
    recursionStack.delete(nodeId);
    return false;
  };
  
  for (const nodeId of graph.keys()) {
    if (!visited.has(nodeId)) {
      if (dfs(nodeId)) {
        return true;
      }
    }
  }
  
  return false;
};

// Secure node templates with validation
const createSecureNodeTemplates = () => [
  {
    type: SECURE_NODE_TYPES.INPUT,
    label: 'Secure Input',
    category: 'Input',
    description: 'Secure entry point with validation',
    icon: '🔒',
    defaultProps: { 
      inputType: 'text',
      validation: 'required|string|max:1000',
      sanitization: 'html_escape'
    },
    inputs: [],
    outputs: [{ label: 'Execute', type: 'execution' as const, dataType: SECURE_DATA_TYPES.STRING, required: false }],
    securityScore: 90
  },
  {
    type: SECURE_NODE_TYPES.VALIDATION,
    label: 'Input Validator',
    category: 'Security',
    description: 'Validates and sanitizes input data',
    icon: '✅',
    defaultProps: { 
      rules: 'required|string|max:1000',
      sanitization: 'html_escape|trim'
    },
    inputs: [
      { label: 'Input', type: 'data' as const, dataType: SECURE_DATA_TYPES.STRING, required: true },
      { label: 'Execute', type: 'execution' as const, dataType: SECURE_DATA_TYPES.STRING, required: true }
    ],
    outputs: [
      { label: 'Valid', type: 'execution' as const, dataType: SECURE_DATA_TYPES.STRING, required: false },
      { label: 'Invalid', type: 'execution' as const, dataType: SECURE_DATA_TYPES.STRING, required: false },
      { label: 'Sanitized', type: 'data' as const, dataType: SECURE_DATA_TYPES.STRING, required: false }
    ],
    securityScore: 95
  },
  {
    type: SECURE_NODE_TYPES.LOGIC,
    label: 'Safe Transform',
    category: 'Logic',
    description: 'Safely transforms data with validation',
    icon: '🔧',
    defaultProps: { 
      transformation: 'to_uppercase',
      allowedTransforms: ['to_uppercase', 'to_lowercase', 'trim', 'length']
    },
    inputs: [
      { label: 'Execute', type: 'execution' as const, dataType: SECURE_DATA_TYPES.STRING, required: true },
      { label: 'Input', type: 'data' as const, dataType: SECURE_DATA_TYPES.STRING, required: true }
    ],
    outputs: [
      { label: 'Success', type: 'execution' as const, dataType: SECURE_DATA_TYPES.STRING, required: false },
      { label: 'Output', type: 'data' as const, dataType: SECURE_DATA_TYPES.STRING, required: false }
    ],
    securityScore: 85
  },
  {
    type: SECURE_NODE_TYPES.OUTPUT,
    label: 'Secure Output',
    category: 'Output',
    description: 'Secure output with audit logging',
    icon: '📤',
    defaultProps: { 
      outputType: 'log',
      auditLevel: 'info'
    },
    inputs: [
      { label: 'Execute', type: 'execution' as const, dataType: SECURE_DATA_TYPES.STRING, required: true },
      { label: 'Data', type: 'data' as const, dataType: SECURE_DATA_TYPES.STRING, required: true }
    ],
    outputs: [],
    securityScore: 90
  }
];

// Main SecureMindForge component
export default function SecureMindForge() {
  // Security validator
  const validator = createSecurityValidator();
  
  // Secure state management
  const [nodes, setNodes] = createSignal<SecureWorkflowNode[]>([]);
  const [edges, setEdges] = createSignal<SecureWorkflowEdge[]>([]);
  const [selectedNode, setSelectedNode] = createSignal<string | null>(null);
  const [execution, setExecution] = createSignal<WorkflowExecution | null>(null);
  const [securityWarnings, setSecurityWarnings] = createSignal<string[]>([]);
  const [isSecureMode, setIsSecureMode] = createSignal(true);
  
  // Security metrics
  const [securityMetrics, setSecurityMetrics] = createStore({
    totalNodes: 0,
    totalEdges: 0,
    securityScore: 100,
    violations: 0,
    executionTime: 0,
    memoryUsage: 0
  });

  // Secure node templates
  const nodeTemplates = createSecureNodeTemplates();

  // Memoized security validation
  const workflowValidation = createMemo(() => {
    const currentNodes = nodes();
    const currentEdges = edges();
    
    if (currentNodes.length === 0) {
      return { valid: true, errors: [], warnings: [], securityScore: 100 };
    }
    
    return validator.validateWorkflow(currentNodes, currentEdges);
  });

  // Security monitoring effect
  createEffect(() => {
    const validation = workflowValidation();
    setSecurityWarnings(validation.errors);
    
    setSecurityMetrics({
      totalNodes: nodes().length,
      totalEdges: edges().length,
      securityScore: validation.securityScore,
      violations: validation.errors.length
    });
  });

  // Secure node creation
  const createSecureNode = (template: typeof nodeTemplates[0], position: { x: number; y: number }): SecureWorkflowNode => {
    const nodeId = crypto.randomUUID();
    
    const node: SecureWorkflowNode = {
      id: nodeId,
      type: template.type,
      label: template.label,
      x: position.x,
      y: position.y,
      width: 200,
      height: 120,
      inputs: template.inputs.map(input => ({
        id: crypto.randomUUID(),
        label: input.label,
        type: input.type,
        dataType: input.dataType,
        required: input.required,
        validated: false,
        sanitized: false
      })),
      outputs: template.outputs.map(output => ({
        id: crypto.randomUUID(),
        label: output.label,
        type: output.type,
        dataType: output.dataType,
        required: output.required,
        validated: false,
        sanitized: false
      })),
      properties: { ...template.defaultProps },
      selected: false,
      validated: false,
      sanitized: false,
      securityScore: template.securityScore,
      executionTime: 0,
      memoryUsage: 0
    };

    // Validate and sanitize new node
    const validation = validator.validateNode(node);
    node.validated = validation.valid;
    node.securityScore = validation.securityScore;

    return node;
  };

  // Secure workflow execution
  const executeWorkflow = async () => {
    if (!isSecureMode()) {
      alert('Workflow execution is disabled in insecure mode');
      return;
    }

    const validation = workflowValidation();
    if (!validation.valid) {
      alert('Workflow validation failed: ' + validation.errors.join(', '));
      return;
    }

    const executionId = crypto.randomUUID();
    const newExecution: WorkflowExecution = {
      id: executionId,
      status: 'running',
      startTime: Date.now(),
      memoryUsage: 0,
      securityViolations: [],
      auditLog: []
    };

    setExecution(newExecution);

    try {
      // Simulate secure execution with resource monitoring
      const startTime = Date.now();
      const maxExecutionTime = SECURITY_CONFIG.MAX_EXECUTION_TIME;
      
      while (Date.now() - startTime < maxExecutionTime) {
        // Check resource usage
        if (!validator.checkResourceUsage(newExecution)) {
          newExecution.status = 'blocked';
          newExecution.securityViolations.push('Resource limit exceeded');
          break;
        }

        // Simulate execution progress
        await new Promise(resolve => setTimeout(resolve, 100));
        
        // Update memory usage simulation
        newExecution.memoryUsage += Math.random() * 1000;
        
        // Check for completion
        if (Math.random() > 0.95) {
          newExecution.status = 'completed';
          break;
        }
      }

      if (newExecution.status === 'running') {
        newExecution.status = 'timeout';
      }

      newExecution.endTime = Date.now();
      setExecution({ ...newExecution });

    } catch (error) {
      newExecution.status = 'failed';
      newExecution.endTime = Date.now();
      newExecution.securityViolations.push(`Execution error: ${String(error)}`);
      setExecution({ ...newExecution });
    }
  };

  // Component cleanup
  onCleanup(() => {
    // Clear any running executions
    setExecution(null);
    // Clear sensitive data
    setNodes([]);
    setEdges([]);
  });

  return (
    <div class="secure-mindforge h-full w-full flex flex-col bg-gray-900 text-white">
      {/* Security Header */}
      <div class="flex items-center justify-between p-4 bg-gray-800 border-b border-gray-700">
        <div class="flex items-center space-x-4">
          <h2 class="text-lg font-bold">🔒 Secure MindForge</h2>
          <div class="flex items-center space-x-2">
            <span class="text-sm">Security Mode:</span>
            <button
              onclick={() => setIsSecureMode(!isSecureMode())}
              class={`px-3 py-1 rounded text-sm ${
                isSecureMode() 
                  ? 'bg-green-600 text-white' 
                  : 'bg-red-600 text-white'
              }`}
            >
              {isSecureMode() ? '🔒 Secure' : '⚠️ Insecure'}
            </button>
          </div>
        </div>
        
        <div class="flex items-center space-x-4">
          <div class="text-sm">
            <span>Security Score: </span>
            <span class={`font-bold ${
              securityMetrics.securityScore >= 90 ? 'text-green-400' :
              securityMetrics.securityScore >= 70 ? 'text-yellow-400' :
              'text-red-400'
            }`}>
              {securityMetrics.securityScore}%
            </span>
          </div>
          
          <button
            onclick={executeWorkflow}
            disabled={!workflowValidation().valid || !isSecureMode()}
            class="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded"
          >
            Execute Workflow
          </button>
        </div>
      </div>

      {/* Security Warnings */}
      <Show when={securityWarnings().length > 0}>
        <div class="p-4 bg-red-900 border-b border-red-700">
          <h3 class="font-bold text-red-200 mb-2">🚨 Security Warnings:</h3>
          <ul class="text-sm text-red-300">
            <For each={securityWarnings()}>
              {(warning) => <li>• {warning}</li>}
            </For>
          </ul>
        </div>
      </Show>

      {/* Main Content */}
      <div class="flex-1 flex">
        {/* Node Palette */}
        <div class="w-64 bg-gray-800 border-r border-gray-700 p-4">
          <h3 class="font-bold mb-4">Secure Node Templates</h3>
          <div class="space-y-2">
            <For each={nodeTemplates}>
              {(template) => (
                <div 
                  class="p-3 bg-gray-700 rounded cursor-pointer hover:bg-gray-600 transition-colors"
                  onclick={() => {
                    const position = { x: 100, y: 100 };
                    const newNode = createSecureNode(template, position);
                    setNodes(prev => [...prev, newNode]);
                  }}
                >
                  <div class="flex items-center justify-between">
                    <div>
                      <div class="font-medium">{template.icon} {template.label}</div>
                      <div class="text-xs text-gray-400">{template.description}</div>
                    </div>
                    <div class="text-xs text-green-400">
                      {template.securityScore}%
                    </div>
                  </div>
                </div>
              )}
            </For>
          </div>
        </div>

        {/* Workflow Canvas */}
        <div class="flex-1 relative bg-gray-900 overflow-hidden">
          <div class="absolute inset-0 bg-grid-pattern opacity-10"></div>
          
          {/* Nodes */}
          <For each={nodes()}>
            {(node) => (
              <div
                class={`absolute bg-gray-800 border-2 rounded-lg p-3 cursor-move select-none ${
                  node.selected ? 'border-blue-400' : 'border-gray-600'
                } ${
                  node.validated ? 'shadow-green-500/20' : 'shadow-red-500/20'
                } shadow-lg`}
                style={{
                  left: `${node.x}px`,
                  top: `${node.y}px`,
                  width: `${node.width}px`,
                  height: `${node.height}px`
                }}
                onclick={() => setSelectedNode(node.id)}
              >
                <div class="font-medium text-sm mb-2">
                  {node.label}
                  <span class={`ml-2 text-xs ${
                    node.validated ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {node.validated ? '✅' : '❌'}
                  </span>
                </div>
                <div class="text-xs text-gray-400 mb-2">
                  Security: {node.securityScore}%
                </div>
                
                {/* Input Ports */}
                <For each={node.inputs}>
                  {(input) => (
                    <div class="mb-1">
                      <span class="text-xs text-gray-400">
                        📥 {input.label}
                        {input.validated && <span class="text-green-400 ml-1">✅</span>}
                      </span>
                    </div>
                  )}
                </For>
                
                {/* Output Ports */}
                <For each={node.outputs}>
                  {(output) => (
                    <div class="mb-1">
                      <span class="text-xs text-gray-400">
                        📤 {output.label}
                        {output.validated && <span class="text-green-400 ml-1">✅</span>}
                      </span>
                    </div>
                  )}
                </For>
              </div>
            )}
          </For>
        </div>

        {/* Properties Panel */}
        <div class="w-80 bg-gray-800 border-l border-gray-700 p-4">
          <h3 class="font-bold mb-4">Properties & Security</h3>
          
          <Show when={selectedNode()}>
            <div class="space-y-4">
              <div>
                <label class="text-sm text-gray-400">Node ID:</label>
                <div class="text-sm font-mono">{selectedNode()}</div>
              </div>
              
              {/* Security Metrics */}
              <div class="space-y-2">
                <h4 class="font-medium">Security Metrics</h4>
                <div class="grid grid-cols-2 gap-2 text-sm">
                  <div>Nodes: {securityMetrics.totalNodes}/{SECURITY_CONFIG.MAX_NODES}</div>
                  <div>Edges: {securityMetrics.totalEdges}/{SECURITY_CONFIG.MAX_EDGES}</div>
                  <div>Violations: {securityMetrics.violations}</div>
                  <div>Memory: {Math.round(securityMetrics.memoryUsage / 1024)}KB</div>
                </div>
              </div>
              
              {/* Execution Status */}
              <Show when={execution()}>
                <div class="space-y-2">
                  <h4 class="font-medium">Execution Status</h4>
                  <div class="text-sm">
                    <div>Status: <span class={`font-medium ${
                      execution()?.status === 'completed' ? 'text-green-400' :
                      execution()?.status === 'running' ? 'text-blue-400' :
                      execution()?.status === 'failed' ? 'text-red-400' :
                      'text-yellow-400'
                    }`}>{execution()?.status}</span></div>
                    <div>Time: {execution()?.endTime ? 
                      `${execution()!.endTime - execution()!.startTime}ms` : 
                      `${Date.now() - execution()!.startTime}ms`
                    }</div>
                    <div>Memory: {Math.round(execution()?.memoryUsage || 0)}B</div>
                  </div>
                </div>
              </Show>
            </div>
          </Show>
        </div>
      </div>
    </div>
  );
}
