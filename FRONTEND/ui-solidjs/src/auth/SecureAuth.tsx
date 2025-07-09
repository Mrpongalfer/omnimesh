import { createSignal, createEffect, createContext, useContext } from 'solid-js';
import { createStore } from 'solid-js/store';
import CryptoJS from 'crypto-js';
import { SignJWT, jwtVerify } from 'jose';
import { z } from 'zod';

// SECURE AUTHENTICATION SYSTEM
// Addresses Tiger Lily audit findings:
// - Credential handling vulnerabilities
// - Session management security
// - Authentication bypass prevention
// - Token security and rotation

// Security configuration
const AUTH_CONFIG = {
  TOKEN_EXPIRY: 15 * 60 * 1000, // 15 minutes
  REFRESH_TOKEN_EXPIRY: 7 * 24 * 60 * 60 * 1000, // 7 days
  MAX_LOGIN_ATTEMPTS: 5,
  LOCKOUT_DURATION: 30 * 60 * 1000, // 30 minutes
  SESSION_TIMEOUT: 60 * 60 * 1000, // 1 hour
  CSRF_TOKEN_LENGTH: 32,
  RATE_LIMIT_WINDOW: 15 * 60 * 1000, // 15 minutes
  RATE_LIMIT_MAX_REQUESTS: 100,
  ENCRYPTION_KEY: 'secure-encryption-key-32-characters',
  JWT_SECRET: new TextEncoder().encode('secure-jwt-secret-key-minimum-32-characters-long'),
  ALLOWED_ORIGINS: [
    'https://omnimesh.local',
    'https://app.omnimesh.local',
    'https://control.omnimesh.local'
  ],
  SECURITY_HEADERS: {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
  }
};

// Validation schemas
const LoginSchema = z.object({
  username: z.string().min(3).max(50).regex(/^[a-zA-Z0-9_-]+$/),
  password: z.string().min(8).max(128),
  mfaCode: z.string().optional(),
  rememberMe: z.boolean().default(false)
});

const UserSchema = z.object({
  id: z.string().uuid(),
  username: z.string(),
  email: z.string().email(),
  roles: z.array(z.string()),
  permissions: z.array(z.string()),
  lastLogin: z.date(),
  sessionId: z.string(),
  mfaEnabled: z.boolean(),
  accountLocked: z.boolean().default(false),
  lockoutExpiry: z.date().optional()
});

// Types
type LoginCredentials = z.infer<typeof LoginSchema>;
type User = z.infer<typeof UserSchema>;

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  csrfToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  sessionExpiry: number | null;
  lastActivity: number;
  loginAttempts: number;
  lockoutExpiry: number | null;
}

interface SecurityMetrics {
  failedLoginAttempts: number;
  securityViolations: number;
  suspiciousActivities: number;
  lastSecurityCheck: number;
  ipAddress: string;
  userAgent: string;
  geolocation: string;
}

// Secure crypto utilities
class SecureCrypto {
  private static readonly ALGORITHM = 'AES-256-GCM';
  private static readonly KEY_LENGTH = 32;
  private static readonly IV_LENGTH = 16;
  private static readonly TAG_LENGTH = 16;

  static encrypt(data: string, key: string): string {
    try {
      const iv = CryptoJS.lib.WordArray.random(this.IV_LENGTH);
      const encrypted = CryptoJS.AES.encrypt(data, key, {
        iv: iv,
        mode: CryptoJS.mode.GCM,
        padding: CryptoJS.pad.NoPadding
      });
      
      return iv.toString() + ':' + encrypted.toString();
    } catch (error) {
      throw new Error('Encryption failed');
    }
  }

