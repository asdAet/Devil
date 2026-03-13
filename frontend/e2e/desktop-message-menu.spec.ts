import { expect, test, type Page } from "@playwright/test";

async function register(page: Page, username: string, password: string) {
  const email = `${username}@e2e.local`;

  for (let attempt = 0; attempt < 4; attempt += 1) {
    await page.goto("/register");
    await page.getByTestId("auth-email-input").fill(email);
    await page.getByTestId("auth-password-input").fill(password);
    await page.getByTestId("auth-confirm-input").fill(password);

    const [response] = await Promise.all([
      page.waitForResponse(
        (res) =>
          res.url().includes("/api/auth/register/") &&
          res.request().method() === "POST",
      ),
      page.getByTestId("auth-submit-button").click(),
    ]);

    if (response.status() === 201) {
      await expect(page).toHaveURL("/");
      return;
    }

    if (response.status() === 429 && attempt < 3) {
      await page.waitForTimeout(1_500 * (attempt + 1));
      continue;
    }

    throw new Error(`Registration failed with status ${response.status()}`);
  }
}

test("desktop opens message action menu with right click", async ({ page }) => {
  const username = `d${Math.random().toString(36).slice(2, 9)}`;
  const password = "pass12345";
  const text = `desktop-menu-${Date.now()}`;

  await register(page, username, password);

  await page.goto("/rooms/public");
  await page.waitForLoadState("networkidle");

  const joinCallout = page.getByTestId("group-join-callout");
  if (await joinCallout.isVisible()) {
    await joinCallout.getByRole("button", { name: /Присоединиться|Join/i }).click();
  }

  const input = page.getByTestId("chat-message-input");
  await expect(input).toBeVisible({ timeout: 15_000 });
  await input.fill(text);
  await page.getByTestId("chat-send-button").click();

  const ownMessage = page.locator("article").filter({ has: page.getByText(text) }).last();
  await expect(ownMessage).toBeVisible({ timeout: 20_000 });

  await ownMessage.click({ button: "right" });

  const menu = page.getByRole("menu");
  await expect(menu).toBeVisible();
  await expect(menu.getByRole("menuitem")).toHaveCount(5);
});
