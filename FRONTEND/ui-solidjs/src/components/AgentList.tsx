import { createSignal, onMount, For } from 'solid-js';
import type { AgentStatus } from '../services/agentApi';
import { fetchAgents, startAgent, stopAgent } from '../services/agentApi';

interface AgentListProps {
  baseUrl: string;
}

export default function AgentList(props: AgentListProps) {
  const [agents, setAgents] = createSignal<AgentStatus[]>([]);
  const [loading, setLoading] = createSignal(true);
  const [error, setError] = createSignal<string | null>(null);

  const loadAgents = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchAgents(props.baseUrl);
      setAgents(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  const handleStart = async (id: string) => {
    await startAgent(props.baseUrl, id);
    await loadAgents();
  };
  const handleStop = async (id: string) => {
    await stopAgent(props.baseUrl, id);
    await loadAgents();
  };

  onMount(loadAgents);

  return (
    <div class="p-4">
      <h2 class="text-xl font-bold mb-4">Agents</h2>
      {loading() && <div>Loading...</div>}
      {error() && <div class="text-red-500">{error()}</div>}
      <ul class="space-y-2">
        <For each={agents()}>
          {(agent) => (
            <li class="border rounded p-2 flex items-center justify-between">
              <div>
                <span class="font-semibold">{agent.name}</span>
                <span
                  class={`ml-2 px-2 py-1 rounded text-xs ${agent.status === 'online' ? 'bg-green-200 text-green-800' : agent.status === 'offline' ? 'bg-gray-200 text-gray-800' : 'bg-red-200 text-red-800'}`}
                >
                  {agent.status}
                </span>
              </div>
              <div class="space-x-2">
                <button
                  class="px-2 py-1 bg-green-500 text-white rounded"
                  onClick={() => handleStart(agent.id)}
                  disabled={agent.status === 'online'}
                >
                  Start
                </button>
                <button
                  class="px-2 py-1 bg-red-500 text-white rounded"
                  onClick={() => handleStop(agent.id)}
                  disabled={agent.status === 'offline'}
                >
                  Stop
                </button>
              </div>
            </li>
          )}
        </For>
      </ul>
      <button
        class="mt-4 px-4 py-2 bg-blue-500 text-white rounded"
        onClick={loadAgents}
      >
        Refresh
      </button>
    </div>
  );
}