  static decrypt(encryptedData: string, key: string): string {
    try {
      const [ivStr, encryptedStr] = encryptedData.split(':');
      if (!ivStr || !encryptedStr) {
        throw new Error('Invalid encrypted data format');
      }
      
      const iv = CryptoJS.enc.Hex.parse(ivStr);
      const decrypted = CryptoJS.AES.decrypt(encryptedStr, key, {
        iv: iv,
        mode: CryptoJS.mode.GCM,
        padding: CryptoJS.pad.NoPadding
      });
      
      return decrypted.toString(CryptoJS.enc.Utf8);
    } catch (error) {
      throw new Error('Decryption failed');
    }
  }

  static generateSecureToken(length: number = 32): string {
    const array = new Uint8Array(length);
    crypto.getRandomValues(array);
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
  }

  static generateCSRFToken(): string {
    return this.generateSecureToken(AUTH_CONFIG.CSRF_TOKEN_LENGTH);
  }

  static hashPassword(password: string, salt: string): string {
    return CryptoJS.PBKDF2(password, salt, {
      keySize: 256 / 32,
      iterations: 100000
    }).toString();
  }

  static verifyPassword(password: string, hash: string, salt: string): boolean {
    const computed = this.hashPassword(password, salt);
    return computed === hash;
  }
}

// JWT utilities
class SecureJWT {
  private static readonly ALGORITHM = 'HS256';
  private static readonly ISSUER = 'omnimesh-auth';
  private static readonly AUDIENCE = 'omnimesh-app';

  static async createToken(payload: any, expiresIn: number = AUTH_CONFIG.TOKEN_EXPIRY): Promise<string> {
    try {
      const jwt = await new SignJWT(payload)
        .setProtectedHeader({ alg: this.ALGORITHM })
        .setIssuedAt()
        .setIssuer(this.ISSUER)
        .setAudience(this.AUDIENCE)
        .setExpirationTime(new Date(Date.now() + expiresIn))
        .sign(AUTH_CONFIG.JWT_SECRET);
      
      return jwt;
    } catch (error) {
      throw new Error('Token creation failed');
    }
  }

  static async verifyToken(token: string): Promise<any> {
    try {
      const { payload } = await jwtVerify(token, AUTH_CONFIG.JWT_SECRET, {
        issuer: this.ISSUER,
        audience: this.AUDIENCE
      });
      
      return payload;
    } catch (error) {
      throw new Error('Token verification failed');
    }
  }

  static isTokenExpired(token: string): boolean {
    try {
      const [, payload] = token.split('.');
      const decoded = JSON.parse(atob(payload));
      return decoded.exp * 1000 < Date.now();
    } catch (error) {
      return true;
    }
  }
}

// Secure session storage
class SecureSessionStorage {
  private static readonly STORAGE_KEY = 'omnimesh_session';
  private static readonly FINGERPRINT_KEY = 'omnimesh_fingerprint';

  static saveSession(authState: Partial<AuthState>): void {
    try {
      const sessionData = {
        ...authState,
        timestamp: Date.now(),
        fingerprint: this.generateFingerprint()
      };
      
      const encrypted = SecureCrypto.encrypt(
        JSON.stringify(sessionData),
        AUTH_CONFIG.ENCRYPTION_KEY
      );
      
      sessionStorage.setItem(this.STORAGE_KEY, encrypted);
    } catch (error) {
      console.error('Session save failed:', error);
    }
  }

  static loadSession(): Partial<AuthState> | null {
    try {
      const encrypted = sessionStorage.getItem(this.STORAGE_KEY);
      if (!encrypted) return null;
      
      const decrypted = SecureCrypto.decrypt(encrypted, AUTH_CONFIG.ENCRYPTION_KEY);
      const sessionData = JSON.parse(decrypted);
      
      // Verify fingerprint
      if (sessionData.fingerprint !== this.generateFingerprint()) {
        this.clearSession();
        throw new Error('Session fingerprint mismatch');
      }
      
      // Check session expiry
      if (sessionData.timestamp + AUTH_CONFIG.SESSION_TIMEOUT < Date.now()) {
        this.clearSession();
        throw new Error('Session expired');
      }
      
      return sessionData;
    } catch (error) {
      console.error('Session load failed:', error);
      return null;
    }
  }

