// src/commands/commandLine.ts
import { agents, nodes, setAgents, setNotifications } from '../store/appState';

// Command execution logic
export function executeCommand(cmd: string): string {
  const [command, ...args] = cmd.trim().split(/\s+/);

  switch (command) {
    case 'deploy':
      if (args[0] === 'agent' && args[1] && args[2]) {
        const fromNode = args[1];
        const toNode = args[2];
        const allNodes = nodes();
        const fromNodeExists = allNodes.find((n) => n.id === fromNode);
        const toNodeExists = allNodes.find((n) => n.id === toNode);

        if (fromNodeExists && toNodeExists) {
          const newAgent = {
            id: `agent-${Date.now()}`,
            from: allNodes.indexOf(fromNodeExists),
            to: allNodes.indexOf(toNodeExists),
            progress: 0,
          };
          setAgents((a) => [...a, newAgent]);
          const msg = `Agent deployed from node ${fromNode} to ${toNode}.`;
          setNotifications((n) => [msg, ...n]);
          return msg;
        }
        return `Error: Invalid node IDs. Usage: deploy agent <from_node_id> <to_node_id>`;
      }
      return `Error: Unknown 'deploy' command. Usage: deploy agent <from_node_id> <to_node_id>`;

    case 'repair':
      if (args[0] === 'node' && args[1]) {
        const node = args[1];
        const nodeExists = nodes().find((n) => n.id === node);
        if (nodeExists) {
          const msg = `Repair sequence initiated for node ${node}.`;
          setNotifications((n) => [msg, ...n]);
          return msg;
        }
        return `Error: Node '${node}' not found.`;
      }
      return `Error: Unknown 'repair' command. Usage: repair node <node_id>`;

    case 'scan':
      if (args[0] === 'network') {
        const msg = 'Network-wide anomaly scan initiated.';
        setNotifications((n) => [msg, ...n]);
        return msg;
      }
      return `Error: Unknown 'scan' command. Usage: scan network`;

    case 'clear':
      if (args[0] === 'notifications') {
        setNotifications([]);
        return 'Notifications cleared.';
      }
      return `Error: Unknown 'clear' command. Usage: clear notifications`;

    case 'show':
      if (args[0] === 'status') {
        const msg = `Status: ${nodes().length} nodes, ${
          agents().length
        } agents.`;
        setNotifications((n) => [msg, ...n]);
        return msg;
      }
      return `Error: Unknown 'show' command. Usage: show status`;

    case 'help':
      return `Available commands: deploy agent <from> <to>, scan network, repair node <node_id>, clear notifications, show status, help`;

    default:
      return `Error: Unknown command \\'${command}\\'. Type 'help' for a list of commands.`;
  }
}
