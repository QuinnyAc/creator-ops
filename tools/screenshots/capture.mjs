import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

const currentDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(currentDir, "../..");
const outputDir = path.join(repoRoot, "docs", "screenshots");
const baseUrl = process.env.CREATOR_OPS_WEB_URL ?? "http://127.0.0.1:3000";

const shots = [
  ["dashboard", "/"],
  ["topics", "/topics"],
  ["content-pipeline", "/content"],
  ["publishing-calendar", "/publishing"],
  ["analytics", "/analytics"],
  ["creator-playbook", "/insights"],
];

fs.mkdirSync(outputDir, { recursive: true });

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({
  viewport: { width: 1440, height: 1000 },
  deviceScaleFactor: 1,
});

try {
  for (const [name, route] of shots) {
    const url = new URL(route, baseUrl).toString();
    console.log(`Capturing ${name}: ${url}`);
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60_000 });
    await page.waitForSelector(".workspace", { timeout: 30_000 });
    await page.waitForLoadState("networkidle", { timeout: 15_000 }).catch(() => undefined);
    await page.addStyleTag({
      content: `
        *, *::before, *::after {
          animation-duration: 0s !important;
          animation-delay: 0s !important;
          transition-duration: 0s !important;
          caret-color: transparent !important;
        }
      `,
    });
    await page.waitForTimeout(800);
    await page.screenshot({
      path: path.join(outputDir, `${name}.png`),
      fullPage: true,
    });
  }
} finally {
  await browser.close();
}

console.log(`Saved ${shots.length} screenshots to ${outputDir}`);
