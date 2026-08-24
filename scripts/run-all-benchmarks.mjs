import { spawn, execSync } from "child_process";
import fs from "fs";
import path from "path";
import http from "http";

function pingServer(url) {
  return new Promise((resolve) => {
    const check = () => {
      http.get(url, (res) => {
        if (res.statusCode === 200 || res.statusCode === 503) {
          resolve(true);
        } else {
          setTimeout(check, 200);
        }
      }).on("error", () => {
        setTimeout(check, 200);
      });
    };
    check();
  });
}

function runCommandSafe(command, envExtra = {}) {
  console.log(`Executing: ${command}...`);
  try {
    execSync(command, {
      stdio: "inherit",
      env: { ...process.env, PYTHONPATH: ".", ...envExtra }
    });
    return true;
  } catch (err) {
    console.error(`Command failed: ${command}\nError: ${err.message}`);
    return false;
  }
}

async function start() {
  console.log("==================================================");
  console.log("STARTING CINEMA PLUS BENCHMARK PIPELINE AUTOMATION");
  console.log("==================================================");

  // 1. Build project first to compile production assets (timed in run-build-benchmarks.mjs)
  runCommandSafe("node scripts/run-build-benchmarks.mjs");

  // Rebuild production assets because next dev in build-benchmarks overwrites the production BUILD_ID
  console.log("Rebuilding production assets for start...");
  runCommandSafe("npm run build");

  const isWin = process.platform === "win32";
  const pythonPath = fs.existsSync(path.resolve(isWin ? ".venv/Scripts/python.exe" : ".venv/bin/python"))
    ? path.resolve(isWin ? ".venv/Scripts/python.exe" : ".venv/bin/python")
    : "python";

  const pytestPath = fs.existsSync(path.resolve(isWin ? ".venv/Scripts/pytest.exe" : ".venv/bin/pytest"))
    ? path.resolve(isWin ? ".venv/Scripts/pytest.exe" : ".venv/bin/pytest")
    : "pytest";

  console.log(`Using Python path: ${pythonPath}`);
  console.log(`Using Pytest path: ${pytestPath}`);

  // 1.5 Seed test SQLite database first so backend has schemas on startup
  console.log("Seeding SQLite testing database...");
  runCommandSafe(`${pythonPath} scripts/seed_db.py`, { TESTING: "True" });

  // 2. Launch Backend API in background using SQLite override
  console.log("Launching backend FastAPI server...");
  const backend = spawn(pythonPath, ["-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8001"], {
    env: { ...process.env, TESTING: "True", PYTHONPATH: "." },
    shell: false,
    detached: true
  });

  // 3. Launch Next.js Frontend in background
  console.log("Launching frontend Next.js server...");
  const frontend = spawn("npx", ["next", "start", "--port", "3005"], {
    shell: true,
    detached: true
  });

  // Catch process exits
  backend.on("error", (err) => console.error("Backend process error:", err));
  frontend.on("error", (err) => console.error("Frontend process error:", err));
  backend.on("exit", (code, signal) => console.log(`Backend process exited with code ${code} and signal ${signal}`));
  frontend.on("exit", (code, signal) => console.log(`Frontend process exited with code ${code} and signal ${signal}`));
  
  backend.stderr?.on("data", (data) => console.error(`[Backend Stderr] ${data}`));
  frontend.stderr?.on("data", (data) => console.error(`[Frontend Stderr] ${data}`));

  try {
    // 4. Wait for servers to be active
    console.log("Waiting for backend API (8001)...");
    await pingServer("http://localhost:8001/health");
    console.log("Backend API is online.");

    console.log("Waiting for frontend Next.js (3005)...");
    await pingServer("http://localhost:3005/");
    console.log("Frontend Next.js is online.");

    // 6. Run Pytest Suite & Coverage
    console.log("Running backend test suite (pytest)...");
    runCommandSafe(`${pytestPath} backend/tests/ --cov=backend --cov-report=json:reports/coverage/backend/coverage.json --cov-report=html:reports/coverage/backend/html`, { TESTING: "True" });

    // 7. Run Vitest Suite & Coverage
    console.log("Running frontend test suite (vitest)...");
    runCommandSafe("npm run test:unit -- --coverage");

    // 8. Run Lighthouse
    runCommandSafe("node scripts/run-lighthouse.mjs --url http://localhost:3005");

    // 9. Run Load Tests
    runCommandSafe(`node scripts/run-load-tests.mjs --pid ${backend.pid} --url http://localhost:8001`);

    // 10. Run DB Benchmarks
    runCommandSafe(`${pythonPath} scripts/run_db_benchmarks.py`);

    // 11. Run Cache Benchmarks
    runCommandSafe(`${pythonPath} scripts/run-cache-benchmarks.py`);

    // 12. Run Bundle Analysis
    runCommandSafe("node scripts/run-bundle-analysis.mjs");

    // 13. Run React rendering performance checks
    runCommandSafe("node scripts/run-react-analysis.mjs --url http://localhost:3005");

    // 14. Run Security Audit
    runCommandSafe("node scripts/run-security-audit.mjs");

    // 15. Run Accessibility audit (Axe-Core)
    runCommandSafe("node scripts/run-accessibility-audit.mjs --url http://localhost:3005");

    // 16. Run static quality metrics (radon, jscpd, eslint count)
    runCommandSafe("node scripts/run-static-analysis.mjs");

    // 17. Run Reliability failure injections
    runCommandSafe("node scripts/run-reliability-tests.mjs --url http://localhost:8001");

    // 18. Run Mutation checks
    runCommandSafe(`${pythonPath} scripts/run-mutation-testing.py`);

    // 19. Run architecture dependencies checking
    runCommandSafe("node scripts/validate-architecture.mjs");

    // 20. Run API Contract validation
    runCommandSafe("node scripts/validate-api-contracts.mjs");

    // 21. Run Soak stress test
    runCommandSafe(`node scripts/run-soak-testing.mjs --pid ${backend.pid} --url http://localhost:8001 --duration 10`);

    // 22. Generate resume summaries, bullets, and scorecards
    runCommandSafe("node scripts/generate-resume-metrics.mjs");
    runCommandSafe("node scripts/generate-resume-bullets.mjs");
    runCommandSafe("node scripts/generate-scorecard.mjs");
    runCommandSafe("node scripts/generate-improvements.mjs");

    // 23. Compile and Inline Dashboard Data
    console.log("Inlining benchmark results to HTML dashboard...");
    const dashboardPath = path.resolve("./reports/index.html");
    if (fs.existsSync(dashboardPath)) {
      const template = fs.readFileSync(dashboardPath, "utf-8");
      
      const scorecard = JSON.parse(fs.readFileSync("./reports/engineering-scorecard/scorecard.json", "utf-8"));
      const metrics = JSON.parse(fs.readFileSync("./resume_metrics.json", "utf-8"));
      const load = JSON.parse(fs.readFileSync("./reports/load-testing/summary.json", "utf-8"));
      const db = JSON.parse(fs.readFileSync("./reports/database/database_report.json", "utf-8"));
      const cache = JSON.parse(fs.readFileSync("./reports/cache/cache_benchmarks.json", "utf-8"));
      const bundle = JSON.parse(fs.readFileSync("./reports/bundle-analysis/bundle_analysis.json", "utf-8"));
      const security = JSON.parse(fs.readFileSync("./reports/security/security_report.json", "utf-8"));
      const accessibility = JSON.parse(fs.readFileSync("./reports/accessibility/accessibility_report.json", "utf-8"));
      
      const dataPayload = {
        scorecard,
        metrics,
        load,
        db,
        cache,
        bundle,
        security,
        accessibility,
        timestamp: new Date().toISOString()
      };
      
      const updatedDashboard = template.replace(/\/\*\s*DATA_PLACEHOLDER\s*\*\/[\s\S]*?(?=\s*\{)/, "")
                                       .replace(/const DATA = [\s\S]*?(?=;\s*function switchTab)/, `const DATA = ${JSON.stringify(dataPayload, null, 2)}`);
      
      fs.writeFileSync(dashboardPath, updatedDashboard);
    }

    // 24. Update badges in README.md
    runCommandSafe("node scripts/update-readme-badges.mjs");

  } finally {
    // 25. Graceful Teardown of background processes
    console.log("Shutting down benchmark environments...");
    try {
      if (process.platform === "win32") {
        execSync(`taskkill /pid ${backend.pid} /t /f`);
        execSync(`taskkill /pid ${frontend.pid} /t /f`);
      } else {
        process.kill(-backend.pid);
        process.kill(-frontend.pid);
      }
    } catch (e) {
      backend.kill("SIGKILL");
      frontend.kill("SIGKILL");
    }
    console.log("Teardown complete. All background servers terminated.");
  }
}

start();
