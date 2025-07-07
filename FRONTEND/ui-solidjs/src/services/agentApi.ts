// src/services/agentApi.ts
// Enhanced Agent API for comprehensive agent orchestration and management

// When Protobuf schemas are available, import the generated message classes:
// import { AgentMessage, AgentCommand, AgentResponse } from '../proto/omnitide_proto';

// Type definitions for agent management
export interface AgentStatus {
  id: string;
  name: string;
  type: 'monitor' | 'processor' | 'analyzer' | 'coordinator';
  status: 'online' | 'offline' | 'error' | 'deploying' | 'stopping';
  lastSeen: string;
  health: number; // 0-1
  currentTask?: string;
  assignedNode?: string;
  metrics: {
    tasksCompleted: number;
    uptime: number;
    memoryUsage: number;
    cpuUsage: number;
  };
  capabilities: string[];
  [key: string]: unknown;
}

export interface AgentDeploymentConfig {
  name: string;
  type: AgentStatus['type'];
  targetNodeId: string;
  capabilities: string[];
  resources?: {
    memory?: number;
    cpu?: number;
  };
  configuration?: Record<string, unknown>;
}

export interface AgentTask {
  id: string;
  agentId: string;
  type: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number; // 0-1
  createdAt: string;
  completedAt?: string;
  result?: unknown;
}

// Configuration for API endpoints - replace with actual backend URLs
const getApiConfig = () => ({
  baseUrl: process.env.VITE_API_BASE_URL || 'http://localhost:8080',
  apiKey: process.env.VITE_API_KEY || '',
  timeout: 10000,
});

// Enhanced HTTP client with error handling and timeout
const apiRequest = async <T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> => {
  const config = getApiConfig();
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), config.timeout);

  try {
    const response = await fetch(`${config.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(config.apiKey && { Authorization: `Bearer ${config.apiKey}` }),
        ...options.headers,
      },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  } catch (error) {
    clearTimeout(timeoutId);
    throw error;
  }
};

// Core agent management functions
export async function fetchAgents(): Promise<AgentStatus[]> {
  return apiRequest<AgentStatus[]>('/api/v1/agents');
}

export async function getAgentStatus(agentId: string): Promise<AgentStatus> {
  return apiRequest<AgentStatus>(`/api/v1/agents/${agentId}/status`);
}

export async function deployAgent(
  config: AgentDeploymentConfig,
): Promise<{ agentId: string; status: string }> {
  return apiRequest<{ agentId: string; status: string }>('/api/v1/agents', {
    method: 'POST',
    body: JSON.stringify(config),
  });
}

export async function startAgent(agentId: string): Promise<void> {
  await apiRequest(`/api/v1/agents/${agentId}/start`, { method: 'POST' });
}

export async function stopAgent(agentId: string): Promise<void> {
  await apiRequest(`/api/v1/agents/${agentId}/stop`, { method: 'POST' });
}

export async function deleteAgent(agentId: string): Promise<void> {
  await apiRequest(`/api/v1/agents/${agentId}`, { method: 'DELETE' });
}

export async function assignTask(
  agentId: string,
  taskConfig: Omit<
    AgentTask,
    'id' | 'agentId' | 'status' | 'progress' | 'createdAt'
  >,
): Promise<AgentTask> {
  return apiRequest<AgentTask>(`/api/v1/agents/${agentId}/tasks`, {
    method: 'POST',
    body: JSON.stringify(taskConfig),
  });
}

export async function getAgentTasks(agentId: string): Promise<AgentTask[]> {
  return apiRequest<AgentTask[]>(`/api/v1/agents/${agentId}/tasks`);
}

export async function getAgentLogs(
  agentId: string,
  options: { limit?: number; level?: string; since?: string } = {},
): Promise<{ logs: string[]; hasMore: boolean }> {
  const params = new URLSearchParams();
  if (options.limit) params.set('limit', options.limit.toString());
  if (options.level) params.set('level', options.level);
  if (options.since) params.set('since', options.since);

  return apiRequest<{ logs: string[]; hasMore: boolean }>(
    `/api/v1/agents/${agentId}/logs?${params}`,
  );
}

export async function migrateAgent(
  agentId: string,
  targetNodeId: string,
): Promise<{ status: string; migrationId: string }> {
  return apiRequest<{ status: string; migrationId: string }>(
    `/api/v1/agents/${agentId}/migrate`,
    {
      method: 'POST',
      body: JSON.stringify({ targetNodeId }),
    },
  );
}

export async function updateAgentConfig(
  agentId: string,
  config: Partial<AgentDeploymentConfig>,
): Promise<AgentStatus> {
  return apiRequest<AgentStatus>(`/api/v1/agents/${agentId}/config`, {
    method: 'PATCH',
    body: JSON.stringify(config),
  });
}

// Bulk operations for efficiency
export async function bulkStartAgents(agentIds: string[]): Promise<void> {
  await apiRequest('/api/v1/agents/bulk/start', {
    method: 'POST',
    body: JSON.stringify({ agentIds }),
  });
}

export async function bulkStopAgents(agentIds: string[]): Promise<void> {
  await apiRequest('/api/v1/agents/bulk/stop', {
    method: 'POST',
    body: JSON.stringify({ agentIds }),
  });
}

// Real-time agent monitoring via WebSocket (to be used with realtime.ts)
export function subscribeToAgentUpdates(
  agentId: string,
  callback: (update: Partial<AgentStatus>) => void,
): () => void {
  // This will be implemented when WebSocket connection is established
  // For now, return a cleanup function
  console.log(`Subscribing to updates for agent ${agentId}`);
  return () => {
    console.log(`Unsubscribing from updates for agent ${agentId}`);
  };
}
