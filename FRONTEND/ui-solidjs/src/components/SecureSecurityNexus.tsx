import { createSignal, For, onMount, onCleanup, createEffect, Show } from 'solid-js';
import { createStore } from 'solid-js/store';
import DOMPurify from 'dompurify';

// Security Configuration Constants
const SECURITY_CONFIG = {
  MAX_DISPLAY_ITEMS: 1000,
  REFRESH_INTERVAL: 5000,
  SESSION_TIMEOUT: 900000, // 15 minutes
  MAX_FAILED_ATTEMPTS: 3,
  REQUIRE_MFA: true,
  ENCRYPT_LOCAL_STORAGE: true,
  CSP_ENABLED: true,
  XSS_PROTECTION: true,
} as const;

// Security-hardened types with validation
interface SecureUser {
  readonly id: string;
  readonly name: string;
  readonly role: 'Admin' | 'Operator' | 'Viewer' | 'Daemon';
  readonly permissions: readonly string[];
  readonly lastAccess: Date;
  readonly status: 'active' | 'disabled' | 'locked';
  readonly mfaEnabled: boolean;
  readonly sessionValid: boolean;
}

interface SecureFirewallRule {
  readonly id: string;
  readonly name: string;
  readonly source: string;
  readonly destination: string;
  readonly port: number | 'any';
  readonly protocol: 'TCP' | 'UDP' | 'ICMP' | 'ANY';
  readonly action: 'allow' | 'deny' | 'log';
  readonly enabled: boolean;
  readonly priority: number;
  readonly createdAt: Date;
  readonly lastModified: Date;
  readonly modifiedBy: string;
}

interface SecureThreatAlert {
  readonly id: string;
  readonly type: 'intrusion' | 'anomaly' | 'malware' | 'policy_violation' | 'data_exfiltration';
  readonly severity: 'critical' | 'high' | 'medium' | 'low';
  readonly source: string;
  readonly target: string;
  readonly description: string;
  readonly timestamp: Date;
  readonly status: 'new' | 'investigating' | 'resolved' | 'false_positive';
  readonly mitigationActions: readonly string[];
  readonly confidence: number;
}

interface SecureEncryptionKey {
  readonly id: string;
  readonly name: string;
  readonly algorithm: 'AES-256' | 'RSA-2048' | 'RSA-4096' | 'ECDSA-P256';
  readonly purpose: 'data_encryption' | 'signing' | 'tls' | 'authentication';
  readonly status: 'active' | 'rotated' | 'revoked';
  readonly createdAt: Date;
  readonly expiresAt: Date;
  readonly lastUsed: Date;
  readonly keyFingerprint: string;
}

interface SecurityMetrics {
  readonly totalThreats: number;
  readonly activeIncidents: number;
  readonly blockedAttempts: number;
  readonly encryptionCompliance: number;
  readonly vulnerabilityScore: number;
  readonly lastUpdate: Date;
}

interface SecurityState {
  readonly isAuthenticated: boolean;
  readonly currentUser: SecureUser | null;
  readonly sessionExpiry: Date | null;
  readonly csrfToken: string | null;
  readonly permissions: readonly string[];
}

// Security validation functions
const validateInput = (input: string, maxLength: number = 255): string => {
  if (typeof input !== 'string') {
    throw new Error('Input must be a string');
  }
  
  if (input.length > maxLength) {
    throw new Error(`Input exceeds maximum length of ${maxLength}`);
  }
  
  // Sanitize HTML to prevent XSS
  return DOMPurify.sanitize(input, { ALLOWED_TAGS: [] });
};

const validateId = (id: string): string => {
  const idRegex = /^[a-zA-Z0-9_-]+$/;
  if (!idRegex.test(id)) {
    throw new Error('Invalid ID format');
  }
  return id;
};

const validatePermission = (operation: string, requiredPermissions: string[]): boolean => {
  const currentUser = getCurrentUser();
  if (!currentUser || !currentUser.sessionValid) {
    return false;
  }
  
  return requiredPermissions.some(perm => 
    currentUser.permissions.includes(perm) || 
    currentUser.permissions.includes('admin:all')
  );
};

// Secure API client with CSRF protection
class SecureApiClient {
  private csrfToken: string | null = null;
  private sessionId: string | null = null;
  
  constructor() {
    this.initializeSecurity();
  }
  
