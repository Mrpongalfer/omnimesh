// Security Test Suite for OmniMesh
// Comprehensive security testing covering authentication, authorization, and attack prevention

const { test, expect } = require('@playwright/test');
const crypto = require('crypto');

// Test configuration
const TEST_CONFIG = {
  BASE_URL: process.env.TEST_URL || 'https://omnimesh.local',
  API_URL: process.env.API_URL || 'https://api.omnimesh.local',
  ADMIN_USERNAME: process.env.ADMIN_USERNAME || 'admin',
  ADMIN_PASSWORD: process.env.ADMIN_PASSWORD || 'secure-password',
  TEST_USERNAME: process.env.TEST_USERNAME || 'testuser',
  TEST_PASSWORD: process.env.TEST_PASSWORD || 'test-password',
  RATE_LIMIT_THRESHOLD: 5,
  SESSION_TIMEOUT: 900000, // 15 minutes
};

test.describe('Authentication Security', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(TEST_CONFIG.BASE_URL);
  });

  test('should reject invalid credentials', async ({ page }) => {
    await page.goto('/login');
    
    // Test invalid username/password
    await page.fill('[data-testid="username"]', 'invalid-user');
    await page.fill('[data-testid="password"]', 'invalid-password');
    await page.click('[data-testid="login-button"]');
    
    // Should show error message
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Invalid credentials');
    
    // Should not be redirected
    expect(page.url()).toContain('/login');
  });

  test('should enforce rate limiting on failed login attempts', async ({ page }) => {
    await page.goto('/login');
    
    // Attempt multiple failed logins rapidly
    for (let i = 0; i < TEST_CONFIG.RATE_LIMIT_THRESHOLD + 1; i++) {
      await page.fill('[data-testid="username"]', 'test-user');
      await page.fill('[data-testid="password"]', `wrong-password-${i}`);
      await page.click('[data-testid="login-button"]');
      
      if (i < TEST_CONFIG.RATE_LIMIT_THRESHOLD) {
        await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
      }
    }
    
    // Should be rate limited after threshold
    await expect(page.locator('[data-testid="rate-limit-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="rate-limit-message"]')).toContainText('Too many attempts');
    
    // Login button should be disabled
    await expect(page.locator('[data-testid="login-button"]')).toBeDisabled();
  });

  test('should require MFA for admin users', async ({ page }) => {
    await page.goto('/login');
    
    // Login with admin credentials
    await page.fill('[data-testid="username"]', TEST_CONFIG.ADMIN_USERNAME);
    await page.fill('[data-testid="password"]', TEST_CONFIG.ADMIN_PASSWORD);
    await page.click('[data-testid="login-button"]');
    
    // Should prompt for MFA
    await expect(page.locator('[data-testid="mfa-prompt"]')).toBeVisible();
    await expect(page.locator('[data-testid="mfa-input"]')).toBeVisible();
    
    // Should not be fully authenticated yet
    expect(page.url()).toContain('/mfa');
  });

  test('should enforce session timeout', async ({ page }) => {
    // Login successfully
    await page.goto('/login');
    await page.fill('[data-testid="username"]', TEST_CONFIG.TEST_USERNAME);
    await page.fill('[data-testid="password"]', TEST_CONFIG.TEST_PASSWORD);
    await page.click('[data-testid="login-button"]');
    
    // Wait for successful login
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
    
    // Simulate session timeout by manipulating localStorage
    await page.evaluate((timeout) => {
      const sessionData = JSON.parse(localStorage.getItem('session') || '{}');
      sessionData.expiresAt = Date.now() - 1000; // Expired 1 second ago
      localStorage.setItem('session', JSON.stringify(sessionData));
    }, TEST_CONFIG.SESSION_TIMEOUT);
    
    // Refresh page to trigger session check
    await page.reload();
    
    // Should be redirected to login
    await expect(page.locator('[data-testid="login-form"]')).toBeVisible();
    expect(page.url()).toContain('/login');
  });

  test('should prevent credential stuffing attacks', async ({ page }) => {
    const commonCredentials = [
      ['admin', 'admin'],
      ['admin', 'password'],
      ['root', 'root'],
      ['user', 'user'],
      ['test', 'test'],
    ];
    
    await page.goto('/login');
    
    for (const [username, password] of commonCredentials) {
      await page.fill('[data-testid="username"]', username);
      await page.fill('[data-testid="password"]', password);
      await page.click('[data-testid="login-button"]');
      
      // Should reject all common credentials
      await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
      
      // Add delay to avoid overwhelming the system
      await page.waitForTimeout(1000);
    }
    
    // Should eventually be rate limited
    await expect(page.locator('[data-testid="rate-limit-message"]')).toBeVisible();
  });
});

