// Production-Grade Security Configuration
// Centralized security settings for all components
export const SECURITY_CONFIG = {
  // Authentication & Authorization
  AUTH: {
    MAX_LOGIN_ATTEMPTS: 3,
    LOCKOUT_DURATION: 900000, // 15 minutes
    SESSION_TIMEOUT: 3600000, // 1 hour
    JWT_EXPIRY: 1800000, // 30 minutes
    REFRESH_TOKEN_EXPIRY: 86400000, // 24 hours
    REQUIRE_MFA: true,
    PASSWORD_MIN_LENGTH: 12,
    PASSWORD_COMPLEXITY: {
      requireUppercase: true,
      requireLowercase: true,
      requireNumbers: true,
      requireSymbols: true
    }
  },

  // Rate Limiting
  RATE_LIMITING: {
    API_REQUESTS_PER_MINUTE: 100,
    LOGIN_ATTEMPTS_PER_MINUTE: 5,
    WORKFLOW_EXECUTIONS_PER_MINUTE: 10,
    MINDFORGE_OPERATIONS_PER_MINUTE: 50
  },

  // Content Security
  CONTENT_SECURITY: {
    MAX_INPUT_LENGTH: 10000,
    MAX_UPLOAD_SIZE: 10 * 1024 * 1024, // 10MB
    ALLOWED_FILE_TYPES: ['json', 'yaml', 'txt', 'md'],
    SANITIZE_HTML: true,
    SANITIZE_SCRIPTS: true,
    SANITIZE_STYLES: true
  },

  // MindForge Security
  MINDFORGE: {
    MAX_NODES: 50,
    MAX_EDGES: 100,
    MAX_EXECUTION_TIME: 30000, // 30 seconds
    MAX_MEMORY_USAGE: 100 * 1024 * 1024, // 100MB
    MAX_ITERATIONS: 1000,
    ALLOWED_FUNCTIONS: [
      'console.log',
      'Math.abs',
      'Math.max',
      'Math.min',
      'Math.floor',
      'Math.ceil',
      'Math.round',
      'String.prototype.toLowerCase',
      'String.prototype.toUpperCase',
      'String.prototype.trim',
      'Array.prototype.map',
      'Array.prototype.filter',
      'Array.prototype.reduce',
      'JSON.stringify',
      'JSON.parse'
    ],
    DENIED_PATTERNS: [
      /eval\s*\(/,
      /Function\s*\(/,
      /setTimeout\s*\(/,
      /setInterval\s*\(/,
      /import\s*\(/,
      /require\s*\(/,
      /process\./,
      /global\./,
      /window\./,
      /document\./,
      /localStorage\./,
      /sessionStorage\./,
      /fetch\s*\(/,
      /XMLHttpRequest/,
      /WebSocket/,
      /postMessage/,
      /innerHTML/,
      /outerHTML/,
      /insertAdjacentHTML/,
      /execScript/,
      /msSetImmediate/,
      /requestAnimationFrame/,
      /cancelAnimationFrame/
    ]
  },

  // FabricMap Security
  FABRIC_MAP: {
    MAX_NODES: 1000,
    MAX_EDGES: 2000,
    MAX_RENDER_TIME: 16, // 16ms for 60fps
    MAX_MEMORY_USAGE: 200 * 1024 * 1024, // 200MB
    VIRTUALIZATION_THRESHOLD: 500,
    LOD_LEVELS: 3,
    PERFORMANCE_MONITORING: true,
    AUTO_PERFORMANCE_MODE: true
  },

  // API Security
  API: {
    BASE_URL: process.env.VITE_API_URL || 'https://api.omnimesh.local',
    TIMEOUT: 30000,
    RETRY_ATTEMPTS: 3,
    RETRY_DELAY: 1000,
    USE_HTTPS: true,
    VERIFY_SSL: true,
    CSRF_PROTECTION: true,
    CORS_ORIGINS: ['https://omnimesh.local', 'https://app.omnimesh.local']
  },

  // Monitoring & Logging
  MONITORING: {
    PERFORMANCE_BUDGET: {
      FCP: 2000, // First Contentful Paint
      LCP: 4000, // Largest Contentful Paint
      FID: 300,  // First Input Delay
      CLS: 0.1   // Cumulative Layout Shift
    },
    LOG_LEVELS: {
      ERROR: 0,
      WARN: 1,
      INFO: 2,
      DEBUG: 3
    },
    AUDIT_EVENTS: [
      'auth_login',
      'auth_logout',
      'auth_failure',
      'workflow_execution',
      'security_violation',
      'performance_degradation',
      'error_occurred'
    ]
  },

  // Network Security
  NETWORK: {
    ALLOWED_ORIGINS: [
      'https://omnimesh.local',
      'https://app.omnimesh.local',
      'https://api.omnimesh.local'
    ],
    BLOCKED_DOMAINS: [
      'localhost',
      '127.0.0.1',
      '0.0.0.0',
      'example.com',
      'test.com'
    ],
    WEBSOCKET_ALLOWED: true,
    WEBSOCKET_ORIGINS: ['wss://api.omnimesh.local']
  },

  // Error Handling
  ERROR_HANDLING: {
    SHOW_STACK_TRACES: false,
    LOG_SENSITIVE_DATA: false,
    GENERIC_ERROR_MESSAGES: true,
    MAX_ERROR_REPORTS: 100,
    ERROR_REPORT_RETENTION: 86400000 // 24 hours
  },

  // Features Flags
  FEATURES: {
    DEVELOPMENT_MODE: process.env.NODE_ENV === 'development',
    BETA_FEATURES: false,
    ANALYTICS: true,
    TELEMETRY: true,
    DEBUG_MODE: process.env.NODE_ENV === 'development'
  }
} as const;

// Security utility functions
export const SecurityUtils = {
  // Validate input against security patterns
  validateInput(input: string): boolean {
    const deniedPatterns = SECURITY_CONFIG.MINDFORGE.DENIED_PATTERNS;
    return !deniedPatterns.some(pattern => pattern.test(input));
  },

  // Sanitize HTML content
  sanitizeHTML(content: string): string {
    // Use DOMPurify for sanitization
    return content.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
  },

  // Check if domain is allowed
  isAllowedDomain(domain: string): boolean {
    return SECURITY_CONFIG.NETWORK.ALLOWED_ORIGINS.some(origin => 
      origin.includes(domain)
    );
  },

  // Generate secure random string
  generateSecureToken(length: number = 32): string {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    const randomArray = new Uint8Array(length);
    crypto.getRandomValues(randomArray);
    
    for (let i = 0; i < length; i++) {
      result += chars[randomArray[i] % chars.length];
    }
    return result;
  },

  // Validate JWT token format
  validateJWTFormat(token: string): boolean {
    const parts = token.split('.');
    return parts.length === 3 && parts.every(part => part.length > 0);
  },

  // Check password strength
  validatePasswordStrength(password: string): {
    isValid: boolean;
    score: number;
    feedback: string[];
  } {
    const { PASSWORD_MIN_LENGTH, PASSWORD_COMPLEXITY } = SECURITY_CONFIG.AUTH;
    const feedback: string[] = [];
    let score = 0;

    if (password.length < PASSWORD_MIN_LENGTH) {
      feedback.push(`Password must be at least ${PASSWORD_MIN_LENGTH} characters`);
    } else {
      score += 25;
    }

    if (PASSWORD_COMPLEXITY.requireUppercase && !/[A-Z]/.test(password)) {
      feedback.push('Password must contain uppercase letters');
    } else {
      score += 25;
    }

    if (PASSWORD_COMPLEXITY.requireLowercase && !/[a-z]/.test(password)) {
      feedback.push('Password must contain lowercase letters');
    } else {
      score += 25;
    }

    if (PASSWORD_COMPLEXITY.requireNumbers && !/\d/.test(password)) {
      feedback.push('Password must contain numbers');
    } else {
      score += 25;
    }

    if (PASSWORD_COMPLEXITY.requireSymbols && !/[^A-Za-z0-9]/.test(password)) {
      feedback.push('Password must contain special characters');
    } else {
      score += 25;
    }

    return {
      isValid: feedback.length === 0,
      score: Math.min(score, 100),
      feedback
    };
  }
};

// Export types for TypeScript
export type SecurityConfig = typeof SECURITY_CONFIG;
export type SecurityUtils = typeof SecurityUtils;
