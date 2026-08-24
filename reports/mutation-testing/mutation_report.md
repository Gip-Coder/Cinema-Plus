# Mutation Testing Report

*Timestamp:* 2026-06-27T12:11:00Z
*Target Component:* `backend/utils/cache.py` (InMemoryCache)
*Test Runner:* pytest

* **Mutation Score (Killed Rate):** 0.0%
* **Mutants Killed:** 0
* **Mutants Survived:** 3

## Mutants Detailed Execution
| Mutant ID | Description | Status | Duration | Observations |
|-----------|-------------|--------|----------|--------------|
| 1 | Mutate cache expiry comparison: change '<' to '>' | **SURVIVED** | 3.82s | Survived - Test gaps identified |
| 2 | Mutate cache version check: change 'not key.endswith' to 'key.endswith' | **SURVIVED** | 3.90s | Survived - Test gaps identified |
| 3 | Mutate cache get fallback: change 'return None' to 'return data' | **SURVIVED** | 3.87s | Survived - Test gaps identified |
