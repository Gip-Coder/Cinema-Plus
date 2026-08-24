import fs from "fs";
import path from "path";
import zlib from "zlib";

const reportsDir = path.resolve("./reports/bundle-analysis");
if (!fs.existsSync(reportsDir)) {
  fs.mkdirSync(reportsDir, { recursive: true });
}

function getFiles(dir, files = []) {
  if (!fs.existsSync(dir)) return files;
  const list = fs.readdirSync(dir);
  for (const item of list) {
    const fullPath = path.join(dir, item);
    if (fs.statSync(fullPath).isDirectory()) {
      getFiles(fullPath, files);
    } else {
      files.push(fullPath);
    }
  }
  return files;
}

function analyzeBundle() {
  console.log("Analyzing Next.js bundle output...");
  
  const staticDir = path.resolve("./.next/static");
  if (!fs.existsSync(staticDir)) {
    console.warn("WARNING: .next/static directory not found. Please run 'npm run build' first.");
    fs.writeFileSync(
      path.join(reportsDir, "bundle_report.md"),
      "# Bundle Analysis\n\n*Error: Next.js build output (.next/static) not found. Run npm run build first.*"
    );
    return;
  }

  const allFiles = getFiles(staticDir);
  const jsFiles = allFiles.filter(f => f.endsWith(".js"));
  const cssFiles = allFiles.filter(f => f.endsWith(".css"));

  let totalJsSize = 0;
  let totalJsGzip = 0;
  let totalJsBrotli = 0;
  
  let totalCssSize = 0;
  let totalCssGzip = 0;
  let totalCssBrotli = 0;

  const chunks = [];

  jsFiles.forEach(file => {
    const stats = fs.statSync(file);
    const content = fs.readFileSync(file);
    const gzip = zlib.gzipSync(content).length;
    const brotli = zlib.brotliCompressSync ? zlib.brotliCompressSync(content).length : gzip;

    totalJsSize += stats.size;
    totalJsGzip += gzip;
    totalJsBrotli += brotli;

    chunks.push({
      name: path.basename(file),
      type: "js",
      size: stats.size,
      gzip,
      brotli
    });
  });

  cssFiles.forEach(file => {
    const stats = fs.statSync(file);
    const content = fs.readFileSync(file);
    const gzip = zlib.gzipSync(content).length;
    const brotli = zlib.brotliCompressSync ? zlib.brotliCompressSync(content).length : gzip;

    totalCssSize += stats.size;
    totalCssGzip += gzip;
    totalCssBrotli += brotli;

    chunks.push({
      name: path.basename(file),
      type: "css",
      size: stats.size,
      gzip,
      brotli
    });
  });

  // Sort chunks by size
  chunks.sort((a, b) => b.size - a.size);

  // Scan duplicate packages in package-lock.json
  const duplicates = [];
  try {
    const lockfile = JSON.parse(fs.readFileSync("./package-lock.json", "utf-8"));
    const packages = lockfile.packages || {};
    const pkgCounts = {};
    
    Object.keys(packages).forEach(pkgPath => {
      if (!pkgPath) return;
      const parts = pkgPath.split("node_modules/");
      const name = parts[parts.length - 1];
      if (!name) return;
      const ver = packages[pkgPath].version;
      if (!pkgCounts[name]) pkgCounts[name] = new Set();
      pkgCounts[name].add(ver);
    });

    Object.keys(pkgCounts).forEach(name => {
      if (pkgCounts[name].size > 1) {
        duplicates.push({
          name,
          versions: Array.from(pkgCounts[name])
        });
      }
    });
  } catch (err) {
    // Fail gracefully
  }

  const results = {
    timestamp: new Date().toISOString(),
    total_js_kb: (totalJsSize / 1024).toFixed(1),
    total_js_gzip_kb: (totalJsGzip / 1024).toFixed(1),
    total_js_brotli_kb: (totalJsBrotli / 1024).toFixed(1),
    total_css_kb: (totalCssSize / 1024).toFixed(1),
    total_css_gzip_kb: (totalCssGzip / 1024).toFixed(1),
    total_css_brotli_kb: (totalCssBrotli / 1024).toFixed(1),
    duplicate_packages_count: duplicates.length,
    duplicate_packages: duplicates,
    largest_chunks: chunks.slice(0, 10)
  };

  fs.writeFileSync(
    path.join(reportsDir, "bundle_analysis.json"),
    JSON.stringify(results, null, 2)
  );

  let md = `# Advanced Bundle Analysis Report

*Timestamp:* ${results.timestamp}
*Auditor:* Static Next.js compilation parser

## Bundle Footprint Summary
* **Total JavaScript Size:** ${results.total_js_kb} KB (Gzip: ${results.total_js_gzip_kb} KB, Brotli: ${results.total_js_brotli_kb} KB)
* **Total Cascading Style Sheets Size:** ${results.total_css_kb} KB (Gzip: ${results.total_css_gzip_kb} KB, Brotli: ${results.total_css_brotli_kb} KB)
* **Duplicate npm Packages Detected:** ${results.duplicate_packages_count} packages

## Top 10 Largest Chunks
| Chunk Name | Type | Raw Size | Gzip Size | Brotli Size |
|------------|------|----------|-----------|-------------|
`;

  results.largest_chunks.forEach(c => {
    md += `| ${c.name} | ${c.type.toUpperCase()} | ${(c.size / 1024).toFixed(1)} KB | ${(c.gzip / 1024).toFixed(1)} KB | ${(c.brotli / 1024).toFixed(1)} KB |\n`;
  });

  md += `\n## Duplicate Dependencies Details\n`;
  if (duplicates.length === 0) {
    md += `*No duplicate packages detected in package-lock.json! Congratulations on perfect dependency isolation.*\n`;
  } else {
    duplicates.forEach(d => {
      md += `* **${d.name}:** Multiple versions found: [${d.versions.join(", ")}]\n`;
    });
  }

  fs.writeFileSync(path.join(reportsDir, "bundle_report.md"), md);

  // Create interactive HTML treemap
  const treemapHtml = `<!DOCTYPE html>
<html>
<head>
  <title>Bundle Size Treemap</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chartjs-chart-treemap@3.0.0"></script>
</head>
<body class="bg-zinc-950 text-zinc-100 p-8">
  <h1 class="text-3xl font-extrabold mb-4 tracking-wider text-red-500">NEXT.JS BUNDLE TREEMAP</h1>
  <p class="text-zinc-400 mb-8">Audited static chunk modules distribution for the Cinema Plus production bundle.</p>
  
  <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
    <div class="lg:col-span-2 bg-zinc-900/50 border border-white/[0.05] p-6 rounded-2xl">
      <h2 class="text-xl font-bold mb-4">Size Treemap</h2>
      <div style="height: 500px; position: relative;">
        <canvas id="treemapCanvas"></canvas>
      </div>
    </div>
    
    <div class="bg-zinc-900/50 border border-white/[0.05] p-6 rounded-2xl flex flex-col justify-between">
      <div>
        <h2 class="text-xl font-bold mb-4">Summary Statistics</h2>
        <div class="space-y-4">
          <div>
            <span class="text-zinc-500 text-sm">Total JS size</span>
            <div class="text-2xl font-semibold">${results.total_js_kb} KB</div>
          </div>
          <div>
            <span class="text-zinc-500 text-sm">JS Brotli size</span>
            <div class="text-2xl font-semibold text-green-400">${results.total_js_brotli_kb} KB</div>
          </div>
          <div>
            <span class="text-zinc-500 text-sm">Total CSS size</span>
            <div class="text-2xl font-semibold">${results.total_css_kb} KB</div>
          </div>
          <div>
            <span class="text-zinc-500 text-sm">Duplicates Count</span>
            <div class="text-2xl font-semibold text-amber-500">${results.duplicate_packages_count}</div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <script>
    const ctx = document.getElementById('treemapCanvas').getContext('2d');
    const chunks = ${JSON.stringify(chunks.slice(0, 30))};
    
    const chart = new Chart(ctx, {
      type: 'treemap',
      data: {
        datasets: [{
          label: 'JS & CSS Static Chunks',
          tree: chunks,
          key: 'size',
          groups: ['type', 'name'],
          borderWidth: 1,
          borderColor: '#18181b',
          backgroundColor: (ctx) => {
            if (ctx.type === 'data') {
              return ctx.raw._data.type === 'js' ? 'rgba(239, 68, 68, 0.7)' : 'rgba(59, 130, 246, 0.7)';
            }
            return 'rgba(255,255,255,0.1)';
          },
          spacing: 1
        }]
      },
      options: {
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              title: (items) => items[0].raw._data.name,
              label: (item) => 'Size: ' + (item.raw._data.size / 1024).toFixed(1) + ' KB'
            }
          }
        }
      }
    });
  </script>
</body>
</html>`;

  fs.writeFileSync(path.join(reportsDir, "index.html"), treemapHtml);
  console.log("Next.js bundle analysis completed and reports saved to /reports/bundle-analysis/");
}

analyzeBundle();
