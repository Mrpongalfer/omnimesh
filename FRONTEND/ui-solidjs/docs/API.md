# API Documentation

> **RESTful & GraphQL API Reference**  
> Comprehensive documentation for the Omnitide Control Panel backend integration

---

## 🎯 **API Overview**

### Base Configuration

```typescript
// API client configuration
const apiConfig = {
  baseURL: process.env.VITE_API_BASE_URL || 'https://api.omnitide.dev',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
    'X-Client-Version': '1.0.0',
  },
  retries: 3,
  retryDelay: 1000,
};

// GraphQL endpoint
const graphqlEndpoint = `${apiConfig.baseURL}/graphql`;

// WebSocket endpoint
const websocketEndpoint = `wss://ws.omnitide.dev/realtime`;

// WebTransport endpoint (HTTP/3)
const webtransportEndpoint = `https://ws.omnitide.dev/webtransport`;
```

### Authentication

```typescript
// JWT Token Management
interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresAt: number;
  tokenType: 'Bearer';
}

// API Key Authentication (for service-to-service)
interface ApiKeyAuth {
  apiKey: string;
  signature: string;
  timestamp: number;
}

// OAuth2 PKCE Flow
interface OAuth2Config {
  clientId: string;
  redirectUri: string;
  scopes: string[];
  codeVerifier: string;
  codeChallenge: string;
}
```

---

## 🔐 **Authentication Endpoints**

### POST `/auth/login`

Authenticate user with credentials.

**Request:**

```typescript
interface LoginRequest {
  email: string;
  password: string;
  mfaToken?: string;
  rememberMe?: boolean;
}
```

**Response:**

```typescript
interface LoginResponse {
  user: {
    id: string;
    email: string;
    name: string;
    role: 'admin' | 'operator' | 'viewer';
    permissions: string[];
    preferences: UserPreferences;
  };
  tokens: AuthTokens;
  session: {
    id: string;
    expiresAt: string;
    deviceId: string;
  };
}
```

**Example:**

```bash
curl -X POST https://api.omnitide.dev/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@omnitide.dev",
    "password": "securePassword123",
    "rememberMe": true
  }'
```

### POST `/auth/refresh`

Refresh access token using refresh token.

**Request:**

```typescript
interface RefreshRequest {
  refreshToken: string;
}
```

**Response:**

```typescript
interface RefreshResponse {
  tokens: AuthTokens;
}
```

### POST `/auth/logout`

Invalidate current session.

**Request:**

```typescript
interface LogoutRequest {
  refreshToken: string;
  allDevices?: boolean;
}
```

---

## 🤖 **Agent Management**

### GET `/agents`

Retrieve list of agents with filtering and pagination.

**Query Parameters:**

```typescript
interface AgentListQuery {
  page?: number; // Default: 1
  limit?: number; // Default: 50, Max: 100
  status?: 'active' | 'inactive' | 'error' | 'pending';
  environment?: string; // Filter by environment
  tags?: string[]; // Filter by tags
  search?: string; // Search by name or description
  sortBy?: 'name' | 'status' | 'lastSeen' | 'created';
  sortOrder?: 'asc' | 'desc';
}
```

**Response:**

```typescript
interface AgentListResponse {
  agents: Agent[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
    hasNext: boolean;
    hasPrev: boolean;
  };
  filters: {
    statusCounts: Record<AgentStatus, number>;
    environments: string[];
    availableTags: string[];
  };
}

interface Agent {
  id: string;
  name: string;
  description?: string;
  status: 'active' | 'inactive' | 'error' | 'pending';
  environment: string;
  version: string;
  tags: string[];
  capabilities: string[];
  metadata: Record<string, any>;
  health: {
    cpu: number;
    memory: number;
    disk: number;
    network: number;
    uptime: number;
    lastHeartbeat: string;
  };
  location: {
    datacenter: string;
    region: string;
    zone: string;
    coordinates?: [number, number]; // [lat, lng]
  };
  created: string;
  updated: string;
  lastSeen: string;
}
```

**Example:**

```bash
curl -X GET "https://api.omnitide.dev/agents?status=active&limit=10&sortBy=lastSeen" \
  -H "Authorization: Bearer <access_token>"