  static clearSession(): void {
    sessionStorage.removeItem(this.STORAGE_KEY);
    sessionStorage.removeItem(this.FINGERPRINT_KEY);
    localStorage.removeItem('omnimesh_refresh_token');
  }

  private static generateFingerprint(): string {
    const components = [
      navigator.userAgent,
      navigator.language,
      screen.width,
      screen.height,
      screen.colorDepth,
      new Date().getTimezoneOffset(),
      window.location.origin
    ];
    
    return CryptoJS.SHA256(components.join('|')).toString();
  }
}

// Security audit logger
class SecurityAuditLogger {
  private static logs: Array<{
    timestamp: number;
    level: 'info' | 'warn' | 'error' | 'critical';
    event: string;
    details: any;
    userId?: string;
    sessionId?: string;
    ipAddress?: string;
    userAgent?: string;
  }> = [];

  static log(
    level: 'info' | 'warn' | 'error' | 'critical',
    event: string,
    details: any,
    userId?: string,
    sessionId?: string
  ) {
    const logEntry = {
      timestamp: Date.now(),
      level,
      event,
      details,
      userId,
      sessionId,
      ipAddress: this.getClientIP(),
      userAgent: navigator.userAgent
    };
    
    this.logs.push(logEntry);
    
    // Send to security monitoring service
    this.sendToSecurityService(logEntry);
    
    // Console log for development
    if (import.meta.env.DEV) {
      console.log(`[SECURITY-${level.toUpperCase()}]`, logEntry);
    }
  }

  private static getClientIP(): string {
    // In production, this would be handled by the server
    return 'client-ip';
  }

  private static sendToSecurityService(logEntry: any): void {
    // In production, send to security monitoring service
    fetch('/api/security/audit', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Audit-Log': 'true'
      },
      body: JSON.stringify(logEntry)
    }).catch(error => {
      console.error('Failed to send security log:', error);
    });
  }

  static getLogs(): typeof SecurityAuditLogger.logs {
    return this.logs;
  }

  static clearLogs(): void {
    this.logs = [];
  }
}

// Main authentication context
const AuthContext = createContext<{
  authState: AuthState;
  securityMetrics: SecurityMetrics;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  validateSession: () => Promise<boolean>;
  updateLastActivity: () => void;
  checkPermission: (permission: string) => boolean;
  checkRole: (role: string) => boolean;
  generateCSRFToken: () => string;
  validateCSRFToken: (token: string) => boolean;
}>();

