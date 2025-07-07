import { createSignal, For, onMount, onCleanup } from 'solid-js';

// Security-related types
interface User {
  id: string;
  name: string;
  role: 'Admin' | 'Operator' | 'Viewer' | 'Daemon';
  permissions: string[];
  lastAccess: Date;
  status: 'active' | 'disabled' | 'locked';
  mfaEnabled: boolean;
}

interface FirewallRule {
  id: string;
  name: string;
  source: string;
  destination: string;
  port: number | 'any';
  protocol: 'TCP' | 'UDP' | 'ICMP' | 'ANY';
  action: 'allow' | 'deny' | 'log';
  enabled: boolean;
  priority: number;
  createdAt: Date;
}

interface ThreatAlert {
  id: string;
  type: 'intrusion' | 'anomaly' | 'malware' | 'policy_violation' | 'data_exfiltration';
  severity: 'critical' | 'high' | 'medium' | 'low';
  source: string;
  target: string;
  description: string;
  timestamp: Date;
  status: 'new' | 'investigating' | 'resolved' | 'false_positive';
  mitigationActions: string[];
}

interface EncryptionKey {
  id: string;
  name: string;
  algorithm: 'AES-256' | 'RSA-2048' | 'RSA-4096' | 'ECDSA-P256';
  purpose: 'data_encryption' | 'signing' | 'tls' | 'authentication';
  status: 'active' | 'rotated' | 'revoked';
  createdAt: Date;
  expiresAt: Date;
  lastUsed: Date;
}

interface SecurityMetrics {
  totalUsers: number;
  activeUsers: number;
  failedLogins: number;
  threatsBlocked: number;
  dataEncrypted: number; // in bytes
  certificatesExpiring: number;
  complianceScore: number; // percentage
}

