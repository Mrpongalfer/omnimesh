// src/services/realtime.ts
// Enhanced real-time communication service with WebSocket and WebTransport support

import { createSignal } from 'solid-js';
import {
  setNodes,
  setAgents,
  setAnomalies,
  setFlows,
  setNotifications,
  setCriticalOverlay,
} from '../store/appState';

// When Protobuf schemas are available, import the generated message classes:
// import { EventMessage, FabricUpdate, AlertMessage } from '../proto/omnitide_proto';
// import * as protobuf from 'protobufjs';

// Type definitions for real-time events
export interface RealtimeEvent {
  type:
    | 'fabric_update'
    | 'agent_status'
    | 'alert'
    | 'metric_update'
    | 'system_event';
  timestamp: string;
  data: unknown;
  severity?: 'info' | 'warning' | 'error' | 'critical';
  source?: string;
}

export interface ConnectionStatus {
  connected: boolean;
  reconnecting: boolean;
  lastConnected?: string;
  connectionType: 'websocket' | 'webtransport' | 'sse' | 'polling';
  latency?: number;
}

// Real-time event and connection status signals
export const [realtimeEvent, setRealtimeEvent] =
  createSignal<RealtimeEvent | null>(null);
export const [connectionStatus, setConnectionStatus] =
  createSignal<ConnectionStatus>({
    connected: false,
    reconnecting: false,
    connectionType: 'websocket',
  });

// Configuration for real-time connections
const getRealtimeConfig = () => ({
  wsUrl: process.env['VITE_WS_URL'] || 'ws://localhost:8081/ws',
  wtUrl: process.env['VITE_WT_URL'] || 'https://localhost:8082/wt',
  sseUrl: process.env['VITE_SSE_URL'] || 'http://localhost:8080/events',
  apiKey: process.env['VITE_API_KEY'] || '',
  reconnectInterval: 3000,
  maxReconnectAttempts: 10,
  heartbeatInterval: 30000,
});

// Enhanced WebSocket connection with reconnection logic
let ws: WebSocket | null = null;
let reconnectAttempts = 0;
let heartbeatInterval: number | null = null;