test.describe('Authorization Security', () => {
  test.beforeEach(async ({ page }) => {
    // Login as regular user
    await page.goto('/login');
    await page.fill('[data-testid="username"]', TEST_CONFIG.TEST_USERNAME);
    await page.fill('[data-testid="password"]', TEST_CONFIG.TEST_PASSWORD);
    await page.click('[data-testid="login-button"]');
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
  });

  test('should prevent privilege escalation', async ({ page }) => {
    // Attempt to access admin-only functionality
    await page.goto('/admin/users');
    
    // Should be denied access
    await expect(page.locator('[data-testid="access-denied"]')).toBeVisible();
    await expect(page.locator('[data-testid="access-denied"]')).toContainText('Insufficient permissions');
  });

  test('should validate permissions for API calls', async ({ page }) => {
    // Intercept API calls
    const unauthorizedCalls = [];
    
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
    }, TEST_CONFIG.API_URL);
    
    // Should have received 403 responses
    expect(unauthorizedCalls.length).toBeGreaterThan(0);
  });

  test('should enforce namespace isolation', async ({ page }) => {
    // Attempt to access resources from unauthorized namespace
    const response = await page.request.get(`${TEST_CONFIG.API_URL}/api/namespaces/kube-system/pods`);
    expect(response.status()).toBe(403);
  });
});

test.describe('XSS Protection', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('[data-testid="username"]', TEST_CONFIG.TEST_USERNAME);
    await page.fill('[data-testid="password"]', TEST_CONFIG.TEST_PASSWORD);
    await page.click('[data-testid="login-button"]');
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
  });

  test('should sanitize user input in search fields', async ({ page }) => {
    const xssPayloads = [
      '<script>alert("XSS")</script>',
      '"><script>alert("XSS")</script>',
      'javascript:alert("XSS")',
      '<img src=x onerror=alert("XSS")>',
      '<svg onload=alert("XSS")>',
    ];
    
    await page.goto('/search');
    
    for (const payload of xssPayloads) {
      await page.fill('[data-testid="search-input"]', payload);
      await page.click('[data-testid="search-button"]');
      
      // Check that script didn't execute
      const alerts = [];
      page.on('dialog', dialog => {
        alerts.push(dialog.message());
        dialog.dismiss();
      });
      
      await page.waitForTimeout(1000);
      expect(alerts).toHaveLength(0);
      
      // Check that input was sanitized
      const searchValue = await page.inputValue('[data-testid="search-input"]');
      expect(searchValue).not.toContain('<script>');
      expect(searchValue).not.toContain('javascript:');
    }
  });

  test('should prevent DOM-based XSS', async ({ page }) => {
    // Test URL parameters
    await page.goto(`/dashboard?name=<script>alert("XSS")</script>`);
    
    // Check that script didn't execute
    const alerts = [];
    page.on('dialog', dialog => {
      alerts.push(dialog.message());
      dialog.dismiss();
    });
    
    await page.waitForTimeout(2000);
    expect(alerts).toHaveLength(0);
  });

  test('should sanitize data in FabricMap component', async ({ page }) => {
    await page.goto('/fabric-map');
    
    // Inject malicious node data
    await page.evaluate(() => {
      const maliciousNode = {
        id: 'malicious',
        name: '<script>alert("XSS")</script>',
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
    });
    
    await page.waitForTimeout(2000);
    
    // Check that no alerts were triggered
    const alerts = [];
    page.on('dialog', dialog => {
      alerts.push(dialog.message());
      dialog.dismiss();
    });
    
    expect(alerts).toHaveLength(0);
  });
});

