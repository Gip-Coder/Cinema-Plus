import autocannon from "autocannon";
import fs from "fs";
import path from "path";
import { execSync } from "child_process";

const reportsDir = path.resolve("./reports/load-testing");
if (!fs.existsSync(reportsDir)) {
  fs.mkdirSync(reportsDir, { recursive: true });
}

// Parse PID and URL arguments
const args = process.argv.slice(2);
let backendPid = null;
let baseUrl = "http://localhost:8001";

for (let i = 0; i < args.length; i++) {
  if (args[i] === "--pid" && args[i + 1]) {
    backendPid = parseInt(args[i + 1], 10);
  }
  if (args[i] === "--url" && args[i + 1]) {
    baseUrl = args[i + 1];
  }
}

const isWin = process.platform === "win32";
const pythonPath = fs.existsSync(path.resolve(isWin ? ".venv/Scripts/python.exe" : ".venv/bin/python"))
  ? path.resolve(isWin ? ".venv/Scripts/python.exe" : ".venv/bin/python")
  : "python";

function getTelemetry(pid) {
  if (!pid) return { process_cpu: 0, process_memory_mb: 0 };
  try {
    const output = execSync(`"${pythonPath}" scripts/get_system_telemetry.py ${pid}`, {
      env: { ...process.env, PYTHONPATH: "." }
    }).toString();
    const data = JSON.parse(output);
    if (data.success) {
      return {
        process_cpu: data.process_cpu,
        process_memory_mb: data.process_memory_mb
      };
    }
  } catch (err) {
    // Fail gracefully
  }
  return { process_cpu: 0, process_memory_mb: 0 };
}

const concurrencies = [25, 50, 100, 250, 500, 1000];
const results = [];

async function runBenchmark(concurrency) {
  console.log(`Running API load test for concurrency: ${concurrency}...`);
  
  // Track telemetry before/during load
  const backendPidOverride = backendPid;
  const initialTelemetry = getTelemetry(backendPidOverride);
  
  const instance = autocannon({
    url: `${baseUrl}/api/movies/`,
    connections: concurrency,
    duration: 5, // 5 seconds per run for fast automated execution
    headers: {
      "Content-Type": "application/json"
    }
  });

  return new Promise((resolve) => {
    autocannon.track(instance, { renderProgressBar: false });
    
    let midTelemetry = { process_cpu: 0, process_memory_mb: 0 };
    const checkInterval = setInterval(() => {
      const tel = getTelemetry(backendPidOverride);
      midTelemetry.process_cpu = Math.max(midTelemetry.process_cpu, tel.process_cpu);
      midTelemetry.process_memory_mb = Math.max(midTelemetry.process_memory_mb, tel.process_memory_mb);
    }, 1000);

    instance.on("done", (res) => {
      clearInterval(checkInterval);
      
      const finalTelemetry = getTelemetry(backendPidOverride);
      const avgCpu = (initialTelemetry.process_cpu + midTelemetry.process_cpu + finalTelemetry.process_cpu) / 3;
      const peakMemory = Math.max(initialTelemetry.process_memory_mb, midTelemetry.process_memory_mb, finalTelemetry.process_memory_mb);
      
      const errorRate = ((res.errors + res.timeouts) / (res.requests.sent || 1)) * 100;
      
      const record = {
        concurrency,
        average_latency_ms: res.latency && typeof res.latency.average === "number" ? res.latency.average : 0,
        p50_latency_ms: res.latency && typeof res.latency.p50 === "number" ? res.latency.p50 : 0,
        p90_latency_ms: res.latency && typeof res.latency.p90 === "number" ? res.latency.p90 : 0,
        p95_latency_ms: res.latency && typeof res.latency.p95 === "number" ? res.latency.p95 : 0,
        p99_latency_ms: res.latency && typeof res.latency.p99 === "number" ? res.latency.p99 : 0,
        requests_per_sec: res.requests && typeof res.requests.average === "number" ? res.requests.average : 0,
        throughput_mb_per_sec: res.throughput && typeof res.throughput.average === "number" ? (res.throughput.average / (1024 * 1024)).toFixed(3) : "0.000",
        error_rate_percent: errorRate ? errorRate.toFixed(2) : "0.00",
        cpu_utilization_percent: avgCpu ? avgCpu.toFixed(1) : "0.0",
        memory_utilization_mb: peakMemory ? peakMemory.toFixed(1) : "0.0",
        timestamp: new Date().toISOString()
      };
      
      fs.writeFileSync(
        path.join(reportsDir, `concurrency_${concurrency}.json`),
        JSON.stringify(res, null, 2)
      );
      
      results.push(record);
      console.log(`Completed concurrency ${concurrency}: Avg Latency: ${record.average_latency_ms}ms, RPS: ${record.requests_per_sec}`);
      resolve();
    });
  });
}

async function start() {
  for (const c of concurrencies) {
    await runBenchmark(c);
  }
  
  // Save summary JSON
  fs.writeFileSync(
    path.join(reportsDir, "summary.json"),
    JSON.stringify(results, null, 2)
  );

  // Generate Markdown report
  let md = `# API Load & Scalability Testing Report\n\n`;
  md += `*Timestamp:* ${new Date().toISOString()}\n`;
  md += `*Tool:* Autocannon (Node)\n\n`;
  md += `| Concurrency | Avg Latency (ms) | P50 (ms) | P95 (ms) | P99 (ms) | Requests/sec | Throughput (MB/s) | Error Rate (%) | Peak CPU (%) | Peak Mem (MB) |\n`;
  md += `|-------------|------------------|----------|----------|----------|--------------|-------------------|----------------|--------------|---------------|\n`;
  
  results.forEach(r => {
    md += `| ${r.concurrency} | ${r.average_latency_ms.toFixed(1)} | ${r.p50_latency_ms.toFixed(1)} | ${r.p95_latency_ms.toFixed(1)} | ${r.p99_latency_ms.toFixed(1)} | ${r.requests_per_sec.toFixed(1)} | ${r.throughput_mb_per_sec} | ${r.error_rate_percent}% | ${r.cpu_utilization_percent}% | ${r.memory_utilization_mb} |\n`;
  });
  
  fs.writeFileSync(path.join(reportsDir, "load_test_report.md"), md);
  console.log("Load testing completed and reports saved to /reports/load-testing/");
}

start();