```

### GET `/agents/{id}`

Retrieve detailed information about a specific agent.

**Response:**

```typescript
interface AgentDetailResponse extends Agent {
  connections: {
    inbound: number;
    outbound: number;
    peers: string[];
  };
  performance: {
    requestsPerSecond: number;
    averageResponseTime: number;
    errorRate: number;
    throughput: number;
  };
  logs: {
    recent: LogEntry[];
    levels: Record<string, number>;
  };
  configuration: {
    [key: string]: any;
  };
}
```

### POST `/agents`

Create a new agent.

**Request:**

```typescript
interface CreateAgentRequest {
  name: string;
  description?: string;
  environment: string;
  tags?: string[];
  capabilities: string[];
  configuration: Record<string, any>;
  location: {
    datacenter: string;
    region: string;
    zone: string;
  };
}
```

### PUT `/agents/{id}`

Update an existing agent.

**Request:**

```typescript
interface UpdateAgentRequest {
  name?: string;
  description?: string;
  tags?: string[];
  configuration?: Record<string, any>;
  status?: 'active' | 'inactive';
}
```

### DELETE `/agents/{id}`

Delete an agent (soft delete with confirmation).

**Query Parameters:**

```typescript
interface DeleteAgentQuery {
  force?: boolean; // Force delete without confirmation
  backup?: boolean; // Create backup before deletion
}
```

---

## 📊 **Network Topology**

### GET `/network/topology`

Retrieve network topology data for visualization.

**Query Parameters:**

```typescript
interface TopologyQuery {
  depth?: number; // Maximum depth of connections (default: 3)
  includeInactive?: boolean; // Include inactive nodes
  layout?: 'force' | 'hierarchical' | 'circular';
  aggregateLevel?: 'node' | 'service' | 'datacenter';
}
```

**Response:**

```typescript
interface NetworkTopology {
  nodes: NetworkNode[];
  edges: NetworkEdge[];
  clusters: NetworkCluster[];
  metadata: {
    totalNodes: number;
    totalEdges: number;
    lastUpdated: string;
    health: 'healthy' | 'degraded' | 'critical';
  };
}

interface NetworkNode {
  id: string;
  label: string;
  type: 'agent' | 'service' | 'database' | 'load-balancer' | 'gateway';
  status: 'active' | 'inactive' | 'error' | 'warning';
  position: {
    x: number;
    y: number;
    z?: number;
  };
  properties: {
    cpu: number;
    memory: number;
    network: number;
    connections: number;
    throughput: number;
  };
  metadata: Record<string, any>;
}

interface NetworkEdge {
  id: string;
  source: string;
  target: string;
  type: 'http' | 'websocket' | 'tcp' | 'udp' | 'grpc';
  status: 'active' | 'inactive' | 'error';
  properties: {
    latency: number;
    bandwidth: number;
    packetLoss: number;
    throughput: number;
  };
  metrics: {
    requestRate: number;
    errorRate: number;
    averageResponseTime: number;
  };
}

interface NetworkCluster {
  id: string;
  label: string;
  nodeIds: string[];
  position: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  health: {
    status: 'healthy' | 'degraded' | 'critical';
    score: number;
  };
}
```

### GET `/network/paths`

Find network paths between nodes.

**Query Parameters:**

```typescript
interface PathQuery {
  source: string; // Source node ID
  target: string; // Target node ID
  algorithm?: 'shortest' | 'fastest' | 'most-reliable';
  maxHops?: number; // Maximum number of hops
}
```

**Response:**

```typescript
interface NetworkPaths {
  paths: NetworkPath[];
  recommendation: {
    primaryPath: string;
    backupPaths: string[];
    reasoning: string;
  };
}

