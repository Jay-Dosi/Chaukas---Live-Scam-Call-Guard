import { test, expect } from '@playwright/test';

test.describe('Live Guard screenshots', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('calm state - English desktop (1280px)', async ({ page }) => {
    await expect(page.locator('h2')).toContainText('CALM');
    await page.screenshot({ path: 'docs/screenshots/liveguard-calm-en-1280.png', fullPage: true });
  });

  test('calm state - English mobile (360px)', async ({ page }) => {
    await page.setViewportSize({ width: 360, height: 640 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('h2')).toContainText('CALM');
    await page.screenshot({ path: 'docs/screenshots/liveguard-calm-en-360.png', fullPage: true });
  });

  test('calm state - English tablet (768px)', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('h2')).toContainText('CALM');
    await page.screenshot({ path: 'docs/screenshots/liveguard-calm-en-768.png', fullPage: true });
  });
});

test.describe('Test Lab screenshots', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/test');
    await page.waitForLoadState('networkidle');
  });

  test('Scenario Player tab - English', async ({ page }) => {
    await expect(page.locator('h3')).toContainText('Scenarios');
    await page.screenshot({ path: 'docs/screenshots/testlab-scenarios-en-1280.png', fullPage: true });
  });

  test('Fire Drill tab - English', async ({ page }) => {
    await page.getByRole('tab', { name: 'Fire Drill' }).click();
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'docs/screenshots/testlab-firedrill-en-1280.png', fullPage: true });
  });

  test('Benchmark tab - English', async ({ page }) => {
    await page.getByRole('tab', { name: 'Benchmark' }).click();
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'docs/screenshots/testlab-benchmark-en-1280.png', fullPage: true });
  });
});

test.describe('Setup and About screenshots', () => {
  test('Setup page - English', async ({ page }) => {
    await page.goto('/setup');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('h1')).toContainText('Setup');
    await page.screenshot({ path: 'docs/screenshots/setup-en-1280.png', fullPage: true });
  });

  test('About page - English', async ({ page }) => {
    await page.goto('/about');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('h1')).toContainText('About and Method');
    await page.screenshot({ path: 'docs/screenshots/about-en-1280.png', fullPage: true });
  });
});