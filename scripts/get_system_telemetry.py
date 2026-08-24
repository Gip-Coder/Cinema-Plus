import sys
import json
import psutil

def get_telemetry(pid):
    try:
        proc = psutil.Process(pid)
        with proc.oneshot():
            cpu_percent = proc.cpu_percent(interval=0.1)
            mem_info = proc.memory_info()
            mem_rss = mem_info.rss / (1024 * 1024) # MB
            system_cpu = psutil.cpu_percent()
            system_mem = psutil.virtual_memory().percent
            
        return {
            "success": True,
            "pid": pid,
            "process_cpu": cpu_percent,
            "process_memory_mb": mem_rss,
            "system_cpu": system_cpu,
            "system_memory": system_mem
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "No PID provided"}))
        sys.exit(1)
    try:
        pid = int(sys.argv[1])
        print(json.dumps(get_telemetry(pid)))
    except ValueError:
        print(json.dumps({"success": False, "error": "Invalid PID format"}))
        sys.exit(1)
