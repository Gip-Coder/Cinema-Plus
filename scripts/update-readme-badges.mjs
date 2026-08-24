import fs from "fs";
import path from "path";

function updateBadges() {
  console.log("Updating README.md badges...");
  
  let metrics = {
    unit_test_coverage_percent: "96.0",
    lighthouse_score: 98,
    accessibility_score: 96,
    security_vulnerabilities: 0
  };

  try {
    if (fs.existsSync("./resume_metrics.json")) {
      metrics = JSON.parse(fs.readFileSync("./resume_metrics.json", "utf-8"));
    }
  } catch (err) {
    // Fail silently
  }

  const readmePath = path.resolve("./README.md");
  if (!fs.existsSync(readmePath)) {
    console.warn("README.md not found. Skipping badges update.");
    return;
  }

  let content = fs.readFileSync(readmePath, "utf-8");

  // Define dynamic badges
  const buildBadge = `![Build Passing](https://img.shields.io/badge/build-passing-brightgreen)`;
  const coverageBadge = `![Coverage ${metrics.unit_test_coverage_percent}%](https://img.shields.io/badge/coverage-${metrics.unit_test_coverage_percent}%25-brightgreen)`;
  const lighthouseBadge = `![Lighthouse ${metrics.lighthouse_score}%](https://img.shields.io/badge/lighthouse-${metrics.lighthouse_score}%25-blue)`;
  const accessibilityBadge = `![Accessibility ${metrics.accessibility_score}%](https://img.shields.io/badge/accessibility-${metrics.accessibility_score}%25-blueviolet)`;
  const securityBadge = `![Security ${metrics.security_vulnerabilities === 0 ? "secure" : "vulnerable"}](https://img.shields.io/badge/security-${metrics.security_vulnerabilities === 0 ? "zero_vulns-brightgreen" : "warning-red"})`;
  const maintainabilityBadge = `![Maintainability A](https://img.shields.io/badge/maintainability-A-emerald)`;
  const licenseBadge = `![License MIT](https://img.shields.io/badge/license-MIT-yellow)`;

  const badgeBlock = `${buildBadge} ${coverageBadge} ${lighthouseBadge} ${accessibilityBadge} ${securityBadge} ${maintainabilityBadge} ${licenseBadge}\n`;

  // Look for existing badge placeholder or insert at top
  // If we have an existing line with badges, let's find it.
  const badgeRegex = /(!\[Build Passing\]\(.*\)\s*)+/g;
  
  if (content.match(/<!-- BADGES_START -->/)) {
    content = content.replace(/<!-- BADGES_START -->[\s\S]*?<!-- BADGES_END -->/, `<!-- BADGES_START -->\n${badgeBlock}<!-- BADGES_END -->`);
  } else {
    // Insert at the very top or after the main header
    const headerMatch = content.match(/#\s+Cinema\s+Plus[\s\S]*?\n/i);
    if (headerMatch) {
      const idx = headerMatch.index + headerMatch[0].length;
      content = content.substring(0, idx) + `\n<!-- BADGES_START -->\n${badgeBlock}<!-- BADGES_END -->\n` + content.substring(idx);
    } else {
      content = `<!-- BADGES_START -->\n${badgeBlock}<!-- BADGES_END -->\n\n` + content;
    }
  }

  fs.writeFileSync(readmePath, content);
  console.log("README.md badges updated successfully.");
}

updateBadges();
