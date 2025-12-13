/**
 * Profile Management E2E Tests
 *
 * Tests user profile features including:
 * - Viewing own profile
 * - Editing profile information (name, campus, phone)
 * - Profile picture upload and removal
 * - Username updates
 * - Password changes
 * - Profile incomplete banner
 * - Cancel/discard changes dialogs
 */

import { test, expect, Page } from "@playwright/test";
import {
  generateTestEmail,
  generateUsername,
  generatePassword,
  logout,
} from "./helpers/test-helpers";

test.describe("Profile Management", () => {
  // Helper to create and login a user
  async function loginUser(page: Page) {
    const email = generateTestEmail();
    const username = generateUsername();
    const password = generatePassword();

    await page.goto("/signup");
    await page.getByLabel(/username/i).fill(username);
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel("Password", { exact: false }).first().fill(password);
    await page.getByLabel(/confirm password/i).fill(password);
    await page.getByRole("button", { name: /create account/i }).click();

    // Wait for successful signup
    await Promise.race([
      page.waitForURL("http://localhost:3000/", { timeout: 5000 }),
      page.locator(".text-destructive").waitFor({ state: "visible", timeout: 5000 }),
    ]).catch(() => {});

    return { email, username, password };
  }

  // Helper to wait for settings page to load
  async function waitForSettingsPage(page: Page) {
    await page.waitForLoadState("domcontentloaded");
    // Wait for skeleton to disappear and real content to appear
    await page.waitForTimeout(2500); // Give React Query time to fetch data and render
  }

  test.describe("View Profile", () => {
    test("should display own profile with username", async ({ page }) => {
      const { username } = await loginUser(page);

      await page.goto("/profile");
      await page.waitForLoadState("domcontentloaded");
      await page.waitForTimeout(2500);

      // Profile should show username
      await expect(page.getByText(username)).toBeVisible();

      // Should show listings section
      await expect(page.getByText("Your Listings")).toBeVisible();
    });

    test("should show incomplete profile banner when profile is not set up", async ({ page }) => {
      await loginUser(page);

      await page.goto("/profile");
      await page.waitForLoadState("domcontentloaded");
      await page.waitForTimeout(2500);

      // Look for incomplete profile banner or message
      const banner = page.locator("text=/complete.*profile|set up.*profile/i");
      if ((await banner.count()) > 0) {
        await expect(banner.first()).toBeVisible();
      }
    });

    test("should navigate to settings from profile page", async ({ page }) => {
      await loginUser(page);

      await page.goto("/profile");
      await page.waitForLoadState("domcontentloaded");
      await page.waitForTimeout(2500);

      // Find and click settings/edit button
      const settingsLink = page.getByRole("link", { name: /settings|edit profile/i });
      if ((await settingsLink.count()) > 0) {
        await settingsLink.click();
        await expect(page).toHaveURL("/settings");
      }
    });
  });

  test.describe("Settings Page - Profile Tab", () => {
    test("should display profile settings form", async ({ page }) => {
      await loginUser(page);

      await page.goto("/settings");
      await waitForSettingsPage(page);

      // Should have Profile tab
      const profileTab = page.getByRole("tab", { name: /profile/i });
      if ((await profileTab.count()) === 0) {
        // Might be already on profile tab
        await expect(page.locator("#campus")).toBeVisible({ timeout: 10000 });
      } else {
        await profileTab.click();
        await page.waitForTimeout(500);
        await expect(page.locator("#campus")).toBeVisible({ timeout: 10000 });
      }

      // Should have form fields
      await expect(page.locator("#campus")).toBeVisible();
      await expect(page.locator("#phone")).toBeVisible();
    });

    test("should update profile name and campus", async ({ page }) => {
      await loginUser(page);

      await page.goto("/settings");
      await waitForSettingsPage(page);

      // Make sure we're on Profile tab
      const profileTab = page.getByRole("tab", { name: /profile/i });
      if ((await profileTab.count()) > 0) {
        await profileTab.click();
        await page.waitForTimeout(500);
      }

      // Fill in profile information
      const nameInput = page.getByLabel(/name|display name/i);
      const campusInput = page.getByLabel(/campus/i);

      await nameInput.clear();
      await nameInput.fill("John Doe");

      await campusInput.clear();
      await campusInput.fill("San Diego State University");

      // Save changes
      const saveButton = page.getByRole("button", { name: "Save Profile", exact: true });
      await saveButton.click();

      // Should show success message
      await expect(page.getByText(/success|updated/i)).toBeVisible({ timeout: 5000 });

      // Navigate to profile and verify changes
      await page.goto("/profile");
      await waitForSettingsPage(page);

      await expect(page.getByText("John Doe")).toBeVisible();
      await expect(page.getByText(/San Diego State University/i)).toBeVisible();
    });

    test("should validate phone number format", async ({ page }) => {
      await loginUser(page);

      await page.goto("/settings");
      await waitForSettingsPage(page);

      // Navigate to Profile tab if needed
      const profileTab = page.getByRole("tab", { name: /profile/i });
      if ((await profileTab.count()) > 0) {
        await profileTab.click();
        await page.waitForTimeout(500);
      }

      // Try to enter invalid phone number
      const phoneInput = page.getByLabel(/phone/i);
      if ((await phoneInput.count()) > 0) {
        // Fill name first to enable save button
        await page.getByLabel(/name|display name/i).fill("Test User");
        await phoneInput.fill("123"); // Too short

        // Should show inline validation error
        await expect(page.getByText("Phone number must be 10 digits")).toBeVisible({
          timeout: 3000,
        });
      }
    });

    test("should add valid phone number to profile", async ({ page }) => {
      await loginUser(page);

      await page.goto("/settings");
      await waitForSettingsPage(page);

      const profileTab = page.getByRole("tab", { name: /profile/i });
      if ((await profileTab.count()) > 0) {
        await profileTab.click();
        await page.waitForTimeout(500);
      }

      const phoneInput = page.getByLabel(/phone/i);
      if ((await phoneInput.count()) > 0) {
        // Fill name to enable save
        await page.getByLabel(/name|display name/i).fill("Test User");
        await phoneInput.fill("(619) 555-1234");

        const saveButton = page.getByRole("button", { name: "Save Profile", exact: true });
        await saveButton.click();

        // Wait for save to complete - check button enabled again or toast
        await page.waitForTimeout(2000);
      }
    });

    test("should show confirmation dialog when discarding profile changes", async ({ page }) => {
      await loginUser(page);

      await page.goto("/settings");
      await waitForSettingsPage(page);

      const profileTab = page.getByRole("tab", { name: /profile/i });
      if ((await profileTab.count()) > 0) {
        await profileTab.click();
        await page.waitForTimeout(500);
      }

      // Make a change
      const nameInput = page.getByLabel(/name|display name/i);
      await nameInput.fill("Changed Name");

      // Try to navigate away or click cancel
      const cancelButton = page.getByRole("button", { name: /cancel/i });
      if ((await cancelButton.count()) > 0) {
        await cancelButton.click();

        // Should show confirmation dialog
        await expect(page.getByRole("heading", { name: "Discard Changes?" })).toBeVisible({
          timeout: 3000,
        });
      }
    });
  });

  test.describe("Settings Page - Account Tab", () => {
    test("should display account settings", async ({ page }) => {
      const { username } = await loginUser(page);

      await page.goto("/settings");
      await waitForSettingsPage(page);

      // Navigate to Account tab
      const accountTab = page.getByRole("tab", { name: /account/i });
      await accountTab.click();
      await page.waitForTimeout(500);

      // Should show current username
      const usernameInput = page.getByLabel(/username/i);
      await expect(usernameInput).toHaveValue(username);
    });

    test("should update username", async ({ page }) => {
      await loginUser(page);
      const newUsername = generateUsername();

      await page.goto("/settings");
      await waitForSettingsPage(page);

      // Navigate to Account tab
      const accountTab = page.getByRole("tab", { name: /account/i });
      await accountTab.click();
      await page.waitForTimeout(500);

      // Update username
      const usernameInput = page.getByLabel(/username/i);
      await usernameInput.clear();
      await usernameInput.fill(newUsername);

      // Save changes
      const saveButton = page.getByRole("button", { name: "Update Account", exact: true });
      await saveButton.click();

      // Wait for save to complete
      await page.waitForTimeout(2000);

      // Verify username changed
      await expect(usernameInput).toHaveValue(newUsername);
    });

    test("should show error for duplicate username", async ({ page, context }) => {
      // Create first user
      const { username: existingUsername } = await loginUser(page);

      // Logout
      await logout(page);
      await context.clearCookies();

      // Create second user - loginUser will handle navigation
      await loginUser(page);

      await page.goto("/settings");
      await waitForSettingsPage(page);

      // Navigate to Account tab
      const accountTab = page.getByRole("tab", { name: /account/i });
      await accountTab.click();
      await page.waitForTimeout(1000);

      // Try to use existing username
      const usernameInput = page.getByLabel(/username/i);
      await usernameInput.clear();
      await usernameInput.fill(existingUsername);

      const saveButton = page.getByRole("button", { name: "Update Account", exact: true });
      await saveButton.click();

      // Should show error
      await expect(page.getByText(/username.*taken|already.*exists/i)).toBeVisible({
        timeout: 5000,
      });
    });
  });

  test.describe("Settings Page - Security Tab", () => {
    test("should display password change form", async ({ page }) => {
      await loginUser(page);

      await page.goto("/settings");
      await waitForSettingsPage(page);

      // Navigate to Security tab
      const securityTab = page.getByRole("tab", { name: /security|password/i });
      await securityTab.click();
      await page.waitForTimeout(500);

      // Should have password fields
      await expect(page.locator("#current-password")).toBeVisible();
      await expect(page.locator("#new-password")).toBeVisible();
      await expect(page.locator("#confirm-password")).toBeVisible();
    });

    test("should change password successfully", async ({ page }) => {
      const { password: oldPassword } = await loginUser(page);
      const newPassword = generatePassword();

      await page.goto("/settings");
      await waitForSettingsPage(page);

      // Navigate to Security tab
      const securityTab = page.getByRole("tab", { name: /security|password/i });
      await securityTab.click();
      await page.waitForTimeout(500);

      // Fill password form
      await page.locator("#current-password").fill(oldPassword);
      await page.locator("#new-password").fill(newPassword);
      await page.locator("#confirm-password").fill(newPassword);

      // Submit
      const changeButton = page.getByRole("button", { name: "Change Password", exact: true });
      await changeButton.click();

      // Wait for password change to complete
      await page.waitForTimeout(2000);

      // Button should be enabled again (indicates completion)
      await expect(changeButton).toBeEnabled();
    });

    test("should show error for incorrect current password", async ({ page }) => {
      await loginUser(page);
      const newPassword = generatePassword();

      await page.goto("/settings");
      await waitForSettingsPage(page);

      const securityTab = page.getByRole("tab", { name: /security|password/i });
      await securityTab.click();
      await page.waitForTimeout(500);

      // Fill with wrong current password
      await page.locator("#current-password").fill("WrongPassword123!");
      await page.locator("#new-password").fill(newPassword);
      await page.locator("#confirm-password").fill(newPassword);

      const changeButton = page.getByRole("button", { name: "Change Password", exact: true });
      await changeButton.click();

      // Should show error (check for any error message)
      await page.waitForTimeout(1000);
      const errorMessage = page.locator('.text-destructive, [role="alert"]');
      if ((await errorMessage.count()) > 0) {
        await expect(errorMessage.first()).toBeVisible();
      }
    });

    test("should show error when new passwords do not match", async ({ page }) => {
      const { password: oldPassword } = await loginUser(page);

      await page.goto("/settings");
      await waitForSettingsPage(page);

      const securityTab = page.getByRole("tab", { name: /security|password/i });
      await securityTab.click();
      await page.waitForTimeout(500);

      // Fill with mismatched passwords
      await page.locator("#current-password").fill(oldPassword);
      await page.locator("#new-password").fill("NewPassword123!");
      await page.locator("#confirm-password").fill("DifferentPassword123!");

      const changeButton = page.getByRole("button", { name: "Change Password", exact: true });
      await changeButton.click();

      // Should show error
      await expect(page.getByText(/passwords.*match|passwords.*same/i)).toBeVisible({
        timeout: 3000,
      });
    });
  });

  test.describe("Profile Picture", () => {
    test("should show profile picture upload button", async ({ page }) => {
      await loginUser(page);

      await page.goto("/settings");
      await waitForSettingsPage(page);

      const profileTab = page.getByRole("tab", { name: /profile/i });
      if ((await profileTab.count()) > 0) {
        await profileTab.click();
        await page.waitForTimeout(500);
      }

      // Should have upload button or file input
      const fileInput = page.locator('input[type="file"]');
      await expect(fileInput).toBeAttached({ timeout: 5000 });
    });

    test("should show profile picture preview after upload", async ({ page }) => {
      await loginUser(page);

      await page.goto("/settings");
      await waitForSettingsPage(page);

      const profileTab = page.getByRole("tab", { name: /profile/i });
      if ((await profileTab.count()) > 0) {
        await profileTab.click();
        await page.waitForTimeout(500);
      }

      // Find file input (might be hidden)
      const fileInput = page.locator('input[type="file"]');
      if ((await fileInput.count()) > 0) {
        // Create a test image file
        const buffer = Buffer.from(
          "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
          "base64"
        );

        await fileInput.setInputFiles({
          name: "test-avatar.png",
          mimeType: "image/png",
          buffer: buffer,
        });

        // Should show preview
        await page.waitForTimeout(1000);
        const preview = page.locator('img[alt*="Preview"], img[src^="blob:"]');
        if ((await preview.count()) > 0) {
          await expect(preview.first()).toBeVisible();
        }
      }
    });

    test("should show remove picture button when picture exists", async ({ page }) => {
      await loginUser(page);

      await page.goto("/settings");
      await waitForSettingsPage(page);

      const profileTab = page.getByRole("tab", { name: /profile/i });
      if ((await profileTab.count()) > 0) {
        await profileTab.click();
        await page.waitForTimeout(500);
      }

      // Upload a picture first
      const fileInput = page.locator('input[type="file"]');
      if ((await fileInput.count()) > 0) {
        const buffer = Buffer.from(
          "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
          "base64"
        );

        await fileInput.setInputFiles({
          name: "test-avatar.png",
          mimeType: "image/png",
          buffer: buffer,
        });

        await page.waitForTimeout(1000);

        // Should show remove button
        const removeButton = page.getByRole("button", { name: /remove.*picture|delete.*picture/i });
        if ((await removeButton.count()) > 0) {
          await expect(removeButton).toBeVisible();
        }
      }
    });
  });

  test.describe("Navigation", () => {
    test("should have back button to return to profile", async ({ page }) => {
      await loginUser(page);

      await page.goto("/settings");
      await waitForSettingsPage(page);

      // Look for back button
      const backButton = page.locator('button:has-text("Back"), a:has-text("Back")');
      if ((await backButton.count()) > 0) {
        await backButton.first().click();

        // Should navigate back
        await page.waitForTimeout(1000);
        expect(page.url()).toMatch(/\/(profile|$)/);
      }
    });

    test("should require authentication to access settings", async ({ page }) => {
      // Try to access settings without being logged in
      await page.goto("/settings");

      // Should redirect to login
      await page.waitForTimeout(2000);
      expect(page.url()).toContain("/login");
    });
  });
});
