import fs from "fs";
import path from "path";

const reportsDir = path.resolve("./reports/api-contracts");
if (!fs.existsSync(reportsDir)) {
  fs.mkdirSync(reportsDir, { recursive: true });
}

function getFiles(dir, extFilter, files = []) {
  if (!fs.existsSync(dir)) return files;
  const list = fs.readdirSync(dir);
  for (const item of list) {
    const fullPath = path.join(dir, item);
    if (fs.statSync(fullPath).isDirectory()) {
      getFiles(fullPath, extFilter, files);
    } else {
      if (extFilter.some(ext => item.endsWith(ext))) {
        files.push(fullPath);
      }
    }
  }
  return files;
}

function validateContracts() {
  console.log("Analyzing API Contract Compatibility...");

  // 1. Extract frontend endpoints from src/lib/api/routes.ts
  const routesPath = path.resolve("./src/lib/api/routes.ts");
  const frontendEndpoints = new Set();
  
  if (fs.existsSync(routesPath)) {
    const content = fs.readFileSync(routesPath, "utf-8");
    // Find strings like "/api/auth/me", "/api/movies/"
    // Match strings starting with /api/ or just /
    const regex = /['"](\/(api|health|auth|movies|bookings|tickets|admin|schedule|reviews|reservations|layouts)[a-zA-Z0-9_\-\/\.\d:\*\{\}]+)['"]/g;
    let match;
    while ((match = regex.exec(content)) !== null) {
      // Normalize parameter segments like ${movieId} or \d+ to generic {id}
      let cleaned = match[1]
        .replace(/\/\$\{?[a-zA-Z0-9_]+\}?/g, "/{id}")
        .replace(/\/\d+/g, "/{id}")
        .replace(/\/$/, "");
      if (!cleaned) cleaned = "/";
      frontendEndpoints.add(cleaned);
    }
  }

  // 2. Scan backend route files to find matching endpoints
  const backendEndpoints = new Set();
  const backendRoutesDir = path.resolve("./backend/routes");
  const pyFiles = getFiles(backendRoutesDir, [".py"]);
  pyFiles.push(path.resolve("./backend/main.py"));

  pyFiles.forEach(file => {
    const content = fs.readFileSync(file, "utf-8");
    const lines = content.split("\n");
    
    // Find router prefix in this file (e.g. prefix="/api/auth", prefix="/api/movies")
    // e.g. app.include_router(auth_routes.router, prefix="/api/auth", tags=["Authentication"])
    let prefix = "";
    if (file.endsWith("main.py")) {
      // We process main.py route registrations
      lines.forEach(line => {
        const includeMatch = line.match(/app\.include_router\([^,]+,\s*prefix=["']([^"']+)["']/);
        if (includeMatch) {
          // e.g. maps auth_routes -> /api/auth
        }
      });
    }

    // Determine default prefix from filename if routes file
    const basename = path.basename(file, ".py");
    if (basename.includes("auth_routes")) prefix = "/api/auth";
    else if (basename.includes("movie_routes")) prefix = "/api/movies";
    else if (basename.includes("booking_routes")) prefix = "/api/bookings";
    else if (basename.includes("ticket_routes")) prefix = "/api/tickets";
    else if (basename.includes("admin_routes")) prefix = "/api/admin";
    else if (basename.includes("schedule_routes")) prefix = "/api/schedule";
    else if (basename.includes("review_routes")) prefix = "/api/reviews";
    else if (basename.includes("reservation_routes")) prefix = "/api";
    else if (basename.includes("layout_routes")) prefix = "/api/layouts";

    lines.forEach(line => {
      // Find decorator: @router.get("/...")
      const routeMatch = line.match(/@router\.(get|post|put|delete)\(["']([^"']+)["']/);
      if (routeMatch) {
        let endpointPath = routeMatch[2];
        // Combine prefix + endpointPath
        let fullPath = (prefix + (endpointPath === "/" ? "" : endpointPath))
          .replace(/\/\{[a-zA-Z0-9_]+\}/g, "/{id}")
          .replace(/\/$/, "");
        if (!fullPath) fullPath = "/";
        backendEndpoints.add(fullPath);
      }
      
      // Also check root decorators in main.py
      if (file.endsWith("main.py")) {
        const rootMatch = line.match(/@app\.(get|post|put|delete)\(["']([^"']+)["']/);
        if (rootMatch) {
          backendEndpoints.add(rootMatch[2].replace(/\/$/, "") || "/");
        }
      }
    });
  });

  // Compare contracts
  const missingInBackend = [];
  frontendEndpoints.forEach(fe => {
    // Check direct matching or parameter matches
    if (!backendEndpoints.has(fe)) {
      missingInBackend.push(fe);
    }
  });

  const results = {
    timestamp: new Date().toISOString(),
    frontend_endpoints_count: frontendEndpoints.size,
    backend_endpoints_count: backendEndpoints.size,
    mismatched_endpoints_count: missingInBackend.length,
    mismatched_endpoints: missingInBackend,
    frontend_endpoints: Array.from(frontendEndpoints),
    backend_endpoints: Array.from(backendEndpoints)
  };

  fs.writeFileSync(
    path.join(reportsDir, "api_contracts.json"),
    JSON.stringify(results, null, 2)
  );

  let md = `# API Contract Validation Report

*Timestamp:* ${results.timestamp}
*Method:* Route Schema Decorators vs Client Endpoint Declarations

* **Client Routes Inspected:** ${results.frontend_endpoints_count} endpoints
* **Server Routes Found:** ${results.backend_endpoints_count} endpoints
* **Mismatched / Missing Endpoints:** ${results.mismatched_endpoints_count} issues

## Mismatched Endpoints Audit
`;

  if (missingInBackend.length === 0) {
    md += "*All frontend API calls mapped perfectly to server router paths. API contracts are 100% synchronized!*\n";
  } else {
    md += "| Mismatched Client Route Path | Recommendation |\n|-----------------------------|----------------|\n";
    missingInBackend.forEach(path => {
      md += `| \`${path}\` | Verify if backend exposes this route or check path parameters definitions |\n`;
    });
  }

  md += `\n## Inspected Server Route Catalog\n`;
  Array.from(backendEndpoints).sort().forEach(e => {
    md += `* \`${e}\`\n`;
  });

  fs.writeFileSync(path.join(reportsDir, "api_contracts_report.md"), md);
  console.log("API contract validation completed and reports saved to /reports/api-contracts/");
}

validateContracts();
