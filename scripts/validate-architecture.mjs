import fs from "fs";
import path from "path";

const reportsDir = path.resolve("./reports/architecture");
if (!fs.existsSync(reportsDir)) {
  fs.mkdirSync(reportsDir, { recursive: true });
}

function getFiles(dir, extFilter, files = []) {
  if (!fs.existsSync(dir)) return files;
  const list = fs.readdirSync(dir);
  for (const item of list) {
    const fullPath = path.join(dir, item);
    if (fs.statSync(fullPath).isDirectory()) {
      if (!["node_modules", ".next", ".git", ".venv", "reports"].includes(item)) {
        getFiles(fullPath, extFilter, files);
      }
    } else {
      if (extFilter.some(ext => item.endsWith(ext))) {
        files.push(fullPath);
      }
    }
  }
  return files;
}

function checkCycle(graph) {
  const visited = new Set();
  const recStack = new Set();
  const cycles = [];

  function dfs(node, pathStack) {
    visited.add(node);
    recStack.add(node);
    pathStack.push(node);

    const neighbors = graph[node] || [];
    for (const neighbor of neighbors) {
      if (!visited.has(neighbor)) {
        dfs(neighbor, pathStack);
      } else if (recStack.has(neighbor)) {
        const cyclePath = pathStack.slice(pathStack.indexOf(neighbor));
        cyclePath.push(neighbor);
        cycles.push(cyclePath);
      }
    }

    recStack.delete(node);
    pathStack.pop();
  }

  for (const node of Object.keys(graph)) {
    if (!visited.has(node)) {
      dfs(node, []);
    }
  }

  return cycles;
}

function validateArchitecture() {
  console.log("Validating architecture patterns and checking import cycles...");

  const pythonFiles = getFiles("./backend", [".py"]);
  const tsFiles = getFiles("./src", [".ts", ".tsx"]);

  const backendGraph = {};
  const frontendGraph = {};
  const layerViolations = [];

  // Parse Python imports
  pythonFiles.forEach(file => {
    const relativePath = path.relative(".", file).replace(/\\/g, "/");
    const moduleName = relativePath.replace(".py", "").replace(/\//g, ".");
    backendGraph[moduleName] = [];

    const content = fs.readFileSync(file, "utf-8");
    const lines = content.split("\n");

    lines.forEach(line => {
      // e.g., from backend.models.booking import Booking
      // e.g., import backend.database
      const fromMatch = line.match(/^\s*from\s+(backend\.[a-zA-Z0-9_\.]+)\s+import/);
      const importMatch = line.match(/^\s*import\s+(backend\.[a-zA-Z0-9_\.]+)/);
      
      const target = fromMatch ? fromMatch[1] : (importMatch ? importMatch[1] : null);
      if (target) {
        backendGraph[moduleName].push(target);
        
        // Check Layer Violations
        // Database Models importing routes or services
        if (moduleName.includes(".models.") && (target.includes(".routes.") || target.includes(".services."))) {
          layerViolations.push({
            file: relativePath,
            rule: "Database Layer Violation",
            detail: `Database model imports presentation/business logic layer: '${target}'`
          });
        }
        // Core/Database layer importing controllers/routes
        if (moduleName.includes(".database") && target.includes(".routes.")) {
          layerViolations.push({
            file: relativePath,
            rule: "Database Layer Violation",
            detail: `Database module imports route logic layer: '${target}'`
          });
        }
      }
    });
  });

  // Parse Frontend TS/TSX imports
  tsFiles.forEach(file => {
    const relativePath = path.relative(".", file).replace(/\\/g, "/");
    frontendGraph[relativePath] = [];

    const content = fs.readFileSync(file, "utf-8");
    const lines = content.split("\n");

    lines.forEach(line => {
      // e.g., import { ... } from "@/components/..."
      // e.g., import ... from "../lib/..."
      const match = line.match(/from\s+['"](@\/|\.\.\/|\.\/)([^'"]+)['"]/);
      if (match) {
        let target = match[1] + match[2];
        frontendGraph[relativePath].push(target);

        // Check if frontend imports backend code
        if (target.includes("backend/")) {
          layerViolations.push({
            file: relativePath,
            rule: "Client-Server Leak",
            detail: `Frontend code directly imports backend source file: '${target}'`
          });
        }
      }
    });
  });

  const backendCycles = checkCycle(backendGraph);
  const frontendCycles = checkCycle(frontendGraph);

  const results = {
    timestamp: new Date().toISOString(),
    backend_cycles_count: backendCycles.length,
    backend_cycles: backendCycles,
    frontend_cycles_count: frontendCycles.length,
    frontend_cycles: frontendCycles,
    layer_violations_count: layerViolations.length,
    layer_violations: layerViolations
  };

  fs.writeFileSync(
    path.join(reportsDir, "architecture_report.json"),
    JSON.stringify(results, null, 2)
  );

  // Generate Mermaid Diagram
  let mermaid = "graph TD\n";
  mermaid += "  subgraph Presentation [Presentation Layer]\n";
  mermaid += "    routes[backend/routes]\n";
  mermaid += "  end\n";
  mermaid += "  subgraph Business [Business Logic Layer]\n";
  mermaid += "    services[backend/services]\n";
  mermaid += "  end\n";
  mermaid += "  subgraph Data [Data Access Layer]\n";
  mermaid += "    models[backend/models]\n";
  mermaid += "    db[backend/database.py]\n";
  mermaid += "  end\n";
  mermaid += "  routes --> services\n";
  mermaid += "  services --> models\n";
  mermaid += "  services --> db\n";
  mermaid += "  models --> db\n";

  let md = `# Architecture Validation Report

*Timestamp:* ${results.timestamp}
*Method:* Directed Import Graph Cycle Search & Layer Constraints Checker

## Integrity Checklist
* **Backend Import Cycles (Circular Dependencies):** ${results.backend_cycles_count} cycles detected
* **Frontend Import Cycles:** ${results.frontend_cycles_count} cycles detected
* **Architecture Layer Violations:** ${results.layer_violations_count} issues flagged

## Layer Isolation Auditing
`;

  if (layerViolations.length === 0) {
    md += "*No layer boundary violations found! Solid architectural partitioning verified.*\n";
  } else {
    md += "| File Location | Rule Violated | Explanation |\n|---------------|---------------|-------------|\n";
    layerViolations.forEach(v => {
      md += `| ${v.file} | **${v.rule}** | ${v.detail} |\n`;
    });
  }

  md += `\n## Circular Dependency Audits\n`;
  if (backendCycles.length === 0 && frontendCycles.length === 0) {
    md += "*No circular imports or import loops detected. Clean dependency graph! Only direct, acyclic dependency hierarchies found.*\n";
  } else {
    if (backendCycles.length > 0) {
      md += `### Backend Import Loops\n`;
      backendCycles.forEach((c, idx) => {
        md += `* **Loop ${idx + 1}:** ${c.join(" ➔ ")}\n`;
      });
    }
  }

  md += `\n## Conceptual Component Dependencies Map (Mermaid)\n\`\`\`mermaid\n${mermaid}\`\`\`\n`;

  fs.writeFileSync(path.join(reportsDir, "architecture_report.md"), md);
  console.log("Architecture validation completed and reports saved to /reports/architecture/");
}

validateArchitecture();