export default function SecurityNexus() {
  const [users, setUsers] = createSignal<User[]>([]);
  const [firewallRules, setFirewallRules] = createSignal<FirewallRule[]>([]);
  const [threats, setThreats] = createSignal<ThreatAlert[]>([]);
  const [encryptionKeys, setEncryptionKeys] = createSignal<EncryptionKey[]>([]);
  const [metrics, setMetrics] = createSignal<SecurityMetrics>({
    totalUsers: 0,
    activeUsers: 0,
    failedLogins: 0,
    threatsBlocked: 0,
    dataEncrypted: 0,
    certificatesExpiring: 0,
    complianceScore: 0
  });
  
  const [selectedTab, setSelectedTab] = createSignal<'access' | 'firewall' | 'threats' | 'encryption'>('access');
  const [selectedUser, setSelectedUser] = createSignal<string | null>(null);
  const [selectedThreat, setSelectedThreat] = createSignal<string | null>(null);

  let metricsInterval: ReturnType<typeof setInterval> | undefined;

  // Initialize security data
  onMount(() => {
    const initialUsers: User[] = [
      {
        id: 'admin-001',
        name: 'System Administrator',
        role: 'Admin',
        permissions: ['*'],
        lastAccess: new Date(Date.now() - 300000), // 5 minutes ago
        status: 'active',
        mfaEnabled: true
      },
      {
        id: 'operator-001',
        name: 'Control Operator',
        role: 'Operator',
        permissions: ['read:nodes', 'write:nodes', 'read:streams'],
        lastAccess: new Date(Date.now() - 600000), // 10 minutes ago
        status: 'active',
        mfaEnabled: true
      },
      {
        id: 'viewer-001',
        name: 'Read-Only User',
        role: 'Viewer',
        permissions: ['read:nodes', 'read:streams', 'read:metrics'],
        lastAccess: new Date(Date.now() - 1800000), // 30 minutes ago
        status: 'active',
        mfaEnabled: false
      },
      {
        id: 'daemon-001',
        name: 'System Daemon',
        role: 'Daemon',
        permissions: ['execute:automation', 'write:metrics'],
        lastAccess: new Date(Date.now() - 60000), // 1 minute ago
        status: 'active',
        mfaEnabled: false
      }
    ];

    const initialFirewallRules: FirewallRule[] = [
      {
        id: 'fw-001',
        name: 'Allow Control Traffic',
        source: '10.0.0.0/24',
        destination: '10.0.1.0/24',
        port: 8080,
        protocol: 'TCP',
        action: 'allow',
        enabled: true,
        priority: 100,
        createdAt: new Date(Date.now() - 86400000)
      },
      {
        id: 'fw-002',
        name: 'Block External SSH',
        source: '0.0.0.0/0',
        destination: '10.0.0.0/16',
        port: 22,
        protocol: 'TCP',
        action: 'deny',
        enabled: true,
        priority: 50,
        createdAt: new Date(Date.now() - 172800000)
      },
      {
        id: 'fw-003',
        name: 'Allow Internal Communication',
        source: '10.0.0.0/16',
        destination: '10.0.0.0/16',
        port: 'any',
        protocol: 'ANY',
        action: 'allow',
        enabled: true,
        priority: 200,
        createdAt: new Date(Date.now() - 259200000)
      }
    ];

    const initialThreats: ThreatAlert[] = [
      {
        id: 'threat-001',
        type: 'intrusion',
        severity: 'high',
        source: '192.168.1.45',
        target: 'control-node-1',
        description: 'Multiple failed login attempts detected',
        timestamp: new Date(Date.now() - 900000),
        status: 'investigating',
        mitigationActions: ['IP blocked', 'Account locked', 'Security team notified']
      },
      {
        id: 'threat-002',
        type: 'anomaly',
        severity: 'medium',
        source: 'data-stream-sensor',
        target: 'aggregation-node',
        description: 'Unusual data pattern detected in sensor stream',
        timestamp: new Date(Date.now() - 1800000),
        status: 'new',
        mitigationActions: ['Data validation triggered', 'Stream quarantined']
      },
      {
        id: 'threat-003',
        type: 'policy_violation',
        severity: 'low',
        source: 'operator-001',
        target: 'admin-config',
        description: 'Unauthorized access attempt to admin configuration',
        timestamp: new Date(Date.now() - 3600000),
        status: 'resolved',
        mitigationActions: ['Access denied', 'Warning issued', 'Training scheduled']
      }
    ];

    const initialKeys: EncryptionKey[] = [
      {
        id: 'key-001',
        name: 'Primary Data Encryption',
        algorithm: 'AES-256',
        purpose: 'data_encryption',
        status: 'active',
        createdAt: new Date(Date.now() - 2592000000), // 30 days ago
        expiresAt: new Date(Date.now() + 7776000000), // 90 days from now
        lastUsed: new Date(Date.now() - 60000)
      },
      {
        id: 'key-002',
        name: 'TLS Certificate',
        algorithm: 'RSA-2048',
        purpose: 'tls',
        status: 'active',
        createdAt: new Date(Date.now() - 7776000000), // 90 days ago
        expiresAt: new Date(Date.now() + 2592000000), // 30 days from now
        lastUsed: new Date(Date.now() - 5000)
      },
      {
        id: 'key-003',
        name: 'Document Signing',
        algorithm: 'ECDSA-P256',
        purpose: 'signing',
        status: 'active',
        createdAt: new Date(Date.now() - 5184000000), // 60 days ago
        expiresAt: new Date(Date.now() + 5184000000), // 60 days from now
        lastUsed: new Date(Date.now() - 3600000)
      }
    ];

    setUsers(initialUsers);
    setFirewallRules(initialFirewallRules);
    setThreats(initialThreats);
    setEncryptionKeys(initialKeys);

    // Update metrics
    updateMetrics();

    // Start real-time metrics updates
    metricsInterval = setInterval(() => {
      updateMetrics();
      simulateThreatUpdates();
    }, 5000);
  });

  onCleanup(() => {
    if (metricsInterval) {
      clearInterval(metricsInterval);
    }
  });

  function updateMetrics() {
    const currentUsers = users();
    const activeUsers = currentUsers.filter(u => u.status === 'active');
    const expiringKeys = encryptionKeys().filter(k => 
      k.expiresAt.getTime() - Date.now() < 2592000000 // 30 days
    );
    
    setMetrics({
      totalUsers: currentUsers.length,
      activeUsers: activeUsers.length,
      failedLogins: Math.floor(Math.random() * 50),
      threatsBlocked: threats().filter(t => t.status === 'resolved').length,
      dataEncrypted: Math.floor(Math.random() * 1000000000), // Random bytes
      certificatesExpiring: expiringKeys.length,
      complianceScore: Math.floor(85 + Math.random() * 10) // 85-95%
    });
  }

  function simulateThreatUpdates() {
    // Randomly update threat statuses
    setThreats(prev => prev.map(threat => {
      if (Math.random() < 0.1 && threat.status === 'new') { // 10% chance
        return { ...threat, status: 'investigating' as const };
      }
      if (Math.random() < 0.05 && threat.status === 'investigating') { // 5% chance
        return { ...threat, status: 'resolved' as const };
      }
      return threat;
    }));
  }

  function getSeverityColor(severity: ThreatAlert['severity']): string {
    switch (severity) {
      case 'critical': return 'bg-red-900 text-red-200 border-red-400';
      case 'high': return 'bg-orange-900 text-orange-200 border-orange-400';
      case 'medium': return 'bg-yellow-900 text-yellow-200 border-yellow-400';
      case 'low': return 'bg-blue-900 text-blue-200 border-blue-400';
    }
  }

  function getStatusColor(status: ThreatAlert['status']): string {
    switch (status) {
      case 'new': return 'bg-red-700';
      case 'investigating': return 'bg-yellow-700';
      case 'resolved': return 'bg-green-700';
      case 'false_positive': return 'bg-gray-700';
    }
  }

  function formatTimeAgo(date: Date): string {
    const diff = Date.now() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'Just now';
  }

  function toggleFirewallRule(ruleId: string) {
    setFirewallRules(prev => prev.map(rule => 
      rule.id === ruleId ? { ...rule, enabled: !rule.enabled } : rule
    ));
  }

  function rotateKey(keyId: string) {
    setEncryptionKeys(prev => prev.map(key => {
      if (key.id === keyId) {
        return {
          ...key,
          status: 'rotated' as const,
          lastUsed: new Date()
        };
      }
      return key;
    }));
    
    // Add new key
    const oldKey = encryptionKeys().find(k => k.id === keyId);
    if (oldKey) {
      const newKey: EncryptionKey = {
        id: `key-${Date.now()}`,
        name: `${oldKey.name} (Rotated)`,
        algorithm: oldKey.algorithm,
        purpose: oldKey.purpose,
        status: 'active',
        createdAt: new Date(),
        expiresAt: new Date(Date.now() + 7776000000), // 90 days
        lastUsed: new Date()
      };
      setEncryptionKeys(prev => [...prev, newKey]);
    }
  }

  return (
    <div class="w-full h-full flex flex-col bg-gradient-to-br from-gray-900 via-gray-800 to-gray-700 rounded-lg shadow-2xl border border-gray-700 relative overflow-hidden">
      {/* Header with metrics */}
      <div class="p-4 border-b border-gray-700 bg-gray-900">
        <h1 class="text-2xl font-bold text-pink-300 mb-4 flex items-center gap-2">
          🛡️ Security Nexus
        </h1>
        
        <div class="grid grid-cols-4 gap-4 text-sm">
          <div class="bg-gray-800 rounded p-3">
            <div class="text-gray-400 text-xs">Active Users</div>
            <div class="text-green-300 text-lg font-bold">{metrics().activeUsers}/{metrics().totalUsers}</div>
          </div>
          <div class="bg-gray-800 rounded p-3">
            <div class="text-gray-400 text-xs">Threats Blocked</div>
            <div class="text-blue-300 text-lg font-bold">{metrics().threatsBlocked}</div>
          </div>
          <div class="bg-gray-800 rounded p-3">
            <div class="text-gray-400 text-xs">Data Encrypted</div>
            <div class="text-purple-300 text-lg font-bold">{(metrics().dataEncrypted / 1024 / 1024).toFixed(1)}MB</div>
          </div>
          <div class="bg-gray-800 rounded p-3">
            <div class="text-gray-400 text-xs">Compliance Score</div>
            <div class="text-yellow-300 text-lg font-bold">{metrics().complianceScore}%</div>
          </div>
        </div>
      </div>

      {/* Navigation tabs */}
      <div class="flex border-b border-gray-700 bg-gray-800">
        {(['access', 'firewall', 'threats', 'encryption'] as const).map(tab => (
          <button
            class={`px-6 py-3 font-semibold transition-colors ${selectedTab() === tab ? 'bg-pink-700 text-white' : 'text-gray-300 hover:bg-gray-700'}`}
            onClick={() => setSelectedTab(tab)}
          >
            {tab === 'access' && '👥 Access Control'}
            {tab === 'firewall' && '🔥 Firewall'}
            {tab === 'threats' && '⚠️ Threats'}
            {tab === 'encryption' && '🔐 Encryption'}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div class="flex-1 overflow-hidden">
        {selectedTab() === 'access' && (
          <div class="h-full flex">
            {/* Users list */}
            <div class="w-1/3 p-4 border-r border-gray-700 overflow-y-auto">
              <div class="flex justify-between items-center mb-4">
                <h3 class="text-lg font-semibold text-white">Users</h3>
                <button class="bg-pink-700 hover:bg-pink-600 text-white px-3 py-1 rounded text-sm">
                  + Add User
                </button>
              </div>
              
              <div class="space-y-2">
                <For each={users()}>
                  {(user) => (
                    <div
                      class={`p-3 rounded border cursor-pointer transition-colors ${selectedUser() === user.id ? 'border-pink-400 bg-pink-900/20' : 'border-gray-600 bg-gray-800 hover:bg-gray-700'}`}
                      onClick={() => setSelectedUser(user.id)}
                    >
                      <div class="flex justify-between items-start">
                        <div>
                          <div class="font-semibold text-white">{user.name}</div>
                          <div class="text-sm text-gray-400">{user.role}</div>
                          <div class="text-xs text-gray-500">Last: {formatTimeAgo(user.lastAccess)}</div>
                        </div>
                        <div class="flex flex-col items-end gap-1">
                          <span class={`text-xs px-2 py-1 rounded ${user.status === 'active' ? 'bg-green-700 text-green-200' : 'bg-red-700 text-red-200'}`}>
                            {user.status}
                          </span>
                          {user.mfaEnabled && (
                            <span class="text-xs text-blue-300">🔒 MFA</span>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </For>
              </div>
            </div>

            {/* User details */}
            <div class="flex-1 p-4 overflow-y-auto">
              {selectedUser() ? (
                <div>
                  {(() => {
                    const user = users().find(u => u.id === selectedUser());
                    if (!user) return null;

                    return (
                      <div class="space-y-4">
                        <h3 class="text-xl font-semibold text-white">{user.name}</h3>
                        
                        <div class="grid grid-cols-2 gap-4">
                          <div class="bg-gray-800 rounded p-3">
                            <div class="text-gray-400 text-sm">Role</div>
                            <div class="text-white font-semibold">{user.role}</div>
                          </div>
                          <div class="bg-gray-800 rounded p-3">
                            <div class="text-gray-400 text-sm">Status</div>
                            <div class={`font-semibold ${user.status === 'active' ? 'text-green-300' : 'text-red-300'}`}>
                              {user.status}
                            </div>
                          </div>
                        </div>

                        <div>
                          <h4 class="text-white font-semibold mb-2">Permissions</h4>
                          <div class="flex flex-wrap gap-2">
                            <For each={user.permissions}>
                              {(permission) => (
                                <span class="bg-blue-700 text-blue-200 text-xs px-2 py-1 rounded">
                                  {permission}
                                </span>
                              )}
                            </For>
                          </div>
                        </div>

                        <div class="bg-gray-800 rounded p-3">
                          <h4 class="text-white font-semibold mb-2">Security Settings</h4>
                          <div class="space-y-2">
                            <label class="flex items-center gap-2 text-sm text-gray-300">
                              <input type="checkbox" checked={user.mfaEnabled} />
                              Multi-Factor Authentication
                            </label>
                            <div class="text-xs text-gray-400">
                              Last access: {user.lastAccess.toLocaleString()}
                            </div>
                          </div>
                        </div>

                        <div class="flex gap-2">
                          <button class="bg-blue-700 hover:bg-blue-600 text-white px-4 py-2 rounded">
                            Edit Permissions
                          </button>
                          <button class="bg-yellow-700 hover:bg-yellow-600 text-white px-4 py-2 rounded">
                            Reset Password
                          </button>
                          <button class="bg-red-700 hover:bg-red-600 text-white px-4 py-2 rounded">
                            Disable User
                          </button>
                        </div>
                      </div>
                    );
                  })()}
                </div>
              ) : (
                <div class="text-gray-400 text-center mt-8">
                  Select a user to view details
                </div>
              )}
            </div>
          </div>
        )}

        {selectedTab() === 'firewall' && (
          <div class="h-full p-4 overflow-y-auto">
            <div class="flex justify-between items-center mb-4">
              <h3 class="text-lg font-semibold text-white">Firewall Rules</h3>
              <button class="bg-pink-700 hover:bg-pink-600 text-white px-3 py-2 rounded">
                + Add Rule
              </button>
            </div>

            <div class="space-y-2">
              <For each={firewallRules().sort((a, b) => a.priority - b.priority)}>
                {(rule) => (
                  <div class="bg-gray-800 rounded p-4 border border-gray-700">
                    <div class="flex justify-between items-start">
                      <div class="flex-1">
                        <div class="flex items-center gap-3 mb-2">
                          <span class="font-semibold text-white">{rule.name}</span>
                          <span class={`text-xs px-2 py-1 rounded ${rule.action === 'allow' ? 'bg-green-700 text-green-200' : rule.action === 'deny' ? 'bg-red-700 text-red-200' : 'bg-blue-700 text-blue-200'}`}>
                            {rule.action.toUpperCase()}
                          </span>
                          <span class="text-xs text-gray-400">Priority: {rule.priority}</span>
                        </div>
                        <div class="text-sm text-gray-300">
                          {rule.source} → {rule.destination}:{rule.port} ({rule.protocol})
                        </div>
                        <div class="text-xs text-gray-500 mt-1">
                          Created: {formatTimeAgo(rule.createdAt)}
                        </div>
                      </div>
                      <div class="flex items-center gap-2">
                        <button
                          class={`px-3 py-1 rounded text-sm ${rule.enabled ? 'bg-green-700 hover:bg-green-600 text-green-200' : 'bg-gray-700 hover:bg-gray-600 text-gray-300'}`}
                          onClick={() => toggleFirewallRule(rule.id)}
                        >
                          {rule.enabled ? 'Enabled' : 'Disabled'}
                        </button>
                        <button class="text-gray-400 hover:text-white">⚙️</button>
                        <button class="text-gray-400 hover:text-red-400">🗑️</button>
                      </div>
                    </div>
                  </div>
                )}
              </For>
            </div>
          </div>
        )}

        {selectedTab() === 'threats' && (
          <div class="h-full flex">
            {/* Threats list */}
            <div class="w-2/3 p-4 border-r border-gray-700 overflow-y-auto">
              <h3 class="text-lg font-semibold text-white mb-4">Threat Alerts</h3>
              
              <div class="space-y-2">
                <For each={threats().sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())}>
                  {(threat) => (
                    <div
                      class={`p-4 rounded border cursor-pointer transition-colors ${selectedThreat() === threat.id ? 'border-pink-400 bg-pink-900/20' : `border-gray-600 ${getSeverityColor(threat.severity)} hover:brightness-110`}`}
                      onClick={() => setSelectedThreat(threat.id)}
                    >
                      <div class="flex justify-between items-start mb-2">
                        <div class="flex items-center gap-2">
                          <span class="font-semibold">{threat.type.replace('_', ' ').toUpperCase()}</span>
                          <span class={`text-xs px-2 py-1 rounded ${getStatusColor(threat.status)} text-white`}>
                            {threat.status.replace('_', ' ')}
                          </span>
                        </div>
                        <div class="text-xs text-gray-300">
                          {formatTimeAgo(threat.timestamp)}
                        </div>
                      </div>
                      <div class="text-sm mb-2">{threat.description}</div>
                      <div class="text-xs text-gray-400">
                        {threat.source} → {threat.target}
                      </div>
                    </div>
                  )}
                </For>
              </div>
            </div>

            {/* Threat details */}
            <div class="w-1/3 p-4 overflow-y-auto">
              {selectedThreat() ? (
                <div>
                  {(() => {
                    const threat = threats().find(t => t.id === selectedThreat());
                    if (!threat) return null;

                    return (
                      <div class="space-y-4">
                        <h3 class="text-lg font-semibold text-white">Threat Details</h3>
                        
                        <div class="space-y-3">
                          <div class="bg-gray-800 rounded p-3">
                            <div class="text-gray-400 text-sm">Type</div>
                            <div class="text-white font-semibold">{threat.type.replace('_', ' ').toUpperCase()}</div>
                          </div>
                          <div class="bg-gray-800 rounded p-3">
                            <div class="text-gray-400 text-sm">Severity</div>
                            <div class={`font-semibold ${threat.severity === 'critical' ? 'text-red-300' : threat.severity === 'high' ? 'text-orange-300' : threat.severity === 'medium' ? 'text-yellow-300' : 'text-blue-300'}`}>
                              {threat.severity.toUpperCase()}
                            </div>
                          </div>
                          <div class="bg-gray-800 rounded p-3">
                            <div class="text-gray-400 text-sm">Status</div>
                            <div class="text-white font-semibold">{threat.status.replace('_', ' ').toUpperCase()}</div>
                          </div>
                        </div>

                        <div>
                          <h4 class="text-white font-semibold mb-2">Description</h4>
                          <div class="text-gray-300 text-sm bg-gray-800 rounded p-3">
                            {threat.description}
                          </div>
                        </div>

                        <div>
                          <h4 class="text-white font-semibold mb-2">Mitigation Actions</h4>
                          <div class="space-y-1">
                            <For each={threat.mitigationActions}>
                              {(action) => (
                                <div class="text-sm text-green-300 flex items-center gap-2">
                                  <span class="text-green-400">✓</span>
                                  {action}
                                </div>
                              )}
                            </For>
                          </div>
                        </div>

                        <div class="text-xs text-gray-400">
                          Detected: {threat.timestamp.toLocaleString()}
                        </div>

                        <div class="flex gap-2">
                          <button class="bg-blue-700 hover:bg-blue-600 text-white px-3 py-2 rounded text-sm">
                            Investigate
                          </button>
                          <button class="bg-green-700 hover:bg-green-600 text-white px-3 py-2 rounded text-sm">
                            Mark Resolved
                          </button>
                          <button class="bg-gray-700 hover:bg-gray-600 text-white px-3 py-2 rounded text-sm">
                            False Positive
                          </button>
                        </div>
                      </div>
                    );
                  })()}
                </div>
              ) : (
                <div class="text-gray-400 text-center mt-8">
                  Select a threat to view details
                </div>
              )}
            </div>
          </div>
        )}

        {selectedTab() === 'encryption' && (
          <div class="h-full p-4 overflow-y-auto">
            <div class="flex justify-between items-center mb-4">
              <h3 class="text-lg font-semibold text-white">Encryption Keys</h3>
              <button class="bg-pink-700 hover:bg-pink-600 text-white px-3 py-2 rounded">
                + Generate Key
              </button>
            </div>

            <div class="space-y-3">
              <For each={encryptionKeys()}>
                {(key) => (
                  <div class="bg-gray-800 rounded p-4 border border-gray-700">
                    <div class="flex justify-between items-start">
                      <div class="flex-1">
                        <div class="flex items-center gap-3 mb-2">
                          <span class="font-semibold text-white">{key.name}</span>
                          <span class={`text-xs px-2 py-1 rounded ${key.status === 'active' ? 'bg-green-700 text-green-200' : key.status === 'rotated' ? 'bg-yellow-700 text-yellow-200' : 'bg-red-700 text-red-200'}`}>
                            {key.status}
                          </span>
                          <span class="text-xs text-blue-300">{key.algorithm}</span>
                        </div>
                        <div class="text-sm text-gray-300 mb-1">
                          Purpose: {key.purpose.replace('_', ' ')}
                        </div>
                        <div class="text-xs text-gray-500 space-y-1">
                          <div>Created: {formatTimeAgo(key.createdAt)}</div>
                          <div>Expires: {key.expiresAt.toLocaleDateString()}</div>
                          <div>Last used: {formatTimeAgo(key.lastUsed)}</div>
                        </div>
                      </div>
                      <div class="flex flex-col gap-2">
                        <button
                          class="bg-blue-700 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm"
                          onClick={() => rotateKey(key.id)}
                          disabled={key.status !== 'active'}
                        >
                          Rotate
                        </button>
                        <button class="bg-red-700 hover:bg-red-600 text-white px-3 py-1 rounded text-sm">
                          Revoke
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </For>
            </div>

            <div class="mt-8 p-4 bg-gray-800 rounded">
              <h4 class="text-white font-semibold mb-3">Key Management Summary</h4>
              <div class="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div class="text-gray-400">Active Keys</div>
                  <div class="text-green-300 font-semibold">
                    {encryptionKeys().filter(k => k.status === 'active').length}
                  </div>
                </div>
                <div>
                  <div class="text-gray-400">Expiring Soon</div>
                  <div class="text-yellow-300 font-semibold">
                    {metrics().certificatesExpiring}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Explainable AI overlay */}
      <div class="absolute bottom-4 right-4 p-3 bg-gray-800 rounded text-pink-200 text-xs shadow-lg max-w-xs">
        <span class="font-bold">Security Intelligence:</span> Real-time threat detection, 
        automated incident response, and ML-powered anomaly detection active.
      </div>
    </div>
  );
}
