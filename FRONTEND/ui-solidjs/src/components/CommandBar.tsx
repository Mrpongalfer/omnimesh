import { createSignal, For, onCleanup, onMount, Show } from 'solid-js';
import { executeCommand } from '../commands/commandLine';
import { selectedNode } from '../store/appState';

// Command types and categories
interface Command {
  id: string;
  name: string;
  description: string;
  category: 'system' | 'network' | 'security' | 'data' | 'ai' | 'agent';
  syntax: string;
  parameters: CommandParameter[];
  aliases: string[];
  examples: string[];
  requiresContext?: 'node' | 'agent' | 'stream' | 'none';
  permissions: string[];
}

interface CommandParameter {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'enum' | 'file' | 'json';
  required: boolean;
  description: string;
  defaultValue?: any;
  enumValues?: string[];
  validation?: string; // regex pattern
}

interface Ability {
  id: string;
  name: string;
  icon: string;
  hotkey: string;
  cooldown: number;
  context?: string;
  description: string;
  commandTemplate: string;
  enabled: boolean;
}

interface CommandHistory {
  command: string;
  timestamp: Date;
  result: 'success' | 'error' | 'warning';
  output: string;
  executionTime: number;
}

// Comprehensive command definitions
const COMMANDS: Command[] = [
  // System commands
  {
    id: 'status',
    name: 'System Status',
    description: 'Display system health and metrics',
    category: 'system',
    syntax: 'status [component]',
    parameters: [
      {
        name: 'component',
        type: 'enum',
        required: false,
        description: 'Specific component to check',
        enumValues: ['all', 'cpu', 'memory', 'network', 'storage', 'services']
      }
    ],
    aliases: ['health', 'check'],
    examples: ['status', 'status cpu', 'status all'],
    permissions: ['read:system']
  },
  {
    id: 'restart',
    name: 'Restart Service',
    description: 'Restart a system service or component',
    category: 'system',
    syntax: 'restart <service>',
    parameters: [
      {
        name: 'service',
        type: 'enum',
        required: true,
        description: 'Service to restart',
        enumValues: ['agent-manager', 'data-processor', 'security-monitor', 'network-scanner']
      }
    ],
    aliases: ['reboot'],
    examples: ['restart agent-manager', 'restart data-processor'],
    permissions: ['admin:system']
  },
  // Network commands
  {
    id: 'scan',
    name: 'Network Scan',
    description: 'Scan network for devices, vulnerabilities, or anomalies',
    category: 'network',
    syntax: 'scan <type> [target]',
    parameters: [
      {
        name: 'type',
        type: 'enum',
        required: true,
        description: 'Type of scan to perform',
        enumValues: ['devices', 'ports', 'vulnerabilities', 'anomalies', 'topology']
      },
      {
        name: 'target',
        type: 'string',
        required: false,
        description: 'Target IP, range, or node ID',
        validation: '^(\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}|\\w+)$'
      }
    ],
    aliases: ['probe', 'discover'],
    examples: ['scan devices', 'scan ports 192.168.1.0/24', 'scan anomalies'],
    permissions: ['read:network', 'execute:scan']
  },
  {
    id: 'trace',
    name: 'Network Trace',
    description: 'Trace network path or data flow',
    category: 'network',
    syntax: 'trace <type> <target>',
    parameters: [
      {
        name: 'type',
        type: 'enum',
        required: true,
        description: 'Type of trace',
        enumValues: ['route', 'data', 'packet', 'latency']
      },
      {
        name: 'target',
        type: 'string',
        required: true,
        description: 'Target IP or node ID'
      }
    ],
    aliases: ['tracert', 'follow'],
    examples: ['trace route 8.8.8.8', 'trace data node-001'],
    permissions: ['read:network']
  },
  // Security commands
  {
    id: 'encrypt',
    name: 'Encrypt Data',
    description: 'Encrypt data or communications',
    category: 'security',
    syntax: 'encrypt <data> [algorithm]',
    parameters: [
      {
        name: 'data',
        type: 'string',
        required: true,
        description: 'Data to encrypt'
      },
      {
        name: 'algorithm',
        type: 'enum',
        required: false,
        description: 'Encryption algorithm',
        enumValues: ['AES-256', 'RSA-2048', 'ChaCha20'],
        defaultValue: 'AES-256'
      }
    ],
    aliases: ['secure'],
    examples: ['encrypt "sensitive data"', 'encrypt file.txt RSA-2048'],
    permissions: ['execute:encryption']
  },
  {
    id: 'audit',
    name: 'Security Audit',
    description: 'Perform security audit',
    category: 'security',
    syntax: 'audit <scope> [depth]',
    parameters: [
      {
        name: 'scope',
        type: 'enum',
        required: true,
        description: 'Audit scope',
        enumValues: ['permissions', 'network', 'data', 'all']
      },
      {
        name: 'depth',
        type: 'enum',
        required: false,
        description: 'Audit depth',
        enumValues: ['quick', 'standard', 'deep'],
        defaultValue: 'standard'
      }
    ],
    aliases: ['check-security'],
    examples: ['audit permissions', 'audit all deep'],
    permissions: ['admin:security']
  },
  // Data commands
  {
    id: 'query',
    name: 'Data Query',
    description: 'Query data streams or storage',
    category: 'data',
    syntax: 'query <source> <filter>',
    parameters: [
      {
        name: 'source',
        type: 'string',
        required: true,
        description: 'Data source or stream ID'
      },
      {
        name: 'filter',
        type: 'json',
        required: true,
        description: 'Query filter in JSON format'
      }
    ],
    aliases: ['search', 'find'],
    examples: ['query sensor-data {"temperature": {"$gt": 25}}', 'query logs {"level": "error"}'],
    permissions: ['read:data']
  },
  {
    id: 'transform',
    name: 'Data Transform',
    description: 'Transform data using specified rules',
    category: 'data',
    syntax: 'transform <input> <rules>',
    parameters: [
      {
        name: 'input',
        type: 'string',
        required: true,
        description: 'Input data source'
      },
      {
        name: 'rules',
        type: 'json',
        required: true,
        description: 'Transformation rules'
      }
    ],
    aliases: ['map', 'convert'],
    examples: ['transform sensor-data {"normalize": "temperature"}'],
    permissions: ['write:data']
  },
  // AI commands
  {
    id: 'predict',
    name: 'AI Prediction',
    description: 'Generate AI predictions or insights',
    category: 'ai',
    syntax: 'predict <model> <data>',
    parameters: [
      {
        name: 'model',
        type: 'enum',
        required: true,
        description: 'AI model to use',
        enumValues: ['anomaly-detection', 'trend-analysis', 'classification', 'clustering']
      },
      {
        name: 'data',
        type: 'string',
        required: true,
        description: 'Input data or stream'
      }
    ],
    aliases: ['ai', 'analyze'],
    examples: ['predict anomaly-detection sensor-stream', 'predict trend-analysis metrics'],
    permissions: ['execute:ai']
  },
  {
    id: 'train',
    name: 'Train Model',
    description: 'Train or retrain AI models',
    category: 'ai',
    syntax: 'train <model> <dataset> [epochs]',
    parameters: [
      {
        name: 'model',
        type: 'string',
        required: true,
        description: 'Model name or type'
      },
      {
        name: 'dataset',
        type: 'string',
        required: true,
        description: 'Training dataset'
      },
      {
        name: 'epochs',
        type: 'number',
        required: false,
        description: 'Number of training epochs',
        defaultValue: 100
      }
    ],
    aliases: ['ml-train'],
    examples: ['train anomaly-model historical-data', 'train classifier dataset.json 200'],
    permissions: ['admin:ai']
  },
  // Agent commands
  {
    id: 'deploy',
    name: 'Deploy Agent',
    description: 'Deploy agent to target node',
    category: 'agent',
    syntax: 'deploy <agent-type> <target> [config]',
    parameters: [
      {
        name: 'agent-type',
        type: 'enum',
        required: true,
        description: 'Type of agent to deploy',
        enumValues: ['monitor', 'scanner', 'analyzer', 'responder']
      },
      {
        name: 'target',
        type: 'string',
        required: true,
        description: 'Target node ID or IP'
      },
      {
        name: 'config',
        type: 'json',
        required: false,
        description: 'Agent configuration'
      }
    ],
    aliases: ['spawn'],
    examples: ['deploy monitor node-001', 'deploy scanner 192.168.1.100 {"interval": 30}'],
    requiresContext: 'node',
    permissions: ['admin:agents']
  },
  {
    id: 'recall',
    name: 'Recall Agent',
    description: 'Recall agent from deployment',
    category: 'agent',
    syntax: 'recall <agent-id>',
    parameters: [
      {
        name: 'agent-id',
        type: 'string',
        required: true,
        description: 'Agent ID to recall'
      }
    ],
    aliases: ['withdraw', 'stop'],
    examples: ['recall agent-monitor-001'],
    permissions: ['admin:agents']
  }
];

