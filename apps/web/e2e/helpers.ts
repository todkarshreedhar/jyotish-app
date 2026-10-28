import { readFileSync } from "node:fs";
import AxeBuilder from "@axe-core/playwright";
import { expect, type Page } from "@playwright/test";

/** Finds the newest sign-in link for an address, from Mailpit or the API log. */
export async function signInLink(email: string): Promise<string> {
  const mailpit = process.env.MAILPIT_URL;
  for (let i = 0; i < 40; i++) {
    let text = "";
    if (mailpit) {
      const r = await fetch(`${mailpit}/api/v1/search?query=${encodeURIComponent(`to:${email}`)}`);
      const list = (await r.json()) as { messages: { ID: string }[] };
      if (list.messages?.length) {
        const m = await fetch(`${mailpit}/api/v1/message/${list.messages[0].ID}`);
        text = ((await m.json()) as { Text: string }).Text;
      }
    } else {
      const log = readFileSync(process.env.API_LOG ?? "api.log", "utf8");
      const at = log.lastIndexOf(`EMAIL to ${email}`);
      text = at >= 0 ? log.slice(at) : "";
    }
    const m = text.match(/https?:\/\/\S+\/auth\/verify\?\S+/);
    if (m) return m[0];
    await new Promise((r) => setTimeout(r, 250));
  }
  throw new Error(`no sign-in email for ${email}`);
}

export async function signIn(page: Page, email: string) {
  await page.goto("/login");
  await page.getByLabel("Email address").fill(email);
  await page.getByRole("button", { name: "Email me a sign-in link" }).click();
  await expect(page.getByText(`We sent a sign-in link to ${email}`)).toBeVisible();
  const link = new URL(await signInLink(email));
  await page.goto(link.pathname + link.search);
}

/** Fails on serious or critical WCAG 2.1 AA problems. */
export async function checkA11y(page: Page) {
  const r = await new AxeBuilder({ page: page as never }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
  const bad = r.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
  expect(bad.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(" ")).join(", ")}`)).toEqual([]);
}