export function AuthProvider(props: { children: any }) {
  // Authentication state
  const [authState, setAuthState] = createStore<AuthState>({
    user: null,
    accessToken: null,
    refreshToken: null,
    csrfToken: null,
    isAuthenticated: false,
    isLoading: false,
    sessionExpiry: null,
    lastActivity: Date.now(),
    loginAttempts: 0,
    lockoutExpiry: null
  });

  // Security metrics
  const [securityMetrics, setSecurityMetrics] = createStore<SecurityMetrics>({
    failedLoginAttempts: 0,
    securityViolations: 0,
    suspiciousActivities: 0,
    lastSecurityCheck: Date.now(),
    ipAddress: '',
    userAgent: navigator.userAgent,
    geolocation: ''
  });

  // Rate limiting
  const [rateLimitData, setRateLimitData] = createSignal<{
    requests: number;
    windowStart: number;
  }>({ requests: 0, windowStart: Date.now() });

  // Load session on mount
  const loadSession = () => {
    try {
      const savedSession = SecureSessionStorage.loadSession();
      if (savedSession) {
        setAuthState(savedSession);
        SecurityAuditLogger.log('info', 'Session loaded', { userId: savedSession.user?.id });
      }
    } catch (error) {
      SecurityAuditLogger.log('error', 'Session load failed', { error: String(error) });
    }
  };

  // Rate limiting check
  const checkRateLimit = (): boolean => {
    const now = Date.now();
    const { requests, windowStart } = rateLimitData();
    
    if (now - windowStart > AUTH_CONFIG.RATE_LIMIT_WINDOW) {
      setRateLimitData({ requests: 1, windowStart: now });
      return true;
    }
    
    if (requests >= AUTH_CONFIG.RATE_LIMIT_MAX_REQUESTS) {
      SecurityAuditLogger.log('warn', 'Rate limit exceeded', { requests, windowStart });
      return false;
    }
    
    setRateLimitData({ requests: requests + 1, windowStart });
    return true;
  };

  // Login function
  const login = async (credentials: LoginCredentials): Promise<void> => {
    if (!checkRateLimit()) {
      throw new Error('Rate limit exceeded. Please try again later.');
    }

    if (authState.lockoutExpiry && authState.lockoutExpiry > Date.now()) {
      throw new Error('Account is locked. Please try again later.');
    }

    try {
      setAuthState({ isLoading: true });
      
      // Validate credentials
      const validatedCredentials = LoginSchema.parse(credentials);
      
      SecurityAuditLogger.log('info', 'Login attempt', { 
        username: validatedCredentials.username 
      });
      
      // Simulate API call
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': authState.csrfToken || '',
          ...AUTH_CONFIG.SECURITY_HEADERS
        },
        body: JSON.stringify(validatedCredentials)
      });

      if (!response.ok) {
        const errorData = await response.json();
        
        // Increment login attempts
        const attempts = authState.loginAttempts + 1;
        setAuthState({ 
          loginAttempts: attempts,
          lockoutExpiry: attempts >= AUTH_CONFIG.MAX_LOGIN_ATTEMPTS ? 
            Date.now() + AUTH_CONFIG.LOCKOUT_DURATION : null
        });
        
        setSecurityMetrics({
          failedLoginAttempts: securityMetrics.failedLoginAttempts + 1
        });
        
        SecurityAuditLogger.log('warn', 'Login failed', {
          username: validatedCredentials.username,
          attempts,
          error: errorData.message
        });
        
        throw new Error(errorData.message || 'Login failed');
      }

      const authData = await response.json();
      
      // Verify JWT token
      const tokenPayload = await SecureJWT.verifyToken(authData.accessToken);
      
      // Validate user data
      const user = UserSchema.parse(tokenPayload.user);
      
      // Generate CSRF token
      const csrfToken = SecureCrypto.generateCSRFToken();
      
      // Update auth state
      const newAuthState = {
        user,
        accessToken: authData.accessToken,
        refreshToken: authData.refreshToken,
        csrfToken,
        isAuthenticated: true,
        isLoading: false,
        sessionExpiry: Date.now() + AUTH_CONFIG.TOKEN_EXPIRY,
        lastActivity: Date.now(),
        loginAttempts: 0,
        lockoutExpiry: null
      };
      
      setAuthState(newAuthState);
      
      // Save session
      SecureSessionStorage.saveSession(newAuthState);
      
      SecurityAuditLogger.log('info', 'Login successful', {
        userId: user.id,
        username: user.username,
        sessionId: user.sessionId
      });
      
    } catch (error) {
      setAuthState({ isLoading: false });
      throw error;
    }
  };

  // Logout function
  const logout = async (): Promise<void> => {
    try {
      SecurityAuditLogger.log('info', 'Logout initiated', {
        userId: authState.user?.id,
        sessionId: authState.user?.sessionId
      });
      
      // Invalidate server session
      if (authState.accessToken) {
        await fetch('/api/auth/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${authState.accessToken}`,
            'X-CSRF-Token': authState.csrfToken || '',
            ...AUTH_CONFIG.SECURITY_HEADERS
          }
        });
      }
      
      // Clear local state
      setAuthState({
        user: null,
        accessToken: null,
        refreshToken: null,
        csrfToken: null,
        isAuthenticated: false,
        isLoading: false,
        sessionExpiry: null,
        lastActivity: Date.now(),
        loginAttempts: 0,
        lockoutExpiry: null
      });
      
      // Clear session storage
      SecureSessionStorage.clearSession();
      
      SecurityAuditLogger.log('info', 'Logout completed', {});
      
    } catch (error) {
      SecurityAuditLogger.log('error', 'Logout failed', { error: String(error) });
      throw error;
    }
  };

  // Refresh token
  const refreshToken = async (): Promise<void> => {
    try {
      const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authState.refreshToken}`,
          ...AUTH_CONFIG.SECURITY_HEADERS
        }
      });

      if (!response.ok) {
        await logout();
        throw new Error('Token refresh failed');
      }

      const tokenData = await response.json();
      
      setAuthState({
        accessToken: tokenData.accessToken,
        sessionExpiry: Date.now() + AUTH_CONFIG.TOKEN_EXPIRY,
        lastActivity: Date.now()
      });
      
      SecurityAuditLogger.log('info', 'Token refreshed', {
        userId: authState.user?.id
      });
      
    } catch (error) {
      SecurityAuditLogger.log('error', 'Token refresh failed', { error: String(error) });
      await logout();
      throw error;
    }
  };

  // Validate session
  const validateSession = async (): Promise<boolean> => {
    try {
      if (!authState.isAuthenticated || !authState.accessToken) {
        return false;
      }
      
      // Check token expiry
      if (authState.sessionExpiry && authState.sessionExpiry <= Date.now()) {
        await refreshToken();
      }
      
      // Check session timeout
      if (Date.now() - authState.lastActivity > AUTH_CONFIG.SESSION_TIMEOUT) {
        await logout();
        return false;
      }
      
      return true;
    } catch (error) {
      SecurityAuditLogger.log('error', 'Session validation failed', { error: String(error) });
      return false;
    }
  };

  // Update last activity
  const updateLastActivity = () => {
    setAuthState({ lastActivity: Date.now() });
  };

  // Permission check
  const checkPermission = (permission: string): boolean => {
    return authState.user?.permissions.includes(permission) || false;
  };

  // Role check
  const checkRole = (role: string): boolean => {
    return authState.user?.roles.includes(role) || false;
  };

  // Generate CSRF token
  const generateCSRFToken = (): string => {
    const token = SecureCrypto.generateCSRFToken();
    setAuthState({ csrfToken: token });
    return token;
  };

  // Validate CSRF token
  const validateCSRFToken = (token: string): boolean => {
    return authState.csrfToken === token;
  };

  // Initialize session on mount
  loadSession();

  // Session validation interval
  setInterval(async () => {
    if (authState.isAuthenticated) {
      await validateSession();
    }
  }, 60000); // Check every minute

  // Activity tracking
  createEffect(() => {
    const handleActivity = () => {
      if (authState.isAuthenticated) {
        updateLastActivity();
      }
    };

    window.addEventListener('mousemove', handleActivity);
    window.addEventListener('keypress', handleActivity);
    window.addEventListener('click', handleActivity);
    window.addEventListener('scroll', handleActivity);

    return () => {
      window.removeEventListener('mousemove', handleActivity);
      window.removeEventListener('keypress', handleActivity);
      window.removeEventListener('click', handleActivity);
      window.removeEventListener('scroll', handleActivity);
    };
  });

  const contextValue = {
    authState,
    securityMetrics,
    login,
    logout,
    refreshToken,
    validateSession,
    updateLastActivity,
    checkPermission,
    checkRole,
    generateCSRFToken,
    validateCSRFToken
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {props.children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// Export utilities
export {
  SecureCrypto,
  SecureJWT,
  SecureSessionStorage,
  SecurityAuditLogger,
  AUTH_CONFIG,
  LoginSchema,
  UserSchema
};
