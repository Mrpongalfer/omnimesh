import type { Plugin } from 'vite';
import { createHash } from 'crypto';

// Content Security Policy configuration for production security
const CSP_POLICY = {
  'default-src': ["'self'"],
  'script-src': [
    "'self'",
    "'unsafe-inline'", // Only for development - remove in production
    "'strict-dynamic'",
    'https://cdnjs.cloudflare.com',
    'https://cdn.jsdelivr.net'
  ],
  'style-src': [
    "'self'",
    "'unsafe-inline'", // Required for CSS-in-JS
    'https://fonts.googleapis.com'
  ],
  'font-src': [
    "'self'",
    'https://fonts.gstatic.com',
    'data:'
  ],
  'img-src': [
    "'self'",
    'data:',
    'https:'
  ],
  'media-src': ["'self'"],
  'object-src': ["'none'"],
  'base-uri': ["'self'"],
  'form-action': ["'self'"],
  'frame-ancestors': ["'none'"],
  'frame-src': ["'none'"],
  'child-src': ["'none'"],
  'worker-src': ["'self'"],
  'manifest-src': ["'self'"],
  'connect-src': [
    "'self'",
    'https://api.omnimesh.local',
    'wss://api.omnimesh.local',
    'https://telemetry.omnimesh.local'
  ],
  'upgrade-insecure-requests': []
};

// Security headers configuration
const SECURITY_HEADERS = {
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'X-XSS-Protection': '1; mode=block',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Permissions-Policy': 'geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=(), speaker=(), vibrate=(), fullscreen=(self), sync-xhr=()',
  'Strict-Transport-Security': 'max-age=63072000; includeSubDomains; preload',
  'Cross-Origin-Embedder-Policy': 'require-corp',
  'Cross-Origin-Opener-Policy': 'same-origin',
  'Cross-Origin-Resource-Policy': 'same-origin'
};

// Generate CSP string
function generateCSPString(policy: typeof CSP_POLICY): string {
  return Object.entries(policy)
    .map(([directive, sources]) => {
      if (sources.length === 0) {
        return directive;
      }
      return `${directive} ${sources.join(' ')}`;
    })
    .join('; ');
}

// Generate nonce for inline scripts
function generateNonce(): string {
  return createHash('sha256').update(Math.random().toString()).digest('base64');
}

// Security plugin for Vite
export function securityPlugin(): Plugin {
  const nonce = generateNonce();
  
  return {
    name: 'security-headers',
    configureServer(server) {
      server.middlewares.use('/', (_req, res, next) => {
        // Add security headers
        Object.entries(SECURITY_HEADERS).forEach(([header, value]) => {
          res.setHeader(header, value);
        });
        
        // Add CSP header with nonce
        const cspPolicy = { ...CSP_POLICY };
        cspPolicy['script-src'] = [
          ...cspPolicy['script-src'],
          `'nonce-${nonce}'`
        ];
        
        res.setHeader('Content-Security-Policy', generateCSPString(cspPolicy));
        next();
      });
    },
    transformIndexHtml: {
      enforce: 'pre',
      transform(html) {
        // Add security meta tags
        const securityMeta = `
          <meta charset="UTF-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1.0" />
          <meta http-equiv="X-UA-Compatible" content="IE=edge" />
          <meta http-equiv="Content-Security-Policy" content="${generateCSPString(CSP_POLICY)}" />
          <meta http-equiv="X-Content-Type-Options" content="nosniff" />
          <meta http-equiv="X-Frame-Options" content="DENY" />
          <meta http-equiv="X-XSS-Protection" content="1; mode=block" />
          <meta http-equiv="Referrer-Policy" content="strict-origin-when-cross-origin" />
          <meta http-equiv="Permissions-Policy" content="geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=(), speaker=(), vibrate=(), fullscreen=(self), sync-xhr=()" />
          <meta name="robots" content="noindex, nofollow" />
          <meta name="description" content="OmniMesh Control Panel - Secure Agent Orchestration" />
          <meta name="keywords" content="omnimesh, security, agent, orchestration" />
          <meta name="author" content="OmniMesh Security Team" />
          <link rel="dns-prefetch" href="https://api.omnimesh.local" />
          <link rel="preconnect" href="https://api.omnimesh.local" crossorigin />
        `;
        
        return html.replace('<head>', `<head>${securityMeta}`);
      }
    },
    generateBundle(_options, bundle) {
      // Add integrity hashes for all assets
      Object.keys(bundle).forEach(fileName => {
        const file = bundle[fileName];
        if (file && (file.type === 'asset' || file.type === 'chunk')) {
          const content = file.type === 'asset' ? 
            (file as any).source : 
            (file as any).code;
          const hash = createHash('sha384').update(content).digest('base64');
          
          // Store integrity hash for use in HTML
          if (file.type === 'chunk') {
            (file as any).code = `/* Integrity: sha384-${hash} */\n${(file as any).code}`;
          }
        }
      });
    }
  };
}

// Rate limiting configuration
export const rateLimitConfig = {
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 1000, // limit each IP to 1000 requests per windowMs
  message: {
    error: 'Too many requests from this IP, please try again later.',
    retryAfter: 900 // 15 minutes in seconds
  },
  standardHeaders: true,
  legacyHeaders: false,
  skipSuccessfulRequests: false,
  skipFailedRequests: false,
  keyGenerator: (req: any) => {
    return req.ip || req.connection.remoteAddress || req.socket.remoteAddress || 'unknown';
  }
};

// CSRF protection configuration
export const csrfConfig = {
  cookieOptions: {
    httpOnly: true,
    secure: true,
    sameSite: 'strict' as const,
    maxAge: 3600000 // 1 hour
  },
  ignoredMethods: ['GET', 'HEAD', 'OPTIONS'],
  value: (req: any) => {
    return req.headers['x-csrf-token'] || req.body._csrf || req.query._csrf;
  }
};

// Security audit configuration
export const auditConfig = {
  logLevel: 'info',
  logFormat: 'json',
  auditEvents: [
    'authentication',
    'authorization',
    'data-access',
    'configuration-change',
    'security-violation',
    'performance-issue',
    'error'
  ],
  retentionDays: 90,
  alertThresholds: {
    failedLogins: 5,
    securityViolations: 1,
    performanceIssues: 10,
    errors: 50
  }
};

export default {
  CSP_POLICY,
  SECURITY_HEADERS,
  securityPlugin,
  rateLimitConfig,
  csrfConfig,
  auditConfig,
  generateCSPString,
  generateNonce
};