interface NetworkPath {
  id: string;
  nodes: string[];
  edges: string[];
  metrics: {
    totalLatency: number;
    reliability: number;
    bandwidth: number;
    hopCount: number;
  };
  health: 'healthy' | 'degraded' | 'critical';
}
```

---

## 📈 **Metrics & Analytics**

### GET `/metrics/timeseries`

Retrieve time-series metrics data.

**Query Parameters:**

```typescript
interface TimeseriesQuery {
  metrics: string[]; // Metric names to retrieve
  startTime: string; // ISO 8601 timestamp
  endTime: string; // ISO 8601 timestamp
  resolution?: string; // '1m', '5m', '1h', '1d'
  aggregation?: 'avg' | 'sum' | 'min' | 'max' | 'count';
  filters?: Record<string, string>; // Label filters
}
```

**Response:**

```typescript
interface TimeseriesResponse {
  metrics: TimeseriesMetric[];
  metadata: {
    query: TimeseriesQuery;
    executionTime: number;
    samplesReturned: number;
  };
}

interface TimeseriesMetric {
  name: string;
  labels: Record<string, string>;
  values: TimeseriesValue[];
  aggregation: string;
  unit: string;
}

interface TimeseriesValue {
  timestamp: string;
  value: number;
}
```

### GET `/metrics/dashboard`

Retrieve pre-aggregated dashboard metrics.

**Response:**

```typescript
interface DashboardMetrics {
  overview: {
    totalAgents: number;
    activeAgents: number;
    totalRequests: number;
    averageResponseTime: number;
    errorRate: number;
    uptime: number;
  };
  health: {
    score: number;
    status: 'healthy' | 'degraded' | 'critical';
    issues: HealthIssue[];
  };
  performance: {
    throughput: number;
    latency: PercentileMetrics;
    cpu: ResourceMetrics;
    memory: ResourceMetrics;
    network: ResourceMetrics;
  };
  alerts: AlertSummary[];
}

interface PercentileMetrics {
  p50: number;
  p90: number;
  p95: number;
  p99: number;
}

interface ResourceMetrics {
  current: number;
  average: number;
  peak: number;
  trend: 'increasing' | 'decreasing' | 'stable';
}

interface HealthIssue {
  id: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  affectedComponents: string[];
  recommendations: string[];
  created: string;
}

interface AlertSummary {
  id: string;
  level: 'info' | 'warning' | 'error' | 'critical';
  title: string;
  count: number;
  lastSeen: string;
}
```

---

## 🚨 **Alerts & Notifications**

### GET `/alerts`

Retrieve alerts with filtering and pagination.

**Query Parameters:**

```typescript
interface AlertQuery {
  page?: number;
  limit?: number;
  level?: 'info' | 'warning' | 'error' | 'critical';
  status?: 'active' | 'acknowledged' | 'resolved';
  component?: string;
  timeRange?: string; // '1h', '24h', '7d', '30d'
}
```

**Response:**

```typescript
interface AlertListResponse {
  alerts: Alert[];
  pagination: PaginationInfo;
  summary: {
    total: number;
    byLevel: Record<string, number>;
    byStatus: Record<string, number>;
  };
}

interface Alert {
  id: string;
  title: string;
  description: string;
  level: 'info' | 'warning' | 'error' | 'critical';
  status: 'active' | 'acknowledged' | 'resolved';
  component: string;
  source: string;
  tags: string[];
  metadata: Record<string, any>;
  created: string;
  updated: string;
  acknowledgedBy?: string;
  acknowledgedAt?: string;
  resolvedAt?: string;
  actions: AlertAction[];
}

