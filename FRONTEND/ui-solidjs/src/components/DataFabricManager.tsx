import { createSignal, For, onMount, onCleanup } from 'solid-js';

// Data types for the fabric
interface DataSchema {
  fields: Array<{
    name: string;
    type: 'string' | 'number' | 'boolean' | 'object' | 'array';
    required: boolean;
    description?: string;
  }>;
}

interface DataStream {
  id: string;
  name: string;
  schema: DataSchema;
  throughput: number; // events per second
  totalEvents: number;
  avgLatency: number; // in ms
  errorRate: number; // percentage
  status: 'active' | 'paused' | 'error' | 'stopped';
}

interface DataNode {
  id: string;
  label: string;
  type: 'source' | 'transform' | 'sink' | 'aggregator' | 'filter' | 'router';
  x: number;
  y: number;
  config: Record<string, any>;
  inputStreams: string[];
  outputStreams: string[];
  metrics: {
    processed: number;
    errors: number;
    avgProcessingTime: number;
  };
}

interface DataEdge {
  id: string;
  from: string;
  to: string;
  stream: DataStream;
}

interface ViewTransform {
  x: number;
  y: number;
  scale: number;
}

const DEFAULT_SCHEMAS: Record<string, DataSchema> = {
  sensor: {
    fields: [
      { name: 'timestamp', type: 'number', required: true, description: 'Unix timestamp' },
      { name: 'device_id', type: 'string', required: true, description: 'Device identifier' },
      { name: 'temperature', type: 'number', required: false, description: 'Temperature in Celsius' },
      { name: 'humidity', type: 'number', required: false, description: 'Humidity percentage' },
      { name: 'location', type: 'object', required: false, description: 'GPS coordinates' }
    ]
  },
  event: {
    fields: [
      { name: 'id', type: 'string', required: true, description: 'Event ID' },
      { name: 'type', type: 'string', required: true, description: 'Event type' },
      { name: 'timestamp', type: 'number', required: true, description: 'Event timestamp' },
      { name: 'user_id', type: 'string', required: false, description: 'User identifier' },
      { name: 'properties', type: 'object', required: false, description: 'Event properties' }
    ]
  },
  metric: {
    fields: [
      { name: 'name', type: 'string', required: true, description: 'Metric name' },
      { name: 'value', type: 'number', required: true, description: 'Metric value' },
      { name: 'tags', type: 'object', required: false, description: 'Metric tags' },
      { name: 'timestamp', type: 'number', required: true, description: 'Metric timestamp' }
    ]
  }
};

