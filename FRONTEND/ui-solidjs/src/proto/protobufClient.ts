// Protobuf Client for Omnitide Control Panel
// Provides type-safe serialization/deserialization for real-time communication

// Note: This is a mock implementation that provides the interface
// In a real implementation, you would use protobuf.js or similar to generate
// actual protobuf encoding/decoding functions from the .proto file

export interface Timestamp {
  seconds: number;
  nanos: number;
}

export interface Vector2D {
  x: number;
  y: number;
}

export interface Vector3D {
  x: number;
  y: number;
  z: number;
}

export interface NodeResources {
  cpu: number;
  memory: number;
  storage: number;
  network: number;
}

export interface NodeMetadata {
  name: string;
  lastSeen: string;
  tags: string[];
  properties: Record<string, string>;
}

export enum NodeType {
  UNSPECIFIED = 0,
  COMPUTE = 1,
  STORAGE = 2,
  NETWORK = 3,
  COORDINATOR = 4,
}

export enum NodeStatus {
  UNSPECIFIED = 0,
  ONLINE = 1,
  OFFLINE = 2,
  MAINTENANCE = 3,
  ERROR = 4,
}

export interface Node {
  id: string;
  position: Vector2D;
  health: number;
  activity: number;
  type: NodeType;
  status: NodeStatus;
  resources: NodeResources;
  metadata: NodeMetadata;
  connections: string[];
}

export enum AgentType {
  UNSPECIFIED = 0,
  MONITOR = 1,
  PROCESSOR = 2,
  ANALYZER = 3,
  COORDINATOR = 4,
}

export enum AgentStatus {
  UNSPECIFIED = 0,
  ACTIVE = 1,
  IDLE = 2,
  DEPLOYING = 3,
  STOPPING = 4,
  ERROR = 5,
}

export interface Agent {
  id: string;
  fromNode: number;
  toNode: number;
  progress: number;
  type: AgentType;
  status: AgentStatus;
  currentTask: string;
  startTime: Timestamp;
  estimatedCompletion: Timestamp;
  configuration: Record<string, string>;
}

export enum FlowStatus {
  UNSPECIFIED = 0,
  ACTIVE = 1,
  CONGESTED = 2,
  ERROR = 3,
  INACTIVE = 4,
}

export interface Flow {
  id: string;
  fromNode: number;
  toNode: number;
  volume: number;
  bandwidth: number;
  latency: number;
  status: FlowStatus;
  protocol: string;
}

export enum AnomalyType {
  UNSPECIFIED = 0,
  PERFORMANCE = 1,
  SECURITY = 2,
  CONNECTIVITY = 3,
  RESOURCE = 4,
}

export enum AnomalySeverity {
  UNSPECIFIED = 0,
  LOW = 1,
  MEDIUM = 2,
  HIGH = 3,
  CRITICAL = 4,
}

export interface Anomaly {
  id: string;
  nodeIndex: number;
  type: AnomalyType;
  severity: AnomalySeverity;
  description: string;
  confidence: number;
  detectedAt: Timestamp;
  acknowledged: boolean;
  metadata: Record<string, string>;
}

export interface SystemMetrics {
  timestamp: Timestamp;
  overallHealth: number;
  networkUtilization: number;
  activeConnections: number;
  throughput: number;
  averageLatency: number;
  errorCount: number;
  customMetrics: Record<string, number>;
}

export interface NetworkState {
  nodes: Node[];
  agents: Agent[];
  flows: Flow[];
  anomalies: Anomaly[];
  metrics: SystemMetrics;
  lastUpdated: Timestamp;
}

export enum CommandType {
  UNSPECIFIED = 0,
  DEPLOY_AGENT = 1,
  STOP_AGENT = 2,
  REPAIR_NODE = 3,
  RESTART_NODE = 4,
  SCAN_NETWORK = 5,
  ACKNOWLEDGE_ANOMALY = 6,
  OPTIMIZE_LAYOUT = 7,
}

