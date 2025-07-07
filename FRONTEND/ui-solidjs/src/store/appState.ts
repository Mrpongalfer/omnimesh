import { createSignal, createMemo } from 'solid-js';

// Enhanced data types for comprehensive state management
export type Node = {
  id: string;
  x: number;
  y: number;
  health: number; // 0-1
  activity: number; // 0-1
  type?: 'compute' | 'storage' | 'network' | 'coordinator';
  status?: 'online' | 'offline' | 'maintenance' | 'error';
  resources?: {
    cpu: number;
    memory: number;
    storage: number;
    network: number;
  };
  metadata?: Record<string, unknown>;
};

export type Agent = {
  id: string;
  from: number;
  to: number;
  progress: number; // 0-1
  type?: 'monitor' | 'processor' | 'analyzer' | 'coordinator';
  status?: 'active' | 'idle' | 'deploying' | 'stopping';
  currentTask?: string;
  startTime?: string;
  estimatedCompletion?: string;
};

export type Anomaly = {
  id: string;
  node: number;
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  detectedAt: string;
  acknowledged?: boolean;
  resolvedAt?: string;
};

export type Flow = {
  id: string;
  from: number;
  to: number;
  volume: number;
  bandwidth?: number;
  latency?: number;
  protocol?: string;
  status?: 'active' | 'congested' | 'error';
};

// UI state management
export type UIState = {
  sidebarOpen: boolean;
  minimapVisible: boolean;
  notificationsVisible: boolean;
  commandLineOpen: boolean;
  selectedTool: string | null;
  viewMode: 'topology' | 'metrics' | 'agents' | 'security';
  zoomLevel: number;
  cameraPosition: { x: number; y: number };
};

// Performance metrics
export type SystemMetrics = {
  timestamp: string;
  cpu: number;
  memory: number;
  network: number;
  activeAgents: number;
  totalNodes: number;
  healthyNodes: number;
  totalFlows: number;
  avgLatency: number;
};

// Core state signals
export const [selectedNode, setSelectedNode] = createSignal<string | null>(
  null,
);
export const [selectedAgent, setSelectedAgent] = createSignal<string | null>(
  null,
);
export const [notifications, setNotifications] = createSignal<string[]>([]);

// Real-time feedback and explainable AI signals
export const [criticalOverlay, setCriticalOverlay] = createSignal<
  string | null
>(null);
export const [explainableAI, setExplainableAI] = createSignal<string | null>(
  null,
);

// Real-time fabric state (populated by backend events)
export const [nodes, setNodes] = createSignal<Node[]>([]);
export const [agents, setAgents] = createSignal<Agent[]>([]);
export const [anomalies, setAnomalies] = createSignal<Anomaly[]>([]);
export const [flows, setFlows] = createSignal<Flow[]>([]);

// UI state
export const [uiState, setUIState] = createSignal<UIState>({
  sidebarOpen: true,
  minimapVisible: true,
  notificationsVisible: true,
  commandLineOpen: false,
  selectedTool: null,
  viewMode: 'topology',
  zoomLevel: 1,
  cameraPosition: { x: 0, y: 0 },
});

// System metrics
export const [systemMetrics, setSystemMetrics] = createSignal<SystemMetrics[]>(
  [],
);

// Computed values (memos) for derived state
export const selectedNodeData = createMemo(() => {
  const selected = selectedNode();
  return selected ? nodes().find((n) => n.id === selected) : null;
});

export const selectedAgentData = createMemo(() => {
  const selected = selectedAgent();
  return selected ? agents().find((a) => a.id === selected) : null;
});

export const criticalAnomalies = createMemo(() =>
  anomalies().filter((a) => a.severity === 'critical' && !a.acknowledged),
);

export const systemHealthScore = createMemo(() => {
  const nodeCount = nodes().length;
  if (nodeCount === 0) return 1;

  const healthSum = nodes().reduce((sum, node) => sum + node.health, 0);
  const criticalCount = criticalAnomalies().length;

  const baseHealth = healthSum / nodeCount;
  const anomalyPenalty = Math.min(criticalCount * 0.1, 0.5);

  return Math.max(0, baseHealth - anomalyPenalty);
});

export const networkActivityLevel = createMemo(() => {
  const totalActivity = nodes().reduce((sum, node) => sum + node.activity, 0);
  return nodes().length > 0 ? totalActivity / nodes().length : 0;
});

export const activeAgentsCount = createMemo(
  () => agents().filter((a) => a.status === 'active').length,
);

export const unacknowledgedNotifications = createMemo(
  () => notifications().length,
);