  private initializeSecurity() {
    // Initialize CSRF token
    this.csrfToken = this.generateCSRFToken();
    
    // Set up session management
    this.setupSessionManagement();
  }
  
  private generateCSRFToken(): string {
    const array = new Uint8Array(32);
    crypto.getRandomValues(array);
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
  }
  
  private setupSessionManagement() {
    // Monitor session expiry
    setInterval(() => {
      this.checkSessionValidity();
    }, 60000); // Check every minute
  }
  
  private checkSessionValidity() {
    const sessionExpiry = getSessionExpiry();
    if (sessionExpiry && new Date() > sessionExpiry) {
      this.logout();
    }
  }
  
  private async secureRequest(url: string, options: RequestInit = {}): Promise<Response> {
    const secureOptions: RequestInit = {
      ...options,
      headers: {
        ...options.headers,
        'X-CSRF-Token': this.csrfToken || '',
        'X-Session-ID': this.sessionId || '',
        'Content-Type': 'application/json',
      },
      credentials: 'same-origin',
    };
    
    // Validate URL to prevent SSRF
    const urlObj = new URL(url, window.location.origin);
    if (urlObj.origin !== window.location.origin) {
      throw new Error('External requests not allowed');
    }
    
    const response = await fetch(url, secureOptions);
    
    if (response.status === 401) {
      this.logout();
      throw new Error('Authentication failed');
    }
    
    if (response.status === 403) {
      throw new Error('Insufficient permissions');
    }
    
    return response;
  }
  
  async getUsers(): Promise<SecureUser[]> {
    const response = await this.secureRequest('/api/security/users');
    const data = await response.json();
    
    // Validate and sanitize response data
    return data.map((user: any) => ({
      id: validateId(user.id),
      name: validateInput(user.name),
      role: user.role,
      permissions: user.permissions || [],
      lastAccess: new Date(user.lastAccess),
      status: user.status,
      mfaEnabled: Boolean(user.mfaEnabled),
      sessionValid: Boolean(user.sessionValid),
    }));
  }
  
  async getFirewallRules(): Promise<SecureFirewallRule[]> {
    const response = await this.secureRequest('/api/security/firewall-rules');
    const data = await response.json();
    
    return data.map((rule: any) => ({
      id: validateId(rule.id),
      name: validateInput(rule.name),
      source: validateInput(rule.source),
      destination: validateInput(rule.destination),
      port: rule.port,
      protocol: rule.protocol,
      action: rule.action,
      enabled: Boolean(rule.enabled),
      priority: Number(rule.priority),
      createdAt: new Date(rule.createdAt),
      lastModified: new Date(rule.lastModified),
      modifiedBy: validateInput(rule.modifiedBy),
    }));
  }
  
  async getThreatAlerts(): Promise<SecureThreatAlert[]> {
    const response = await this.secureRequest('/api/security/threat-alerts');
    const data = await response.json();
    
    return data.slice(0, SECURITY_CONFIG.MAX_DISPLAY_ITEMS).map((alert: any) => ({
      id: validateId(alert.id),
      type: alert.type,
      severity: alert.severity,
      source: validateInput(alert.source),
      target: validateInput(alert.target),
      description: validateInput(alert.description, 1000),
      timestamp: new Date(alert.timestamp),
      status: alert.status,
      mitigationActions: alert.mitigationActions.map((action: string) => validateInput(action)),
      confidence: Math.max(0, Math.min(100, Number(alert.confidence))),
    }));
  }
  
  async getEncryptionKeys(): Promise<SecureEncryptionKey[]> {
    const response = await this.secureRequest('/api/security/encryption-keys');
    const data = await response.json();
    
    return data.map((key: any) => ({
      id: validateId(key.id),
      name: validateInput(key.name),
      algorithm: key.algorithm,
      purpose: key.purpose,
      status: key.status,
      createdAt: new Date(key.createdAt),
      expiresAt: new Date(key.expiresAt),
      lastUsed: new Date(key.lastUsed),
      keyFingerprint: validateInput(key.keyFingerprint),
    }));
  }
  
