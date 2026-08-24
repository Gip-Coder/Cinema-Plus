import { execSync } from "child_process";
import fs from "fs";
import path from "path";

const reportsDir = path.resolve("./reports/static-analysis");
if (!fs.existsSync(reportsDir)) {
  fs.mkdirSync(reportsDir, { recursive: true });
}

function runCommandSafe(command) {
  try {
    return {
      success: true,
      stdout: execSync(command, { stdio: "pipe" }).toString()
    };
  } catch (err) {
    return {
      success: false,
      error: err.message,
      stdout: err.stdout ? err.stdout.toString() : "",
      stderr: err.stderr ? err.stderr.toString() : ""
    };
  }
}

function analyzeStatic() {
  console.log("Running static code analysis...");

  const isWin = process.platform === "win32";
  const radonPath = fs.existsSync(path.resolve(isWin ? ".venv/Scripts/radon.exe" : ".venv/bin/radon"))
    ? path.resolve(isWin ? ".venv/Scripts/radon.exe" : ".venv/bin/radon")
    : "radon";

  // 1. Radon Cyclomatic Complexity (Python)
  console.log("Running Radon Cyclomatic Complexity...");
  let ccData = "Not Executed";
  let ccSuccess = false;
  const ccRes = runCommandSafe(`"${radonPath}" cc backend -j`);
  if (ccRes.success) {
    ccData = JSON.parse(ccRes.stdout);
    ccSuccess = true;
  } else {
    console.warn("Radon CC execution skipped or failed. Ensure radon is installed.");
  }

  // 2. Radon Maintainability Index (Python)
  console.log("Running Radon Maintainability Index...");
  let miData = "Not Executed";
  let miSuccess = false;
  const miRes = runCommandSafe(`"${radonPath}" mi backend -j`);
  if (miRes.success) {
    miData = JSON.parse(miRes.stdout);
    miSuccess = true;
  }

  // 3. Duplicate Code scan (jscpd via npx)
  console.log("Running duplication code scan (jscpd)...");
  let duplicationPercent = 0;
  let dupsChecked = false;
  const dupRes = runCommandSafe("npx jscpd src backend --threshold 15");
  if (dupRes.success || dupRes.stdout.includes("Clone found")) {
    dupsChecked = true;
    const match = dupRes.stdout.match(/(\d+\.\d+)%/);
    if (match && match[1]) {
      duplicationPercent = parseFloat(match[1]);
    }
  }

  // 4. ESLint Errors (Frontend)
  console.log("Running ESLint checks...");
  let eslintErrorsCount = 0;
  let eslintChecked = false;
  const eslintRes = runCommandSafe("npm run lint");
  if (eslintRes.success) {
    eslintChecked = true;
  } else {
    // ESLint exited with non-zero or failed
    eslintChecked = true;
    const errMatch = eslintRes.stdout.match(/(\d+) problems/);
    if (errMatch && errMatch[1]) {
      eslintErrorsCount = parseInt(errMatch[1], 10);
    } else {
      eslintErrorsCount = 1; // Default fallback if ESLint reported failures
    }
  }

  // Compile metrics
  let avgCc = 1.2; // default mock if failed
  let avgMi = 95.0; // default mock
  
  if (ccSuccess && typeof ccData === "object") {
    let totalCc = 0;
    let counts = 0;
    Object.keys(ccData).forEach(file => {
      ccData[file].forEach(item => {
        if (item.complexity) {
          totalCc += item.complexity;
          counts++;
        }
      });
    });
    if (counts > 0) avgCc = totalCc / counts;
  }

  if (miSuccess && typeof miData === "object") {
    let totalMi = 0;
    let counts = 0;
    Object.keys(miData).forEach(file => {
      if (typeof miData[file] === "number") {
        totalMi += miData[file];
        counts++;
      } else if (miData[file] && miData[file].mi) {
        totalMi += miData[file].mi;
        counts++;
      }
    });
    if (counts > 0) avgMi = totalMi / counts;
  }

  const results = {
    timestamp: new Date().toISOString(),
    average_cyclomatic_complexity: avgCc.toFixed(2),
    average_maintainability_index: avgMi.toFixed(2),
    duplication_rate_percent: duplicationPercent.toFixed(1),
    eslint_problems: eslintErrorsCount,
    radon_cc_executed: ccSuccess,
    radon_mi_executed: miSuccess,
    jscpd_executed: dupsChecked,
    eslint_executed: eslintChecked
  };

  fs.writeFileSync(
    path.join(reportsDir, "static_analysis.json"),
    JSON.stringify(results, null, 2)
  );

  let md = `# Static Code Quality & Metrics Report

*Timestamp:* ${results.timestamp}
*Auditing Tools:* Radon (Python), jscpd (npm), ESLint (npm)

## Code Health Summary
* **Average Cyclomatic Complexity:** ${results.radon_cc_executed ? results.average_cyclomatic_complexity : "Not Executed (radon cc)"}
* **Average Maintainability Index:** ${results.radon_mi_executed ? results.average_maintainability_index : "Not Executed (radon mi)"}
* **Code Duplication Rate:** ${results.jscpd_executed ? `${results.duplication_rate_percent}%` : "Not Executed (jscpd)"}
* **ESLint Problems / Errors:** ${results.eslint_executed ? results.eslint_problems : "Not Executed (eslint)"}

## Code Metrics Interpretations
* **Cyclomatic Complexity (CC):** A score below 5 represents highly structured, low-risk modular procedures.
* **Maintainability Index (MI):** A score above 80 indicates excellent maintainability.
* **Duplication:** A clone detection below 5% is optimal.
`;

  fs.writeFileSync(path.join(reportsDir, "static_analysis_report.md"), md);
  console.log("Static analysis completed and reports saved to /reports/static-analysis/");
}

analyzeStatic();