test.describe('CSRF Protection', () => {
  test('should include CSRF token in forms', async ({ page }) => {
    await page.goto('/login');
    await page.fill('[data-testid="username"]', TEST_CONFIG.TEST_USERNAME);
    await page.fill('[data-testid="password"]', TEST_CONFIG.TEST_PASSWORD);
    await page.click('[data-testid="login-button"]');
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
    
    // Navigate to a form page
    await page.goto('/settings');
    
    // Check for CSRF token
    const csrfToken = await page.locator('input[name="csrf_token"]').getAttribute('value');
    expect(csrfToken).toBeTruthy();
    expect(csrfToken.length).toBeGreaterThan(16);
  });

  test('should reject requests without valid CSRF token', async ({ page }) => {
    await page.goto('/login');
    await page.fill('[data-testid="username"]', TEST_CONFIG.TEST_USERNAME);
    await page.fill('[data-testid="password"]', TEST_CONFIG.TEST_PASSWORD);
    await page.click('[data-testid="login-button"]');
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
    
    // Make API request without CSRF token
    const response = await page.request.post(`${TEST_CONFIG.API_URL}/api/settings`, {
      data: { key: 'value' }
    });
    
    expect(response.status()).toBe(403);
  });
});

test.describe('Performance DoS Protection', () => {
  test('should limit FabricMap node rendering', async ({ page }) => {
    await page.goto('/login');
    await page.fill('[data-testid="username"]', TEST_CONFIG.TEST_USERNAME);
    await page.fill('[data-testid="password"]', TEST_CONFIG.TEST_PASSWORD);
    await page.click('[data-testid="login-button"]');
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
    
    await page.goto('/fabric-map');
    
    // Monitor memory usage
    const memoryBefore = await page.evaluate(() => {
      return (performance as any).memory ? (performance as any).memory.usedJSHeapSize : 0;
    });
    
    // Generate large dataset
    await page.evaluate(() => {
      const largeDataset = Array.from({ length: 10000 }, (_, i) => ({
        id: `stress-node-${i}`,
        x: Math.random() * 2000,
        y: Math.random() * 2000,
        status: 'active',
        name: `Stress Node ${i}`,
        connections: Array.from({ length: 10 }, (_, j) => `stress-node-${(i + j) % 10000}`)
      }));
      
      // Simulate data update
      window.postMessage({
        type: 'UPDATE_NODES',
        data: largeDataset
      }, '*');
    });
    
    // Wait for rendering
    await page.waitForTimeout(5000);
    
    const memoryAfter = await page.evaluate(() => {
      return (performance as any).memory ? (performance as any).memory.usedJSHeapSize : 0;
    });
    
    // Check that memory usage is controlled
    const memoryIncrease = memoryAfter - memoryBefore;
    expect(memoryIncrease).toBeLessThan(200 * 1024 * 1024); // 200MB limit
    
    // Check that performance warning is shown
    await expect(page.locator('[data-testid="performance-warning"]')).toBeVisible();
    
    // Check that performance mode is automatically enabled
    const isPerformanceMode = await page.locator('[data-testid="performance-mode-indicator"]').isVisible();
    expect(isPerformanceMode).toBe(true);
  });

  test('should throttle API requests', async ({ page }) => {
    await page.goto('/login');
    await page.fill('[data-testid="username"]', TEST_CONFIG.TEST_USERNAME);
    await page.fill('[data-testid="password"]', TEST_CONFIG.TEST_PASSWORD);
    await page.click('[data-testid="login-button"]');
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
    
    // Make rapid API requests
    const responses = await Promise.all(
      Array.from({ length: 20 }, () => 
        page.request.get(`${TEST_CONFIG.API_URL}/api/nodes`)
      )
    );
    
    // Should have some rate-limited responses
    const rateLimitedResponses = responses.filter(r => r.status() === 429);
    expect(rateLimitedResponses.length).toBeGreaterThan(0);
  });
});