export interface Command {
  id: string;
  type: CommandType;
  target: string;
  parameters: Record<string, string>;
  issuedAt: Timestamp;
  issuedBy: string;
}

export enum CommandStatus {
  UNSPECIFIED = 0,
  PENDING = 1,
  EXECUTING = 2,
  COMPLETED = 3,
  FAILED = 4,
  CANCELLED = 5,
}

export interface CommandResponse {
  commandId: string;
  status: CommandStatus;
  message: string;
  results: Record<string, string>;
  completedAt: Timestamp;
}

export enum NotificationType {
  UNSPECIFIED = 0,
  INFO = 1,
  WARNING = 2,
  ERROR = 3,
  SUCCESS = 4,
  ALERT = 5,
}

export enum NotificationSeverity {
  UNSPECIFIED = 0,
  LOW = 1,
  NORMAL = 2,
  HIGH = 3,
  CRITICAL = 4,
}

export interface Notification {
  id: string;
  type: NotificationType;
  severity: NotificationSeverity;
  title: string;
  message: string;
  timestamp: Timestamp;
  acknowledged: boolean;
  metadata: Record<string, string>;
}

export enum MessageType {
  UNSPECIFIED = 0,
  NETWORK_STATE = 1,
  COMMAND = 2,
  COMMAND_RESPONSE = 3,
  NOTIFICATION = 4,
  SUBSCRIPTION_REQUEST = 5,
  SUBSCRIPTION_RESPONSE = 6,
  HEARTBEAT_REQUEST = 7,
  HEARTBEAT_RESPONSE = 8,
}

export interface Message {
  messageId: string;
  type: MessageType;
  timestamp: Timestamp;
  payload: 
    | { type: 'networkState'; data: NetworkState }
    | { type: 'command'; data: Command }
    | { type: 'commandResponse'; data: CommandResponse }
    | { type: 'notification'; data: Notification }
    | { type: 'subscriptionRequest'; data: SubscriptionRequest }
    | { type: 'subscriptionResponse'; data: SubscriptionResponse }
    | { type: 'heartbeatRequest'; data: HeartbeatRequest }
    | { type: 'heartbeatResponse'; data: HeartbeatResponse };
}

export enum SubscriptionAction {
  UNSPECIFIED = 0,
  SUBSCRIBE = 1,
  UNSUBSCRIBE = 2,
  MODIFY = 3,
}

export enum SubscriptionTopic {
  UNSPECIFIED = 0,
  NETWORK_STATE = 1,
  ANOMALIES = 2,
  METRICS = 3,
  NOTIFICATIONS = 4,
  COMMANDS = 5,
}

export interface SubscriptionRequest {
  subscriptionId: string;
  action: SubscriptionAction;
  topics: SubscriptionTopic[];
  filters: Record<string, string>;
}

export enum SubscriptionStatus {
  UNSPECIFIED = 0,
  ACTIVE = 1,
  INACTIVE = 2,
  ERROR = 3,
}

export interface SubscriptionResponse {
  subscriptionId: string;
  status: SubscriptionStatus;
  message: string;
}

export interface HeartbeatRequest {
  clientTime: Timestamp;
  clientId: string;
}

export interface HeartbeatResponse {
  serverTime: Timestamp;
  clientTime: Timestamp;
  latency: number;
  serverId: string;
}

// Utility functions for timestamp conversion
export function timestampToDate(timestamp: Timestamp): Date {
  return new Date(timestamp.seconds * 1000 + timestamp.nanos / 1000000);
}

export function dateToTimestamp(date: Date): Timestamp {
  const ms = date.getTime();
  return {
    seconds: Math.floor(ms / 1000),
    nanos: (ms % 1000) * 1000000,
  };
}

export function nowTimestamp(): Timestamp {
  return dateToTimestamp(new Date());
}

