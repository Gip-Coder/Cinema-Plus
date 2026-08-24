import os
import sys
import shutil
import subprocess
import json
import time

def run_mutation_tests():
    reports_dir = os.path.abspath("./reports/mutation-testing")
    os.makedirs(reports_dir, exist_ok=True)
    
    target_file = os.path.abspath("./backend/utils/cache.py")
    backup_file = target_file + ".bak"
    
    # Verify file exists
    if not os.path.exists(target_file):
        print(f"Target file {target_file} not found. Skipping mutation tests.")
        return
        
    # Create backup
    shutil.copyfile(target_file, backup_file)
    
    mutants = [
        {
            "id": 1,
            "description": "Mutate cache expiry comparison: change '<' to '>'",
            "target_line": "if time.time() < expiry:",
            "mutated_line": "if time.time() > expiry:"
        },
        {
            "id": 2,
            "description": "Mutate cache version check: change 'not key.endswith' to 'key.endswith'",
            "target_line": "if not key.endswith(f\":{self.version}\"):",
            "mutated_line": "if key.endswith(f\":{self.version}\"):"
        },
        {
            "id": 3,
            "description": "Mutate cache get fallback: change 'return None' to 'return data'",
            "target_line": "return None",
            "mutated_line": "return data"
        }
    ]
    
    killed = 0
    survived = 0
    results = []
    
    try:
        for m in mutants:
            print(f"Applying mutant {m['id']}: {m['description']}...")
            
            # Read and mutate
            with open(target_file, "r") as f:
                content = f.read()
                
            target_line = str(m["target_line"])
            mutated_line = str(m["mutated_line"])
            
            if target_line not in content:
                print(f"Target line not found in file. Skipping mutant {m['id']}.")
                continue
                
            mutated_content = content.replace(target_line, mutated_line, 1)
            
            with open(target_file, "w") as f:
                f.write(mutated_content)
                
            # Run pytest
            t_start = time.perf_counter()
            # Set TESTING=True env
            env = os.environ.copy()
            env["TESTING"] = "True"
            
            is_win = sys.platform == "win32"
            pytest_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".venv", "Scripts", "pytest.exe" if is_win else "bin/pytest"))
            if not os.path.exists(pytest_path):
                pytest_path = "pytest"
                
            # Run pytest with a timeout to avoid hanging
            process = subprocess.run(
                [pytest_path, "backend/tests/test_auth.py", "-q"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30
            )
            
            duration = time.perf_counter() - t_start
            
            # If pytest returns non-zero, it means the tests failed (mutant killed)
            # If pytest returns zero, it means the tests passed (mutant survived)
            is_killed = process.returncode != 0
            
            if is_killed:
                killed += 1
                status_str = "KILLED"
                print(f"Mutant {m['id']} was KILLED by tests in {duration:.2f}s.")
            else:
                survived += 1
                status_str = "SURVIVED"
                print(f"Mutant {m['id']} SURVIVED tests.")
                
            results.append({
                "mutant_id": m["id"],
                "description": m["description"],
                "status": status_str,
                "duration_sec": duration,
                "stdout_snippet": process.stdout[:150] if is_killed else ""
            })
            
            # Restore
            shutil.copyfile(backup_file, target_file)
            
    finally:
        # Clean up backup and ensure original is restored
        if os.path.exists(backup_file):
            shutil.copyfile(backup_file, target_file)
            os.remove(backup_file)
            
    score = (killed / (killed + survived) * 100) if (killed + survived) > 0 else 100
    
    output = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "mutation_score_percent": score,
        "mutants_killed": killed,
        "mutants_survived": survived,
        "mutants": results
    }
    
    with open(os.path.join(reports_dir, "mutation_report.json"), "w") as f:
        json.dump(output, f, indent=2)
        
    md = f"""# Mutation Testing Report

*Timestamp:* {output['timestamp']}
*Target Component:* `backend/utils/cache.py` (InMemoryCache)
*Test Runner:* pytest

* **Mutation Score (Killed Rate):** {output['mutation_score_percent']:.1f}%
* **Mutants Killed:** {output['mutants_killed']}
* **Mutants Survived:** {output['mutants_survived']}

## Mutants Detailed Execution
| Mutant ID | Description | Status | Duration | Observations |
|-----------|-------------|--------|----------|--------------|
"""
    for r in results:
        md += f"| {r['mutant_id']} | {r['description']} | **{r['status']}** | {r['duration_sec']:.2f}s | {'Killed by assertion failure' if r['status'] == 'KILLED' else 'Survived - Test gaps identified'} |\n"

    with open(os.path.join(reports_dir, "mutation_report.md"), "w") as f:
        f.write(md)
        
    print("Mutation testing completed and reports saved to /reports/mutation-testing/")

if __name__ == "__main__":
    run_mutation_tests()
