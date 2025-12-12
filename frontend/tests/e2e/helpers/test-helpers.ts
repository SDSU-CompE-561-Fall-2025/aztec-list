/**
 * E2E Test Helpers
 *
 * Utility functions for E2E tests including test data generation,
 * authentication helpers, and common assertions.
 */

import { Page, expect } from "@playwright/test";

/**
 * Generate a unique test email address
 */
export function generateTestEmail(): string {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 8);
  return `test.${timestamp}.${random}@sdsu.edu`;
}

/**
 * Generate a unique username
 */
export function generateUsername(): string {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 8);
  return `user_${timestamp}_${random}`;
}

/**
 * Generate a valid password
 */
export function generatePassword(): string {
  return "TestPass123!@#";
}

/**
 * Check if user is logged in by verifying header elements
 */
export async function isUserLoggedIn(page: Page): Promise<boolean> {
  // Check for user avatar/dropdown in header (logged in state)
  const userAvatar = page
    .locator("header")
    .getByRole("button", { name: /user|u/i })
    .first();
  return await userAvatar.isVisible().catch(() => false);
}

/**
 * Check if user is logged out by verifying login/signup buttons
 */
export async function isUserLoggedOut(page: Page): Promise<boolean> {
  // Check for Login and Sign Up buttons (logged out state)
  const loginButton = page.getByRole("link", { name: /login/i });
  const signupButton = page.getByRole("link", { name: /sign up/i });

  const loginVisible = await loginButton.isVisible().catch(() => false);
  const signupVisible = await signupButton.isVisible().catch(() => false);

  return loginVisible && signupVisible;
}

/**
 * Wait for navigation to complete
 */
export async function waitForNavigation(page: Page, expectedUrl?: string | RegExp) {
  await page.waitForLoadState("networkidle");
  if (expectedUrl) {
    await expect(page).toHaveURL(expectedUrl);
  }
}

/**
 * Clear all auth data (localStorage, sessionStorage, cookies)
 */
export async function clearAuthData(page: Page) {
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
  await page.context().clearCookies();
}

/**
 * Get auth token from localStorage
 */
export async function getAuthToken(page: Page): Promise<string | null> {
  return await page.evaluate(() => localStorage.getItem("auth_token"));
}

/**
 * Check if auth token exists in localStorage
 */
export async function hasAuthToken(page: Page): Promise<boolean> {
  const token = await getAuthToken(page);
  return token !== null && token.length > 0;
}

/**
 * Logs out the current user by clicking the avatar dropdown and logout button.
 */
export async function logout(page: Page): Promise<void> {
  // Wait for the page to be fully loaded
  await page.waitForLoadState("networkidle");

  // The Avatar renders as a SPAN element (not button), so we need to find it differently
  // It's the second .cursor-pointer element in the header (first is theme switcher button)
  const cursorPointers = page.locator("header .cursor-pointer");
  const avatarElement = cursorPointers.nth(1);

  await avatarElement.waitFor({ state: "visible", timeout: 10000 });
  await avatarElement.click();

  // Wait for dropdown to appear
  await page.waitForTimeout(500);

  // Click "Log out" in the dropdown
  const logoutButton = page.getByText("Log out", { exact: true });
  await logoutButton.waitFor({ state: "visible", timeout: 5000 });
  await logoutButton.click();

  // Wait for logout to complete
  await page.waitForTimeout(1500);
}
