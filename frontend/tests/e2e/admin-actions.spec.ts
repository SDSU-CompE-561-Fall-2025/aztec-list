/**
 * Admin Dashboard E2E Tests - Actions History
 *
 * Tests admin action viewing functionality including:
 * - Viewing list of admin actions
 * - Displaying action details (type, target, reason)
 * - Revoking admin actions
 * - Empty state when no actions exist
 * - Action type badges and formatting
 */

/* eslint-disable @typescript-eslint/no-unused-vars */

import { test, expect, Page } from "@playwright/test";
import {
  generateTestEmail,
  generateUsername,
  generatePassword,
  createAdminUser,
  createTestUser,
} from "./helpers/test-helpers";

test.describe("Admin Actions History", () => {
  // Helper to create regular (non-admin) user
  async function createRegularUser(page: Page) {
    const email = generateTestEmail();
    const username = generateUsername();
    const password = generatePassword();

    await page.goto("/signup");
    await page.getByLabel(/username/i).fill(username);
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel("Password", { exact: false }).first().fill(password);
    await page.getByLabel(/confirm password/i).fill(password);
    await page.getByRole("button", { name: /create account/i }).click();

    await Promise.race([
      page.waitForURL("http://localhost:3000/", { timeout: 5000 }),
      page.locator(".text-destructive").waitFor({ state: "visible", timeout: 5000 }),
    ]).catch(() => {});

    return { email, username, password };
  }

  test.describe("Non-Admin Access Control", () => {
    test("should redirect non-admin users away from admin dashboard", async ({ page }) => {
      // Create regular user and login
      await createRegularUser(page);

      // Try to access admin page
      await page.goto("/admin");
      await page.waitForLoadState("domcontentloaded");
      await page.waitForTimeout(1500);

      // Should be redirected away from /admin (likely to home page)
      expect(page.url()).not.toContain("/admin");
      expect(page.url()).toMatch(/\/(|listings)$/);
    });

    test("should not show admin dashboard to regular users", async ({ page }) => {
      await createRegularUser(page);

      await page.goto("/admin");
      await page.waitForTimeout(1500);

      // Should not see admin dashboard content
      const adminHeading = page.getByRole("heading", { name: /admin dashboard/i });
      await expect(adminHeading).not.toBeVisible();
    });
  });

  test.describe("Admin Dashboard Access", () => {
    test("should display admin dashboard for admin users", async ({ page }) => {
      // Create admin user
      await createAdminUser(page);

      // Navigate to /admin
      await page.goto("/admin");
      await page.waitForLoadState("domcontentloaded");
      await page.waitForTimeout(1000);

      // Verify dashboard loads
      expect(page.url()).toContain("/admin");

      // Check for "Admin Dashboard" heading
      const adminHeading = page.getByRole("heading", { name: /admin dashboard/i });
      await expect(adminHeading).toBeVisible();

      // Verify tabs are visible
      await expect(page.getByRole("button", { name: /actions history/i })).toBeVisible();
      await expect(page.getByRole("button", { name: /issue strike/i })).toBeVisible();
    });

    test("should show actions history tab by default", async ({ page }) => {
      // Create admin user
      await createAdminUser(page);

      // Navigate to admin dashboard
      await page.goto("/admin");
      await page.waitForLoadState("domcontentloaded");
      await page.waitForTimeout(1000);

      // Verify "Actions History" tab has active styling
      const actionsTab = page.getByRole("button", { name: /actions history/i });
      await expect(actionsTab).toHaveClass(/border-purple-500/);

      // Verify actions list or empty state is visible
      const emptyState = page.getByText(/no actions recorded/i);
      await expect(emptyState).toBeVisible();
    });

    test("should display all navigation tabs", async ({ page }) => {
      // Create admin user
      await createAdminUser(page);

      // Navigate to admin dashboard
      await page.goto("/admin");
      await page.waitForLoadState("domcontentloaded");
      await page.waitForTimeout(1000);

      // Verify all tabs are present
      await expect(page.getByRole("button", { name: /^actions history$/i })).toBeVisible();
      await expect(page.getByRole("button", { name: /^issue strike$/i })).toBeVisible();
      await expect(page.getByRole("button", { name: /^ban user$/i })).toBeVisible();
      await expect(page.getByRole("button", { name: /^remove listing$/i })).toBeVisible();
      await expect(page.getByRole("button", { name: /^support tickets$/i })).toBeVisible();
    });
  });

  test.describe("Actions List Display", () => {
    test("should show empty state when no actions exist", async ({ page }) => {
      // Create admin user (fresh user has no actions)
      await createAdminUser(page);

      // Navigate to admin dashboard
      await page.goto("/admin");
      await page.waitForLoadState("domcontentloaded");
      await page.waitForTimeout(1000);

      // Verify "No actions recorded yet" message is visible
      await expect(page.getByText(/no actions recorded/i)).toBeVisible();
    });

    test.skip("should display list of admin actions", async ({ page: _page }) => {
      // TODO: Requires admin user + test data
      // Prerequisites: Have some admin actions in the database
      // Verify actions are displayed in cards
      // Each action should show:
      // - Action type badge (Strike, Ban, Listing Removed)
      // - Timestamp
      // - Target user information
      // - Admin information
      // - Reason (if present)
      // - Revoke button
    });

    test.skip("should show correct action type badges", async ({ page: _page }) => {
      // TODO: Requires admin user + test data with different action types
      // Verify strike actions show yellow badge
      // Verify ban actions show red badge
      // Verify listing_removal actions show purple badge
      // Each badge should have correct styling and label
    });

    test.skip("should display action timestamps correctly", async ({ page: _page }) => {
      // TODO: Requires admin user + test data
      // Verify timestamps are formatted correctly (localeString)
      // Verify timestamps are visible for each action
    });

    test.skip("should show target user information", async ({ page: _page }) => {
      // TODO: Requires admin user + test data
      // Verify target username is displayed
      // Verify target user ID is displayed (in monospace font)
      // Verify "Target:" label is present
    });

    test.skip("should show admin user information", async ({ page: _page }) => {
      // TODO: Requires admin user + test data
      // Verify admin username is displayed
      // Verify admin user ID is displayed
      // Verify "Admin:" label is present
    });

    test.skip("should display action reason when present", async ({ page: _page }) => {
      // TODO: Requires admin user + test data
      // Verify reason text is displayed
      // Verify "Reason:" label is present
    });

    test.skip("should show target listing ID for listing removal actions", async ({
      page: _page,
    }) => {
      // TODO: Requires admin user + listing removal action data
      // Verify listing ID is displayed for listing_removal actions
      // Verify listing ID is not shown for other action types
    });

    test.skip("should show expiration date for temporary bans", async ({ page: _page }) => {
      // TODO: Requires admin user + temporary ban action data
      // Verify expires_at date is displayed
      // Verify "Expires:" label is present
      // Verify permanent bans don't show expiration
    });
  });

  test.describe("Action Revocation", () => {
    test.skip("should have revoke button for each action", async ({ page: _page }) => {
      // TODO: Requires admin user + test data
      // Verify each action card has a "Revoke" button
      // Button should be visible and enabled
    });

    test.skip("should revoke action when revoke button is clicked", async ({ page: _page }) => {
      // TODO: Requires admin user + test data
      // Click revoke button on an action
      // Verify confirmation (if implemented) or immediate revoke
      // Wait for success toast
      // Verify action is removed from list or marked as revoked
    });

    test.skip("should show success message after revoking action", async ({ page: _page }) => {
      // TODO: Requires admin user + test data
      // Revoke an action
      // Verify "Action revoked successfully!" toast appears
      // Toast should have warning style (orange/yellow)
    });

    test.skip("should refresh actions list after revoke", async ({ page: _page }) => {
      // TODO: Requires admin user + test data
      // Count actions before revoke
      // Revoke an action
      // Wait for list to refresh
      // Verify count decreased by 1
    });

    test.skip("should handle revoke errors gracefully", async ({ page: _page }) => {
      // TODO: Requires admin user + test scenario for revoke failure
      // Attempt to revoke action that doesn't exist or already revoked
      // Verify error toast appears
      // Verify error message is helpful
    });
  });

  test.describe("Loading States", () => {
    test.skip("should show loading spinner while fetching actions", async ({ page: _page }) => {
      // TODO: Requires admin user
      // Navigate to admin dashboard
      // Immediately check for loading spinner
      // Verify "Loading actions..." text is visible
      // Wait for spinner to disappear
    });

    test.skip("should show loading state when revoking action", async ({ page: _page }) => {
      // TODO: Requires admin user + test data
      // Click revoke button
      // Verify button is disabled during revoke
      // Verify button text or icon changes to indicate loading
    });
  });

  test.describe("Navigation Between Tabs", () => {
    test.skip("should switch to different tabs without losing state", async ({ page }) => {
      // TODO: Requires admin user
      // Start on Actions History tab
      // Switch to Issue Strike tab
      // Switch back to Actions History
      // Verify actions list is still displayed (not reloaded unnecessarily)
    });

    test.skip("should highlight active tab correctly", async ({ page }) => {
      // TODO: Requires admin user
      // Verify Actions History tab is highlighted by default
      // Click Issue Strike tab
      // Verify Issue Strike tab is highlighted
      // Verify Actions History tab is no longer highlighted
    });
  });

  test.describe("Responsive Design", () => {
    test.skip("should display actions correctly on mobile", async ({ page }) => {
      // TODO: Requires admin user + test data
      // Set viewport to mobile size
      await page.setViewportSize({ width: 375, height: 667 });
      // Navigate to admin dashboard
      // Verify actions are readable and properly formatted
      // Verify all information is accessible
    });

    test.skip("should show responsive tabs on mobile", async ({ page }) => {
      // TODO: Requires admin user
      // Set viewport to mobile size
      await page.setViewportSize({ width: 375, height: 667 });
      // Navigate to admin dashboard
      // Verify tabs are visible and clickable
      // Verify tab layout works on small screens
    });
  });
});
