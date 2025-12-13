/**
 * Listings E2E Tests - Create Listing
 *
 * Tests listing creation functionality including:
 * - Accessing create listing page (requires auth)
 * - Form validation
 * - Creating listing with all required fields
 * - Image upload
 * - Redirects and error handling
 */

import { test, expect, Page } from "@playwright/test";
import { generateTestEmail, generateUsername, generatePassword } from "./helpers/test-helpers";

test.describe("Create Listing", () => {
  // Helper to create and login a user
  async function loginUser(page: Page) {
    const email = generateTestEmail();
    const username = generateUsername();
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

    return { email, username, password };
  }

  test("should redirect to login if not authenticated", async ({ page }) => {
    // Try to access create listing page without being logged in
    await page.goto("/listings/create");

    // Should redirect to login (with redirect param)
    await page.waitForTimeout(1000);
    expect(page.url()).toContain("/login");
  });

  test("should display create listing form when authenticated", async ({ page }) => {
    // Login first
    await loginUser(page);

    // Navigate to create listing page
    await page.goto("/listings/create");

    // Verify form elements are present
    await expect(page.getByLabel(/title/i)).toBeVisible();
    await expect(page.getByLabel(/description/i)).toBeVisible();
    await expect(page.getByLabel(/price/i)).toBeVisible();
    await expect(page.getByLabel(/category/i)).toBeVisible();
    await expect(page.getByLabel(/condition/i)).toBeVisible();

    // Verify Create Listing button exists
    await expect(page.getByRole("button", { name: /create listing/i })).toBeVisible();
  });

  test("should show validation errors for empty required fields", async ({ page }) => {
    // Login first
    await loginUser(page);

    // Navigate to create listing page
    await page.goto("/listings/create");

    // Try to submit without filling anything
    await page.getByRole("button", { name: /create listing/i }).click();

    // Wait a moment for validation errors to appear
    await page.waitForTimeout(500);

    // Verify error messages appear
    await expect(page.getByText(/title is required/i)).toBeVisible();
    await expect(page.getByText(/description is required/i)).toBeVisible();
    await expect(page.getByText(/price is required/i)).toBeVisible();
    await expect(page.getByText(/category is required/i)).toBeVisible();
    await expect(page.getByText(/condition is required/i)).toBeVisible();
  });

  test("should show error for invalid price", async ({ page }) => {
    // Login first
    await loginUser(page);

    // Navigate to create listing page
    await page.goto("/listings/create");

    // Fill in title and description to avoid those errors
    await page.getByLabel(/title/i).fill("Test Item");
    await page.getByLabel(/description/i).fill("Test description");

    // Enter invalid price (negative or zero)
    const priceInput = page.getByLabel(/price/i);
    await priceInput.fill("0");
    await priceInput.blur();

    // Verify error message
    await expect(page.getByText(/price must be at least/i)).toBeVisible();
  });

  test("should successfully create a listing with valid data", async ({ page }) => {
    // Login first
    await loginUser(page);

    // Navigate to create listing page
    await page.goto("/listings/create");

    // Fill in all required fields
    await page.getByLabel(/title/i).fill("Test Laptop");
    await page.getByLabel(/description/i).fill("A great laptop for sale in excellent condition");
    await page.getByLabel(/price/i).fill("500.00");

    // Select category
    const categorySelect = page.getByLabel(/category/i);
    await categorySelect.selectOption("electronics");

    // Select condition
    const conditionSelect = page.getByLabel(/condition/i);
    await conditionSelect.selectOption("like_new");

    // Submit the form
    await page.getByRole("button", { name: /create listing/i }).click();

    // Wait for success message or listing to be created
    await page.waitForTimeout(2000);

    // Verify success toast appears
    const successMessage = page.getByText(/listing created successfully/i);
    await expect(successMessage.first()).toBeVisible({ timeout: 5000 });
  });

  test("should show character count for title", async ({ page }) => {
    // Login first
    await loginUser(page);

    // Navigate to create listing page
    await page.goto("/listings/create");

    // Type in title
    await page.getByLabel(/title/i).fill("Test");

    // Verify character count is displayed
    await expect(page.getByText(/4\/100 characters/i)).toBeVisible();
  });

  test("should show character count for description", async ({ page }) => {
    // Login first
    await loginUser(page);

    // Navigate to create listing page
    await page.goto("/listings/create");

    // Type in description
    await page.getByLabel(/description/i).fill("Test description");

    // Verify character count is displayed
    await expect(page.getByText(/16\/500 characters/i)).toBeVisible();
  });

  test("should format price to 2 decimal places on blur", async ({ page }) => {
    // Login first
    await loginUser(page);

    // Navigate to create listing page
    await page.goto("/listings/create");

    // Enter price without decimals
    const priceInput = page.getByLabel(/price/i);
    await priceInput.fill("100");
    await priceInput.blur();

    // Verify it formats to 2 decimals
    await expect(priceInput).toHaveValue("100.00");
  });

  test("should toggle listing status active/inactive", async ({ page }) => {
    // Login first
    await loginUser(page);

    // Navigate to create listing page
    await page.goto("/listings/create");

    // Find the status toggle - it's inside a label
    const statusToggle = page.locator('input[type="checkbox"]').first();

    // Verify it starts checked (active)
    await expect(statusToggle).toBeChecked();

    // Click the label containing the toggle (not the checkbox itself which is sr-only)
    const toggleLabel = page.locator("label").filter({ has: statusToggle });
    await toggleLabel.click();

    // Verify it's now unchecked
    await expect(statusToggle).not.toBeChecked();
  });

  test("should have back button that navigates to previous page", async ({ page }) => {
    // Login first
    await loginUser(page);

    // Go to home page first
    await page.goto("/");

    // Navigate to create listing page
    await page.goto("/listings/create");

    // Find and click Back button
    const backButton = page
      .getByRole("button", { name: /back/i })
      .or(page.locator("button").filter({ hasText: /back/i }));

    await backButton.click();

    // Should navigate back to home page
    await page.waitForTimeout(1000);
    expect(page.url()).not.toContain("/listings/create");
  });

  test("should have cancel button that navigates to profile", async ({ page }) => {
    // Login first
    await loginUser(page);

    // Navigate to create listing page
    await page.goto("/listings/create");

    // Find and click Cancel link
    const cancelLink = page.getByRole("link", { name: /cancel/i });
    await cancelLink.click();

    // Should navigate to profile page
    await page.waitForURL("/profile", { timeout: 5000 });
    expect(page.url()).toContain("/profile");
  });

  test("should disable form fields after listing is created", async ({ page }) => {
    // Login first
    await loginUser(page);

    // Navigate to create listing page
    await page.goto("/listings/create");

    // Fill and submit form
    await page.getByLabel(/title/i).fill("Test Item");
    await page.getByLabel(/description/i).fill("Test description for this item");
    await page.getByLabel(/price/i).fill("50.00");

    const categorySelect = page.getByLabel(/category/i);
    await categorySelect.selectOption("electronics");

    const conditionSelect = page.getByLabel(/condition/i);
    await conditionSelect.selectOption("new");

    await page.getByRole("button", { name: /create listing/i }).click();

    // Wait for listing to be created
    await page.waitForTimeout(2000);

    // Verify fields are disabled
    await expect(page.getByLabel(/title/i)).toBeDisabled();
    await expect(page.getByLabel(/description/i)).toBeDisabled();
    await expect(page.getByLabel(/price/i)).toBeDisabled();
  });

  test("should show info message before creating listing", async ({ page }) => {
    // Login first
    await loginUser(page);

    // Navigate to create listing page
    await page.goto("/listings/create");

    // Verify info message about creating listing first
    await expect(page.getByText(/create your listing first.*then.*upload images/i)).toBeVisible();
  });

  test("should show Done button after listing is created", async ({ page }) => {
    // Login first
    await loginUser(page);

    // Navigate to create listing page
    await page.goto("/listings/create");

    // Fill and submit form
    await page.getByLabel(/title/i).fill("Test Item");
    await page.getByLabel(/description/i).fill("Test description");
    await page.getByLabel(/price/i).fill("25.00");

    const categorySelect = page.getByLabel(/category/i);
    await categorySelect.selectOption("electronics");

    const conditionSelect = page.getByLabel(/condition/i);
    await conditionSelect.selectOption("good");

    await page.getByRole("button", { name: /create listing/i }).click();

    // Wait for listing to be created
    await page.waitForTimeout(2000);

    // Verify Done button appears
    await expect(page.getByRole("button", { name: /done/i })).toBeVisible();
  });
});
