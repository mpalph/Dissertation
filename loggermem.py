# loggermem.py
# 🧠 Live ECU Memory Usage Monitor (No CPU Stats)
# ──────────────────────────────────────────────────────
# ✅ Tracks memory usage of all ECUs (Static + MTD)
# ✅ Matches by partial script path
# ✅ Clean single-line refresh every second

import psutil
import time
import datetime
import os

# 🔍 Static instance ECU script paths
STATIC_SWITCH_PATH = "Static/ECUs/HeadlampSwitch/headlamp_switch_ecu.py"
STATIC_HEADLAMP_PATH = "Static/ECUs/Headlamp/headlamp_ecu.py"
STATIC_FORCESENSOR_PATH = "Static/ECUs/ForceSensor/force_sensor_ecu.py"
STATIC_CRASHDETECTOR_PATH = "Static/ECUs/CrashDetector/crash_detector_ecu.py"
STATIC_AIRBAG_PATH = "Static/ECUs/Airbag/airbag_ecu.py"
STATIC_INDICATOR_SWITCH_PATH = "Static/ECUs/IndicatorSwitch/indicator_switch_ecu.py"
STATIC_LEFT_INDICATOR_PATH = "Static/ECUs/LeftIndicator/left_indicator_ecu.py"
STATIC_RIGHT_INDICATOR_PATH = "Static/ECUs/RightIndicator/right_indicator_ecu.py"

# 🔍 MTD instance ECU script paths
MTD_SWITCH_PATH = "MTD/ECUs/HeadlampSwitch/headlamp_switch_ecu.py"
MTD_HEADLAMP_PATH = "MTD/ECUs/Headlamp/headlamp_ecu.py"
MTD_FORCESENSOR_PATH = "MTD/ECUs/ForceSensor/force_sensor_ecu.py"
MTD_CRASHDETECTOR_PATH = "MTD/ECUs/CrashDetector/crash_detector_ecu.py"
MTD_AIRBAG_PATH = "MTD/ECUs/Airbag/airbag_ecu.py"
MTD_INDICATOR_SWITCH_PATH = "MTD/ECUs/IndicatorSwitch/indicator_switch_ecu.py"
MTD_LEFT_INDICATOR_PATH = "MTD/ECUs/LeftIndicator/left_indicator_ecu.py"
MTD_RIGHT_INDICATOR_PATH = "MTD/ECUs/RightIndicator/right_indicator_ecu.py"

def find_process_by_path(target_path):
    """
    Return a psutil.Process object matching the full path to the script.
    """
    for proc in psutil.process_iter(['cmdline']):
        try:
            if proc.info['cmdline'] and len(proc.info['cmdline']) > 1:
                script_path = proc.info['cmdline'][1]
                if target_path in script_path:
                    return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

def monitor_resources():
    print("[Logger] 🚀 Monitoring ECU memory usage...\nPress Ctrl+C to stop.\n")
    time.sleep(1)

    try:
        while True:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")

            # 🔍 Find each ECU process
            static_ecus = {
                "STATIC HEADLIGHT SWITCH ECU": find_process_by_path(STATIC_SWITCH_PATH),
                "STATIC HEADLAMP ECU": find_process_by_path(STATIC_HEADLAMP_PATH),
                "STATIC FORCE SENSOR ECU": find_process_by_path(STATIC_FORCESENSOR_PATH),
                "STATIC CRASH DETECTOR ECU": find_process_by_path(STATIC_CRASHDETECTOR_PATH),
                "STATIC AIRBAG ECU": find_process_by_path(STATIC_AIRBAG_PATH),
                "STATIC INDICATOR SWITCH ECU": find_process_by_path(STATIC_INDICATOR_SWITCH_PATH),
                "STATIC LEFT INDICATOR ECU": find_process_by_path(STATIC_LEFT_INDICATOR_PATH),
                "STATIC RIGHT INDICATOR ECU": find_process_by_path(STATIC_RIGHT_INDICATOR_PATH),
            }

            mtd_ecus = {
                "MTD HEADLIGHT SWITCH ECU": find_process_by_path(MTD_SWITCH_PATH),
                "MTD HEADLAMP ECU": find_process_by_path(MTD_HEADLAMP_PATH),
                "MTD FORCE SENSOR ECU": find_process_by_path(MTD_FORCESENSOR_PATH),
                "MTD CRASH DETECTOR ECU": find_process_by_path(MTD_CRASHDETECTOR_PATH),
                "MTD AIRBAG ECU": find_process_by_path(MTD_AIRBAG_PATH),
                "MTD INDICATOR SWITCH ECU": find_process_by_path(MTD_INDICATOR_SWITCH_PATH),
                "MTD LEFT INDICATOR ECU": find_process_by_path(MTD_LEFT_INDICATOR_PATH),
                "MTD RIGHT INDICATOR ECU": find_process_by_path(MTD_RIGHT_INDICATOR_PATH),
            }

            def get_mem(proc):
                if proc:
                    return proc.memory_info().rss / (1024 ** 2)  # MB
                else:
                    return 0.0

            # 🧹 Clear screen before reprinting
            os.system('clear')

            # 📊 Print memory usage
            print(f"[{timestamp}] ECU Memory Usage (MB)\n")

            print("── Static ECUs ───────────────────────────")
            for name, proc in static_ecus.items():
                print(f"{name:<30} -> {get_mem(proc):.2f} MB")
            print()

            print("── MTD ECUs ──────────────────────────────")
            for name, proc in mtd_ecus.items():
                print(f"{name:<30} -> {get_mem(proc):.2f} MB")

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[Logger] 🧯 Monitoring stopped.")

if __name__ == "__main__":
    monitor_resources()