  async getSecurityMetrics(): Promise<SecurityMetrics> {
    const response = await this.secureRequest('/api/security/metrics');
    const data = await response.json();
    
    return {
      totalThreats: Number(data.totalThreats),
      activeIncidents: Number(data.activeIncidents),
      blockedAttempts: Number(data.blockedAttempts),
      encryptionCompliance: Math.max(0, Math.min(100, Number(data.encryptionCompliance))),
      vulnerabilityScore: Math.max(0, Math.min(100, Number(data.vulnerabilityScore))),
      lastUpdate: new Date(data.lastUpdate),
    };
  }
  
  private logout() {
    // Clear session data
    this.sessionId = null;
    this.csrfToken = null;
    
    // Clear sensitive data from memory
    clearSecurityState();
    
    // Redirect to login
    window.location.href = '/login';
  }
}

// Security state management
const [securityState, setSecurityState] = createStore<SecurityState>({
  isAuthenticated: false,
  currentUser: null,
  sessionExpiry: null,
  csrfToken: null,
  permissions: [],
});

// Helper functions
const getCurrentUser = (): SecureUser | null => securityState.currentUser;
const getSessionExpiry = (): Date | null => securityState.sessionExpiry;
const clearSecurityState = () => {
  setSecurityState({
    isAuthenticated: false,
    currentUser: null,
    sessionExpiry: null,
    csrfToken: null,
    permissions: [],
  });
};

