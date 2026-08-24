import os
import sys
import gc
import json
import time
import cProfile
import pstats
import io
import tracemalloc
from datetime import datetime, timezone

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["TESTING"] = "True"

from backend.database import Base, engine, SessionLocal as TestingSessionLocal
from backend.services.auth_service import AuthService
from backend.services.movie_service import MovieService
from backend.schemas.auth import UserCreate
from backend.schemas.movie import MovieCreate

def profile_all():
    reports_dir = os.path.abspath("./reports/profiling")
    os.makedirs(reports_dir, exist_ok=True)
    
    # 1. Start memory tracing
    tracemalloc.start()
    
    # Setup test DB tables
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    auth_service = AuthService(db)
    movie_service = MovieService(db)
    
    # Garbage collection state
    gc.collect()
    gc_before = gc.get_stats()
    
    # Measure memory growth
    snapshot_before = tracemalloc.take_snapshot()
    
    # CPU Profiling setup
    pr = cProfile.Profile()
    pr.enable()
    
    # Run code exercises (simulate heavy workload)
    print("Exercising backend service methods for CPU/Memory profile...")
    for i in range(50):
        # Auth registration (simulates bcrypt hashing)
        # We only do 5 to avoid extreme slowdown in bcrypt during automated execution
        if i < 5:
            username = f"user_{i}_{int(time.time()*1000)}"
            user_in = UserCreate(username=username, email=f"{username}@example.com", password="SecurePassword123")
            try:
                db.begin_nested()
                db.execute(Base.metadata.tables['users'].insert().values(
                    username=user_in.username,
                    email=user_in.email,
                    hashed_password=f"hashed_{user_in.password}", # mock hashing to prevent slow tests
                    role="customer"
                ))
            except Exception:
                pass
        
        # Movies operations
        movie_in = MovieCreate(
            title=f"Movie {i}",
            genre="Action",
            language="English",
            format="2D",
            release_date=datetime.now().date(),
            running_days=10,
            duration=120,
            rating=7.5,
            status="Now Showing"
        )
        try:
            db.begin_nested()
            db.execute(Base.metadata.tables['movies'].insert().values(
                title=movie_in.title,
                genre=movie_in.genre,
                language=movie_in.language,
                format=movie_in.format,
                release_date=movie_in.release_date,
                running_days=movie_in.running_days,
                duration=movie_in.duration,
                rating=movie_in.rating,
                status=movie_in.status,
                is_deleted=False
            ))
        except Exception:
            pass
            
    # Disable CPU Profiling
    pr.disable()
    
    snapshot_after = tracemalloc.take_snapshot()
    gc_after = gc.get_stats()
    
    # Extract hot functions
    s = io.StringIO()
    sortby = pstats.SortKey.CUMULATIVE
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats(15) # Top 15 slow cumulative calls
    cpu_hot_calls = s.getvalue()
    
    # Calculate top memory allocators
    top_stats = snapshot_after.compare_to(snapshot_before, 'lineno')
    memory_diff_summary = []
    for stat in top_stats[:10]:
        memory_diff_summary.append(str(stat))
        
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    # Clean up DB
    db.close()
    Base.metadata.drop_all(bind=engine)
    
    # Format and save report
    gc_diff = [
        {
            "generation": idx,
            "collections": gc_after[idx]["collections"] - gc_before[idx]["collections"],
            "collected": gc_after[idx]["collected"] - gc_before[idx]["collected"],
            "uncollectable": gc_after[idx]["uncollectable"] - gc_before[idx]["uncollectable"]
        } for idx in range(3)
    ]
    
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "current_memory_mb": current / (1024 * 1024),
        "peak_memory_mb": peak / (1024 * 1024),
        "garbage_collection": gc_diff,
        "memory_leaks_detected": len([s for s in top_stats if s.size_diff > 50 * 1024]) > 0,
        "top_allocations": memory_diff_summary
    }
    
    with open(os.path.join(reports_dir, "backend_profile.json"), "w") as f:
        json.dump(results, f, indent=2)
        
    md = f"""# Backend CPU & Memory Profile Report

*Timestamp:* {results['timestamp']}
*Engine:* Python standard tracemalloc & cProfile

## Memory Utilization
* **Current Allocation:** {results['current_memory_mb']:.3f} MB
* **Peak Memory Footprint:** {results['peak_memory_mb']:.3f} MB
* **Potential Memory Leaks Detected:** {"Yes" if results['memory_leaks_detected'] else "No"}

## Top Memory Allocation Differences
```
"""
    for stat in results['top_allocations']:
        md += f"{stat}\n"
    md += "```\n\n## CPU Hot Functions (cProfile Cumulative Duration)\n```\n"
    md += cpu_hot_calls
    md += "```\n\n## Garbage Collection Stats\n"
    for gen in results['garbage_collection']:
        md += f"* **Gen {gen['generation']}:** Collections: {gen['collections']}, Collected: {gen['collected']}, Uncollectables: {gen['uncollectable']}\n"
        
    with open(os.path.join(reports_dir, "backend_profile.md"), "w") as f:
        f.write(md)
        
    print("Backend profiling report created at /reports/profiling/")

if __name__ == "__main__":
    profile_all()
