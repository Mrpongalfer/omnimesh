import {
  nodes,
  setNodes,
  setAgents,
  setAnomalies,
  setFlows,
  setNotifications,
  setSelectedNode,
  setSelectedAgent,
} from '../store/appState';
import type { Node, Agent, Anomaly, Flow } from '../store/appState';

// --- MOCK DATA GENERATORS ---

const randomId = () => `id_${Math.random().toString(36).substr(2, 9)}`;
const randomName = (prefix: string) =>
  `${prefix}-${Math.random().toString(36).substr(2, 5)}`;
const randomInt = (min: number, max: number) =>
  Math.floor(Math.random() * (max - min + 1)) + min;
const randomFloat = (min: number, max: number) =>
  Math.random() * (max - min) + min;
const randomElement = <T>(arr: T[]): T =>
  arr[Math.floor(Math.random() * arr.length)];

const createMockNode = (): Node => ({
  id: randomId(),
  x: randomInt(50, 1800),
  y: randomInt(50, 900),
  health: randomFloat(0, 1),
  activity: randomFloat(0, 1),
  type: randomElement(['compute', 'storage', 'network', 'coordinator']),
  status: randomElement(['online', 'offline', 'maintenance', 'error']),
  resources: {
    cpu: randomFloat(0, 100),
    memory: randomFloat(0, 100),
    storage: randomFloat(0, 100),
    network: randomFloat(0, 100),
  },
  metadata: {
    name: randomName('node'),
    lastSeen: new Date().toISOString(),
    tags: ['mock', randomName('tag')],
  },
});

const createMockAgent = (nodeCount: number): Agent => ({
  id: randomId(),
  from: randomInt(0, nodeCount - 1),
  to: randomInt(0, nodeCount - 1),
  progress: randomFloat(0, 1),
  type: randomElement(['monitor', 'processor', 'analyzer', 'coordinator']),
  status: randomElement(['active', 'idle', 'deploying', 'stopping']),
  currentTask: 'Simulated Task',
  startTime: new Date().toISOString(),
  estimatedCompletion: new Date(Date.now() + 30000).toISOString(),
});

const createMockAnomaly = (nodeCount: number): Anomaly => ({
  id: randomId(),
  node: randomInt(0, nodeCount - 1),
  type: randomElement(['security', 'performance', 'resource']),
  severity: randomElement(['low', 'medium', 'high', 'critical']),
  description: 'A simulated anomaly has been detected.',
  detectedAt: new Date().toISOString(),
  acknowledged: false,
});

const createMockFlow = (nodeCount: number): Flow => ({
  id: randomId(),
  from: randomInt(0, nodeCount - 1),
  to: randomInt(0, nodeCount - 1),
  volume: randomFloat(0, 100),
  bandwidth: randomFloat(1, 1000),
  latency: randomInt(1, 200),
  protocol: randomElement(['TCP', 'UDP', 'HTTP', 'WEBSOCKET']),
  status: randomElement(['active', 'congested', 'error']),
});

const createMockNotification = (): string =>
  `Mock event: ${randomName('event')} at ${new Date().toLocaleTimeString()}`;

// --- SIMULATION LOGIC ---

let simulationInterval: number | null = null;
const SIMULATION_TICK_RATE = 2000; // ms

function simulationTick() {
  const currentNodes = nodes();

  // Add a new node occasionally
  if (Math.random() < 0.1 && currentNodes.length < 30) {
    const newNode = createMockNode();
    setNodes((n) => [...n, newNode]);
    setNotifications((n) =>
      [
        `New node detected: ${newNode.metadata?.name || newNode.id}`,
        ...n,
      ].slice(0, 50),
    );
  }

  // Update existing nodes
  setNodes((nodes) =>
    nodes.map((node) => ({
      ...node,
      health: Math.max(0, Math.min(1, node.health + randomFloat(-0.1, 0.1))),
      activity: Math.max(
        0,
        Math.min(1, node.activity + randomFloat(-0.2, 0.2)),
      ),
      status:
        Math.random() < 0.05
          ? randomElement(['online', 'offline', 'maintenance', 'error'])
          : node.status,
      resources: {
        cpu: Math.max(
          0,
          Math.min(100, (node.resources?.cpu || 0) + randomFloat(-5, 5)),
        ),
        memory: Math.max(
          0,
          Math.min(100, (node.resources?.memory || 0) + randomFloat(-5, 5)),
        ),
        storage: Math.max(
          0,
          Math.min(100, (node.resources?.storage || 0) + randomFloat(-2, 2)),
        ),
        network: Math.max(
          0,
          Math.min(100, (node.resources?.network || 0) + randomFloat(-10, 10)),
        ),
      },
    })),
  );

  // Update agents
  setAgents((agents) =>
    agents.map((agent) => ({
      ...agent,
      progress: Math.min(1, agent.progress + randomFloat(0, 0.1)),
      to:
        Math.random() < 0.1 ? randomInt(0, currentNodes.length - 1) : agent.to,
    })),
  );

  // Add a new notification
  if (Math.random() < 0.2) {
    setNotifications((n) => [createMockNotification(), ...n].slice(0, 50));
  }
}

export function initializeMockRealtime() {
  startMockRealtime();
}

export function startMockRealtime() {
  if (simulationInterval) {
    console.log('Mock realtime service already running.');
    return;
  }

  console.log('Starting mock realtime service...');

  // Initial state
  const initialNodes = Array.from({ length: 15 }, createMockNode);
  const initialAgents = Array.from({ length: 5 }, () =>
    createMockAgent(initialNodes.length),
  );
  const initialAnomalies = Array.from({ length: 3 }, () =>
    createMockAnomaly(initialNodes.length),
  );
  const initialFlows = Array.from({ length: 10 }, () =>
    createMockFlow(initialNodes.length),
  );
  const initialNotifications = Array.from(
    { length: 5 },
    createMockNotification,
  );

  setNodes(initialNodes);
  setAgents(initialAgents);
  setAnomalies(initialAnomalies);
  setFlows(initialFlows);
  setNotifications(initialNotifications);
  setSelectedNode(null);
  setSelectedAgent(null);

  simulationInterval = window.setInterval(simulationTick, SIMULATION_TICK_RATE);
}

export function stopMockRealtime() {
  if (simulationInterval) {
    console.log('Stopping mock realtime service.');
    window.clearInterval(simulationInterval);
    simulationInterval = null;
  }
}