test.describe('Data Validation', () => {
  test('should validate input lengths', async ({ page }) => {
    await page.goto('/login');
    await page.fill('[data-testid="username"]', TEST_CONFIG.TEST_USERNAME);
    await page.fill('[data-testid="password"]', TEST_CONFIG.TEST_PASSWORD);
    await page.click('[data-testid="login-button"]');
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
    
    await page.goto('/settings');
    
    // Test extremely long input
    const longString = 'A'.repeat(10000);
    await page.fill('[data-testid="description-input"]', longString);
    await page.click('[data-testid="save-button"]');
    
    // Should show validation error
    await expect(page.locator('[data-testid="validation-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="validation-error"]')).toContainText('too long');
  });

  test('should validate data types', async ({ page }) => {
    await page.goto('/login');
    await page.fill('[data-testid="username"]', TEST_CONFIG.TEST_USERNAME);
    await page.fill('[data-testid="password"]', TEST_CONFIG.TEST_PASSWORD);
    await page.click('[data-testid="login-button"]');
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
    
    // Test invalid data types in API calls
    const response = await page.request.post(`${TEST_CONFIG.API_URL}/api/nodes`, {
      data: {
        id: 123, // Should be string
        coordinates: 'invalid', // Should be number array
        status: 'invalid-status' // Should be valid enum
      }
    });
    
    expect(response.status()).toBe(400);
  });
});

test.describe('Security Headers', () => {
  test('should include security headers', async ({ page }) => {
    const response = await page.request.get(TEST_CONFIG.BASE_URL);
    
    const headers = response.headers();
    
    // Check for essential security headers
    expect(headers['x-frame-options']).toBeTruthy();
    expect(headers['x-content-type-options']).toBe('nosniff');
    expect(headers['x-xss-protection']).toBeTruthy();
    expect(headers['strict-transport-security']).toBeTruthy();
    expect(headers['content-security-policy']).toBeTruthy();
    expect(headers['referrer-policy']).toBeTruthy();
  });

  test('should have proper CSP directives', async ({ page }) => {
    const response = await page.request.get(TEST_CONFIG.BASE_URL);
    const csp = response.headers()['content-security-policy'];
    
    expect(csp).toContain("default-src 'self'");
    expect(csp).toContain("script-src 'self'");
    expect(csp).toContain("style-src 'self'");
    expect(csp).toContain("img-src 'self'");
    expect(csp).not.toContain("'unsafe-eval'");
    expect(csp).not.toContain("'unsafe-inline'");
  });
});

test.describe('Session Management', () => {
  test('should invalidate session on logout', async ({ page }) => {
    await page.goto('/login');
    await page.fill('[data-testid="username"]', TEST_CONFIG.TEST_USERNAME);
    await page.fill('[data-testid="password"]', TEST_CONFIG.TEST_PASSWORD);
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
    const response = await page.request.get(`${TEST_CONFIG.API_URL}/api/user`, {
      headers: {
        'X-Session-ID': sessionId
      }
    });
    
    expect(response.status()).toBe(401);
  });

  test('should regenerate session ID after login', async ({ page }) => {
    await page.goto('/login');
    
    // Get initial session ID (if any)
    const initialSessionId = await page.evaluate(() => {
      const session = JSON.parse(localStorage.getItem('session') || '{}');
      return session.id;
    });
    
    // Login
    await page.fill('[data-testid="username"]', TEST_CONFIG.TEST_USERNAME);
    await page.fill('[data-testid="password"]', TEST_CONFIG.TEST_PASSWORD);
    await page.click('[data-testid="login-button"]');
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
    
    // Get new session ID
    const newSessionId = await page.evaluate(() => {
      const session = JSON.parse(localStorage.getItem('session') || '{}');
      return session.id;
    });
    
    // Session ID should be different
    expect(newSessionId).not.toBe(initialSessionId);
    expect(newSessionId).toBeTruthy();
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
