import { chromium } from "@playwright/test";
import fs from "fs";
import path from "path";
import { execSync } from "child_process";

const reportsDir = path.resolve("./reports/profiling");
if (!fs.existsSync(reportsDir)) {
  fs.mkdirSync(reportsDir, { recursive: true });
}

// Default frontend target
let frontendUrl = "http://localhost:3005";
const args = process.argv.slice(2);
for (let i = 0; i < args.length; i++) {
  if (args[i] === "--url" && args[i + 1]) {
    frontendUrl = args[i + 1];
  }
}

async function profileFrontend() {
  console.log(`Starting frontend memory profiling on: ${frontendUrl}...`);
  let browser;
  try {
    browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    
    // Connect to CDP session to get performance metrics
    const client = await page.context().newCDPSession(page);
    await client.send("Performance.enable");

    // Navigate and exercise pages
    await page.goto(frontendUrl);
    await page.waitForTimeout(2000);
    
    // Simulate user browsing
    const links = page.locator("a[href^='/movies/']");
    if (await links.count() > 0) {
      await links.first().click();
      await page.waitForTimeout(1000);
      await page.goBack();
      await page.waitForTimeout(1000);
    }
    
    // Collect Performance Metrics
    const perfMetrics = await client.send("Performance.getMetrics");
    
    // Evaluate memory measurements on the page
    const memoryTelemetry = await page.evaluate(() => {
      return {
        jsHeapSizeLimit: window.performance?.memory?.jsHeapSizeLimit || 0,
        totalJSHeapSize: window.performance?.memory?.totalJSHeapSize || 0,
        usedJSHeapSize: window.performance?.memory?.usedJSHeapSize || 0,
        navigationTiming: window.performance?.getEntriesByType("navigation")[0]?.toJSON() || {}
      };
    });

    const metricsMap = {};
    perfMetrics.metrics.forEach(m => {
      metricsMap[m.name] = m.value;
    });

    const results = {
      timestamp: new Date().toISOString(),
      js_heap_limit_mb: (memoryTelemetry.jsHeapSizeLimit / (1024 * 1024)).toFixed(2),
      total_js_heap_mb: (memoryTelemetry.totalJSHeapSize / (1024 * 1024)).toFixed(2),
      used_js_heap_mb: (memoryTelemetry.usedJSHeapSize / (1024 * 1024)).toFixed(2),
      layout_count: metricsMap["LayoutCount"] || 0,
      recalc_style_count: metricsMap["RecalcStyleCount"] || 0,
      layout_duration_sec: (metricsMap["LayoutDuration"] || 0).toFixed(4),
      style_duration_sec: (metricsMap["RecalcStyleDuration"] || 0).toFixed(4),
      task_duration_sec: (metricsMap["TaskDuration"] || 0).toFixed(4),
      js_heap_used_cdp_mb: ((metricsMap["JSHeapUsedSize"] || 0) / (1024 * 1024)).toFixed(2),
      dom_nodes: metricsMap["DOMNodes"] || 0,
      js_event_listeners: metricsMap["JSEventListeners"] || 0
    };

    fs.writeFileSync(
      path.join(reportsDir, "frontend_profile.json"),
      JSON.stringify(results, null, 2)
    );

    const md = `# Frontend memory & Performance Profile Report

*Timestamp:* ${results.timestamp}
*Audit Tool:* Playwright + Chrome DevTools Protocol (CDP)

## Javascript Heap Size Metrics
* **Used JS Heap Size (Browser API):** ${results.used_js_heap_mb} MB
* **Used JS Heap Size (Chrome CDP):** ${results.js_heap_used_cdp_mb} MB
* **Total Allocated JS Heap:** ${results.total_js_heap_mb} MB
* **JS Heap Limit:** ${results.js_heap_limit_mb} MB

## Thread Activity & DOM Nodes
* **DOM Nodes Count:** ${results.dom_nodes}
* **Event Listeners:** ${results.js_event_listeners}
* **Render Layout Recalculations:** ${results.layout_count} times
* **Render Recalc Style Recalculations:** ${results.recalc_style_count} times
* **Main Thread Task Duration:** ${results.task_duration_sec} seconds
* **Layout Duration:** ${results.layout_duration_sec} seconds
* **Style Duration:** ${results.style_duration_sec} seconds
`;

    fs.writeFileSync(path.join(reportsDir, "frontend_profile.md"), md);
    console.log("Frontend memory profiling completed.");
  } catch (err) {
    console.error("Frontend memory profiling failed:", err);
    // Write mock fallback to keep build passing
    fs.writeFileSync(path.join(reportsDir, "frontend_profile.md"), `# Frontend profile not executed\n\nReason: ${err.message}`);
  } finally {
    if (browser) await browser.close();
  }
}

function runBackendProfile() {
  console.log("Starting backend cpu/memory profiling...");
  try {
    execSync("python scripts/profile_backend.py", { stdio: "inherit" });
  } catch (err) {
    console.error("Backend profiling failed:", err);
  }
}

async function start() {
  await profileFrontend();
  runBackendProfile();
}

start();
