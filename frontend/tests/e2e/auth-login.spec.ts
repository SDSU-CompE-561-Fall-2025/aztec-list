/**
 * Authentication E2E Tests - Login Flow
 *
 * Tests user login functionality including:
 * - Successful login with valid credentials
 * - Validation errors for invalid inputs
 * - Login persistence and token storage
 * - Navigation between auth pages
 */

import { test, expect } from "@playwright/test";
import {
  generateTestEmail,
  generateUsername,
  generatePassword,
  hasAuthToken,
  logout,
} from "./helpers/test-helpers";

test.describe("Login", () => {
  test.beforeEach(async ({ page, context }) => {
    // Start with clean state - clear storage and cookies
    await context.clearCookies();

    // Navigate to login page
    await page.goto("/login");

    // Wait for the page to be interactive
    await page.waitForLoadState("domcontentloaded");
  });

  test("should display login form with all required fields", async ({ page }) => {
    // Verify page title
    await expect(page).toHaveTitle(/AztecList/i);

    // Verify form heading (CardTitle is likely a div)
    await expect(page.getByText(/login to your account/i)).toBeVisible();

    // Verify all input fields are present
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/^password$/i, { exact: true })).toBeVisible();

    // Verify submit button
    await expect(page.getByRole("button", { name: /^login$/i })).toBeVisible();

    // Verify link to signup page
    await expect(page.getByRole("main").getByRole("link", { name: /sign up/i })).toBeVisible();
  });

  test("should successfully login with valid credentials", async ({ page }) => {
    // First, create a user by signing up
    const username = generateUsername();
    const email = generateTestEmail();
    const password = generatePassword();

    // Go to signup page
    await page.goto("/signup");
    await page.getByLabel(/username/i).fill(username);
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel("Password", { exact: false }).first().fill(password);
    await page.getByLabel(/confirm password/i).fill(password);
    await page.getByRole("button", { name: /create account/i }).click();

    // Wait for signup to complete and redirect
    await page.waitForURL("/", { timeout: 10000 });

    // Debug: Check if we're actually logged in after signup
    const isLoggedIn = await hasAuthToken(page);
    if (!isLoggedIn) {
      throw new Error("Signup did not log user in - no auth token found");
    }

    // Debug: Check what buttons are visible in header
    const loginButtonVisible = await page
      .getByRole("button", { name: /^login$/i })
      .isVisible()
      .catch(() => false);
    if (loginButtonVisible) {
      throw new Error("Login button still visible after signup - user not logged in");
    }

    // Now logout
    await logout(page);

    // Go to login page
    await page.goto("/login");
    await page.waitForLoadState("domcontentloaded");

    // Fill in login form with the created credentials
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel(/^password$/i, { exact: true }).fill(password);

    // Submit the form
    await page.getByRole("button", { name: /^login$/i }).click();

    // Wait for navigation to home page
    await page.waitForURL("/", { timeout: 10000 });

    // Verify we're not on login page anymore
    await expect(page).not.toHaveURL("/login");

    // Verify auth token is stored
    expect(await hasAuthToken(page)).toBe(true);
  });

  test("should show error for non-existent user", async ({ page }) => {
    const email = generateTestEmail();
    const password = generatePassword();

    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel(/^password$/i, { exact: true }).fill(password);

    await page.getByRole("button", { name: /^login$/i }).click();

    // Verify error message is displayed
    await expect(page.locator(".text-destructive")).toBeVisible();

    // Verify we're still on login page
    await expect(page).toHaveURL("/login");

    // Verify no auth token is stored
    expect(await hasAuthToken(page)).toBe(false);
  });

  test("should show error for incorrect password", async ({ page }) => {
    // First, create a user
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

    // Try to login with wrong password
    await page.goto("/login");
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel(/^password$/i, { exact: true }).fill("WrongPassword123!");
    await page.getByRole("button", { name: /^login$/i }).click();

    // Verify error message
    await expect(page.locator(".text-destructive")).toBeVisible();
    await expect(page).toHaveURL("/login");
    expect(await hasAuthToken(page)).toBe(false);
  });

  test("should toggle password visibility", async ({ page }) => {
    const password = generatePassword();

    // Fill password field
    const passwordInput = page.getByLabel(/^password$/i, { exact: true });
    await passwordInput.fill(password);

    // Verify password is hidden by default
    await expect(passwordInput).toHaveAttribute("type", "password");

    // Find the toggle button next to the password field (the eye icon)
    const passwordField = passwordInput.locator("..");
    const toggleButton = passwordField.locator('button[type="button"]');
    await toggleButton.click();

    // Verify password is now visible
    await expect(passwordInput).toHaveAttribute("type", "text");

    // Click again to hide
    await toggleButton.click();

    // Verify password is hidden again
    await expect(passwordInput).toHaveAttribute("type", "password");
  });

  test("should navigate to signup page when clicking signup link", async ({ page }) => {
    // Click the signup link in the login form
    await page
      .getByRole("main")
      .getByRole("link", { name: /sign up/i })
      .click();

    // Verify navigation to signup page
    await expect(page).toHaveURL("/signup");
    await expect(page.getByText(/create an account/i)).toBeVisible();
  });

  test("should show error for empty email", async ({ page }) => {
    // Try to submit with empty email
    await page.getByLabel(/^password$/i, { exact: true }).fill("SomePassword123!");
    await page.getByRole("button", { name: /^login$/i }).click();

    // HTML5 validation should prevent submission or show error
    // The form should still be on login page
    await expect(page).toHaveURL("/login");
  });

  test("should show error for empty password", async ({ page }) => {
    // Try to submit with empty password
    await page.getByLabel(/email/i).fill(generateTestEmail());
    await page.getByRole("button", { name: /^login$/i }).click();

    // HTML5 validation should prevent submission
    await expect(page).toHaveURL("/login");
  });
});