// Secure SecurityNexus component
export default function SecurityNexus() {
  const [users, setUsers] = createSignal<SecureUser[]>([]);
  const [firewallRules, setFirewallRules] = createSignal<SecureFirewallRule[]>([]);
  const [threatAlerts, setThreatAlerts] = createSignal<SecureThreatAlert[]>([]);
  const [encryptionKeys, setEncryptionKeys] = createSignal<SecureEncryptionKey[]>([]);
  const [metrics, setMetrics] = createSignal<SecurityMetrics>();
  const [loading, setLoading] = createSignal(false);
  const [error, setError] = createSignal<string | null>(null);
  const [selectedTab, setSelectedTab] = createSignal<'users' | 'firewall' | 'threats' | 'encryption' | 'metrics'>('metrics');
  
  const apiClient = new SecureApiClient();
  let refreshInterval: number;
  
  // Authentication check
  createEffect(() => {
    if (!securityState.isAuthenticated) {
      window.location.href = '/login';
      return;
    }
    
    // Check permissions
    if (!validatePermission('security:read', ['security:read', 'security:admin'])) {
      setError('Insufficient permissions to view security data');
      return;
    }
    
    loadSecurityData();
  });
  
  const loadSecurityData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [usersData, rulesData, alertsData, keysData, metricsData] = await Promise.all([
        apiClient.getUsers(),
        apiClient.getFirewallRules(),
        apiClient.getThreatAlerts(),
        apiClient.getEncryptionKeys(),
        apiClient.getSecurityMetrics(),
      ]);
      
      setUsers(usersData);
      setFirewallRules(rulesData);
      setThreatAlerts(alertsData);
      setEncryptionKeys(keysData);
      setMetrics(metricsData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load security data';
      setError(errorMessage);
      console.error('Security data loading error:', err);
    } finally {
      setLoading(false);
    }
  };
  
  onMount(() => {
    refreshInterval = setInterval(loadSecurityData, SECURITY_CONFIG.REFRESH_INTERVAL);
  });
  
  onCleanup(() => {
    if (refreshInterval) {
      clearInterval(refreshInterval);
    }
  });
  
  const renderSecurityMetrics = () => {
    const metricsData = metrics();
    if (!metricsData) return null;
    
    return (
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div class="bg-red-900/20 border border-red-500/30 rounded-lg p-6">
          <div class="text-red-400 text-sm font-medium">Active Threats</div>
          <div class="text-3xl font-bold text-red-300 mt-2">{metricsData.totalThreats}</div>
          <div class="text-red-500 text-sm mt-1">
            {metricsData.activeIncidents} active incidents
          </div>
        </div>
        
        <div class="bg-blue-900/20 border border-blue-500/30 rounded-lg p-6">
          <div class="text-blue-400 text-sm font-medium">Blocked Attempts</div>
          <div class="text-3xl font-bold text-blue-300 mt-2">{metricsData.blockedAttempts}</div>
          <div class="text-blue-500 text-sm mt-1">Last 24 hours</div>
        </div>
        
        <div class="bg-green-900/20 border border-green-500/30 rounded-lg p-6">
          <div class="text-green-400 text-sm font-medium">Encryption Compliance</div>
          <div class="text-3xl font-bold text-green-300 mt-2">{metricsData.encryptionCompliance}%</div>
          <div class="text-green-500 text-sm mt-1">
            Target: 100%
          </div>
        </div>
        
        <div class="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-6">
          <div class="text-yellow-400 text-sm font-medium">Vulnerability Score</div>
          <div class="text-3xl font-bold text-yellow-300 mt-2">{metricsData.vulnerabilityScore}</div>
          <div class="text-yellow-500 text-sm mt-1">
            Lower is better
          </div>
        </div>
      </div>
    );
  };
  
  const renderThreatAlerts = () => (
    <div class="space-y-4">
      <For each={threatAlerts()}>
        {(alert) => (
          <div class={`border rounded-lg p-4 ${
            alert.severity === 'critical' ? 'border-red-500/50 bg-red-900/10' :
            alert.severity === 'high' ? 'border-orange-500/50 bg-orange-900/10' :
            alert.severity === 'medium' ? 'border-yellow-500/50 bg-yellow-900/10' :
            'border-blue-500/50 bg-blue-900/10'
          }`}>
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <div class="flex items-center gap-2">
                  <span class={`inline-block w-2 h-2 rounded-full ${
                    alert.severity === 'critical' ? 'bg-red-500' :
                    alert.severity === 'high' ? 'bg-orange-500' :
                    alert.severity === 'medium' ? 'bg-yellow-500' :
                    'bg-blue-500'
                  }`}></span>
                  <span class="text-sm font-medium text-gray-200">
                    {alert.type.replace('_', ' ').toUpperCase()}
                  </span>
                  <span class="text-xs text-gray-400">
                    {alert.confidence}% confidence
                  </span>
                </div>
                <div class="mt-2 text-sm text-gray-300">
                  {alert.description}
                </div>
                <div class="mt-2 text-xs text-gray-400">
                  {alert.source} → {alert.target}
                </div>
              </div>
              <div class="text-xs text-gray-500">
                {alert.timestamp.toLocaleString()}
              </div>
            </div>
          </div>
        )}
      </For>
    </div>
  );
  
  return (
    <div class="h-full flex flex-col bg-gray-900 text-white">
      {/* Header */}
      <div class="p-6 border-b border-gray-700">
        <div class="flex items-center justify-between">
          <h1 class="text-2xl font-bold">🔐 Security Nexus</h1>
          <div class="flex items-center gap-4">
            <Show when={metrics()}>
              <div class="text-sm">
                Last Updated: {metrics()?.lastUpdate.toLocaleTimeString()}
              </div>
            </Show>
            <button 
              onClick={loadSecurityData}
              disabled={loading()}
              class="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded-lg text-sm font-medium"
            >
              {loading() ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
        </div>
      </div>
      
      {/* Error Display */}
      <Show when={error()}>
        <div class="mx-6 mt-4 p-4 bg-red-900/20 border border-red-500/30 rounded-lg">
          <div class="text-red-400 text-sm">
            ⚠️ Error: {error()}
          </div>
        </div>
      </Show>
      
      {/* Tab Navigation */}
      <div class="px-6 pt-4">
        <div class="flex space-x-1 border-b border-gray-700">
          {['metrics', 'threats', 'firewall', 'encryption', 'users'].map(tab => (
            <button
              key={tab}
              onClick={() => setSelectedTab(tab as any)}
              class={`px-4 py-2 text-sm font-medium rounded-t-lg ${
                selectedTab() === tab 
                  ? 'bg-blue-600 text-white' 
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>
      </div>
      
      {/* Content */}
      <div class="flex-1 p-6 overflow-auto">
        <Show when={selectedTab() === 'metrics'}>
          {renderSecurityMetrics()}
        </Show>
        
        <Show when={selectedTab() === 'threats'}>
          {renderThreatAlerts()}
        </Show>
        
        <Show when={selectedTab() === 'firewall'}>
          <div class="text-gray-400">
            Firewall rules view - Implementation requires backend security validation
          </div>
        </Show>
        
        <Show when={selectedTab() === 'encryption'}>
          <div class="text-gray-400">
            Encryption keys view - Implementation requires backend security validation
          </div>
        </Show>
        
        <Show when={selectedTab() === 'users'}>
          <div class="text-gray-400">
            User management view - Implementation requires backend security validation
          </div>
        </Show>
      </div>
    </div>
  );
}
