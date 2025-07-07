import {
  selectedNode,
  setSelectedNode,
  nodes,
  agents,
  anomalies,
} from '../store/appState';
import { For, createSignal, onMount } from 'solid-js';

export default function Minimap() {
  const scale = 0.18;
  const [focused, setFocused] = createSignal(false);
  let mapRef: HTMLDivElement | undefined;

  // Keyboard navigation: focus and jump to node
  onMount(() => {
    const handler = (e: KeyboardEvent) => {
      if (!focused()) return;
      nodes().forEach((node, idx) => {
        if (e.key === String(idx + 1)) setSelectedNode(node.id);
      });
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  });

  // Click/touch navigation
  const handleMapClick = (e: MouseEvent) => {
    const rect = (e.target as SVGElement).getBoundingClientRect();
    const x = (e.clientX - rect.left) / scale;
    const y = (e.clientY - rect.top) / scale;
    // Find nearest node
    let minDist = Infinity;
    let nearest: string | null = null;
    nodes().forEach((node) => {
      const dx = node.x + 70 - x;
      const dy = node.y + 40 - y;
      const dist = dx * dx + dy * dy;
      if (dist < minDist) {
        minDist = dist;
        nearest = node.id;
      }
    });
    if (nearest) setSelectedNode(nearest);
  };

  return (
    <div
      ref={mapRef}
      class="w-48 h-32 bg-gray-800 border border-gray-600 rounded absolute top-4 right-4 cursor-pointer z-30 focus:outline-none md:rounded-xl shadow-xl transition-all duration-300"
      tabIndex={0}
      aria-label="Minimap Overview"
      role="region"
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
      onClick={handleMapClick}
      onTouchEnd={handleMapClick}
    >
      <svg width="100%" height="100%" viewBox="0 0 800 500">
        {/* Nodes */}
        <For each={nodes()}>
          {(node, idx) => (
            <g>
              <rect
                x={node.x * scale}
                y={node.y * scale}
                width={140 * scale}
                height={80 * scale}
                fill={selectedNode() === node.id ? '#fbbf24' : '#4ade80'}
                stroke="#fff"
                stroke-width="2"
                rx="6"
                class={selectedNode() === node.id ? 'animate-pulse' : ''}
              />
              {/* Event/critical overlay */}
              <For each={anomalies().filter((ev) => ev.node === idx())}>
                {() => (
                  <circle
                    cx={node.x * scale + 120 * scale}
                    cy={node.y * scale + 20 * scale}
                    r={14 * scale}
                    fill="#f87171"
                    opacity="0.7"
                  />
                )}
              </For>
            </g>
          )}
        </For>
        {/* Agents */}
        <For each={agents()}>
          {(agent) => {
            const nodeList = nodes();
            const from = nodeList[agent.from];
            const to = nodeList[agent.to];
            if (!from || !to) return null;
            const x = from.x + (to.x - from.x) * agent.progress + 70;
            const y = from.y + (to.y - from.y) * agent.progress + 40;
            return (
              <circle
                cx={x * scale}
                cy={y * scale}
                r={18 * scale}
                fill="#3b82f6"
                stroke="#fff"
                stroke-width="2"
                class="animate-pulse"
              />
            );
          }}
        </For>
      </svg>
      <div class="absolute top-1 right-2 text-xs text-white opacity-70 pointer-events-none select-none">
        [Minimap]
      </div>
      {/* Explainable AI overlay */}
      <div class="absolute left-2 bottom-2 bg-gray-900 bg-opacity-80 rounded px-2 py-1 text-blue-200 text-xs shadow pointer-events-none animate-fade-in">
        <span class="font-bold">Explainable:</span> Click/tap a node to jump.
        Critical events are highlighted.
      </div>
    </div>
  );
}