// Command abilities for quick access
const globalAbilities: Ability[] = [
  {
    id: 'quick-scan',
    name: 'Quick Scan',
    icon: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z',
    hotkey: 'Q',
    cooldown: 5,
    description: 'Perform a quick network scan',
    commandTemplate: 'scan devices',
    enabled: true
  },
  {
    id: 'system-status',
    name: 'Status',
    icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
    hotkey: 'S',
    cooldown: 2,
    description: 'Check system status',
    commandTemplate: 'status all',
    enabled: true
  },
  {
    id: 'security-audit',
    name: 'Audit',
    icon: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
    hotkey: 'A',
    cooldown: 10,
    description: 'Perform security audit',
    commandTemplate: 'audit all',
    enabled: true
  },
  {
    id: 'ai-predict',
    name: 'AI Analyze',
    icon: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z',
    hotkey: 'AI',
    cooldown: 15,
    description: 'Run AI anomaly detection',
    commandTemplate: 'predict anomaly-detection',
    enabled: true
  }
];

const contextAbilities: Ability[] = [
  {
    id: 'deploy-monitor',
    name: 'Deploy Monitor',
    icon: 'M15 12a3 3 0 11-6 0 3 3 0 016 0z M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z',
    hotkey: 'M',
    cooldown: 8,
    context: 'node',
    description: 'Deploy monitoring agent to selected node',
    commandTemplate: 'deploy monitor',
    enabled: true
  },
  {
    id: 'node-trace',
    name: 'Trace Node',
    icon: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    hotkey: 'T',
    cooldown: 6,
    context: 'node',
    description: 'Trace network path to selected node',
    commandTemplate: 'trace route',
    enabled: true
  }
];