interface AlertAction {
  id: string;
  type: 'acknowledge' | 'resolve' | 'escalate' | 'suppress';
  label: string;
  description: string;
  requiresConfirmation: boolean;
}
```

### POST `/alerts/{id}/acknowledge`

Acknowledge an alert.

**Request:**

```typescript
interface AcknowledgeRequest {
  comment?: string;
  suppressFor?: string; // Duration to suppress (e.g., '1h', '24h')
}
```

---

## 🔄 **Real-Time Communications**

### WebSocket Connection

```typescript
// WebSocket client implementation
class RealtimeClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  connect(token: string): Promise<void> {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(`${websocketEndpoint}?token=${token}`);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        resolve();
      };

      this.ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        this.handleMessage(message);
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        reject(error);
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.attemptReconnect(token);
      };
    });
  }

  private handleMessage(message: RealtimeMessage): void {
    switch (message.type) {
      case 'agent_status_update':
        this.onAgentStatusUpdate(message.data);
        break;
      case 'metric_update':
        this.onMetricUpdate(message.data);
        break;
      case 'alert':
        this.onAlert(message.data);
        break;
      case 'topology_change':
        this.onTopologyChange(message.data);
        break;
    }
  }

  subscribe(channel: string, filters?: Record<string, any>): void {
    this.send({
      type: 'subscribe',
      channel,
      filters,
    });
  }

  unsubscribe(channel: string): void {
    this.send({
      type: 'unsubscribe',
      channel,
    });
  }

  private send(message: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }
}
```

### Message Types

```typescript
interface RealtimeMessage {
  id: string;
  type: string;
  timestamp: string;
  data: any;
}

// Agent status updates
interface AgentStatusUpdate {
  agentId: string;
  status: AgentStatus;
  health: AgentHealth;
  metadata: Record<string, any>;
}

// Metric updates
interface MetricUpdate {
  metric: string;
  value: number;
  timestamp: string;
  labels: Record<string, string>;
}

// Alert notifications
interface AlertNotification {
  alert: Alert;
  action: 'created' | 'updated' | 'resolved';
}

// Topology changes
interface TopologyChange {
  type:
    | 'node_added'
    | 'node_removed'
    | 'edge_added'
    | 'edge_removed'
    | 'cluster_updated';
  nodeId?: string;
  edgeId?: string;
  clusterId?: string;
  data: any;
}
```

---

## 🔌 **GraphQL API**

### Schema Overview

```graphql
type Query {
  # Agents
  agents(
    filter: AgentFilter
    pagination: PaginationInput
    sort: SortInput
  ): AgentConnection!

  agent(id: ID!): Agent

  # Network
  networkTopology(
    depth: Int
    includeInactive: Boolean
    layout: LayoutType
  ): NetworkTopology!

  networkPaths(
    source: ID!
    target: ID!
    algorithm: PathAlgorithm
  ): [NetworkPath!]!

  # Metrics
  metrics(
    names: [String!]!
    timeRange: TimeRange!
    resolution: Resolution
    filters: MetricFilters
  ): [TimeSeries!]!

  dashboardMetrics: DashboardMetrics!

  # Alerts
  alerts(filter: AlertFilter, pagination: PaginationInput): AlertConnection!
}

type Mutation {
  # Agents
  createAgent(input: CreateAgentInput!): Agent!
  updateAgent(id: ID!, input: UpdateAgentInput!): Agent!
  deleteAgent(id: ID!, force: Boolean): Boolean!

  # Alerts
  acknowledgeAlert(id: ID!, comment: String): Alert!
  resolveAlert(id: ID!, comment: String): Alert!
}

type Subscription {
  # Real-time updates
  agentStatusUpdates(agentIds: [ID!]): AgentStatusUpdate!
  metricUpdates(metrics: [String!]!): MetricUpdate!
  alertNotifications: AlertNotification!
  topologyChanges: TopologyChange!
}
```

### Example Queries

```graphql
# Get agents with health information
query GetAgents($filter: AgentFilter!) {
  agents(filter: $filter) {
    edges {
      node {
        id
        name
        status
        environment
        health {
          cpu
          memory
          uptime
          lastHeartbeat
        }
        location {
          datacenter
          region
        }
      }
    }
    pageInfo {
      hasNextPage
      hasPreviousPage
      startCursor
      endCursor
    }
    totalCount
  }
}

