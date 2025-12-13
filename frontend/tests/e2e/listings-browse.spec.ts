/**
 * Listings E2E Tests - Browse & Search
 *
 * Tests marketplace browsing functionality including:
 * - Viewing listings page
 * - Search functionality
 * - Filtering by category, condition, price
 * - Sorting options
 * - Pagination
 */

import { test, expect } from "@playwright/test";
import { generateTestEmail, generateUsername, generatePassword } from "./helpers/test-helpers";

test.describe("Listings Browse & Search", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to listings page before each test
    await page.goto("/listings");
  });

  test("should display listings page with filters", async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState("networkidle");

    // Verify filter sidebar exists - look for Category heading
    const categoryHeading = page
      .getByText("Category", { exact: true })
      .or(page.locator("h3").filter({ hasText: "Category" }));
    await expect(categoryHeading).toBeVisible({ timeout: 10000 });

    // Verify Apply Filters button exists
    await expect(page.getByRole("button", { name: "Apply Filters" })).toBeVisible();

    // Verify Sort By section exists
    await expect(page.getByText("Sort By")).toBeVisible();
  });

  test("should search for listings by keyword", async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState("networkidle");

    // Find the search input in the header
    const searchInput = page
      .locator('header input[type="text"]')
      .or(page.getByPlaceholder(/search/i));
    await searchInput.waitFor({ state: "visible", timeout: 5000 });

    // Type search query
    await searchInput.fill("laptop");
    await searchInput.press("Enter");

    // Wait for search results
    await page.waitForURL(/q=laptop/, { timeout: 5000 });

    // Verify search results heading or URL contains the query
    expect(page.url()).toContain("q=laptop");
  });

  test("should filter listings by category", async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState("networkidle");

    // Find the category select dropdown
    const categorySelect = page
      .locator("select")
      .filter({ has: page.locator('option[value="electronics"]') })
      .first();
    await categorySelect.waitFor({ state: "visible", timeout: 10000 });

    // Select Electronics category
    await categorySelect.selectOption("electronics");

    // Click Apply Filters button
    await page.getByRole("button", { name: "Apply Filters" }).click();

    // Verify URL has category parameter
    await page.waitForURL(/category=electronics/, { timeout: 3000 });
    expect(page.url()).toMatch(/category=electronics/);
  });

  test("should filter listings by price range", async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState("networkidle");

    // Find price inputs by placeholder text
    const minPriceInput = page.getByPlaceholder("Min");
    const maxPriceInput = page.getByPlaceholder("Max");

    await minPriceInput.waitFor({ state: "visible", timeout: 10000 });

    // Fill price range
    await minPriceInput.fill("10");
    await maxPriceInput.fill("100");

    // Click Apply Filters button (first one to avoid strict mode)
    await page.getByRole("button", { name: "Apply Filters" }).first().click();

    // Verify URL has price parameters
    await page.waitForURL(/minPrice=10.*maxPrice=100|maxPrice=100.*minPrice=10/, { timeout: 3000 });
    expect(page.url()).toMatch(/minPrice=10/);
    expect(page.url()).toMatch(/maxPrice=100/);
  });

  test("should filter listings by condition", async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState("networkidle");

    // Find the "New" condition checkbox by label
    const newConditionLabel = page.locator("label").filter({ hasText: "New" }).first();
    await newConditionLabel.waitFor({ state: "visible", timeout: 10000 });

    // Click the New condition checkbox
    await newConditionLabel.click();

    // Click Apply Filters button
    await page.getByRole("button", { name: "Apply Filters" }).first().click();

    // Verify URL has condition parameter
    await page.waitForURL(/condition=new/, { timeout: 3000 });
    expect(page.url()).toMatch(/condition=new/);
  });

  test("should change sort order", async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState("networkidle");

    // Find the Sort By select under the "Sort By" heading
    const sortSelect = page
      .locator("select")
      .filter({ has: page.locator('option[value="price_asc"]') })
      .first();
    await sortSelect.waitFor({ state: "visible", timeout: 10000 });

    // Change sort to Price: Low to High
    await sortSelect.selectOption("price_asc");

    // Click Apply Filters button
    await page.getByRole("button", { name: "Apply Filters" }).first().click();

    // Verify URL has sort parameter
    await page.waitForURL(/sort=price_asc/, { timeout: 3000 });
    expect(page.url()).toMatch(/sort=price_asc/);
  });

  test("should navigate through pagination", async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState("networkidle");

    // Look for Next button in pagination
    const nextButton = page
      .getByRole("button", { name: /next/i })
      .or(page.locator('button[aria-label="Next page"]'));

    // Check if pagination exists (only if there are enough listings)
    const paginationCount = await nextButton.count();

    if (paginationCount > 0) {
      await nextButton.first().click();

      // Verify URL has offset parameter
      await page.waitForURL(/offset=/, { timeout: 3000 });
      expect(page.url()).toMatch(/offset=/);
    } else {
      // If no pagination, skip test
      test.skip();
    }
  });

  test("should display no results message for invalid search", async ({ page }) => {
    // Search for something that definitely won't exist
    const searchInput = page
      .locator('header input[type="text"]')
      .or(page.getByPlaceholder(/search/i));
    await searchInput.waitFor({ state: "visible", timeout: 5000 });

    await searchInput.fill("xyzqwertynonexistent12345");
    await searchInput.press("Enter");

    // Wait for search to complete
    await page.waitForLoadState("networkidle");

    // Verify no results message (should be unique in main content)
    const noResultsText = page.getByText("No listings match your search");
    await expect(noResultsText).toBeVisible({ timeout: 5000 });
  });

  test("should clear filters", async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState("networkidle");

    // Find and select a category
    const categorySelect = page
      .locator("select")
      .filter({ has: page.locator('option[value="electronics"]') })
      .first();
    await categorySelect.waitFor({ state: "visible", timeout: 10000 });
    await categorySelect.selectOption("electronics");

    // Apply the filter
    await page.getByRole("button", { name: "Apply Filters" }).first().click();
    await page.waitForURL(/category=electronics/, { timeout: 3000 });

    // Click Clear Filters
    await page.getByRole("button", { name: "Clear Filters" }).first().click();

    // Verify URL no longer has category parameter
    await page.waitForTimeout(1000);
    const url = page.url();
    expect(url).not.toContain("category=electronics");
  });

  test("should display listing cards with basic information", async ({ page }) => {
    // Create a listing first to ensure there's at least one
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

    // Create a listing
    await page.goto("/listings/create");
    await page.getByLabel(/title/i).fill("Browse Test Listing");
    await page.getByLabel(/description/i).fill("Test description");
    await page.getByLabel(/price/i).fill("99.99");
    await page.getByLabel(/category/i).selectOption("textbooks");
    await page.getByLabel(/condition/i).selectOption("good");
    await page.getByRole("button", { name: /create listing/i }).click();
    await page.waitForTimeout(2000);

    // Go to browse page
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Look for listing cards - they are Link elements with href starting with /listings/
    const listingCards = page.locator('a[href^="/listings/"]').filter({
      has: page.locator("h3"),
    });

    // Wait for at least one listing card to appear
    await listingCards.first().waitFor({ state: "visible", timeout: 10000 });

    // Verify at least one card is visible
    const count = await listingCards.count();
    expect(count).toBeGreaterThan(0);
  });

  test("should navigate to listing detail page when clicking a listing", async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState("networkidle");

    // Find first listing link
    const firstListing = page.locator('a[href*="/listings/"]').first();
    await firstListing.waitFor({ state: "visible", timeout: 10000 });

    // Click the listing
    await firstListing.click();

    // Verify navigation to detail page
    await page.waitForURL(/\/listings\/[a-f0-9-]+/, { timeout: 5000 });
    expect(page.url()).toMatch(/\/listings\/[a-f0-9-]+/);
  });
});