export default function CommandBar() {
  const [commandInput, setCommandInput] = createSignal('');
  const [showCommandLine, setShowCommandLine] = createSignal(false);
  const [cooldowns, setCooldowns] = createSignal<{ [id: string]: number }>({});
  const [commandHistory, setCommandHistory] = createSignal<CommandHistory[]>([]);
  const [suggestionIndex, setSuggestionIndex] = createSignal(-1);
  const [showHelp, setShowHelp] = createSignal(false);

  let commandInputRef: HTMLInputElement | undefined;
  let interval: ReturnType<typeof setInterval> | undefined;

  // Get available abilities based on context
  const abilities = () => [
    ...globalAbilities,
    ...(selectedNode() ? contextAbilities : [])
  ];

  // Get command suggestions based on input
  const suggestions = () => {
    const input = commandInput().toLowerCase().trim();
    if (!input) return [];
    
    return COMMANDS.filter(cmd => 
      cmd.name.toLowerCase().includes(input) ||
      cmd.id.toLowerCase().includes(input) ||
      cmd.aliases.some(alias => alias.toLowerCase().includes(input)) ||
      cmd.category.toLowerCase().includes(input)
    ).slice(0, 5);
  };

  // Hotkey handler
  const handleKeyDown = (e: KeyboardEvent) => {
    // Toggle command line with backtick
    if (e.key === '`' || e.key === '~') {
      setShowCommandLine(!showCommandLine());
      e.preventDefault();
      return;
    }

    // Handle command line navigation
    if (showCommandLine()) {
      if (e.key === 'Escape') {
        setShowCommandLine(false);
        setCommandInput('');
        setSuggestionIndex(-1);
        e.preventDefault();
        return;
      }
      
      if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
        const sug = suggestions();
        if (sug.length > 0) {
          const newIndex = e.key === 'ArrowUp' 
            ? Math.max(-1, suggestionIndex() - 1)
            : Math.min(sug.length - 1, suggestionIndex() + 1);
          setSuggestionIndex(newIndex);
          
          if (newIndex >= 0) {
            setCommandInput(sug[newIndex]!.syntax);
          }
        }
        e.preventDefault();
        return;
      }
      
      if (e.key === 'Enter') {
        executeCurrentCommand();
        e.preventDefault();
        return;
      }
      
      if (e.key === 'Tab') {
        const sug = suggestions();
        if (sug.length > 0) {
          setCommandInput(sug[0]!.syntax);
          setSuggestionIndex(0);
        }
        e.preventDefault();
        return;
      }
    }

    // Handle ability hotkeys
    if (!showCommandLine()) {
      const ability = abilities().find(a => a.hotkey.toLowerCase() === e.key.toLowerCase());
      if (ability && !cooldowns()[ability.id] && ability.enabled) {
        triggerAbility(ability);
        e.preventDefault();
      }
    }

    // F1 for help
    if (e.key === 'F1') {
      setShowHelp(!showHelp());
      e.preventDefault();
    }
  };

  // Initialize
  onMount(() => {
    window.addEventListener('keydown', handleKeyDown);
    
    // Cooldown timer
    interval = setInterval(() => {
      setCooldowns(prev => {
        const next: { [id: string]: number } = {};
        for (const id in prev) {
          if (prev[id]! > 0) next[id] = prev[id]! - 1;
        }
        return next;
      });
    }, 1000);

    // Focus command input when shown
    if (showCommandLine() && commandInputRef) {
      commandInputRef.focus();
    }
  });

  onCleanup(() => {
    window.removeEventListener('keydown', handleKeyDown);
    if (interval) clearInterval(interval);
  });

  // Execute command from input
  function executeCurrentCommand() {
    const command = commandInput().trim();
    if (!command) return;

    const startTime = Date.now();
    
    try {
      const result = executeCommand(command);
      const executionTime = Date.now() - startTime;
      
      setCommandHistory(prev => [...prev, {
        command,
        timestamp: new Date(),
        result: 'success' as const,
        output: result || 'Command executed successfully',
        executionTime
      }].slice(-50)); // Keep last 50 commands
      
    } catch (error) {
      const executionTime = Date.now() - startTime;
      
      setCommandHistory(prev => [...prev, {
        command,
        timestamp: new Date(),
        result: 'error' as const,
        output: error instanceof Error ? error.message : 'Unknown error',
        executionTime
      }].slice(-50));
    }

    setCommandInput('');
    setSuggestionIndex(-1);
    setShowCommandLine(false);
  }

  // Trigger ability
  function triggerAbility(ability: Ability) {
    let command = ability.commandTemplate;
    
    // Add context if needed
    if (ability.context === 'node' && selectedNode()) {
      command += ` ${selectedNode()}`;
    }

    const startTime = Date.now();
    
    try {
      const result = executeCommand(command);
      const executionTime = Date.now() - startTime;
      
      setCommandHistory(prev => [...prev, {
        command: `[${ability.name}] ${command}`,
        timestamp: new Date(),
        result: 'success' as const,
        output: result || `${ability.name} executed successfully`,
        executionTime
      }].slice(-50));
      
      setCooldowns(prev => ({ ...prev, [ability.id]: ability.cooldown }));
      
    } catch (error) {
      const executionTime = Date.now() - startTime;
      
      setCommandHistory(prev => [...prev, {
        command: `[${ability.name}] ${command}`,
        timestamp: new Date(),
        result: 'error' as const,
        output: error instanceof Error ? error.message : 'Unknown error',
        executionTime
      }].slice(-50));
    }
  }

  function formatExecutionTime(ms: number): string {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  }

  return (
    <>
      {/* Command Line Interface */}
      <Show when={showCommandLine()}>
        <div class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
          <div class="bg-gray-900 border border-gray-700 rounded-lg shadow-2xl w-3/4 max-w-4xl">
            {/* Header */}
            <div class="p-4 border-b border-gray-700 bg-gray-800 rounded-t-lg">
              <h2 class="text-white font-bold text-lg">Command Interface</h2>
              <p class="text-gray-300 text-sm">Type commands or use Tab for suggestions. Press ESC to close.</p>
            </div>
            
            {/* Command Input */}
            <div class="p-4">
              <div class="flex items-center gap-2 bg-gray-800 rounded px-3 py-2 border border-gray-600">
                <span class="text-green-400 font-mono">$</span>
                <input
                  ref={commandInputRef}
                  type="text"
                  value={commandInput()}
                  onInput={(e) => {
                    setCommandInput(e.currentTarget.value);
                    setSuggestionIndex(-1);
                  }}
                  placeholder="Enter command..."
                  class="flex-1 bg-transparent text-white font-mono outline-none"
                  autocomplete="off"
                />
              </div>
              
              {/* Suggestions */}
              <Show when={suggestions().length > 0}>
                <div class="mt-2 bg-gray-800 border border-gray-600 rounded max-h-48 overflow-y-auto">
                  <For each={suggestions()}>
                    {(cmd, index) => (
                      <div
                        class={`p-3 cursor-pointer border-b border-gray-700 last:border-b-0 hover:bg-gray-700 ${suggestionIndex() === index() ? 'bg-blue-800' : ''}`}
                        onClick={() => {
                          setCommandInput(cmd.syntax);
                          setSuggestionIndex(index());
                        }}
                      >
                        <div class="flex justify-between items-start">
                          <div>
                            <div class="text-white font-semibold">{cmd.name}</div>
                            <div class="text-gray-300 text-sm font-mono">{cmd.syntax}</div>
                            <div class="text-gray-400 text-xs">{cmd.description}</div>
                          </div>
                          <span class="text-blue-300 text-xs px-2 py-1 bg-blue-900 rounded">
                            {cmd.category}
                          </span>
                        </div>
                      </div>
                    )}
                  </For>
                </div>
              </Show>
              
              {/* Command History */}
              <Show when={commandHistory().length > 0}>
                <div class="mt-4">
                  <h3 class="text-gray-300 font-semibold mb-2">Recent Commands</h3>
                  <div class="bg-gray-800 border border-gray-600 rounded max-h-32 overflow-y-auto">
                    <For each={commandHistory().slice(-5).reverse()}>
                      {(entry) => (
                        <div class="p-2 border-b border-gray-700 last:border-b-0 text-sm">
                          <div class="flex justify-between items-center">
                            <span class="text-gray-300 font-mono">{entry.command}</span>
                            <div class="flex items-center gap-2">
                              <span class="text-gray-500 text-xs">
                                {formatExecutionTime(entry.executionTime)}
                              </span>
                              <span class={`text-xs px-2 py-1 rounded ${
                                entry.result === 'success' ? 'bg-green-800 text-green-200' :
                                entry.result === 'error' ? 'bg-red-800 text-red-200' :
                                'bg-yellow-800 text-yellow-200'
                              }`}>
                                {entry.result}
                              </span>
                            </div>
                          </div>
                          <div class="text-gray-400 text-xs mt-1">{entry.output}</div>
                        </div>
                      )}
                    </For>
                  </div>
                </div>
              </Show>
            </div>
          </div>
        </div>
      </Show>

      {/* Help Panel */}
      <Show when={showHelp()}>
        <div class="fixed top-4 right-4 bg-gray-900 border border-gray-700 rounded-lg shadow-2xl w-80 max-h-96 overflow-y-auto z-40">
          <div class="p-4 border-b border-gray-700 bg-gray-800 rounded-t-lg">
            <div class="flex justify-between items-center">
              <h3 class="text-white font-bold">Command Help</h3>
              <button
                class="text-gray-400 hover:text-white"
                onClick={() => setShowHelp(false)}
              >
                ✕
              </button>
            </div>
          </div>
          <div class="p-3 space-y-3 text-sm">
            <div>
              <div class="text-gray-300 font-semibold">Hotkeys</div>
              <div class="text-gray-400 space-y-1 mt-1">
                <div><kbd class="bg-gray-800 px-1 rounded">~</kbd> Open command line</div>
                <div><kbd class="bg-gray-800 px-1 rounded">F1</kbd> Toggle this help</div>
                <div><kbd class="bg-gray-800 px-1 rounded">Tab</kbd> Auto-complete</div>
                <div><kbd class="bg-gray-800 px-1 rounded">↑↓</kbd> Navigate suggestions</div>
              </div>
            </div>
            <div>
              <div class="text-gray-300 font-semibold">Quick Actions</div>
              <div class="space-y-1 mt-1">
                <For each={abilities().filter(a => a.enabled)}>
                  {(ability) => (
                    <div class="flex justify-between items-center text-xs">
                      <span class="text-gray-400">{ability.name}</span>
                      <kbd class="bg-gray-800 px-1 rounded text-gray-300">{ability.hotkey}</kbd>
                    </div>
                  )}
                </For>
              </div>
            </div>
          </div>
        </div>
      </Show>

      {/* Ability Bar */}
      <div class="fixed bottom-0 left-0 right-0 bg-gradient-to-t from-gray-900 via-gray-800 to-gray-700 border-t border-gray-700 p-4 z-30 shadow-2xl">
        <div class="flex justify-center">
          <div class="flex gap-3">
            <For each={abilities().filter(a => a.enabled)}>
              {(ability) => {
                const cd = () => cooldowns()[ability.id] || 0;
                const isDisabled = () => cd() > 0 || (ability.context === 'node' && !selectedNode());
                
                return (
                  <button
                    class={`relative group flex flex-col items-center px-4 py-3 rounded-lg transition-all duration-200 shadow-lg border-2 ${
                      isDisabled() 
                        ? 'bg-gray-800 border-gray-600 opacity-50 cursor-not-allowed' 
                        : 'bg-gray-700 border-gray-600 hover:bg-blue-700 hover:border-blue-400'
                    }`}
                    disabled={isDisabled()}
                    onClick={() => !isDisabled() && triggerAbility(ability)}
                  >
                    <svg
                      class="w-6 h-6 mb-1"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    >
                      <path d={ability.icon} />
                    </svg>
                    <span class="text-xs text-white font-medium">
                      {ability.name}
                    </span>
                    <span class="absolute top-1 right-1 text-xs text-blue-300 bg-gray-900 bg-opacity-80 rounded px-1">
                      {ability.hotkey}
                    </span>
                    
                    {/* Tooltip */}
                    <div class="absolute bottom-full mb-2 w-48 bg-gray-900 text-white text-xs rounded py-2 px-3 text-center opacity-0 group-hover:opacity-100 transition-opacity duration-300 shadow-lg pointer-events-none">
                      {ability.description}
                      <div class="absolute top-full left-1/2 -translate-x-1/2 w-0 h-0 border-x-4 border-x-transparent border-t-4 border-t-gray-900" />
                    </div>
                    
                    {/* Cooldown overlay */}
                    <Show when={cd() > 0}>
                      <div class="absolute inset-0 bg-black bg-opacity-70 flex items-center justify-center rounded-lg">
                        <span class="text-white font-bold text-lg">{cd()}</span>
                      </div>
                    </Show>
                  </button>
                );
              }}
            </For>
            
            {/* Command line toggle */}
            <button
              class="flex flex-col items-center px-4 py-3 rounded-lg bg-purple-700 hover:bg-purple-600 border-2 border-purple-600 hover:border-purple-400 transition-all duration-200 shadow-lg"
              onClick={() => setShowCommandLine(!showCommandLine())}
            >
              <svg
                class="w-6 h-6 mb-1"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <polyline points="4,17 10,11 4,5" />
                <line x1="12" y1="19" x2="20" y2="19" />
              </svg>
              <span class="text-xs text-white font-medium">Console</span>
              <span class="absolute top-1 right-1 text-xs text-purple-300 bg-gray-900 bg-opacity-80 rounded px-1">~</span>
            </button>
          </div>
        </div>

        {/* Status indicators */}
        <div class="flex justify-between items-center mt-2 text-xs text-gray-400">
          <div class="flex gap-4">
            <span>Commands: {COMMANDS.length}</span>
            <span>History: {commandHistory().length}</span>
            <Show when={selectedNode()}>
              <span class="text-blue-300">Context: {selectedNode()}</span>
            </Show>
          </div>
          <div class="flex gap-2">
            <span class="text-purple-300">Press ~ for console</span>
            <span class="text-gray-500">•</span>
            <span class="text-blue-300">F1 for help</span>
          </div>
        </div>
      </div>
    </>
  );
}
