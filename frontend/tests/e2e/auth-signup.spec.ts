/**
 * Authentication E2E Tests - Signup Flow
 *
 * Tests user registration functionality including:
 * - Successful signup with valid credentials
 * - Validation errors for invalid inputs
 * - Duplicate email/username handling
 * - Password visibility toggle
 * - Navigation between auth pages
 */

import { test, expect } from "@playwright/test";
import {
  generateTestEmail,
  generateUsername,
  generatePassword,
  hasAuthToken,
  waitForNavigation,
  logout,
} from "./helpers/test-helpers";

test.describe("Signup", () => {
  test.beforeEach(async ({ page, context }) => {
    // Start with clean state - clear storage and cookies
    await context.clearCookies();

    // Navigate to signup page
    await page.goto("/signup");

    // Wait for the page to be interactive
    await page.waitForLoadState("domcontentloaded");
  });

  test("should display signup form with all required fields", async ({ page }) => {
    // Verify page title
    await expect(page).toHaveTitle(/AztecList/i);

    // Verify form heading (CardTitle is a div, not heading element)
    await expect(page.getByText("Create an account")).toBeVisible();

    // Verify all input fields are present
    await expect(page.getByLabel(/username/i)).toBeVisible();
    await expect(page.getByLabel(/^email$/i)).toBeVisible();
    // Use exact: true to distinguish "Password" from "Confirm Password"
    await expect(page.getByLabel("Password", { exact: true })).toBeVisible();
    await expect(page.getByLabel(/confirm password/i)).toBeVisible();

    // Verify submit button (actual text is "Create account")
    await expect(page.getByRole("button", { name: /create account/i })).toBeVisible();

    // Verify link to login page (scope to main to avoid header link)
    await expect(page.getByRole("main").getByRole("link", { name: /login/i })).toBeVisible();
  });

  test("should successfully sign up with valid credentials", async ({ page }) => {
    const username = generateUsername();
    const email = generateTestEmail();
    const password = generatePassword();

    // Fill in the signup form
    await page.getByLabel(/username/i).fill(username);
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel("Password", { exact: false }).first().fill(password);
    await page.getByLabel(/confirm password/i).fill(password);

    // Submit the form and wait for navigation
    await page.getByRole("button", { name: /create account/i }).click();

    // Wait for either navigation to home or an error message
    await Promise.race([
      page.waitForURL("http://localhost:3000/", { timeout: 5000 }),
      page.locator(".text-destructive").waitFor({ state: "visible", timeout: 5000 }),
    ]).catch(() => {
      // Timeout is ok, we'll check the state below
    });

    // Check if there's an error message - if so, fail with the error
    const errorElement = page.locator(".text-destructive");
    if (await errorElement.isVisible()) {
      const errorText = await errorElement.textContent();
      throw new Error(`Signup failed with error: ${errorText}`);
    }

    // Should have navigated to home
    expect(page.url()).toBe("http://localhost:3000/");
    expect(await hasAuthToken(page)).toBe(true);
  });

  test("should show error for non-.edu email", async ({ page }) => {
    const username = generateUsername();
    const email = `test@gmail.com`; // Invalid - not .edu
    const password = generatePassword();

    await page.getByLabel(/username/i).fill(username);
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel("Password", { exact: false }).first().fill(password);
    await page.getByLabel(/confirm password/i).fill(password);

    await page.getByRole("button", { name: /create account/i }).click();

    // Verify error message is displayed (look for the error div, not the hint text)
    await expect(page.locator(".text-destructive").getByText(/valid \.edu email/i)).toBeVisible();

    // Verify we're still on signup page
    await expect(page).toHaveURL("/signup");
  });

  test("should show error for password mismatch", async ({ page }) => {
    const username = generateUsername();
    const email = generateTestEmail();
    const password = generatePassword();

    await page.getByLabel(/username/i).fill(username);
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel("Password", { exact: false }).first().fill(password);
    await page.getByLabel(/confirm password/i).fill("DifferentPassword123!");

    await page.getByRole("button", { name: /create account/i }).click();

    // Verify error message
    await expect(page.getByText(/passwords do not match/i)).toBeVisible();

    // Verify still on signup page
    await expect(page).toHaveURL("/signup");
  });

  test("should show error for weak password (less than 8 characters)", async ({ page }) => {
    const username = generateUsername();
    const email = generateTestEmail();
    const weakPassword = "Pass1!"; // Only 6 characters

    await page.getByLabel(/username/i).fill(username);
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel("Password", { exact: false }).first().fill(weakPassword);
    await page.getByLabel(/confirm password/i).fill(weakPassword);

    await page.getByRole("button", { name: /create account/i }).click();

    // Verify error message about password length
    await expect(page.getByText(/at least 8 characters/i)).toBeVisible();

    // Verify still on signup page
    await expect(page).toHaveURL("/signup");
  });

  test("should show error for username too short (less than 3 characters)", async ({ page }) => {
    const shortUsername = "ab"; // Only 2 characters
    const email = generateTestEmail();
    const password = generatePassword();

    await page.getByLabel(/username/i).fill(shortUsername);
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel("Password", { exact: false }).first().fill(password);
    await page.getByLabel(/confirm password/i).fill(password);

    await page.getByRole("button", { name: /create account/i }).click();

    // Verify error message about username length
    await expect(page.getByText(/at least 3 characters/i)).toBeVisible();

    // Verify still on signup page
    await expect(page).toHaveURL("/signup");
  });

  test("should show error for duplicate email", async ({ page }) => {
    const username1 = generateUsername();
    const username2 = generateUsername();
    const email = generateTestEmail();
    const password = generatePassword();

    // First signup - should succeed
    await page.getByLabel(/username/i).fill(username1);
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel("Password", { exact: false }).first().fill(password);
    await page.getByLabel(/confirm password/i).fill(password);
    await page.getByRole("button", { name: /create account/i }).click();

    // Wait for successful signup and navigation
    await waitForNavigation(page, "/");

    // Logout
    await logout(page);

    // Go back to signup page
    await page.goto("/signup");

    // Try to signup again with same email but different username
    await page.getByLabel(/username/i).fill(username2);
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel("Password", { exact: false }).first().fill(password);
    await page.getByLabel(/confirm password/i).fill(password);
    await page.getByRole("button", { name: /create account/i }).click();

    // Verify error message about duplicate email
    await expect(page.getByText(/email.*already/i)).toBeVisible();
  });

  test("should show error for duplicate username", async ({ page }) => {
    const username = generateUsername();
    const email1 = generateTestEmail();
    const email2 = generateTestEmail();
    const password = generatePassword();

    // First signup - should succeed
    await page.getByLabel(/username/i).fill(username);
    await page.getByLabel(/email/i).fill(email1);
    await page.getByLabel("Password", { exact: false }).first().fill(password);
    await page.getByLabel(/confirm password/i).fill(password);
    await page.getByRole("button", { name: /create account/i }).click();

    // Wait for successful signup
    await waitForNavigation(page, "/");

    // Logout
    await logout(page);

    // Go back to signup
    await page.goto("/signup");

    // Try to signup with same username but different email
    await page.getByLabel(/username/i).fill(username);
    await page.getByLabel(/email/i).fill(email2);
    await page.getByLabel("Password", { exact: false }).first().fill(password);
    await page.getByLabel(/confirm password/i).fill(password);
    await page.getByRole("button", { name: /create account/i }).click();

    // Verify error message about duplicate username
    await expect(page.getByText(/username.*already/i)).toBeVisible();
  });

  test("should toggle password visibility", async ({ page }) => {
    const password = generatePassword();

    // Fill password field
    const passwordInput = page.getByLabel("Password", { exact: false }).first();
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

  test("should navigate to login page when clicking login link", async ({ page }) => {
    // Click the login link in the signup form (not the header)
    await page.getByRole("main").getByRole("link", { name: /login/i }).click();

    // Verify navigation to login page
    await expect(page).toHaveURL("/login");
    // Login page also likely uses CardTitle (div), not heading
    await expect(page.getByText(/login to your account/i)).toBeVisible();
  });

  test("should redirect to home if already logged in", async ({ page }) => {
    // First, sign up to get logged in
    const username = generateUsername();
    const email = generateTestEmail();
    const password = generatePassword();

    await page.getByLabel(/username/i).fill(username);
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel("Password", { exact: false }).first().fill(password);
    await page.getByLabel(/confirm password/i).fill(password);
    await page.getByRole("button", { name: /create account/i }).click();

    // Wait for navigation to home
    await waitForNavigation(page, "/");

    // Now try to visit signup page while logged in
    await page.goto("/signup");

    // Should redirect back to home
    await expect(page).toHaveURL("/");
  });
});
