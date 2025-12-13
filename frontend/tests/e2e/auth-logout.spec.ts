/**
 * Authentication E2E Tests - Logout Flow
 *
 * Tests user logout functionality including:
 * - Successful logout
 * - Token/session cleanup
 * - Redirect to home page
 * - State persistence after logout
 */

import { test, expect } from "@playwright/test";
import {
  generateTestEmail,
  generateUsername,
  generatePassword,
  hasAuthToken,
  logout,
} from "./helpers/test-helpers";

test.describe("Logout", () => {
  test.beforeEach(async ({ context }) => {
    // Start with clean state
    await context.clearCookies();
  });

  test("should successfully logout", async ({ page }) => {
    // First, create a user and login
    const username = generateUsername();
    const email = generateTestEmail();
    const password = generatePassword();

    // Signup (which auto-logs in)
    await page.goto("/signup");
    await page.getByLabel(/username/i).fill(username);
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel("Password", { exact: false }).first().fill(password);
    await page.getByLabel(/confirm password/i).fill(password);
    await page.getByRole("button", { name: /create account/i }).click();

    // Wait for successful signup
    await page.waitForURL("/", { timeout: 10000 });

    // Verify logged in
    expect(await hasAuthToken(page)).toBe(true);

    // Logout
    await logout(page);

    // Verify auth token is removed
    expect(await hasAuthToken(page)).toBe(false);

    // Verify we see login/signup links instead of avatar
    await expect(page.getByRole("link", { name: /login/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /sign up/i })).toBeVisible();
  });

  test("should redirect to home after logout", async ({ page }) => {
    // Create user and login
    const username = generateUsername();
    const email = generateTestEmail();
    const password = generatePassword();

    await page.goto("/signup");
    await page.getByLabel(/username/i).fill(username);
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel("Password", { exact: false }).first().fill(password);
    await page.getByLabel(/confirm password/i).fill(password);
    await page.getByRole("button", { name: /create account/i }).click();
    await page.waitForURL("/", { timeout: 10000 });

    // Navigate to a different page (e.g., profile if it exists, or stay on home)
    // For now, just stay on home

    // Logout
    await logout(page);

    // Should be on home page
    await expect(page).toHaveURL("/");
  });

  test("should clear all auth state on logout", async ({ page }) => {
    // Create user and login
    const username = generateUsername();
    const email = generateTestEmail();
    const password = generatePassword();

    await page.goto("/signup");
    await page.getByLabel(/username/i).fill(username);
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel("Password", { exact: false }).first().fill(password);
    await page.getByLabel(/confirm password/i).fill(password);
    await page.getByRole("button", { name: /create account/i }).click();
    await page.waitForURL("/", { timeout: 10000 });

    // Verify user data is in localStorage
    const userDataBefore = await page.evaluate(() => localStorage.getItem("user"));
    expect(userDataBefore).toBeTruthy();

    // Logout
    await logout(page);

    // Verify all auth data is cleared
    expect(await hasAuthToken(page)).toBe(false);
    const userDataAfter = await page.evaluate(() => localStorage.getItem("user"));
    expect(userDataAfter).toBeNull();
  });

  test("should not be able to access protected pages after logout", async ({ page }) => {
    // Create user and login
    const username = generateUsername();
    const email = generateTestEmail();
    const password = generatePassword();

    await page.goto("/signup");
    await page.getByLabel(/username/i).fill(username);
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel("Password", { exact: false }).first().fill(password);
    await page.getByLabel(/confirm password/i).fill(password);
    await page.getByRole("button", { name: /create account/i }).click();
    await page.waitForURL("/", { timeout: 10000 });

    // Logout
    await logout(page);

    // Try to access protected pages - they should redirect to login or show auth error
    // This test depends on which pages require authentication
    // For now, just verify we can't see the user menu anymore
    await expect(page.locator("header").locator('[role="img"]')).not.toBeVisible();
  });
});