export function connectRealtime(): () => void {
  const config = getRealtimeConfig();

  const connect = () => {
    try {
      setConnectionStatus((prev) => ({ ...prev, reconnecting: true }));

      ws = new WebSocket(config.wsUrl);
      ws.binaryType = 'arraybuffer';

      ws.onopen = () => {
        console.info('Real-time connection established');
        reconnectAttempts = 0;
        setConnectionStatus({
          connected: true,
          reconnecting: false,
          lastConnected: new Date().toISOString(),
          connectionType: 'websocket',
        });

        // Start heartbeat
        if (heartbeatInterval) clearInterval(heartbeatInterval);
        heartbeatInterval = window.setInterval(() => {
          if (ws?.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, config.heartbeatInterval);

        // Subscribe to relevant events
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(
            JSON.stringify({
              type: 'subscribe',
              channels: ['fabric_updates', 'agent_status', 'alerts', 'metrics'],
            }),
          );
        }
      };

      ws.onmessage = async (event) => {
        try {
          let eventData: RealtimeEvent;

          if (event.data instanceof ArrayBuffer) {
            // Handle Protobuf binary messages
            try {
              // Import the protobuf client for message decoding
              const { ProtobufClient } = await import('../proto/protobufClient');
              const decodedMessage = ProtobufClient.deserialize(new Uint8Array(event.data));
              
              eventData = {
                type: (decodedMessage.payload?.type as RealtimeEvent['type']) || 'system_event',
                timestamp: decodedMessage.timestamp?.seconds ? 
                  new Date(decodedMessage.timestamp.seconds * 1000).toISOString() : 
                  new Date().toISOString(),
                data: decodedMessage.payload?.data || `Decoded Protobuf event (${event.data.byteLength} bytes)`,
                severity: 'info',
                source: 'protobuf',
              };
            } catch (decodeError) {
              console.warn('Failed to decode Protobuf message, falling back to binary info:', decodeError);
              eventData = {
                type: 'system_event',
                timestamp: new Date().toISOString(),
                data: `Binary Protobuf event (${event.data.byteLength} bytes) - decode failed`,
                severity: 'warning',
                source: 'protobuf-fallback',
              };
            }
          } else {
            // Handle JSON messages
            eventData = JSON.parse(event.data);
          }

          // Update application state based on event type
          handleRealtimeEvent(eventData);
        } catch (error) {
          console.error('Failed to process real-time event:', error);
          setRealtimeEvent({
            type: 'system_event',
            timestamp: new Date().toISOString(),
            data: 'Failed to decode real-time event',
            severity: 'error',
          });
        }
      };

      ws.onerror = (error) => {
        console.error('Real-time connection error:', error);
        setConnectionStatus((prev) => ({ ...prev, connected: false }));
      };

      ws.onclose = (event) => {
        console.warn('Real-time connection closed:', event.code, event.reason);
        setConnectionStatus((prev) => ({ ...prev, connected: false }));

        if (heartbeatInterval) {
          clearInterval(heartbeatInterval);
          heartbeatInterval = null;
        }

        // Attempt reconnection if not intentionally closed
        if (
          event.code !== 1000 &&
          reconnectAttempts < config.maxReconnectAttempts
        ) {
          reconnectAttempts++;
          setTimeout(() => {
            console.log(`Reconnecting... (attempt ${reconnectAttempts})`);
            connect();
          }, config.reconnectInterval * reconnectAttempts);
        }
      };
    } catch (error) {
      console.error('Failed to establish real-time connection:', error);
      setConnectionStatus((prev) => ({
        ...prev,
        connected: false,
        reconnecting: false,
      }));
    }
  };

  // Initial connection
  connect();

  // Return cleanup function
  return () => {
    if (heartbeatInterval) {
      clearInterval(heartbeatInterval);
      heartbeatInterval = null;
    }
    if (ws) {
      ws.close(1000, 'Client disconnecting');
      ws = null;
    }
    setConnectionStatus((prev) => ({
      ...prev,
      connected: false,
      reconnecting: false,
    }));
  };
}

// Process incoming real-time events and update application state
function handleRealtimeEvent(event: RealtimeEvent): void {
  setRealtimeEvent(event);

  switch (event.type) {
    case 'fabric_update':
      // Update nodes, agents, flows based on fabric changes
      if (event.data && typeof event.data === 'object') {
        const update = event.data as any;
        if (update.nodes) setNodes(update.nodes);
        if (update.agents) setAgents(update.agents);
        if (update.flows) setFlows(update.flows);
        if (update.anomalies) setAnomalies(update.anomalies);
      }
      break;

    case 'agent_status':
      // Handle agent status changes
      setNotifications((prev) => [
        `Agent status update: ${JSON.stringify(event.data)}`,
        ...prev.slice(0, 19),
      ]);
      break;

    case 'alert':
      // Handle critical alerts
      const alertData = event.data as any;
      const message = alertData?.message || 'Critical system alert';

      if (event.severity === 'critical') {
        setCriticalOverlay(message);
      }

      setNotifications((prev) => [
        `${event.severity?.toUpperCase() || 'ALERT'}: ${message}`,
        ...prev.slice(0, 19),
      ]);
      break;

    case 'metric_update':
      // Handle performance metrics updates
      // Could update charts, graphs, or performance indicators
      break;

    case 'system_event':
      // Handle general system events
      setNotifications((prev) => [
        `System: ${event.data}`,
        ...prev.slice(0, 19),
      ]);
      break;
  }
}

// Send commands to the backend via WebSocket
export function sendRealtimeCommand(command: {
  type: string;
  target?: string;
  payload?: unknown;
}): boolean {
  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(command));
    return true;
  }
  return false;
}

// Alternative connection methods for fallback

// Server-Sent Events fallback
export function connectSSE(): () => void {
  const config = getRealtimeConfig();
  const eventSource = new EventSource(config.sseUrl);

  eventSource.onopen = () => {
    setConnectionStatus({
      connected: true,
      reconnecting: false,
      lastConnected: new Date().toISOString(),
      connectionType: 'sse',
    });
  };

  eventSource.onmessage = (event) => {
    try {
      const eventData: RealtimeEvent = JSON.parse(event.data);
      handleRealtimeEvent(eventData);
    } catch (error) {
      console.error('Failed to process SSE event:', error);
    }
  };

  eventSource.onerror = () => {
    setConnectionStatus((prev) => ({ ...prev, connected: false }));
  };

  return () => {
    eventSource.close();
  };
}

// Polling fallback for environments without WebSocket/SSE support
export function connectPolling(): () => void {
  const config = getRealtimeConfig();
  let polling = true;

  const poll = async () => {
    while (polling) {
      try {
        const response = await fetch(
          `${config.sseUrl.replace('/events', '/poll')}`,
          {
            headers: config.apiKey
              ? { Authorization: `Bearer ${config.apiKey}` }
              : {},
          },
        );

        if (response.ok) {
          const events: RealtimeEvent[] = await response.json();
          events.forEach(handleRealtimeEvent);

          setConnectionStatus({
            connected: true,
            reconnecting: false,
            lastConnected: new Date().toISOString(),
            connectionType: 'polling',
          });
        }
      } catch (error) {
        console.error('Polling error:', error);
        setConnectionStatus((prev) => ({ ...prev, connected: false }));
      }

      await new Promise((resolve) => setTimeout(resolve, 2000));
    }
  };

  poll();

  return () => {
    polling = false;
  };
}