// Mock protobuf serialization (in real implementation, use protobuf.js)
export class ProtobufClient {
  // Serialize message to binary (mock implementation)
  static serialize(message: Message): Uint8Array {
    // In a real implementation, this would use protobuf encoding
    const jsonString = JSON.stringify(message);
    const encoder = new TextEncoder();
    return encoder.encode(jsonString);
  }

  // Deserialize binary to message (mock implementation)
  static deserialize(data: Uint8Array): Message {
    // In a real implementation, this would use protobuf decoding
    const decoder = new TextDecoder();
    const jsonString = decoder.decode(data);
    return JSON.parse(jsonString) as Message;
  }

  // Create a network state message
  static createNetworkStateMessage(networkState: NetworkState): Message {
    return {
      messageId: this.generateMessageId(),
      type: MessageType.NETWORK_STATE,
      timestamp: nowTimestamp(),
      payload: { type: 'networkState', data: networkState },
    };
  }

  // Create a command message
  static createCommandMessage(command: Command): Message {
    return {
      messageId: this.generateMessageId(),
      type: MessageType.COMMAND,
      timestamp: nowTimestamp(),
      payload: { type: 'command', data: command },
    };
  }

  // Create a notification message
  static createNotificationMessage(notification: Notification): Message {
    return {
      messageId: this.generateMessageId(),
      type: MessageType.NOTIFICATION,
      timestamp: nowTimestamp(),
      payload: { type: 'notification', data: notification },
    };
  }

  // Create a subscription request message
  static createSubscriptionRequestMessage(request: SubscriptionRequest): Message {
    return {
      messageId: this.generateMessageId(),
      type: MessageType.SUBSCRIPTION_REQUEST,
      timestamp: nowTimestamp(),
      payload: { type: 'subscriptionRequest', data: request },
    };
  }

  // Create a heartbeat request message
  static createHeartbeatRequestMessage(clientId: string): Message {
    return {
      messageId: this.generateMessageId(),
      type: MessageType.HEARTBEAT_REQUEST,
      timestamp: nowTimestamp(),
      payload: {
        type: 'heartbeatRequest',
        data: {
          clientTime: nowTimestamp(),
          clientId,
        },
      },
    };
  }

