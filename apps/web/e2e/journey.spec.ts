import { expect, test, type Page } from "@playwright/test";
import { checkA11y, signIn } from "./helpers";

test("public pages are accessible", async ({ page }) => {
  for (const path of ["/", "/login", "/privacy", "/terms", "/developers", "/try", "/panchang"]) {
    await page.goto(path);
    await expect(page.locator("h1").first()).toBeVisible();
    await checkA11y(page);
  }
});

test("sign up, make a chart, read it, switch language", async ({ page }, info) => {
  const email = `e2e-${info.project.name}-${Date.now()}@example.com`;
  await signIn(page, email);

  // First sign-in asks for consent (US-08).
  await expect(page.getByRole("heading", { name: "Before we start" })).toBeVisible();
  await checkA11y(page);
  await page.getByLabel("I agree that my birth details are stored to calculate charts.").check();
  await page.getByRole("button", { name: "Continue" }).click();

  await expect(page.getByRole("heading", { name: "My charts" })).toBeVisible();
  await page.getByRole("link", { name: /Create your first chart|New chart/ }).first().click();

  await page.getByLabel("Name", { exact: true }).fill("Test Pune");
  await page.getByLabel("Date of birth").fill("1990-01-15");
  await page.getByLabel("Time of birth").fill("10:30");
  await page.getByLabel("Town or village name").fill("Pune");
  await page.getByRole("option", { name: /Pune/ }).first().click();
  await expect(page.getByText("Asia/Kolkata")).toBeVisible();
  await checkA11y(page);
  await page.getByRole("button", { name: "Save chart" }).click();

  // Chart page: Lagna for 1990-01-15 10:30 IST Pune is Aquarius (Lahiri).
  await expect(page.getByRole("heading", { name: "Test Pune" })).toBeVisible();
  await expect(page.locator(".kundli").first()).toBeVisible();
  await expect(page.getByText(/Aquarius/).first()).toBeVisible();
  // Every server thread must use the Swiss Ephemeris files, never the Moshier fallback.
  await expect(page.getByText("High-precision ephemeris files were not found")).toHaveCount(0);
  await checkA11y(page);
  await page.screenshot({ path: `test-results/chart-north-${info.project.name}.png`, fullPage: true });

  await page.getByLabel("South Indian").check();
  await expect(page.locator(".kundli").first()).toBeVisible();
  await page.screenshot({ path: `test-results/chart-south-${info.project.name}.png`, fullPage: true });

  for (const tab of ["Planets", "Dasha", "Transits", "Readings", "Strength", "Report"]) {
    await page.getByRole("tab", { name: tab }).click();
    await expect(page.getByRole("tabpanel")).toBeVisible();
    await checkA11y(page);
  }

  // Hindi everywhere (US-70).
  await openMenu(page, "Menu");
  await page.getByRole("banner").getByLabel("Language").selectOption("hi");
  await expect(page.getByRole("tab", { name: "कुंडली" })).toBeVisible();
  await page.getByRole("tab", { name: "कुंडली" }).click();
  await expect(page.getByText(/कुंभ/).first()).toBeVisible();
  await page.screenshot({ path: `test-results/chart-hindi-${info.project.name}.png`, fullPage: true });
  await openMenu(page, "मेनू");
  await page.getByRole("banner").getByLabel("भाषा").selectOption("mr");
  await expect(page.getByRole("tab", { name: "फलादेश" })).toBeVisible();
});

/** On phones the navigation sits behind a Menu button. */
async function openMenu(page: Page, label: string) {
  const button = page.getByRole("button", { name: label });
  if (await button.isVisible()) await button.click();
}
