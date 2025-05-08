# logger.py
# 🧠 Live System + ECU Resource Monitor (Terminal Only)
# ──────────────────────────────────────────────────────
# ✅ Tracks memory usage of both ECUs individually
# ✅ Matches by absolute script paths
# ✅ Prints clean output (one block per process)

import psutil
import time
import datetime

# 🔍 Full paths to each ECU script (adjust if your project path changes)
SWITCH_PATH = "/ECUs/HeadlampSwitch/headlamp_switch_ecu.py"
HEADLAMP_PATH = "ECUs/Headlamp/headlamp_ecu.py"

def find_process_by_path(target_path):
    """
    Return a psutil.Process object matching the full path to the script.
    """
    for proc in psutil.process_iter(['cmdline']):
        try:
            if proc.info['cmdline'] and len(proc.info['cmdline']) > 1:
                script_path = proc.info['cmdline'][1]
                if script_path == target_path:
                    return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

def monitor_resources():
    print("[Logger] 🚀 Monitoring system + ECU resources...\nPress Ctrl+C to stop.\n")

    try:
        while True:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")

            # 🌐 System-wide metrics
            cpu_system = psutil.cpu_percent(interval=0.1)
            mem_system = psutil.virtual_memory().percent

            # 🔍 ECU process metrics
            switch_proc = find_process_by_path(SWITCH_PATH)
            headlamp_proc = find_process_by_path(HEADLAMP_PATH)

            switch_cpu, switch_mem = (0.0, 0.0)
            headlamp_cpu, headlamp_mem = (0.0, 0.0)

            if switch_proc:
                switch_cpu = switch_proc.cpu_percent(interval=0.1)
                switch_mem = switch_proc.memory_info().rss / (1024 ** 2)

            if headlamp_proc:
                headlamp_cpu = headlamp_proc.cpu_percent(interval=0.1)
                headlamp_mem = headlamp_proc.memory_info().rss / (1024 ** 2)

            # 📊 Print everything in a clean format
            print(f"\n[{timestamp}] SYSTEM Resources")
            print(f"CPU Usage: {cpu_system:.1f}%   |   Memory Usage: {mem_system:.1f}%")

            print(f"\n[{timestamp}] SWITCH ECU")
            print(f"CPU Usage: {switch_cpu:.1f}%   |   Memory Usage: {switch_mem:.2f} MB")

            print(f"\n[{timestamp}] HEADLAMP ECU")
            print(f"CPU Usage: {headlamp_cpu:.1f}%   |   Memory Usage: {headlamp_mem:.2f} MB")

            print("\n" + "-"*50)

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[Logger] 🧯 Monitoring stopped.")

if __name__ == "__main__":
    monitor_resources()