  // Utility to generate unique message IDs
  private static generateMessageId(): string {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // Validate message structure
  static validateMessage(message: any): message is Message {
    return (
      typeof message === 'object' &&
      typeof message.messageId === 'string' &&
      typeof message.type === 'number' &&
      typeof message.timestamp === 'object' &&
      typeof message.payload === 'object'
    );
  }

  // Convert legacy data structures to protobuf format
  static convertLegacyNode(legacyNode: any): Node {
    return {
      id: legacyNode.id || '',
      position: { x: legacyNode.x || 0, y: legacyNode.y || 0 },
      health: legacyNode.health || 0,
      activity: legacyNode.activity || 0,
      type: this.convertNodeType(legacyNode.type),
      status: this.convertNodeStatus(legacyNode.status),
      resources: legacyNode.resources || { cpu: 0, memory: 0, storage: 0, network: 0 },
      metadata: legacyNode.metadata || { name: '', lastSeen: '', tags: [], properties: {} },
      connections: legacyNode.connections || [],
    };
  }

  static convertLegacyAgent(legacyAgent: any): Agent {
    return {
      id: legacyAgent.id || '',
      fromNode: legacyAgent.from || 0,
      toNode: legacyAgent.to || 0,
      progress: legacyAgent.progress || 0,
      type: this.convertAgentType(legacyAgent.type),
      status: this.convertAgentStatus(legacyAgent.status),
      currentTask: legacyAgent.currentTask || '',
      startTime: legacyAgent.startTime ? dateToTimestamp(new Date(legacyAgent.startTime)) : nowTimestamp(),
      estimatedCompletion: legacyAgent.estimatedCompletion ? dateToTimestamp(new Date(legacyAgent.estimatedCompletion)) : nowTimestamp(),
      configuration: legacyAgent.configuration || {},
    };
  }

  static convertLegacyFlow(legacyFlow: any): Flow {
    return {
      id: legacyFlow.id || '',
      fromNode: legacyFlow.from || 0,
      toNode: legacyFlow.to || 0,
      volume: legacyFlow.volume || 0,
      bandwidth: legacyFlow.bandwidth || 0,
      latency: legacyFlow.latency || 0,
      status: this.convertFlowStatus(legacyFlow.status),
      protocol: legacyFlow.protocol || 'TCP',
    };
  }

  static convertLegacyAnomaly(legacyAnomaly: any): Anomaly {
    return {
      id: legacyAnomaly.id || '',
      nodeIndex: legacyAnomaly.node || 0,
      type: this.convertAnomalyType(legacyAnomaly.type),
      severity: this.convertAnomalySeverity(legacyAnomaly.severity),
      description: legacyAnomaly.description || '',
      confidence: legacyAnomaly.confidence || 0,
      detectedAt: legacyAnomaly.detectedAt ? dateToTimestamp(new Date(legacyAnomaly.detectedAt)) : nowTimestamp(),
      acknowledged: legacyAnomaly.acknowledged || false,
      metadata: legacyAnomaly.metadata || {},
    };
  }

  private static convertNodeType(type: string): NodeType {
    switch (type) {
      case 'compute': return NodeType.COMPUTE;
      case 'storage': return NodeType.STORAGE;
      case 'network': return NodeType.NETWORK;
      case 'coordinator': return NodeType.COORDINATOR;
      default: return NodeType.UNSPECIFIED;
    }
  }

  private static convertNodeStatus(status: string): NodeStatus {
    switch (status) {
      case 'online': return NodeStatus.ONLINE;
      case 'offline': return NodeStatus.OFFLINE;
      case 'maintenance': return NodeStatus.MAINTENANCE;
      case 'error': return NodeStatus.ERROR;
      default: return NodeStatus.UNSPECIFIED;
    }
  }

  private static convertAgentType(type: string): AgentType {
    switch (type) {
      case 'monitor': return AgentType.MONITOR;
      case 'processor': return AgentType.PROCESSOR;
      case 'analyzer': return AgentType.ANALYZER;
      case 'coordinator': return AgentType.COORDINATOR;
      default: return AgentType.UNSPECIFIED;
    }
  }

  private static convertAgentStatus(status: string): AgentStatus {
    switch (status) {
      case 'active': return AgentStatus.ACTIVE;
      case 'idle': return AgentStatus.IDLE;
      case 'deploying': return AgentStatus.DEPLOYING;
      case 'stopping': return AgentStatus.STOPPING;
      case 'error': return AgentStatus.ERROR;
      default: return AgentStatus.UNSPECIFIED;
    }
  }

  private static convertFlowStatus(status: string): FlowStatus {
    switch (status) {
      case 'active': return FlowStatus.ACTIVE;
      case 'congested': return FlowStatus.CONGESTED;
      case 'error': return FlowStatus.ERROR;
      case 'inactive': return FlowStatus.INACTIVE;
      default: return FlowStatus.UNSPECIFIED;
    }
  }

  private static convertAnomalyType(type: string): AnomalyType {
    switch (type) {
      case 'performance': return AnomalyType.PERFORMANCE;
      case 'security': return AnomalyType.SECURITY;
      case 'connectivity': return AnomalyType.CONNECTIVITY;
      case 'resource': return AnomalyType.RESOURCE;
      default: return AnomalyType.UNSPECIFIED;
    }
  }

  private static convertAnomalySeverity(severity: string): AnomalySeverity {
    switch (severity) {
      case 'low': return AnomalySeverity.LOW;
      case 'medium': return AnomalySeverity.MEDIUM;
      case 'high': return AnomalySeverity.HIGH;
      case 'critical': return AnomalySeverity.CRITICAL;
      default: return AnomalySeverity.UNSPECIFIED;
    }
  }
}
