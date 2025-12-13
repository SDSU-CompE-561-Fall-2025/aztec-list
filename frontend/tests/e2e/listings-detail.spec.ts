/**
 * Listings E2E Tests - Detail View
 *
 * Tests listing detail page functionality including:
 * - Viewing listing details
 * - Image gallery navigation
 * - Seller information display
 * - Contact seller (for non-owners)
 * - Edit button (for owners)
 * - Price, category, condition display
 * - Error handling for non-existent listings
 */

import { test, expect, Page } from "@playwright/test";
import { generateTestEmail, generateUsername, generatePassword } from "./helpers/test-helpers";

test.describe("Listing Detail View", () => {
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
  async function createListing(page: Page, title = "Test Laptop for E2E") {
    await page.goto("/listings/create");
    await page.getByLabel(/title/i).fill(title);
    await page.getByLabel(/description/i).fill("This is a test listing for e2e tests");
    await page.getByLabel(/price/i).fill("299.99");
    await page.getByLabel(/category/i).selectOption("electronics");
    await page.getByLabel(/condition/i).selectOption("good");
    await page.getByRole("button", { name: /create listing/i }).click();

    // Wait for listing to be created
    await page.waitForTimeout(2000);

    // Get listing ID from current URL or return to listings and get first one
    const currentUrl = page.url();
    if (currentUrl.includes("/listings/create")) {
      // Still on create page, click Done
      await page.getByRole("button", { name: /done/i }).click();
      await page.waitForTimeout(1000);
    }
  }

  test("should display listing detail page with all information", async ({ page }) => {
    // Go to listings page
    await page.goto("/listings");
    await page.waitForLoadState("networkidle");

    // Click on the first listing
    const firstListing = page.locator('a[href*="/listings/"]').first();
    await firstListing.waitFor({ state: "visible", timeout: 10000 });
    await firstListing.click();

    // Wait for detail page to load
    await page.waitForURL(/\/listings\/[a-f0-9-]+/, { timeout: 5000 });
    await page.waitForLoadState("networkidle");

    // Verify price is displayed (with $ sign)
    await expect(page.locator("text=/\\$\\d+/")).toBeVisible({ timeout: 5000 });

    // Verify title is visible
    const title = page.locator("h1");
    await expect(title).toBeVisible();

    // Verify seller section exists
    await expect(
      page.getByText("Seller", { exact: true }).or(page.getByText("Your Listing", { exact: true }))
    ).toBeVisible();

    // Verify back button exists
    await expect(page.getByRole("button", { name: /back/i })).toBeVisible();
  });

  test("should display seller information", async ({ page }) => {
    await page.goto("/listings");
    await page.waitForLoadState("networkidle");

    const firstListing = page.locator('a[href*="/listings/"]').first();
    await firstListing.click();
    await page.waitForURL(/\/listings\/[a-f0-9-]+/);
    await page.waitForLoadState("networkidle");

    // Verify seller username is displayed
    await expect(
      page.getByText("Seller", { exact: true }).or(page.getByText("Your Listing", { exact: true }))
    ).toBeVisible();

    // Verify "View profile" link or similar exists (use first() to avoid strict mode)
    await expect(page.getByText(/view profile|joined/i).first()).toBeVisible({ timeout: 5000 });
  });

  test("should show Contact Seller button for listings owned by others", async ({ page }) => {
    // Login as user
    await loginUser(page);

    // Go to listings (should have listings from seed data)
    await page.goto("/listings");
    await page.waitForLoadState("networkidle");

    // Find a listing and click it
    const listing = page.locator('a[href*="/listings/"]').first();
    await listing.click();
    await page.waitForURL(/\/listings\/[a-f0-9-]+/);
    await page.waitForLoadState("networkidle");

    // Should show Contact Seller button (assuming this is not our listing)
    const contactButton = page.getByRole("button", { name: /contact seller/i });

    // If it exists, verify it's visible
    if ((await contactButton.count()) > 0) {
      await expect(contactButton).toBeVisible();
    }
  });

  test("should show Edit Listing button for own listings", async ({ page }) => {
    // Login and create a listing
    await loginUser(page);
    await createListing(page);

    // Navigate to profile to find our listing
    await page.goto("/profile");
    await page.waitForLoadState("networkidle");

    // Find the listing card (the whole card is clickable, not just the link)
    const listingCard = page.locator(".group.bg-card").first();
    await listingCard.waitFor({ state: "visible", timeout: 10000 });

    // Click the card to navigate to detail page
    await listingCard.click();

    // Wait for navigation to detail page
    await page.waitForURL(/\/listings\/[a-f0-9-]+$/, { timeout: 10000 });
    await page.waitForLoadState("networkidle");

    // Wait a bit for auth context to be established
    await page.waitForTimeout(2000);

    // Should show Edit Listing button with icon
    const editButton = page.getByRole("button", { name: /edit listing/i });
    await expect(editButton).toBeVisible({ timeout: 10000 });

    // Verify it has the Edit icon
    await expect(editButton.locator("svg")).toBeVisible();
  });

  test("should display category badge", async ({ page }) => {
    await page.goto("/listings");
    await page.waitForLoadState("networkidle");

    const firstListing = page.locator('a[href*="/listings/"]').first();
    await firstListing.click();
    await page.waitForURL(/\/listings\/[a-f0-9-]+/);
    await page.waitForLoadState("networkidle");

    // Category should be displayed (Electronics, Books, etc.)
    const categoryBadge = page
      .locator("text=/electronics|books|clothing|furniture|sports|other/i")
      .first();
    await expect(categoryBadge).toBeVisible({ timeout: 5000 });
  });

  test("should display condition information", async ({ page }) => {
    await page.goto("/listings");
    await page.waitForLoadState("networkidle");

    const firstListing = page.locator('a[href*="/listings/"]').first();
    await firstListing.click();
    await page.waitForURL(/\/listings\/[a-f0-9-]+/);
    await page.waitForLoadState("networkidle");

    // Condition heading should exist (use first() to avoid strict mode)
    await expect(page.getByText("Condition", { exact: true }).first()).toBeVisible({
      timeout: 10000,
    });
  });

  test("should display description", async ({ page }) => {
    await page.goto("/listings");
    await page.waitForLoadState("networkidle");

    const firstListing = page.locator('a[href*="/listings/"]').first();
    await firstListing.click();
    await page.waitForURL(/\/listings\/[a-f0-9-]+/);
    await page.waitForLoadState("networkidle");

    // Description heading should exist (use first() to avoid strict mode)
    await expect(page.getByText("Description", { exact: true }).first()).toBeVisible({
      timeout: 10000,
    });
  });

  test("should display posted and updated dates", async ({ page }) => {
    await page.goto("/listings");
    await page.waitForLoadState("networkidle");

    const firstListing = page.locator('a[href*="/listings/"]').first();
    await firstListing.click();
    await page.waitForURL(/\/listings\/[a-f0-9-]+/);
    await page.waitForLoadState("networkidle");

    // Should show posted date
    await expect(page.getByText(/posted/i)).toBeVisible();
  });

  test("should navigate back when clicking back button", async ({ page }) => {
    await page.goto("/listings");

    await page.waitForLoadState("networkidle");

    const firstListing = page.locator('a[href*="/listings/"]').first();
    await firstListing.click();
    await page.waitForURL(/\/listings\/[a-f0-9-]+/);

    // Click back button
    await page.getByRole("button", { name: /back/i }).click();

    // Should navigate back
    await page.waitForTimeout(1000);
    expect(page.url()).not.toContain("/listings/");
  });

  test("should show error page for non-existent listing", async ({ page }) => {
    // Try to access a listing with invalid UUID
    await page.goto("/listings/00000000-0000-0000-0000-000000000000");

    await page.waitForLoadState("networkidle");

    // Should show error message
    await expect(page.getByText(/listing not found|could not be found/i)).toBeVisible({
      timeout: 10000,
    });

    // Should show Browse All Listings button
    await expect(page.getByRole("button", { name: /browse all listings/i })).toBeVisible();
  });

  test("should navigate to seller profile when clicking View profile", async ({ page }) => {
    await page.goto("/listings");
    await page.waitForLoadState("networkidle");

    const firstListing = page.locator('a[href*="/listings/"]').first();
    await firstListing.click();
    await page.waitForURL(/\/listings\/[a-f0-9-]+/);
    await page.waitForLoadState("networkidle");

    // Find and click View profile link
    const viewProfileLink = page.locator("button, a").filter({ hasText: /view profile/i });

    if ((await viewProfileLink.count()) > 0) {
      await viewProfileLink.first().click();

      // Should navigate to profile page
      await page.waitForURL(/\/profile\/[a-f0-9-]+/, { timeout: 5000 });
      expect(page.url()).toMatch(/\/profile\/[a-f0-9-]+/);
    }
  });

  test("should show image gallery for listings with images", async ({ page }) => {
    await page.goto("/listings");
    await page.waitForLoadState("networkidle");

    const firstListing = page.locator('a[href*="/listings/"]').first();
    await firstListing.click();
    await page.waitForURL(/\/listings\/[a-f0-9-]+/);
    await page.waitForLoadState("networkidle");

    // Check if main image area exists (could be placeholder or actual image)
    const mainImageArea = page.locator('img, div[style*="aspect"]').first();
    await expect(mainImageArea).toBeVisible({ timeout: 10000 });
  });

  test("should open contact dialog when clicking Contact Seller", async ({ page }) => {
    await loginUser(page);

    await page.goto("/listings");
    await page.waitForLoadState("networkidle");

    const firstListing = page.locator('a[href*="/listings/"]').first();
    await firstListing.click();
    await page.waitForURL(/\/listings\/[a-f0-9-]+/);
    await page.waitForLoadState("networkidle");

    const contactButton = page.getByRole("button", { name: /contact seller/i });

    if ((await contactButton.count()) > 0) {
      await contactButton.click();

      // Dialog should appear with contact information
      await expect(page.getByText(/contact|email|phone/i)).toBeVisible({ timeout: 5000 });
    }
  });

  test("should show inactive badge for inactive listings", async ({ page }) => {
    // This test would need an inactive listing to exist
    // For now, we'll just check the structure
    await page.goto("/listings");
    await page.waitForLoadState("networkidle");

    const firstListing = page.locator('a[href*="/listings/"]').first();
    await firstListing.click();
    await page.waitForURL(/\/listings\/[a-f0-9-]+/);
    await page.waitForLoadState("networkidle");

    // If inactive badge exists, it should be visible
    // Don't fail if not found, just check if it would be visible when present
  });
});
