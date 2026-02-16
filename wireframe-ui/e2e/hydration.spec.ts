// Code was generated via OCI AI and was reviewed by a human SDE
// Tag: #ai-assisted
import { expect, test } from "@playwright/test";

test("page loads without hydration errors", async ({ page }) => {
  const runtimeSignals: string[] = [];

  page.on("console", (msg) => {
    const text = msg.text();
    if (
      /hydration failed|didn't match the client|react-hydration-error|runtime error|cannot find module|module not found/i.test(
        text
      )
    ) {
      runtimeSignals.push(text);
    }
  });

  page.on("pageerror", (err) => {
    if (
      /hydration failed|didn't match the client|react-hydration-error|runtime error|cannot find module|module not found/i.test(
        err.message
      )
    ) {
      runtimeSignals.push(err.message);
    }
  });

  await page.goto("/");
  await expect(page.getByText(/smart tickets' classifier \(stc\)/i)).toBeVisible();
  await expect(page.getByText(/runtime error/i)).toHaveCount(0);

  // Give the app a short window to surface hydration issues.
  await page.waitForTimeout(1200);

  expect(runtimeSignals, runtimeSignals.join("\n")).toHaveLength(0);
});
