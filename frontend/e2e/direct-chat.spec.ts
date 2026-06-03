import { expect, type Locator, type Page, test } from "@playwright/test";

import { registerAndSetUsername } from "./helpers/profile";

const DIRECT_CHAT_FLOW_TIMEOUT_MS = 90_000;
const DIRECT_CHAT_COMPOSER_TIMEOUT_MS = 45_000;

function randomLetters(length: number): string {
  const alphabet = "abcdefghijklmnopqrstuvwxyz";
  let result = "";
  for (let index = 0; index < length; index += 1) {
    result += alphabet[Math.floor(Math.random() * alphabet.length)];
  }
  return result;
}

async function expectDirectChatComposer(page: Page): Promise<Locator> {
  const input = page.getByTestId("chat-message-input");
  await expect(input).toBeVisible({
    timeout: DIRECT_CHAT_COMPOSER_TIMEOUT_MS,
  });
  return input;
}

test("direct chat by username opens and delivers messages between users", async ({
  page,
  browser,
}) => {
  test.setTimeout(DIRECT_CHAT_FLOW_TIMEOUT_MS);

  const alice = `alice${randomLetters(6)}`;
  const bob = `bob${randomLetters(6)}`;
  const password = "pass12345";
  const text = `dm-${Date.now()}`;

  await registerAndSetUsername(page, alice, password);

  const bobContext = await browser.newContext();
  const bobPage = await bobContext.newPage();
  try {
    await registerAndSetUsername(bobPage, bob, password);

    await bobPage.goto(`/@${encodeURIComponent(alice)}`);
    await expect(bobPage).toHaveURL(`/@${encodeURIComponent(alice)}`);

    const input = await expectDirectChatComposer(bobPage);
    await input.fill(text);
    await bobPage.getByTestId("chat-send-button").click();
    await expect(
      bobPage.getByRole("article").filter({ hasText: text }).first(),
    ).toBeVisible({ timeout: 15_000 });

    await page.goto(`/@${encodeURIComponent(bob)}`);
    await expectDirectChatComposer(page);
    await expect(
      page.getByRole("article").filter({ hasText: text }).first(),
    ).toBeVisible({ timeout: 15_000 });
  } finally {
    await bobContext.close();
  }
});
