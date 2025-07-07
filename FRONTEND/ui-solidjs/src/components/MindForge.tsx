import { createSignal, For, onMount, onCleanup, createEffect } from 'solid-js';

// Advanced agent workflow designer with node graph functionality
// Provides visual programming interface for agent behavior configuration

interface WorkflowNode {
  id: string;
  type: 'input' | 'logic' | 'action' | 'condition' | 'loop' | 'variable';
  label: string;
  x: number;
  y: number;
  width: number;
  height: number;
  inputs: NodePort[];
  outputs: NodePort[];
  properties: Record<string, any>;
  selected: boolean;
}

interface NodePort {
  id: string;
  label: string;
  type: 'data' | 'execution' | 'condition';
  dataType?: 'string' | 'number' | 'boolean' | 'object' | 'array';
  required: boolean;
}

interface WorkflowEdge {
  id: string;
  from: { nodeId: string; portId: string };
  to: { nodeId: string; portId: string };
  type: 'data' | 'execution';
  label?: string;
}

interface NodeTemplate {
  type: string;
  label: string;
  category: 'Input' | 'Logic' | 'Action' | 'Control';
  description: string;
  icon: string;
  defaultProps: Record<string, any>;
  inputs: Omit<NodePort, 'id'>[];
  outputs: Omit<NodePort, 'id'>[];
}

