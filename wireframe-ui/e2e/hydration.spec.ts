// Code was generated via OCI AI and was reviewed by a human SDE
// Tag: #ai-assisted
import { expect, test } from "@playwright/test";

test("page loads without hydration errors", async ({ page }) => {
  const hydrationSignals: string[] = [];

  page.on("console", (msg) => {
    const text = msg.text();
    if (/hydration failed|didn't match the client|react-hydration-error/i.test(text)) {
      hydrationSignals.push(text);
    }
  });

  page.on("pageerror", (err) => {
    if (/hydration failed|didn't match the client|react-hydration-error/i.test(err.message)) {
      hydrationSignals.push(err.message);
    }
  });

  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: /smart \(sudha's\) tickets' classifier/i })
  ).toBeVisible();

  // Give the app a short window to surface hydration issues.
  await page.waitForTimeout(1200);

  expect(hydrationSignals, hydrationSignals.join("\n")).toHaveLength(0);
});
