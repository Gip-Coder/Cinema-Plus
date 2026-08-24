import { test, expect } from "@playwright/test";

test.describe("Authentication Flow", () => {
  test("should allow user to navigate to login and register", async ({ page }) => {
    // Navigate to homepage
    await page.goto("/");
    
    // Find and click Login button
    const loginLink = page.getByRole("link", { name: "Login" });
    await expect(loginLink).toBeVisible();
    await loginLink.click();
    
    // Assert on login page URL
    await expect(page).toHaveURL(/\/login/);
    
    // Check form fields
    const usernameInput = page.locator("input[name='username']");
    const passwordInput = page.locator("input[name='password']");
    await expect(usernameInput).toBeVisible();
    await expect(passwordInput).toBeVisible();
    
    // Click register link
    const registerLink = page.getByRole("link", { name: "Register here" });
    if (await registerLink.isVisible()) {
      await registerLink.click();
      await expect(page).toHaveURL(/\/register/);
      
      const emailInput = page.locator("input[name='email']");
      await expect(emailInput).toBeVisible();
    }
  });

  test("should authenticate admin user and load dashboard", async ({ page }) => {
    await page.goto("/login");
    
    // Fill credentials
    await page.locator("input[name='username']").fill("admin");
    await page.locator("input[name='password']").fill("admin123");
    
    // Click submit
    const submitBtn = page.getByRole("button", { name: "Sign In" }).first();
    await submitBtn.click();
    
    // Admin redirected to admin page
    await expect(page).toHaveURL(/\/admin/);
    await expect(page.getByText("Dashboard")).toBeVisible();
  });
});
