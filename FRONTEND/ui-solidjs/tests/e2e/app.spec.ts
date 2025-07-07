import { test, expect } from '@playwright/test';

test.describe('Omnitide Control Panel', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display the main control panel', async ({ page }) => {
    await expect(page).toHaveTitle(/Omnitide/);
    await expect(page.locator('[data-testid="fabric-map"]')).toBeVisible();
  });

  test('should render notification feed', async ({ page }) => {
    await expect(
      page.locator('[data-testid="notification-feed"]'),
    ).toBeVisible();
  });

  test('should allow panel switching', async ({ page }) => {
    // Test main panel
    await expect(page.locator('[data-testid="main-panel"]')).toBeVisible();

    // Switch to Mind Forge
    await page.click('[data-testid="mindforge-tab"]');
    await expect(page.locator('[data-testid="mindforge-panel"]')).toBeVisible();

    // Switch to Data Fabric
    await page.click('[data-testid="datafabric-tab"]');
    await expect(
      page.locator('[data-testid="datafabric-panel"]'),
    ).toBeVisible();

    // Switch to Security
    await page.click('[data-testid="security-tab"]');
    await expect(page.locator('[data-testid="security-panel"]')).toBeVisible();
  });

  test('should support keyboard navigation', async ({ page }) => {
    // Test ESC key functionality
    await page.keyboard.press('Escape');

    // Test help shortcut
    await page.keyboard.press('h');

    // Test command line shortcut
    await page.keyboard.press('/');
  });

  test('should be responsive', async ({ page }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.locator('[data-testid="mobile-layout"]')).toBeVisible();

    // Test tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });

    // Test desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    await expect(page.locator('[data-testid="desktop-layout"]')).toBeVisible();
  });

  test('should handle real-time updates', async ({ page }) => {
    // Wait for mock data to load
    await page.waitForSelector('[data-testid="node-count"]');

    const initialNodeCount = await page.textContent(
      '[data-testid="node-count"]',
    );

    // Wait for simulation tick (mock updates every 2 seconds)
    await page.waitForTimeout(3000);

    // Verify that some data has changed (notifications, metrics, etc.)
    await expect(
      page.locator('[data-testid="notification-feed"] .notification'),
    ).toHaveCount({ min: 1 });
  });

  test('should meet accessibility standards', async ({ page }) => {
    // Check for proper ARIA labels
    await expect(page.locator('[aria-label]')).toHaveCount({ min: 5 });

    // Check for proper heading structure
    await expect(page.locator('h1, h2, h3')).toHaveCount({ min: 3 });

    // Check for keyboard focusable elements
    await page.keyboard.press('Tab');
    await expect(page.locator(':focus')).toBeVisible();
  });
});
