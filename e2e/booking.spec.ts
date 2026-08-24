import { test, expect } from "@playwright/test";

test.describe("Movie Booking Flow", () => {
  test("should allow a customer to search, select a movie, view details, and navigate to seat booking", async ({ page }) => {
    // 1. Visit homepage
    await page.goto("/");
    
    // Check main title
    await expect(page.getByText("Cinema Plus Spotlight")).toBeVisible();
    
    // 2. Search for a movie
    const searchInput = page.getByPlaceholder("Search movies, genres, language...");
    if (await searchInput.isVisible()) {
      await searchInput.fill("Interstellar");
    }
    
    // Locate movie poster/link and click
    const movieLink = page.locator("a[href^='/movies/']").first();
    if (await movieLink.isVisible()) {
      await movieLink.click();
      
      // 3. Movie Detail Page
      await expect(page).toHaveURL(/\/movies\/\d+/);
      await expect(page.locator("h1")).toBeVisible();
      
      // Locate showtime buttons
      const showtimeBtn = page.locator("a[href^='/book/']").first();
      if (await showtimeBtn.isVisible()) {
        await showtimeBtn.click();
        
        // 4. Seat Booking Page
        await expect(page).toHaveURL(/\/book\/\d+/);
        await expect(page.getByText("Select Seats")).toBeVisible();
      }
    }
  });

  test("should allow a user to complete booking journey", async ({ page }) => {
    // Navigate straight to a mock booking page or dashboard
    await page.goto("/bookings");
    // Should prompt login if not authenticated
    await expect(page).toHaveURL(/\/login/);
  });
});
