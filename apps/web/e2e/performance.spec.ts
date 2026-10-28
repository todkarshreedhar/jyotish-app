import { expect, test } from "@playwright/test";

// US-53: Largest Contentful Paint under 2.5 s on a mid-range phone over 4G.
// Chromium only: throttles the network (Lighthouse "Slow 4G": 1.6 Mbps, 150 ms)
// and the CPU (4x slower) through the DevTools protocol.
const PAGES = ["/", "/try", "/login", "/panchang"];

for (const path of PAGES) {
  test(`LCP under 2.5 s on a throttled phone: ${path}`, async ({ page, context }, info) => {
    test.skip(info.project.name !== "mobile", "measured once, on the phone profile");
    const cdp = await context.newCDPSession(page);
    await cdp.send("Network.enable");
    await cdp.send("Network.emulateNetworkConditions", {
      offline: false,
      latency: 150,
      downloadThroughput: (1.6 * 1024 * 1024) / 8,
      uploadThroughput: (750 * 1024) / 8,
    });
    await cdp.send("Emulation.setCPUThrottlingRate", { rate: 4 });

    await page.goto(path, { waitUntil: "load" });
    const lcp = await page.evaluate(
      () =>
        new Promise<number>((resolve) => {
          let last = 0;
          new PerformanceObserver((list) => {
            for (const e of list.getEntries()) last = e.startTime;
          }).observe({ type: "largest-contentful-paint", buffered: true });
          setTimeout(() => resolve(last), 1500);
        }),
    );
    console.log(`LCP ${path}: ${Math.round(lcp)} ms`);
    expect(lcp).toBeGreaterThan(0);
    expect(lcp).toBeLessThan(2500);
  });
}