# Get network topology
query GetNetworkTopology {
  networkTopology(depth: 3, includeInactive: false) {
    nodes {
      id
      label
      type
      status
      position {
        x
        y
      }
      properties {
        cpu
        memory
        connections
      }
    }
    edges {
      id
      source
      target
      type
      status
      properties {
        latency
        bandwidth
      }
    }
    clusters {
      id
      label
      nodeIds
      health {
        status
        score
      }
    }
  }
}

# Get real-time metrics
subscription MetricUpdates {
  metricUpdates(metrics: ["cpu", "memory", "network"]) {
    metric
    value
    timestamp
    labels {
      agentId
      environment
    }
  }
}
```

---

## 🔧 **SDK & Client Libraries**

### TypeScript SDK

```bash
npm install @omnitide/client-sdk
```

```typescript
import { OmnitideClient } from '@omnitide/client-sdk';

// Initialize client
const client = new OmnitideClient({
  baseURL: 'https://api.omnitide.dev',
  apiKey: process.env.OMNITIDE_API_KEY,
  timeout: 30000,
});

// Authenticate
await client.auth.login({
  email: 'user@omnitide.dev',
  password: 'password',
});

// Get agents
const agents = await client.agents.list({
  status: 'active',
  limit: 10,
});

// Real-time subscriptions
const unsubscribe = client.realtime.subscribe(
  'agent_status_updates',
  {
    agentIds: ['agent-1', 'agent-2'],
  },
  (update) => {
    console.log('Agent update:', update);
  },
);
```

### Error Handling

```typescript
interface APIError {
  code: string;
  message: string;
  details?: Record<string, any>;
  requestId: string;
  timestamp: string;
}

// Error codes
enum ErrorCodes {
  UNAUTHORIZED = 'UNAUTHORIZED',
  FORBIDDEN = 'FORBIDDEN',
  NOT_FOUND = 'NOT_FOUND',
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  RATE_LIMITED = 'RATE_LIMITED',
  INTERNAL_ERROR = 'INTERNAL_ERROR',
  SERVICE_UNAVAILABLE = 'SERVICE_UNAVAILABLE',
}
```

### Rate Limiting

```typescript
// Rate limit headers
interface RateLimitHeaders {
  'X-RateLimit-Limit': string; // Requests per window
  'X-RateLimit-Remaining': string; // Remaining requests
  'X-RateLimit-Reset': string; // Reset time (Unix timestamp)
  'X-RateLimit-Window': string; // Window duration in seconds
}

// Rate limits by endpoint
const rateLimits = {
  '/agents': '1000/hour',
  '/metrics': '10000/hour',
  '/network/topology': '100/hour',
  '/alerts': '500/hour',
};
```

---

## 📚 **Additional Resources**

### OpenAPI Specification

Full OpenAPI 3.0 specification available at: `https://api.omnitide.dev/openapi.json`

### Postman Collection

Import our Postman collection: `https://api.omnitide.dev/postman/collection.json`

### SDK Documentation

- [TypeScript SDK](https://docs.omnitide.dev/sdk/typescript)
- [Python SDK](https://docs.omnitide.dev/sdk/python)
- [Go SDK](https://docs.omnitide.dev/sdk/go)

### Support

- **Documentation**: https://docs.omnitide.dev
- **Support Email**: api-support@omnitide.dev
- **Discord**: https://discord.gg/omnitide
- **GitHub Issues**: https://github.com/omnitide/control-panel/issues

---

_Last updated: January 2025_
_API Version: 1.0.0_
