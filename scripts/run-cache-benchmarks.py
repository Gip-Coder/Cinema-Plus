import os
import sys
import time
import json
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["TESTING"] = "True"

from backend.utils.cache import InMemoryCache

def run_cache_bench():
    reports_dir = os.path.abspath("./reports/cache")
    os.makedirs(reports_dir, exist_ok=True)

    cache = InMemoryCache(version="v1")
    
    # 1. Warm-up
    for i in range(100):
        cache.set(f"warmup:{i}", {"data": i}, ttl=10)
        
    # 2. Benchmark Write Latency
    t0 = time.perf_counter()
    iterations = 5000
    for i in range(iterations):
        cache.set(f"key:{i}", {"value": f"item_{i}" * 10}, ttl=60)
    t_write = (time.perf_counter() - t0) * 1000 # ms
    avg_write_ms = t_write / iterations

    # 3. Benchmark Hit Latency
    t0 = time.perf_counter()
    for i in range(iterations):
        val = cache.get(f"key:{i}")
    t_hit = (time.perf_counter() - t0) * 1000
    avg_hit_ms = t_hit / iterations

    # 4. Benchmark Miss Latency
    t0 = time.perf_counter()
    for i in range(iterations):
        val = cache.get(f"non_existent:{i}")
    t_miss = (time.perf_counter() - t0) * 1000
    avg_miss_ms = t_miss / iterations

    # 5. Measure Latency Reduction
    # Suppose a DB query takes 2.0 ms
    db_latency_estimate_ms = 2.0
    latency_reduction_percent = ((db_latency_estimate_ms - avg_hit_ms) / db_latency_estimate_ms) * 100

    # 6. Evaluate eviction and memory size
    initial_size = len(cache._cache)
    cache.invalidate("key:*")
    post_eviction_size = len(cache._cache)
    keys_evicted = initial_size - post_eviction_size

    # Memory usage approximation
    dict_bytes = sys.getsizeof(cache._cache)

    results = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_cache_size": initial_size,
        "write_latency_ms": avg_write_ms,
        "hit_latency_ms": avg_hit_ms,
        "miss_latency_ms": avg_miss_ms,
        "latency_reduction_percent": latency_reduction_percent,
        "keys_evicted": keys_evicted,
        "approx_dictionary_bytes": dict_bytes
    }

    with open(os.path.join(reports_dir, "cache_benchmarks.json"), "w") as f:
        json.dump(results, f, indent=2)

    md = f"""# Cache Efficiency & Benchmarks Report

*Timestamp:* {results['timestamp']}
*Target:* InMemoryCache (backend/utils/cache.py)

## Cache Latency Statistics
* **Average Write Latency:** {results['write_latency_ms']:.6f} ms
* **Average Hit Read Latency:** {results['hit_latency_ms']:.6f} ms
* **Average Miss Read Latency:** {results['miss_latency_ms']:.6f} ms
* **Relative Latency Reduction vs DB (estimated 2ms):** {results['latency_reduction_percent']:.2f}%

## Capacity & Eviction Auditing
* **Keys Populated:** {results['total_cache_size']} items
* **Keys Invalidated in Bulk (Pattern 'key:*'):** {results['keys_evicted']} items
* **Internal Registry Memory Footprint:** {results['approx_dictionary_bytes']} bytes
"""

    with open(os.path.join(reports_dir, "cache_report.md"), "w") as f:
        f.write(md)
        
    print("Caching benchmarks completed and saved to /reports/cache/")

if __name__ == "__main__":
    run_cache_bench()
