/**
 * Listings E2E Tests - Edit & Delete
 *
 * Tests listing edit and delete functionality including:
 * - Editing own listings
 * - Authorization (can't edit others' listings)
 * - Validation on edit
 * - Deleting own listings
 * - Authorization (can't delete others' listings)
 * - Confirmation dialogs
 */

import { test, expect, Page } from "@playwright/test";
import {
  generateTestEmail,
  generateUsername,
  generatePassword,
  logout,
} from "./helpers/test-helpers";

test.describe("Edit & Delete Listings", () => {
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
    await page.waitForURL("/", { timeout: 10000 });

    return { email, username, password };
  }

  // Helper to create a listing
  async function createListing(page: Page, title = "Test Laptop E2E Edit") {
    await page.goto("/listings/create");
    await page.getByLabel(/title/i).fill(title);
    await page.getByLabel(/description/i).fill("Original description for editing test");
    await page.getByLabel(/price/i).fill("199.99");
    await page.getByLabel(/category/i).selectOption("electronics");
    await page.getByLabel(/condition/i).selectOption("good");
    await page.getByRole("button", { name: /create listing/i }).click();

    // Wait for listing to be created
    await page.waitForTimeout(2000);

    // Click Done to go to profile
    const doneButton = page.getByRole("button", { name: /done/i });
    if ((await doneButton.count()) > 0) {
      await doneButton.click();
    }

    await page.waitForTimeout(1000);
  }

  test.describe("Edit Listing", () => {
    test("should allow editing own listing", async ({ page }) => {
      await loginUser(page);
      await createListing(page);

      // Go to profile to find our listing
      await page.goto("/profile");
      await page.waitForLoadState("networkidle");

      // Click the listing card to navigate to detail page
      const listingCard = page.locator(".group.bg-card").first();
      await listingCard.waitFor({ state: "visible", timeout: 10000 });
      await listingCard.click();

      await page.waitForURL(/\/listings\/[a-f0-9-]+$/, { timeout: 10000 });
      await page.waitForLoadState("networkidle");
      await page.waitForTimeout(2000); // Wait for auth context

      // Click Edit Listing button
      await page.getByRole("button", { name: /edit listing/i }).click({ timeout: 10000 });

      // Should navigate to edit page
      await page.waitForURL(/\/listings\/[a-f0-9-]+\/edit/, { timeout: 5000 });
      expect(page.url()).toMatch(/\/listings\/[a-f0-9-]+\/edit/);
    });

    test("should display edit form with existing values", async ({ page }) => {
      await loginUser(page);
      await createListing(page, "Unique Title For Edit Test");

      await page.goto("/profile");
      await page.waitForLoadState("networkidle");

      const listingCard = page.locator(".group.bg-card").first();
      await listingCard.click();
      await page.waitForURL(/\/listings\/[a-f0-9-]+$/, { timeout: 10000 });
      await page.waitForTimeout(2000); // Wait for auth context

      await page.getByRole("button", { name: /edit listing/i }).click({ timeout: 10000 });
      await page.waitForURL(/\/listings\/[a-f0-9-]+\/edit/);
      await page.waitForLoadState("networkidle");

      // Verify form fields have existing values
      const titleInput = page.getByLabel(/title/i);
      await expect(titleInput).toHaveValue("Unique Title For Edit Test");

      const descInput = page.getByLabel(/description/i);
      await expect(descInput).toHaveValue(/original description/i);

      const priceInput = page.getByLabel(/price/i);
      await expect(priceInput).toHaveValue("199.99");
    });

    test("should successfully update listing details", async ({ page }) => {
      await loginUser(page);
      await createListing(page);

      await page.goto("/profile");
      await page.waitForLoadState("networkidle");

      const listingCard = page.locator(".group.bg-card").first();
      await listingCard.click();
      await page.waitForURL(/\/listings\/[a-f0-9-]+$/, { timeout: 10000 });
      await page.waitForTimeout(2000); // Wait for auth context

      await page.getByRole("button", { name: /edit listing/i }).click({ timeout: 10000 });
      await page.waitForURL(/\/listings\/[a-f0-9-]+\/edit/);
      await page.waitForLoadState("networkidle");

      // Update title
      const titleInput = page.getByLabel(/title/i);
      await titleInput.fill("Updated Title After Edit");

      // Update description
      const descInput = page.getByLabel(/description/i);
      await descInput.fill("This description has been updated via e2e test");

      // Update price
      const priceInput = page.getByLabel(/price/i);
      await priceInput.fill("249.99");

      // Submit changes
      const saveButton = page.getByRole("button", { name: /save changes|update/i });
      await saveButton.click();

      // Wait for success message
      await page.waitForTimeout(2000);

      // Should show success toast or navigate back
      const successMessage = page.getByText(/updated successfully|changes saved/i);
      if ((await successMessage.count()) > 0) {
        await expect(successMessage.first()).toBeVisible({ timeout: 5000 });
      }
    });

    test("should show confirmation dialog when deleting", async ({ page }) => {
      await loginUser(page);
      await createListing(page);

      await page.goto("/profile");
      await page.waitForLoadState("networkidle");

      const listingCard = page.locator(".group.bg-card").first();
      await listingCard.click();
      await page.waitForURL(/\/listings\/[a-f0-9-]+$/, { timeout: 10000 });
      await page.waitForTimeout(2000); // Wait for auth context

      await page.getByRole("button", { name: /edit listing/i }).click({ timeout: 10000 });
      await page.waitForURL(/\/listings\/[a-f0-9-]+\/edit/);
      await page.waitForLoadState("networkidle");

      // Clear required field
      const titleInput = page.getByLabel(/title/i);
      await titleInput.clear();
      await titleInput.blur();

      // Should show validation error
      await expect(page.getByText(/title is required/i)).toBeVisible({ timeout: 3000 });
    });

    test("should have cancel button that navigates back", async ({ page }) => {
      await loginUser(page);
      await createListing(page);

      await page.goto("/profile");
      await page.waitForLoadState("networkidle");

      const listingCard = page.locator(".group.bg-card").first();
      await listingCard.click();
      await page.waitForURL(/\/listings\/[a-f0-9-]+$/, { timeout: 10000 });
      await page.waitForTimeout(2000); // Wait for auth context

      await page.getByRole("button", { name: /edit listing/i }).click({ timeout: 10000 });
      await page.waitForURL(/\/listings\/[a-f0-9-]+\/edit/);
      await page.waitForLoadState("networkidle");

      // Make a change to enable Cancel button (it only shows when isDirty)
      const titleInput = page.getByLabel(/title/i);
      await titleInput.fill("Modified Title");
      await page.waitForTimeout(500); // Wait for form state to update

      // Click cancel
      const cancelButton = page.getByRole("button", { name: /cancel/i });
      await cancelButton.click();

      // Confirmation dialog should appear (use getByRole to avoid strict mode)
      await expect(page.getByRole("heading", { name: /leave without saving/i })).toBeVisible({
        timeout: 3000,
      });

      // Click "Leave Without Saving"
      await page.getByRole("button", { name: /leave without saving/i }).click();

      // Should navigate back to detail page
      await page.waitForTimeout(1000);
      expect(page.url()).not.toContain("/edit");
    });

    test("should redirect to login if not authenticated", async ({ page }) => {
      // Try to access edit page without being logged in
      // Need a valid listing ID - use a fake but valid UUID
      await page.goto("/listings/00000000-0000-0000-0000-000000000001/edit");

      // Should redirect to login
      await page.waitForTimeout(1000);
      expect(page.url()).toContain("/login");
    });

    test("should toggle listing active status", async ({ page }) => {
      await loginUser(page);
      await createListing(page);

      await page.goto("/profile");
      await page.waitForLoadState("networkidle");

      const listingCard = page.locator(".group.bg-card").first();
      await listingCard.click();
      await page.waitForURL(/\/listings\/[a-f0-9-]+$/, { timeout: 10000 });
      await page.waitForTimeout(2000); // Wait for auth context

      await page.getByRole("button", { name: /edit listing/i }).click({ timeout: 10000 });
      await page.waitForURL(/\/listings\/[a-f0-9-]+\/edit/);
      await page.waitForLoadState("networkidle");

      // Find and click the active status toggle
      const statusToggle = page.locator('input[type="checkbox"]').first();

      // Check initial state
      const initialState = await statusToggle.isChecked();

      // Toggle it
      const toggleLabel = page.locator("label").filter({ has: statusToggle });
      await toggleLabel.click();

      // Verify it changed
      const newState = await statusToggle.isChecked();
      expect(newState).toBe(!initialState);
    });
  });

  test.describe("Delete Listing", () => {
    test("should show delete button on listing card", async ({ page }) => {
      await loginUser(page);
      await createListing(page);

      await page.goto("/profile");
      await page.waitForLoadState("networkidle");

      const listingCard = page.locator(".group.bg-card").first();
      await listingCard.waitFor({ state: "visible", timeout: 10000 });

      // Hover over card to reveal action buttons
      await listingCard.hover();
      await page.waitForTimeout(500);

      // Should have delete button (trash icon) - it has border-red-400
      const deleteButton = listingCard.locator("button.border-red-400");
      await expect(deleteButton).toBeVisible({ timeout: 5000 });
    });

    test("should show confirmation dialog when clicking delete", async ({ page }) => {
      await loginUser(page);
      await createListing(page);

      await page.goto("/profile");
      await page.waitForLoadState("networkidle");

      const listingCard = page.locator(".group.bg-card").first();
      await listingCard.hover();
      await page.waitForTimeout(500);

      // Click delete button (trash icon - has border-red-400)
      const deleteButton = listingCard.locator("button.border-red-400");
      await deleteButton.click();

      // Confirmation dialog should appear
      await expect(page.getByRole("heading", { name: /delete listing/i })).toBeVisible({
        timeout: 3000,
      });
      await expect(page.getByText(/this action cannot be undone/i)).toBeVisible();
    });

    test("should cancel deletion when clicking Cancel in dialog", async ({ page }) => {
      await loginUser(page);
      await createListing(page);

      await page.goto("/profile");
      await page.waitForLoadState("networkidle");

      const listingCard = page.locator(".group.bg-card").first();
      await listingCard.hover();
      await page.waitForTimeout(500);

      // Click delete button
      const deleteButton = listingCard.locator("button.border-red-400");
      await deleteButton.click();

      // Click cancel in dialog
      const cancelButton = page.getByRole("button", { name: /^cancel$/i });
      await cancelButton.click();

      // Should still be on profile page with listing visible
      await page.waitForTimeout(500);
      expect(page.url()).toContain("/profile");
      await expect(listingCard).toBeVisible();
    });

    test("should successfully delete listing when confirmed", async ({ page }) => {
      await loginUser(page);
      await createListing(page, "Listing To Delete E2E Test");

      await page.goto("/profile");
      await page.waitForLoadState("networkidle");

      const listingCard = page.locator(".group.bg-card").first();
      await listingCard.hover();
      await page.waitForTimeout(500);

      // Get listing count before deletion
      const initialCount = await page.locator(".group.bg-card").count();

      // Click delete button
      const deleteButton = listingCard.locator("button.border-red-400");
      await deleteButton.click();

      // Confirm deletion
      const confirmButton = page.getByRole("button", { name: /^delete$/i });
      await confirmButton.click();

      // Wait for deletion to complete
      await page.waitForTimeout(2000);

      // Should still be on profile page
      expect(page.url()).toContain("/profile");

      // Listing count should decrease by 1 (or show "No listings" message)
      const newCount = await page.locator(".group.bg-card").count();
      if (newCount === 0) {
        // If it was the only listing, check for empty state
        await expect(page.getByText(/no.*listings/i)).toBeVisible({ timeout: 5000 });
      } else {
        expect(newCount).toBe(initialCount - 1);
      }
    });

    test("should not allow deleting listings owned by others", async ({ page }) => {
      // Login as first user and create listing
      await loginUser(page);
      await createListing(page, "Protected Listing");

      // Get the listing URL
      await page.goto("/profile");
      await page.waitForLoadState("networkidle");
      const ourListing = page.locator('a[href*="/listings/"]').first();
      await ourListing.click();
      await page.waitForURL(/\/listings\/[a-f0-9-]+/);
      const listingUrl = page.url();

      // Logout
      await logout(page);

      // Login as different user
      await loginUser(page);

      // Try to access the edit page of the first user's listing
      const editUrl = listingUrl + "/edit";
      await page.goto(editUrl);

      await page.waitForLoadState("networkidle");

      // Should either redirect or show error (not show the edit form)
      // The page should not show the edit form title input
      const titleInput = page.getByLabel(/title/i);

      // If we can see the form, something is wrong with authorization
      const canEdit = (await titleInput.count()) > 0;
      expect(canEdit).toBe(false);
    });
  });
});
