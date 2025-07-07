import { createSignal, For, Show } from 'solid-js';
import { executeCommand } from '../commands/commandLine';

const commands = [
  { cmd: 'deploy agent', desc: 'Deploy a new agent to the selected node.' },
  { cmd: 'scan network', desc: 'Scan the network for anomalies.' },
  { cmd: 'clear notifications', desc: 'Clear all notifications.' },
  { cmd: 'show status', desc: 'Show current system status.' },
  { cmd: 'help', desc: 'Shows all available commands.' },
];

export default function UniversalCommandLine() {
  const [input, setInput] = createSignal('');
  const [history, setHistory] = createSignal<string[]>([]);
  const [show, setShow] = createSignal(false);
  const [selected, setSelected] = createSignal(0);

  const suggestions = () =>
    input().length > 0
      ? commands.filter((c) => c.cmd.startsWith(input().toLowerCase()))
      : [];

  function handleKeyDown(e: KeyboardEvent) {
    if (!show()) return;
    if (e.key === 'Enter') {
      const cmd = input();
      if (cmd) {
        executeCommand(cmd);
        setHistory((h) => [cmd, ...h]);
      }
      setInput('');
      setShow(false);
      setSelected(0);
    } else if (e.key === 'ArrowDown') {
      setSelected((s) => Math.min(s + 1, suggestions().length - 1));
    } else if (e.key === 'ArrowUp') {
      setSelected((s) => Math.max(s - 1, 0));
    } else if (e.key === 'Tab') {
      if (suggestions().length > 0) {
        setInput(suggestions()[selected()].cmd);
        e.preventDefault();
      }
    } else if (e.key === 'Escape') {
      setShow(false);
    }
  }

  function globalKey(e: KeyboardEvent) {
    if (e.key === '/' && !show()) {
      setShow(true);
      setTimeout(() => {
        const el = document.getElementById('omni-cmd-input');
        if (el) (el as HTMLInputElement).focus();
      }, 10);
    }
  }
  if (typeof window !== 'undefined') {
    window.addEventListener('keydown', globalKey);
  }

  return (
    <Show when={show()}>
      <div class="fixed bottom-16 left-1/2 transform -translate-x-1/2 w-2/3 bg-gray-900 border border-blue-700 rounded-lg p-4 z-40 shadow-2xl flex flex-col gap-2 animate-fade-in">
        <input
          id="omni-cmd-input"
          class="w-full bg-gray-800 text-white text-lg rounded px-4 py-2 outline-none border border-gray-700 focus:border-blue-400 shadow"
          value={input()}
          onInput={(e) => setInput(e.currentTarget.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a command... (try 'deploy agent', 'scan', etc.)"
          autocomplete="off"
        />
        <Show when={suggestions().length > 0}>
          <div class="bg-gray-800 rounded shadow-lg border border-gray-700 mt-1">
            <For each={suggestions()}>
              {(s, i) => (
                <div
                  class={`px-4 py-2 cursor-pointer flex items-center gap-2 ${
                    selected() === i()
                      ? 'bg-blue-700 text-white'
                      : 'text-blue-200 hover:bg-blue-900'
                  }`}
                  onMouseDown={() => {
                    setInput(s.cmd);
                    setSelected(i());
                  }}
                >
                  <span class="font-mono text-base">{s.cmd}</span>
                  <span class="text-xs text-blue-300">{s.desc}</span>
                </div>
              )}
            </For>
          </div>
        </Show>
        <Show when={input().length > 0}>
          <div class="mt-2 p-2 bg-gray-800 rounded text-blue-200 text-xs shadow-inner">
            <span class="font-bold">Explainable AI:</span>{' '}
            {suggestions()[selected()]?.desc || 'Type a command for details.'}
          </div>
        </Show>
        <Show when={history().length > 0}>
          <div class="mt-2 text-xs text-gray-400">
            <span class="font-bold">History:</span>{' '}
            {history().slice(0, 3).join(' | ')}
          </div>
        </Show>
      </div>
    </Show>
  );
}
