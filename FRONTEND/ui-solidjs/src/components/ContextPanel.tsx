import { Show, For, createSignal, onMount } from 'solid-js';
import { selectedNode, nodes } from '../store/appState';

export default function ContextPanel() {
  const nodeId = selectedNode();
  const [focused, setFocused] = createSignal(false);
  let panelRef: HTMLDivElement | undefined;

  // Find the node object by id
  const node = () => nodes().find((n) => n.id === nodeId);

  // Keyboard navigation: close on Escape
  onMount(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && focused()) {
        setFocused(false);
        panelRef?.blur();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  });

  return (
    <Show when={node()}>
      <aside
        ref={panelRef}
        class="w-80 max-w-full bg-gray-800 border-l border-gray-700 p-4 fixed right-0 top-0 h-full z-10 focus:outline-none md:rounded-l-xl shadow-2xl transition-all duration-300"
        tabIndex={0}
        aria-label="Node Details Panel"
        role="region"
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
      >
        <h3 class="text-lg font-bold text-white mb-2">Node Details</h3>
        <div class="mb-2 text-white">ID: {node()?.id}</div>
        <div class="mb-2 text-white">Status: {node()?.status ?? 'Unknown'}</div>
        <div class="mb-2 text-white">
          Current Action: {node()?.currentAction ?? 'Unknown'}
        </div>
        <div class="mb-2 text-white">
          Health:
          <div class="w-full bg-gray-700 rounded h-2 mt-1">
            <div
              class="bg-cyan-400 h-2 rounded transition-all duration-500"
              style={{ width: `${node()?.health ? node()!.health * 100 : 0}%` }}
              aria-valuenow={node()?.health ? node()!.health * 100 : 0}
              aria-valuemin={0}
              aria-valuemax={100}
              role="progressbar"
            />
          </div>
        </div>
        <div class="mb-2 text-white">
          Progress:
          <div class="w-full bg-gray-700 rounded h-2 mt-1">
            <div
              class="bg-yellow-400 h-2 rounded transition-all duration-500 animate-pulse"
              style={{
                width: `${node()?.progress ? node()!.progress * 100 : 0}%`,
              }}
              aria-valuenow={node()?.progress ? node()!.progress * 100 : 0}
              aria-valuemin={0}
              aria-valuemax={100}
              role="progressbar"
            />
          </div>
        </div>
        <div class="mb-2 text-white">
          Tasks:
          <ul class="list-disc ml-6">
            <For each={node()?.tasks ?? []}>{(task) => <li>{task}</li>}</For>
          </ul>
        </div>
        <Show when={node()?.anomaly}>
          <div class="mb-2 p-2 bg-red-700 text-white rounded animate-pulse shadow-lg">
            <strong>Anomaly:</strong> {node()?.anomaly}
          </div>
        </Show>
        {/* Explainable AI feedback region */}
        <div class="mt-4 p-2 bg-gray-900 rounded text-blue-200 text-xs shadow-inner animate-fade-in">
          <span class="font-bold">Explainable AI:</span>{' '}
          {node()?.anomaly
            ? 'Anomaly detected. Click for root cause analysis.'
            : 'All systems nominal. Hover for more.'}
        </div>
      </aside>
    </Show>
  );
}