export default function MindForge() {
  // State management
  const [nodes, setNodes] = createSignal<WorkflowNode[]>([]);
  const [edges, setEdges] = createSignal<WorkflowEdge[]>([]);
  const [selectedNode, setSelectedNode] = createSignal<string | null>(null);
  const [selectedEdge, setSelectedEdge] = createSignal<string | null>(null);
  const [dragState, setDragState] = createSignal<{
    isDragging: boolean;
    dragType: 'node' | 'edge' | 'canvas' | 'selection';
    startPos: { x: number; y: number };
    offset: { x: number; y: number };
    nodeId?: string;
  } | null>(null);
  const [viewTransform, setViewTransform] = createSignal({ x: 0, y: 0, scale: 1 });
  const [isConnecting, setIsConnecting] = createSignal<{
    fromNodeId: string;
    fromPortId: string;
    tempToPos: { x: number; y: number };
  } | null>(null);

  let canvasRef: HTMLDivElement | undefined;
  let svgRef: SVGSVGElement | undefined;

  // Node templates for the palette
  const nodeTemplates: NodeTemplate[] = [
    {
      type: 'input',
      label: 'Start',
      category: 'Input',
      description: 'Entry point for agent workflow',
      icon: '▶️',
      defaultProps: { trigger: 'manual' },
      inputs: [],
      outputs: [{ label: 'Execute', type: 'execution', required: false }]
    },
    {
      type: 'condition',
      label: 'If/Then',
      category: 'Logic',
      description: 'Conditional branching logic',
      icon: '❓',
      defaultProps: { condition: 'value > 0' },
      inputs: [
        { label: 'Execute', type: 'execution', required: true },
        { label: 'Value', type: 'data', dataType: 'number', required: true }
      ],
      outputs: [
        { label: 'True', type: 'execution', required: false },
        { label: 'False', type: 'execution', required: false }
      ]
    },
    {
      type: 'action',
      label: 'Execute Task',
      category: 'Action',
      description: 'Perform a specific action',
      icon: '⚡',
      defaultProps: { task: 'scan_network', timeout: 30000 },
      inputs: [
        { label: 'Execute', type: 'execution', required: true },
        { label: 'Parameters', type: 'data', dataType: 'object', required: false }
      ],
      outputs: [
        { label: 'Success', type: 'execution', required: false },
        { label: 'Error', type: 'execution', required: false },
        { label: 'Result', type: 'data', dataType: 'object', required: false }
      ]
    },
    {
      type: 'loop',
      label: 'For Each',
      category: 'Control',
      description: 'Iterate over collection',
      icon: '🔄',
      defaultProps: { maxIterations: 100 },
      inputs: [
        { label: 'Execute', type: 'execution', required: true },
        { label: 'Collection', type: 'data', dataType: 'array', required: true }
      ],
      outputs: [
        { label: 'Each Item', type: 'execution', required: false },
        { label: 'Complete', type: 'execution', required: false },
        { label: 'Current Item', type: 'data', dataType: 'object', required: false }
      ]
    },
    {
      type: 'variable',
      label: 'Variable',
      category: 'Logic',
      description: 'Store and retrieve values',
      icon: '📝',
      defaultProps: { variableName: 'result', initialValue: '' },
      inputs: [
        { label: 'Set', type: 'execution', required: false },
        { label: 'Value', type: 'data', dataType: 'object', required: false }
      ],
      outputs: [
        { label: 'Get', type: 'data', dataType: 'object', required: false }
      ]
    },
    {
      type: 'logic',
      label: 'Transform',
      category: 'Logic',
      description: 'Transform data between formats',
      icon: '🔧',
      defaultProps: { transformation: 'json_to_object' },
      inputs: [
        { label: 'Execute', type: 'execution', required: true },
        { label: 'Input', type: 'data', dataType: 'object', required: true }
      ],
      outputs: [
        { label: 'Success', type: 'execution', required: false },
        { label: 'Output', type: 'data', dataType: 'object', required: false }
      ]
    }
  ];

  // Initialize with sample workflow
  onMount(() => {
    if (nodeTemplates.length < 3) return; // Ensure we have enough templates
    
    const initialNodes: WorkflowNode[] = [
      createNodeFromTemplate(nodeTemplates[0]!, { x: 100, y: 200 }),
      createNodeFromTemplate(nodeTemplates[1]!, { x: 300, y: 200 }),
      createNodeFromTemplate(nodeTemplates[2]!, { x: 500, y: 150 }),
      createNodeFromTemplate(nodeTemplates[2]!, { x: 500, y: 250 })
    ];

    const initialEdges: WorkflowEdge[] = [
      {
        id: 'edge-1',
        from: { nodeId: initialNodes[0]!.id, portId: initialNodes[0]!.outputs[0]!.id },
        to: { nodeId: initialNodes[1]!.id, portId: initialNodes[1]!.inputs[0]!.id },
        type: 'execution'
      },
      {
        id: 'edge-2',
        from: { nodeId: initialNodes[1]!.id, portId: initialNodes[1]!.outputs[0]!.id },
        to: { nodeId: initialNodes[2]!.id, portId: initialNodes[2]!.inputs[0]!.id },
        type: 'execution',
        label: 'True'
      },
      {
        id: 'edge-3',
        from: { nodeId: initialNodes[1]!.id, portId: initialNodes[1]!.outputs[1]!.id },
        to: { nodeId: initialNodes[3]!.id, portId: initialNodes[3]!.inputs[0]!.id },
        type: 'execution',
        label: 'False'
      }
    ];

    setNodes(initialNodes);
    setEdges(initialEdges);
  });

  // Create node from template
  function createNodeFromTemplate(template: NodeTemplate, position: { x: number; y: number }): WorkflowNode {
    const nodeId = `node_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    return {
      id: nodeId,
      type: template.type as WorkflowNode['type'],
      label: template.label,
      x: position.x,
      y: position.y,
      width: 160,
      height: 80 + (Math.max(template.inputs.length, template.outputs.length) * 20),
      inputs: template.inputs.map((input, index) => ({
        ...input,
        id: `${nodeId}_input_${index}`
      })),
      outputs: template.outputs.map((output, index) => ({
        ...output,
        id: `${nodeId}_output_${index}`
      })),
      properties: { ...template.defaultProps },
      selected: false
    };
  }

  // Mouse event handlers
  function handleMouseDown(event: MouseEvent) {
    const target = event.target as Element;
    const rect = canvasRef?.getBoundingClientRect();
    if (!rect) return;

    const pos = {
      x: (event.clientX - rect.left - viewTransform().x) / viewTransform().scale,
      y: (event.clientY - rect.top - viewTransform().y) / viewTransform().scale
    };

    // Check if clicking on a node
    const nodeElement = target.closest('[data-node-id]');
    if (nodeElement) {
      const nodeId = nodeElement.getAttribute('data-node-id')!;
      const node = nodes().find(n => n.id === nodeId);
      if (node) {
        setSelectedNode(nodeId);
        setDragState({
          isDragging: true,
          dragType: 'node',
          startPos: pos,
          offset: { x: pos.x - node.x, y: pos.y - node.y },
          nodeId
        });
        return;
      }
    }

    // Check if clicking on a connection port
    const portElement = target.closest('[data-port-id]');
    if (portElement) {
      const nodeId = portElement.getAttribute('data-node-id')!;
      const portId = portElement.getAttribute('data-port-id')!;
      const portType = portElement.getAttribute('data-port-type') as 'input' | 'output';
      
      if (portType === 'output') {
        setIsConnecting({
          fromNodeId: nodeId,
          fromPortId: portId,
          tempToPos: pos
        });
      } else if (isConnecting()) {
        // Complete connection
        const newEdge: WorkflowEdge = {
          id: `edge_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          from: { nodeId: isConnecting()!.fromNodeId, portId: isConnecting()!.fromPortId },
          to: { nodeId, portId },
          type: 'execution'
        };
        setEdges(prev => [...prev, newEdge]);
        setIsConnecting(null);
      }
      return;
    }

    // Canvas panning
    setSelectedNode(null);
    setSelectedEdge(null);
    setDragState({
      isDragging: true,
      dragType: 'canvas',
      startPos: pos,
      offset: { x: 0, y: 0 }
    });
  }

  function handleMouseMove(event: MouseEvent) {
    const rect = canvasRef?.getBoundingClientRect();
    if (!rect) return;

    const pos = {
      x: (event.clientX - rect.left - viewTransform().x) / viewTransform().scale,
      y: (event.clientY - rect.top - viewTransform().y) / viewTransform().scale
    };

    const drag = dragState();
    if (drag?.isDragging) {
      if (drag.dragType === 'node' && drag.nodeId) {
        setNodes(prev => prev.map(node => 
          node.id === drag.nodeId 
            ? { ...node, x: pos.x - drag.offset.x, y: pos.y - drag.offset.y }
            : node
        ));
      } else if (drag.dragType === 'canvas') {
        const deltaX = (pos.x - drag.startPos.x) * viewTransform().scale;
        const deltaY = (pos.y - drag.startPos.y) * viewTransform().scale;
        setViewTransform(prev => ({
          ...prev,
          x: prev.x + deltaX,
          y: prev.y + deltaY
        }));
      }
    }

    if (isConnecting()) {
      setIsConnecting(prev => prev ? { ...prev, tempToPos: pos } : null);
    }
  }

  function handleMouseUp() {
    setDragState(null);
  }

  function handleWheel(event: WheelEvent) {
    event.preventDefault();
    const scaleFactor = event.deltaY > 0 ? 0.9 : 1.1;
    const newScale = Math.max(0.1, Math.min(3, viewTransform().scale * scaleFactor));
    
    setViewTransform(prev => ({
      ...prev,
      scale: newScale
    }));
  }

  // Add node from palette
  function addNode(template: NodeTemplate) {
    const newNode = createNodeFromTemplate(template, { 
      x: (200 - viewTransform().x) / viewTransform().scale, 
      y: (200 - viewTransform().y) / viewTransform().scale 
    });
    setNodes(prev => [...prev, newNode]);
  }

  // Delete selected node
  function deleteSelectedNode() {
    const selected = selectedNode();
    if (selected) {
      setNodes(prev => prev.filter(n => n.id !== selected));
      setEdges(prev => prev.filter(e => 
        e.from.nodeId !== selected && e.to.nodeId !== selected
      ));
      setSelectedNode(null);
    }
  }

  // Keyboard shortcuts
  createEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Delete' || event.key === 'Backspace') {
        deleteSelectedNode();
      } else if (event.key === 'Escape') {
        setSelectedNode(null);
        setSelectedEdge(null);
        setIsConnecting(null);
      }
    }

    document.addEventListener('keydown', handleKeyDown);
    onCleanup(() => document.removeEventListener('keydown', handleKeyDown));
  });

  // Setup mouse events
  createEffect(() => {
    if (canvasRef) {
      canvasRef.addEventListener('mousedown', handleMouseDown);
      canvasRef.addEventListener('mousemove', handleMouseMove);
      canvasRef.addEventListener('mouseup', handleMouseUp);
      canvasRef.addEventListener('wheel', handleWheel);

      onCleanup(() => {
        canvasRef?.removeEventListener('mousedown', handleMouseDown);
        canvasRef?.removeEventListener('mousemove', handleMouseMove);
        canvasRef?.removeEventListener('mouseup', handleMouseUp);
        canvasRef?.removeEventListener('wheel', handleWheel);
      });
    }
  });

  // Get port position
  function getPortPosition(nodeId: string, portId: string, portType: 'input' | 'output') {
    const node = nodes().find(n => n.id === nodeId);
    if (!node) return { x: 0, y: 0 };

    const ports = portType === 'input' ? node.inputs : node.outputs;
    const portIndex = ports.findIndex(p => p.id === portId);
    const x = portType === 'input' ? node.x : node.x + node.width;
    const y = node.y + 40 + (portIndex * 25);

    return { x, y };
  }

  return (
    <div class="w-full h-full flex flex-row bg-gradient-to-br from-gray-900 via-gray-800 to-gray-700 rounded-lg shadow-2xl border border-gray-700 relative overflow-hidden">
      {/* Node Palette */}
      <div class="w-64 bg-gray-900 border-r border-gray-700 p-4 flex flex-col gap-2 z-10 overflow-y-auto">
        <h2 class="text-blue-300 text-lg font-bold mb-4 flex items-center gap-2">
          🧠 Agent Workflow Designer
        </h2>
        
        <div class="space-y-4">
          <For each={Object.keys(nodeTemplates.reduce((acc, template) => { acc[template.category] = true; return acc; }, {} as Record<string, boolean>))}>
            {(category) => (
              <div>
                <h3 class="text-sm font-semibold text-gray-300 mb-2">{category}</h3>
                <div class="space-y-1">
                  <For each={nodeTemplates.filter(t => t.category === category)}>
                    {(template) => (
                      <button
                        class="w-full bg-gray-800 hover:bg-blue-700 text-white rounded px-3 py-2 font-semibold shadow text-left transition-colors duration-150 flex items-center gap-2"
                        onClick={() => addNode(template)}
                        title={template.description}
                      >
                        <span class="text-lg">{template.icon}</span>
                        <div class="flex-1">
                          <div class="text-sm">{template.label}</div>
                          <div class="text-xs text-gray-400 truncate">{template.description}</div>
                        </div>
                      </button>
                    )}
                  </For>
                </div>
              </div>
            )}
          </For>
        </div>

        {/* Quick Actions */}
        <div class="mt-auto pt-4 border-t border-gray-700">
          <h3 class="text-sm font-semibold text-gray-300 mb-2">Actions</h3>
          <div class="space-y-2">
            <button 
              class="w-full bg-green-700 hover:bg-green-600 text-white rounded px-3 py-2 text-sm"
              onClick={() => console.log('Export workflow:', { nodes: nodes(), edges: edges() })}
            >
              💾 Export Workflow
            </button>
            <button 
              class="w-full bg-blue-700 hover:bg-blue-600 text-white rounded px-3 py-2 text-sm"
              onClick={() => console.log('Validate workflow')}
            >
              ✅ Validate
            </button>
            <button 
              class="w-full bg-purple-700 hover:bg-purple-600 text-white rounded px-3 py-2 text-sm"
              onClick={() => setNodes([])}
            >
              🗑️ Clear All
            </button>
          </div>
        </div>
      </div>

      {/* Workflow Canvas */}
      <div class="flex-1 relative overflow-hidden" ref={canvasRef}>
        <svg
          ref={svgRef}
          class="absolute inset-0 w-full h-full"
          style={{ 
            cursor: dragState()?.isDragging ? 'grabbing' : 'grab',
            transform: `translate(${viewTransform().x}px, ${viewTransform().y}px) scale(${viewTransform().scale})`
          }}
        >
          {/* Grid Background */}
          <defs>
            <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
              <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#374151" stroke-width="1" opacity="0.3"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />

          {/* Edges */}
          <For each={edges()}>
            {(edge) => {
              const fromPos = getPortPosition(edge.from.nodeId, edge.from.portId, 'output');
              const toPos = getPortPosition(edge.to.nodeId, edge.to.portId, 'input');
              const controlOffset = Math.abs(toPos.x - fromPos.x) * 0.5;
              
              return (
                <g>
                  <path
                    d={`M ${fromPos.x} ${fromPos.y} C ${fromPos.x + controlOffset} ${fromPos.y} ${toPos.x - controlOffset} ${toPos.y} ${toPos.x} ${toPos.y}`}
                    fill="none"
                    stroke={edge.type === 'execution' ? '#3b82f6' : '#10b981'}
                    stroke-width="2"
                    class={`transition-colors duration-150 ${selectedEdge() === edge.id ? 'stroke-yellow-400' : ''}`}
                    onClick={() => setSelectedEdge(edge.id)}
                  />
                  {edge.label && (
                    <text
                      x={(fromPos.x + toPos.x) / 2}
                      y={(fromPos.y + toPos.y) / 2 - 5}
                      fill="#9ca3af"
                      font-size="12"
                      text-anchor="middle"
                      class="pointer-events-none"
                    >
                      {edge.label}
                    </text>
                  )}
                </g>
              );
            }}
          </For>

          {/* Temporary connection line */}
          {isConnecting() && (
            <path
              d={`M ${getPortPosition(isConnecting()!.fromNodeId, isConnecting()!.fromPortId, 'output').x} ${getPortPosition(isConnecting()!.fromNodeId, isConnecting()!.fromPortId, 'output').y} L ${isConnecting()!.tempToPos.x} ${isConnecting()!.tempToPos.y}`}
              fill="none"
              stroke="#fbbf24"
              stroke-width="2"
              stroke-dasharray="5,5"
              class="pointer-events-none"
            />
          )}

          {/* Nodes */}
          <For each={nodes()}>
            {(node) => (
              <g 
                data-node-id={node.id}
                class={`cursor-pointer transition-all duration-150 ${node.selected || selectedNode() === node.id ? 'drop-shadow-lg' : ''}`}
              >
                {/* Node body */}
                <rect
                  x={node.x}
                  y={node.y}
                  width={node.width}
                  height={node.height}
                  rx="8"
                  fill={selectedNode() === node.id ? '#1e40af' : '#374151'}
                  stroke={selectedNode() === node.id ? '#3b82f6' : '#6b7280'}
                  stroke-width="2"
                  class="transition-colors duration-150"
                />
                
                {/* Node header */}
                <rect
                  x={node.x}
                  y={node.y}
                  width={node.width}
                  height="30"
                  rx="8"
                  fill={selectedNode() === node.id ? '#1e3a8a' : '#1f2937'}
                />
                
                {/* Node title */}
                <text
                  x={node.x + node.width / 2}
                  y={node.y + 20}
                  fill="white"
                  font-size="14"
                  font-weight="bold"
                  text-anchor="middle"
                  class="pointer-events-none"
                >
                  {node.label}
                </text>

                {/* Input ports */}
                <For each={node.inputs}>
                  {(port, index) => (
                    <g>
                      <circle
                        cx={node.x}
                        cy={node.y + 40 + (index() * 25)}
                        r="6"
                        fill={port.type === 'execution' ? '#3b82f6' : '#10b981'}
                        stroke="white"
                        stroke-width="2"
                        data-node-id={node.id}
                        data-port-id={port.id}
                        data-port-type="input"
                        class="cursor-crosshair hover:r-8 transition-all duration-150"
                      />
                      <text
                        x={node.x + 15}
                        y={node.y + 45 + (index() * 25)}
                        fill="#d1d5db"
                        font-size="12"
                        class="pointer-events-none"
                      >
                        {port.label}
                        {port.required && <tspan fill="#ef4444">*</tspan>}
                      </text>
                    </g>
                  )}
                </For>

                {/* Output ports */}
                <For each={node.outputs}>
                  {(port, index) => (
                    <g>
                      <circle
                        cx={node.x + node.width}
                        cy={node.y + 40 + (index() * 25)}
                        r="6"
                        fill={port.type === 'execution' ? '#3b82f6' : '#10b981'}
                        stroke="white"
                        stroke-width="2"
                        data-node-id={node.id}
                        data-port-id={port.id}
                        data-port-type="output"
                        class="cursor-crosshair hover:r-8 transition-all duration-150"
                      />
                      <text
                        x={node.x + node.width - 15}
                        y={node.y + 45 + (index() * 25)}
                        fill="#d1d5db"
                        font-size="12"
                        text-anchor="end"
                        class="pointer-events-none"
                      >
                        {port.label}
                      </text>
                    </g>
                  )}
                </For>
              </g>
            )}
          </For>
        </svg>

        {/* Mini-map */}
        <div class="absolute top-4 right-4 w-48 h-32 bg-gray-800 bg-opacity-80 rounded border border-gray-600 p-2">
          <div class="text-xs text-gray-300 mb-1">Workflow Overview</div>
          <div class="relative w-full h-24 bg-gray-900 rounded overflow-hidden">
            <For each={nodes()}>
              {(node) => (
                <div
                  class="absolute bg-blue-500 rounded"
                  style={{
                    left: `${(node.x / 2000) * 100}%`,
                    top: `${(node.y / 1000) * 100}%`,
                    width: '8px',
                    height: '6px'
                  }}
                />
              )}
            </For>
          </div>
        </div>

        {/* Controls */}
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

      {/* Properties Panel */}
      {selectedNode() && (
        <div class="w-80 bg-gray-900 border-l border-gray-700 p-4 overflow-y-auto">
          <h3 class="text-blue-300 text-lg font-bold mb-4">Node Properties</h3>
          {(() => {
            const node = nodes().find(n => n.id === selectedNode());
            if (!node) return null;
            
            return (
              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-gray-300 mb-2">Label</label>
                  <input
                    type="text"
                    value={node.label}
                    class="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white"
                    onInput={(e) => {
                      setNodes(prev => prev.map(n => 
                        n.id === selectedNode() ? { ...n, label: e.currentTarget.value } : n
                      ));
                    }}
                  />
                </div>

                <For each={Object.entries(node.properties)}>
                  {([key, value]) => (
                    <div>
                      <label class="block text-sm font-medium text-gray-300 mb-2 capitalize">
                        {key.replace(/([A-Z])/g, ' $1').trim()}
                      </label>
                      <input
                        type={typeof value === 'number' ? 'number' : 'text'}
                        value={String(value)}
                        class="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white"
                        onInput={(e) => {
                          const newValue = typeof value === 'number' 
                            ? Number(e.currentTarget.value) 
                            : e.currentTarget.value;
                          
                          setNodes(prev => prev.map(n => 
                            n.id === selectedNode() 
                              ? { ...n, properties: { ...n.properties, [key]: newValue } } 
                              : n
                          ));
                        }}
                      />
                    </div>
                  )}
                </For>

                <div class="pt-4 border-t border-gray-700">
                  <button
                    class="w-full bg-red-700 hover:bg-red-600 text-white rounded px-3 py-2"
                    onClick={deleteSelectedNode}
                  >
                    🗑️ Delete Node
                  </button>
                </div>
              </div>
            );
          })()}
        </div>
      )}

      {/* Explainable AI Overlay */}
      <div class="absolute bottom-4 left-4 p-2 bg-gray-800 rounded text-blue-200 text-xs shadow-inner max-w-xs">
        <span class="font-bold">Explainable AI:</span> Hover nodes for logic
        explanations. State and parameter changes are reflected in real time.
      </div>
    </div>
  );
}
