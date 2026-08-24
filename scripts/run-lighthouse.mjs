import fs from "fs";
import path from "path";
import * as chromeLauncher from "chrome-launcher";
import lighthouse from "lighthouse";

const reportsDir = path.resolve("./reports/lighthouse");
if (!fs.existsSync(reportsDir)) {
  fs.mkdirSync(reportsDir, { recursive: true });
}

let targetUrl = "http://localhost:3005";
const args = process.argv.slice(2);
for (let i = 0; i < args.length; i++) {
  if (args[i] === "--url" && args[i + 1]) {
    targetUrl = args[i + 1];
  }
}

async function runLighthouseAudit() {
  console.log(`Starting Lighthouse audit on: ${targetUrl}...`);
  let chrome;
  try {
    // Launch headless Chrome
    chrome = await chromeLauncher.launch({
      chromeFlags: ["--headless", "--no-sandbox", "--disable-gpu"]
    });

    const options = {
      logLevel: "info",
      output: "html",
      onlyCategories: ["performance", "accessibility", "best-practices", "seo"],
      port: chrome.port
    };

    // Run Lighthouse
    const runnerResult = await lighthouse(targetUrl, options);
    
    // Save report HTML
    const reportHtml = runnerResult.report;
    fs.writeFileSync(path.join(reportsDir, "lighthouse_report.html"), reportHtml);

    // Save JSON output
    const reportJson = JSON.stringify(runnerResult.lhr, null, 2);
    fs.writeFileSync(path.join(reportsDir, "lighthouse_report.json"), reportJson);

    // Extract scores
    const scores = {
      performance: Math.round(runnerResult.lhr.categories.performance.score * 100),
      accessibility: Math.round(runnerResult.lhr.categories.accessibility.score * 100),
      bestPractices: Math.round(runnerResult.lhr.categories["best-practices"].score * 100),
      seo: Math.round(runnerResult.lhr.categories.seo.score * 100)
    };

    console.log(`Lighthouse Audit completed successfully!`);
    console.log(`Performance: ${scores.performance}`);
    console.log(`Accessibility: ${scores.accessibility}`);
    console.log(`Best Practices: ${scores.bestPractices}`);
    console.log(`SEO: ${scores.seo}`);

    const md = `# Automated Lighthouse Performance Report

*Timestamp:* ${new Date().toISOString()}
*Target URL:* ${targetUrl}

## Category Scores
* **Performance:** ${scores.performance}/100
* **Accessibility:** ${scores.accessibility}/100
* **Best Practices:** ${scores.bestPractices}/100
* **SEO:** ${scores.seo}/100

## Core Web Vitals Telemetry
* **First Contentful Paint (FCP):** ${runnerResult.lhr.audits["first-contentful-paint"].displayValue}
* **Largest Contentful Paint (LCP):** ${runnerResult.lhr.audits["largest-contentful-paint"].displayValue}
* **Cumulative Layout Shift (CLS):** ${runnerResult.lhr.audits["cumulative-layout-shift"].displayValue}
* **Total Blocking Time (TBT):** ${runnerResult.lhr.audits["total-blocking-time"].displayValue}
* **Speed Index:** ${runnerResult.lhr.audits["speed-index"].displayValue}
`;

    fs.writeFileSync(path.join(reportsDir, "lighthouse_report.md"), md);
  } catch (err) {
    console.error("Lighthouse execution failed:", err);
    // Write fallback reports to keep run-all script flowing
    fs.writeFileSync(
      path.join(reportsDir, "lighthouse_report.md"),
      `# Lighthouse Report not executed\n\nReason: ${err.message}`
    );
  } finally {
    if (chrome) await chrome.kill();
  }
}

runLighthouseAudit();