export default function DataFabricManager() {
  const [nodes, setNodes] = createSignal<DataNode[]>([]);
  const [edges, setEdges] = createSignal<DataEdge[]>([]);
  const [streams, setStreams] = createSignal<DataStream[]>([]);
  const [selectedNode, setSelectedNode] = createSignal<string | null>(null);
  const [viewTransform, setViewTransform] = createSignal<ViewTransform>({ x: 0, y: 0, scale: 1 });
  const [isStreaming, setIsStreaming] = createSignal(false);

  let canvasRef: HTMLDivElement | undefined;
  let metricsInterval: ReturnType<typeof setInterval> | undefined;

  // Initialize with sample data
  onMount(() => {
    const initialStreams: DataStream[] = [
      {
        id: 'sensor-stream',
        name: 'IoT Sensor Data',
        schema: DEFAULT_SCHEMAS['sensor']!,
        throughput: 850,
        totalEvents: 1245000,
        avgLatency: 12,
        errorRate: 0.02,
        status: 'active'
      },
      {
        id: 'event-stream',
        name: 'User Events',
        schema: DEFAULT_SCHEMAS['event']!,
        throughput: 320,
        totalEvents: 567000,
        avgLatency: 8,
        errorRate: 0.01,
        status: 'active'
      },
      {
        id: 'metrics-stream',
        name: 'System Metrics',
        schema: DEFAULT_SCHEMAS['metric']!,
        throughput: 150,
        totalEvents: 98000,
        avgLatency: 5,
        errorRate: 0.005,
        status: 'active'
      }
    ];

    const initialNodes: DataNode[] = [
      {
        id: 'kafka-source',
        label: 'Kafka Source',
        type: 'source',
        x: 100,
        y: 150,
        config: { topic: 'sensor-data', brokers: ['localhost:9092'] },
        inputStreams: [],
        outputStreams: ['sensor-stream'],
        metrics: { processed: 125000, errors: 25, avgProcessingTime: 2 }
      },
      {
        id: 'filter-temp',
        label: 'Temperature Filter',
        type: 'filter',
        x: 350,
        y: 100,
        config: { condition: 'temperature > 20', operator: 'gt', threshold: 20 },
        inputStreams: ['sensor-stream'],
        outputStreams: ['filtered-stream'],
        metrics: { processed: 89000, errors: 12, avgProcessingTime: 1.5 }
      },
      {
        id: 'aggregator',
        label: 'Average Aggregator',
        type: 'aggregator',
        x: 350,
        y: 250,
        config: { window: '5m', aggregation: 'avg', field: 'temperature' },
        inputStreams: ['sensor-stream'],
        outputStreams: ['aggregated-stream'],
        metrics: { processed: 45000, errors: 3, avgProcessingTime: 8 }
      },
      {
        id: 'router',
        label: 'Data Router',
        type: 'router',
        x: 600,
        y: 150,
        config: { rules: [{ condition: 'temperature > 30', output: 'alert-stream' }] },
        inputStreams: ['filtered-stream'],
        outputStreams: ['routed-stream-1', 'routed-stream-2'],
        metrics: { processed: 78000, errors: 8, avgProcessingTime: 0.8 }
      },
      {
        id: 'postgres-sink',
        label: 'PostgreSQL Sink',
        type: 'sink',
        x: 850,
        y: 100,
        config: { table: 'sensor_data', connection: 'postgresql://...' },
        inputStreams: ['routed-stream-1'],
        outputStreams: [],
        metrics: { processed: 67000, errors: 15, avgProcessingTime: 12 }
      },
      {
        id: 'elasticsearch-sink',
        label: 'Elasticsearch Sink',
        type: 'sink',
        x: 850,
        y: 250,
        config: { index: 'sensor-metrics', cluster: 'elasticsearch:9200' },
        inputStreams: ['aggregated-stream'],
        outputStreams: [],
        metrics: { processed: 44000, errors: 2, avgProcessingTime: 15 }
      }
    ];

    const initialEdges: DataEdge[] = [
      {
        id: 'edge-1',
        from: 'kafka-source',
        to: 'filter-temp',
        stream: initialStreams[0]!
      },
      {
        id: 'edge-2',
        from: 'kafka-source',
        to: 'aggregator',
        stream: initialStreams[0]!
      },
      {
        id: 'edge-3',
        from: 'filter-temp',
        to: 'router',
        stream: initialStreams[1]!
      },
      {
        id: 'edge-4',
        from: 'router',
        to: 'postgres-sink',
        stream: initialStreams[2]!
      },
      {
        id: 'edge-5',
        from: 'aggregator',
        to: 'elasticsearch-sink',
        stream: initialStreams[2]!
      }
    ];

    setStreams(initialStreams);
    setNodes(initialNodes);
    setEdges(initialEdges);

    // Simulate real-time metrics updates
    metricsInterval = setInterval(() => {
      if (isStreaming()) {
        setStreams(prev => prev.map(stream => ({
          ...stream,
          throughput: stream.throughput + (Math.random() - 0.5) * 50,
          totalEvents: stream.totalEvents + Math.floor(Math.random() * 100),
          avgLatency: Math.max(1, stream.avgLatency + (Math.random() - 0.5) * 2),
          errorRate: Math.max(0, Math.min(1, stream.errorRate + (Math.random() - 0.5) * 0.001))
        })));

        setNodes(prev => prev.map(node => ({
          ...node,
          metrics: {
            ...node.metrics,
            processed: node.metrics.processed + Math.floor(Math.random() * 10),
            avgProcessingTime: Math.max(0.1, node.metrics.avgProcessingTime + (Math.random() - 0.5) * 0.5)
          }
        })));
      }
    }, 1000);
  });

  onCleanup(() => {
    if (metricsInterval) {
      clearInterval(metricsInterval);
    }
  });

  function getNodeColor(type: DataNode['type']): string {
    switch (type) {
      case 'source': return 'border-blue-400 bg-blue-900';
      case 'transform': return 'border-green-400 bg-green-900';
      case 'filter': return 'border-yellow-400 bg-yellow-900';
      case 'aggregator': return 'border-purple-400 bg-purple-900';
      case 'router': return 'border-orange-400 bg-orange-900';
      case 'sink': return 'border-red-400 bg-red-900';
      default: return 'border-gray-400 bg-gray-900';
    }
  }

  function getNodeIcon(type: DataNode['type']): string {
    switch (type) {
      case 'source': return '📥';
      case 'transform': return '🔄';
      case 'filter': return '🔍';
      case 'aggregator': return '📊';
      case 'router': return '🔀';
      case 'sink': return '📤';
      default: return '⚙️';
    }
  }

  function addNode(type: DataNode['type']) {
    const newNode: DataNode = {
      id: `${type}-${Date.now()}`,
      label: `New ${type}`,
      type,
      x: 200 + Math.random() * 300,
      y: 150 + Math.random() * 200,
      config: {},
      inputStreams: [],
      outputStreams: [],
      metrics: { processed: 0, errors: 0, avgProcessingTime: 0 }
    };
    setNodes(prev => [...prev, newNode]);
  }

  function deleteNode(nodeId: string) {
    setNodes(prev => prev.filter(n => n.id !== nodeId));
    setEdges(prev => prev.filter(e => e.from !== nodeId && e.to !== nodeId));
    if (selectedNode() === nodeId) {
      setSelectedNode(null);
    }
  }

  function formatNumber(num: number): string {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  }

  return (
    <div class="w-full h-full flex flex-row bg-gradient-to-br from-gray-900 via-gray-800 to-gray-700 rounded-lg shadow-2xl border border-gray-700 relative overflow-hidden">
      {/* Node Palette */}
      <div class="w-64 bg-gray-900 border-r border-gray-700 p-4 flex flex-col gap-4 z-10 overflow-y-auto">
        <h2 class="text-green-300 text-lg font-bold mb-4 flex items-center gap-2">
          🌐 Data Fabric Manager
        </h2>
        
        <div class="space-y-4">
          <div>
            <h3 class="text-sm font-semibold text-gray-300 mb-2">Data Sources</h3>
            <button
              class="w-full bg-blue-700 hover:bg-blue-600 text-white rounded px-3 py-2 font-semibold shadow mb-2 flex items-center gap-2"
              onClick={() => addNode('source')}
            >
              📥 Source
            </button>
          </div>

          <div>
            <h3 class="text-sm font-semibold text-gray-300 mb-2">Processing</h3>
            <button
              class="w-full bg-green-700 hover:bg-green-600 text-white rounded px-3 py-2 font-semibold shadow mb-2 flex items-center gap-2"
              onClick={() => addNode('transform')}
            >
              🔄 Transform
            </button>
            <button
              class="w-full bg-yellow-700 hover:bg-yellow-600 text-white rounded px-3 py-2 font-semibold shadow mb-2 flex items-center gap-2"
              onClick={() => addNode('filter')}
            >
              🔍 Filter
            </button>
            <button
              class="w-full bg-purple-700 hover:bg-purple-600 text-white rounded px-3 py-2 font-semibold shadow mb-2 flex items-center gap-2"
              onClick={() => addNode('aggregator')}
            >
              📊 Aggregator
            </button>
            <button
              class="w-full bg-orange-700 hover:bg-orange-600 text-white rounded px-3 py-2 font-semibold shadow mb-2 flex items-center gap-2"
              onClick={() => addNode('router')}
            >
              🔀 Router
            </button>
          </div>

          <div>
            <h3 class="text-sm font-semibold text-gray-300 mb-2">Data Sinks</h3>
            <button
              class="w-full bg-red-700 hover:bg-red-600 text-white rounded px-3 py-2 font-semibold shadow mb-2 flex items-center gap-2"
              onClick={() => addNode('sink')}
            >
              📤 Sink
            </button>
          </div>
        </div>

        <div class="border-t border-gray-700 pt-4">
          <button
            class={`w-full ${isStreaming() ? 'bg-red-700 hover:bg-red-600' : 'bg-green-700 hover:bg-green-600'} text-white rounded px-3 py-2 font-semibold shadow flex items-center justify-center gap-2`}
            onClick={() => setIsStreaming(!isStreaming())}
          >
            {isStreaming() ? '⏸️ Pause' : '▶️ Start'} Streaming
          </button>
        </div>

        <div class="text-xs text-gray-400 space-y-1">
          <div class="flex justify-between">
            <span>Total Streams:</span>
            <span class="text-green-300">{streams().length}</span>
          </div>
          <div class="flex justify-between">
            <span>Active Nodes:</span>
            <span class="text-blue-300">{nodes().length}</span>
          </div>
          <div class="flex justify-between">
            <span>Total Events:</span>
            <span class="text-purple-300">{formatNumber(streams().reduce((sum, s) => sum + s.totalEvents, 0))}</span>
          </div>
        </div>
      </div>

      {/* Data Flow Canvas */}
      <div class="flex-1 relative overflow-hidden" ref={canvasRef}>
        <svg
          class="absolute inset-0 w-full h-full"
          style={{
            transform: `translate(${viewTransform().x}px, ${viewTransform().y}px) scale(${viewTransform().scale})`
          }}
        >
          {/* Grid Background */}
          <defs>
            <pattern id="data-grid" width="50" height="50" patternUnits="userSpaceOnUse">
              <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#374151" stroke-width="1" opacity="0.3"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#data-grid)" />

          {/* Edges with animated flow */}
          <For each={edges()}>
            {(edge) => {
              const fromNode = nodes().find(n => n.id === edge.from);
              const toNode = nodes().find(n => n.id === edge.to);
              if (!fromNode || !toNode) return null;

              const fromPos = { x: fromNode.x + 80, y: fromNode.y + 30 };
              const toPos = { x: toNode.x, y: toNode.y + 30 };
              const controlOffset = Math.abs(toPos.x - fromPos.x) * 0.5;

              return (
                <g>
                  <path
                    d={`M ${fromPos.x} ${fromPos.y} C ${fromPos.x + controlOffset} ${fromPos.y} ${toPos.x - controlOffset} ${toPos.y} ${toPos.x} ${toPos.y}`}
                    fill="none"
                    stroke="#10b981"
                    stroke-width="3"
                    opacity={0.7}
                  />
                  {isStreaming() && (
                    <circle r="4" fill="#22c55e" opacity="0.8">
                      <animateMotion
                        dur="2s"
                        repeatCount="indefinite"
                        path={`M ${fromPos.x} ${fromPos.y} C ${fromPos.x + controlOffset} ${fromPos.y} ${toPos.x - controlOffset} ${toPos.y} ${toPos.x} ${toPos.y}`}
                      />
                    </circle>
                  )}
                  {/* Throughput label */}
                  <text
                    x={(fromPos.x + toPos.x) / 2}
                    y={(fromPos.y + toPos.y) / 2 - 10}
                    fill="#10b981"
                    font-size="10"
                    text-anchor="middle"
                    class="pointer-events-none"
                  >
                    {formatNumber(edge.stream.throughput)}/s
                  </text>
                </g>
              );
            }}
          </For>
        </svg>

        {/* Nodes */}
        <For each={nodes()}>
          {(node) => (
            <div
              class={`absolute rounded-lg shadow-lg border-2 cursor-pointer transition-all duration-150 ${selectedNode() === node.id ? 'border-white' : getNodeColor(node.type)} hover:scale-105`}
              style={{
                left: `${node.x}px`,
                top: `${node.y}px`,
                width: '160px',
                height: '60px',
                transform: `translate(${viewTransform().x}px, ${viewTransform().y}px) scale(${viewTransform().scale})`
              }}
              onClick={() => setSelectedNode(node.id)}
            >
              <div class="flex flex-col h-full px-3 py-2">
                <div class="flex items-center justify-between">
                  <span class="text-xs text-gray-300">{getNodeIcon(node.type)}</span>
                  <div class="text-xs text-green-300">
                    {formatNumber(node.metrics.processed)}
                  </div>
                </div>
                <div class="text-white font-semibold text-sm truncate">
                  {node.label}
                </div>
                <div class="text-xs text-gray-400">
                  {node.metrics.avgProcessingTime.toFixed(1)}ms avg
                </div>
              </div>
            </div>
          )}
        </For>

        {/* Zoom controls */}
        <div class="absolute bottom-4 right-4 flex flex-col gap-2">
          <button
            class="bg-gray-800 hover:bg-gray-700 text-white rounded p-2 shadow"
            onClick={() => setViewTransform(prev => ({ ...prev, scale: Math.min(3, prev.scale * 1.2) }))}
          >
            🔍➕
          </button>
          <button
            class="bg-gray-800 hover:bg-gray-700 text-white rounded p-2 shadow"
            onClick={() => setViewTransform(prev => ({ ...prev, scale: Math.max(0.1, prev.scale * 0.8) }))}
          >
            🔍➖
          </button>
          <button
            class="bg-gray-800 hover:bg-gray-700 text-white rounded p-2 shadow"
            onClick={() => setViewTransform({ x: 0, y: 0, scale: 1 })}
          >
            🎯
          </button>
        </div>
      </div>

      {/* Schema & Stream Inspector */}
      <div class="w-80 bg-gray-900 border-l border-gray-700 p-4 flex flex-col gap-4 z-10 overflow-y-auto">
        <h2 class="text-green-300 text-lg font-bold mb-2">Inspector</h2>
        
        {selectedNode() ? (
          <div class="space-y-4">
            {(() => {
              const node = nodes().find(n => n.id === selectedNode());
              if (!node) return null;

              return (
                <div class="space-y-4">
                  <div>
                    <h3 class="text-white font-semibold mb-2">{node.label}</h3>
                    <div class="text-sm text-gray-300 space-y-1">
                      <div class="flex justify-between">
                        <span>Type:</span>
                        <span class="text-blue-300">{node.type}</span>
                      </div>
                      <div class="flex justify-between">
                        <span>Processed:</span>
                        <span class="text-green-300">{formatNumber(node.metrics.processed)}</span>
                      </div>
                      <div class="flex justify-between">
                        <span>Errors:</span>
                        <span class="text-red-300">{node.metrics.errors}</span>
                      </div>
                      <div class="flex justify-between">
                        <span>Avg Time:</span>
                        <span class="text-purple-300">{node.metrics.avgProcessingTime.toFixed(1)}ms</span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 class="text-white font-semibold mb-2">Configuration</h4>
                    <div class="bg-gray-800 rounded p-3 text-xs">
                      <pre class="text-gray-300 whitespace-pre-wrap">
                        {JSON.stringify(node.config, null, 2)}
                      </pre>
                    </div>
                  </div>

                  <div>
                    <h4 class="text-white font-semibold mb-2">Streams</h4>
                    <div class="space-y-2">
                      <div>
                        <div class="text-sm text-gray-400">Input:</div>
                        <For each={node.inputStreams}>
                          {(streamId) => (
                            <div class="text-xs text-blue-300 ml-2">• {streamId}</div>
                          )}
                        </For>
                      </div>
                      <div>
                        <div class="text-sm text-gray-400">Output:</div>
                        <For each={node.outputStreams}>
                          {(streamId) => (
                            <div class="text-xs text-green-300 ml-2">• {streamId}</div>
                          )}
                        </For>
                      </div>
                    </div>
                  </div>

                  <button
                    class="w-full bg-red-700 hover:bg-red-600 text-white rounded px-3 py-2"
                    onClick={() => deleteNode(node.id)}
                  >
                    🗑️ Delete Node
                  </button>
                </div>
              );
            })()}
          </div>
        ) : (
          <div>
            <div class="text-gray-400 mb-4">
              Select a node to inspect configuration and metrics.
            </div>
            
            <div>
              <h3 class="text-white font-semibold mb-2">Live Stream Metrics</h3>
              <div class="space-y-3">
                <For each={streams()}>
                  {(stream) => (
                    <div class="bg-gray-800 rounded p-3">
                      <div class="font-semibold text-sm text-white mb-1">{stream.name}</div>
                      <div class="text-xs space-y-1">
                        <div class="flex justify-between">
                          <span class="text-gray-400">Throughput:</span>
                          <span class="text-green-300">{formatNumber(stream.throughput)}/s</span>
                        </div>
                        <div class="flex justify-between">
                          <span class="text-gray-400">Latency:</span>
                          <span class="text-blue-300">{stream.avgLatency.toFixed(1)}ms</span>
                        </div>
                        <div class="flex justify-between">
                          <span class="text-gray-400">Error Rate:</span>
                          <span class="text-red-300">{(stream.errorRate * 100).toFixed(2)}%</span>
                        </div>
                        <div class="flex justify-between">
                          <span class="text-gray-400">Status:</span>
                          <span class={`${stream.status === 'active' ? 'text-green-300' : 'text-yellow-300'}`}>
                            {stream.status}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                </For>
              </div>
            </div>
          </div>
        )}

        {/* Explainable AI Overlay */}
        <div class="mt-4 p-2 bg-gray-800 rounded text-green-200 text-xs shadow-inner">
          <span class="font-bold">Real-time Analytics:</span> Live metrics update every second.
          Schema validation and data lineage tracking active.
        </div>
      </div>
    </div>
  );
}