// State update helper functions
export function updateUIState(updates: Partial<UIState>): void {
  setUIState((prev) => ({ ...prev, ...updates }));
}

export function addNotification(
  message: string,
  type: 'info' | 'warning' | 'error' | 'success' = 'info',
): void {
  const timestamp = new Date().toLocaleTimeString();
  const formattedMessage = `[${timestamp}] ${type.toUpperCase()}: ${message}`;

  setNotifications((prev) => [formattedMessage, ...prev.slice(0, 99)]); // Keep last 100 notifications
}

export function clearNotifications(): void {
  setNotifications([]);
}

export function acknowledgeAnomaly(anomalyId: string): void {
  setAnomalies((prev) =>
    prev.map((anomaly) =>
      anomaly.id === anomalyId ? { ...anomaly, acknowledged: true } : anomaly,
    ),
  );
}

export function resolveAnomaly(anomalyId: string): void {
  setAnomalies((prev) =>
    prev.map((anomaly) =>
      anomaly.id === anomalyId
        ? {
            ...anomaly,
            acknowledged: true,
            resolvedAt: new Date().toISOString(),
          }
        : anomaly,
    ),
  );
}

export function addSystemMetric(metric: SystemMetrics): void {
  setSystemMetrics((prev) => [metric, ...prev.slice(0, 999)]); // Keep last 1000 metrics
}

export function updateNodeHealth(nodeId: string, health: number): void {
  setNodes((prev) =>
    prev.map((node) =>
      node.id === nodeId
        ? { ...node, health: Math.max(0, Math.min(1, health)) }
        : node,
    ),
  );
}

export function updateAgentProgress(agentId: string, progress: number): void {
  setAgents((prev) =>
    prev.map((agent) =>
      agent.id === agentId
        ? { ...agent, progress: Math.max(0, Math.min(1, progress)) }
        : agent,
    ),
  );
}

export function deployAgent(
  fromNodeIndex: number,
  toNodeIndex: number,
): string {
  const agentId = `agent-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
  const newAgent: Agent = {
    id: agentId,
    from: fromNodeIndex,
    to: toNodeIndex,
    progress: 0,
    type: 'processor',
    status: 'deploying',
    startTime: new Date().toISOString(),
  };

  setAgents((prev) => [...prev, newAgent]);
  addNotification(
    `Agent ${agentId} deployed from node ${fromNodeIndex} to ${toNodeIndex}`,
    'success',
  );

  return agentId;
}

export function removeAgent(agentId: string): void {
  setAgents((prev) => prev.filter((agent) => agent.id !== agentId));
  addNotification(`Agent ${agentId} removed`, 'info');
}

// Data initialization functions for development/testing
export function initializeMockData(): void {
  // Initialize with sample data for development
  const mockNodes: Node[] = Array.from({ length: 8 }, (_, i) => ({
    id: `node-${i}`,
    x: (i % 4) * 200 + 100,
    y: Math.floor(i / 4) * 200 + 100,
    health: 0.7 + Math.random() * 0.3,
    activity: Math.random(),
    type: ['compute', 'storage', 'network', 'coordinator'][
      i % 4
    ] as Node['type'],
    status: Math.random() > 0.1 ? 'online' : 'maintenance',
    resources: {
      cpu: Math.random() * 100,
      memory: Math.random() * 100,
      storage: Math.random() * 100,
      network: Math.random() * 100,
    },
  }));

  const mockFlows: Flow[] = Array.from({ length: 12 }, (_, i) => ({
    id: `flow-${i}`,
    from: Math.floor(Math.random() * 8),
    to: Math.floor(Math.random() * 8),
    volume: Math.random() * 100,
    bandwidth: Math.random() * 1000,
    latency: Math.random() * 50,
    status: Math.random() > 0.1 ? 'active' : 'congested',
  }));

  const mockAnomalies: Anomaly[] = Array.from({ length: 3 }, (_, i) => ({
    id: `anomaly-${i}`,
    node: Math.floor(Math.random() * 8),
    type: ['performance', 'security', 'connectivity'][i % 3],
    severity: ['low', 'medium', 'high', 'critical'][
      Math.floor(Math.random() * 4)
    ] as Anomaly['severity'],
    description: `Sample anomaly ${i + 1} detected`,
    detectedAt: new Date(Date.now() - Math.random() * 3600000).toISOString(),
    acknowledged: Math.random() > 0.5,
  }));

  setNodes(mockNodes);
  setFlows(mockFlows);
  setAnomalies(mockAnomalies);

  addNotification('Mock data initialized for development', 'info');
}
