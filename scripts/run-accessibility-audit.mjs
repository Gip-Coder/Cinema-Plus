import { chromium } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import fs from "fs";
import path from "path";

const reportsDir = path.resolve("./reports/accessibility");
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

async function runAxeAudit() {
  console.log(`Starting accessibility WCAG compliance audit on: ${targetUrl}...`);
  let browser;
  try {
    browser = await chromium.launch({ headless: true });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    await page.goto(targetUrl);
    await page.waitForTimeout(1000);

    const AxeBuilderClass = AxeBuilder.default || AxeBuilder;
    const builder = new AxeBuilderClass({ page });
    const results = await builder.analyze();

    // Calculate score
    const violationsCount = results.violations.length;
    const passesCount = results.passes.length;
    const score = Math.max(0, 100 - violationsCount * 5); // 5 points deduction per violation type

    const compiledResults = {
      timestamp: new Date().toISOString(),
      accessibility_score: score,
      violations_count: violationsCount,
      passes_count: passesCount,
      violations: results.violations.map(v => ({
        id: v.id,
        impact: v.impact,
        description: v.description,
        help: v.help,
        helpUrl: v.helpUrl,
        nodes_count: v.nodes.length
      }))
    };

    fs.writeFileSync(
      path.join(reportsDir, "accessibility_report.json"),
      JSON.stringify(compiledResults, null, 2)
    );

    let md = `# Accessibility WCAG Compliance Report

*Timestamp:* ${compiledResults.timestamp}
*Auditing Engine:* Axe-Core (Playwright)

* **Accessibility Compliance Score:** ${compiledResults.accessibility_score}/100
* **Passes Rules Count:** ${compiledResults.passes_count}
* **Violations Rules Count:** ${compiledResults.violations_count}

## Accessibility Violations Details
| Issue ID | Impact | Description | Elements Impacted | Recommendation |
|----------|--------|-------------|-------------------|----------------|
`;

    if (violationsCount === 0) {
      md += "| None | N/A | No violations detected! Perfect accessibility compliance! | 0 | Keep maintaining proper semantic markup. |\n";
    } else {
      compiledResults.violations.forEach(v => {
        md += `| ${v.id} | **${v.impact.toUpperCase()}** | ${v.description} | ${v.nodes_count} | Ensure ARIA tags are matching, contrast is >4.5:1, and roles are correct. |\n`;
      });
    }

    fs.writeFileSync(path.join(reportsDir, "accessibility_report.md"), md);
    console.log("Accessibility audit completed and reports saved to /reports/accessibility/");
  } catch (err) {
    console.error("Accessibility audit failed:", err);
    fs.writeFileSync(
      path.join(reportsDir, "accessibility_report.md"),
      `# Accessibility Report not executed\n\nReason: ${err.message}`
    );
  } finally {
    if (browser) await browser.close();
  }
}

runAxeAudit();
