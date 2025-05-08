# logger.py
# 🧠 ECU Memory + Instant Latency Monitor (Static + MTD)
# ───────────────────────────────────────────────────────────
# ✅ Memory updates every 1s
# ✅ Latency updates immediately after CAN responses
# ✅ No lag, no flickering, clean terminal layout

import psutil
import time
import datetime
import os
import can
import threading
import sys
from Crypto.Cipher import AES

# 🛡️ AES Shared Key for MTD
AES_KEY = b'SecureECUSharedK'

# 📡 CAN IDs
CONTROL_ID = 0x001
STATUS_ID_HEADLAMP_ECU = 0x301
STATUS_ID_AIRBAG_ECU = 0x501
STATUS_ID_LEFT_INDICATOR = 0x602
STATUS_ID_RIGHT_INDICATOR = 0x603

# 🔍 Static ECU paths
STATIC_SWITCH_PATH = "Static/ECUs/HeadlampSwitch/headlamp_switch_ecu.py"
STATIC_HEADLAMP_PATH = "Static/ECUs/Headlamp/headlamp_ecu.py"
STATIC_FORCESENSOR_PATH = "Static/ECUs/ForceSensor/force_sensor_ecu.py"
STATIC_CRASHDETECTOR_PATH = "Static/ECUs/CrashDetector/crash_detector_ecu.py"
STATIC_AIRBAG_PATH = "Static/ECUs/Airbag/airbag_ecu.py"
STATIC_LEFT_INDICATOR_PATH = "Static/ECUs/LeftIndicator/left_indicator_ecu.py"
STATIC_RIGHT_INDICATOR_PATH = "Static/ECUs/RightIndicator/right_indicator_ecu.py"
STATIC_INDICATOR_SWITCH_PATH = "Static/ECUs/IndicatorSwitch/indicator_switch_ecu.py"

# 🔍 MTD ECU paths
MTD_SWITCH_PATH = "MTD/ECUs/HeadlampSwitch/headlamp_switch_ecu.py"
MTD_HEADLAMP_PATH = "MTD/ECUs/Headlamp/headlamp_ecu.py"
MTD_FORCESENSOR_PATH = "MTD/ECUs/ForceSensor/force_sensor_ecu.py"
MTD_CRASHDETECTOR_PATH = "MTD/ECUs/CrashDetector/crash_detector_ecu.py"
MTD_AIRBAG_PATH = "MTD/ECUs/Airbag/airbag_ecu.py"
MTD_LEFT_INDICATOR_PATH = "MTD/ECUs/LeftIndicator/left_indicator_ecu.py"
MTD_RIGHT_INDICATOR_PATH = "MTD/ECUs/RightIndicator/right_indicator_ecu.py"
MTD_INDICATOR_SWITCH_PATH = "MTD/ECUs/IndicatorSwitch/indicator_switch_ecu.py"

# 📈 Memory and Latency Storage
memory_data = {}
latency_data = {}

# ⏱️ Latency Timing
last_trigger = {
    "STATIC_HEADLAMP": None,
    "MTD_HEADLAMP": None,
    "STATIC_AIRBAG": None,
    "MTD_AIRBAG": None,
    "STATIC_LEFT_INDICATOR": None,
    "MTD_LEFT_INDICATOR": None,
    "STATIC_RIGHT_INDICATOR": None,
    "MTD_RIGHT_INDICATOR": None,
}

# Lock to protect data
data_lock = threading.Lock()

def decrypt_id(arbitration_id):
    if arbitration_id == CONTROL_ID:
        return CONTROL_ID
    now = time.localtime()
    seed = (now.tm_min * 60 + now.tm_sec).to_bytes(16, byteorder='big')
    cipher = AES.new(AES_KEY, AES.MODE_ECB)
    encrypted = cipher.encrypt(seed)
    mask = int.from_bytes(encrypted[:2], byteorder='big') & 0x7FF
    return arbitration_id ^ mask

def find_process_by_path(target_path):
    for proc in psutil.process_iter(['cmdline']):
        try:
            if proc.info['cmdline'] and len(proc.info['cmdline']) > 1:
                if target_path in proc.info['cmdline'][1]:
                    return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

def monitor_memory():
    while True:
        processes = {
            # Static
            "STATIC_SWITCH": find_process_by_path(STATIC_SWITCH_PATH),
            "STATIC_HEADLAMP": find_process_by_path(STATIC_HEADLAMP_PATH),
            "STATIC_FORCESENSOR": find_process_by_path(STATIC_FORCESENSOR_PATH),
            "STATIC_CRASHDETECTOR": find_process_by_path(STATIC_CRASHDETECTOR_PATH),
            "STATIC_AIRBAG": find_process_by_path(STATIC_AIRBAG_PATH),
            "STATIC_LEFT_INDICATOR": find_process_by_path(STATIC_LEFT_INDICATOR_PATH),
            "STATIC_RIGHT_INDICATOR": find_process_by_path(STATIC_RIGHT_INDICATOR_PATH),
            "STATIC_INDICATOR_SWITCH": find_process_by_path(STATIC_INDICATOR_SWITCH_PATH),
            # MTD
            "MTD_SWITCH": find_process_by_path(MTD_SWITCH_PATH),
            "MTD_HEADLAMP": find_process_by_path(MTD_HEADLAMP_PATH),
            "MTD_FORCESENSOR": find_process_by_path(MTD_FORCESENSOR_PATH),
            "MTD_CRASHDETECTOR": find_process_by_path(MTD_CRASHDETECTOR_PATH),
            "MTD_AIRBAG": find_process_by_path(MTD_AIRBAG_PATH),
            "MTD_LEFT_INDICATOR": find_process_by_path(MTD_LEFT_INDICATOR_PATH),
            "MTD_RIGHT_INDICATOR": find_process_by_path(MTD_RIGHT_INDICATOR_PATH),
            "MTD_INDICATOR_SWITCH": find_process_by_path(MTD_INDICATOR_SWITCH_PATH),
        }
        with data_lock:
            for name, proc in processes.items():
                if proc:
                    memory_data[name] = proc.memory_info().rss / (1024 ** 2)
                else:
                    memory_data[name] = 0.0
        time.sleep(1)

def monitor_latency():
    bus = can.interface.Bus(channel="vcan0", interface="socketcan")
    while True:
        msg = bus.recv(timeout=0.0001)
        if msg:
            now = time.perf_counter()
            raw_id = msg.arbitration_id
            decoded_id = decrypt_id(raw_id)
            with data_lock:
                if raw_id == CONTROL_ID:
                    command = msg.data[0]
                    if command == 0x02:  # Headlamp toggle
                        last_trigger["STATIC_HEADLAMP"] = now
                        last_trigger["MTD_HEADLAMP"] = now
                        latency_data["STATIC_HEADLAMP"] = "waiting..."
                        latency_data["MTD_HEADLAMP"] = "waiting..."
                    elif command == 0x03:  # Crash
                        last_trigger["STATIC_AIRBAG"] = now
                        last_trigger["MTD_AIRBAG"] = now
                        latency_data["STATIC_AIRBAG"] = "waiting..."
                        latency_data["MTD_AIRBAG"] = "waiting..."
                    elif command == 0x04:  # Left Indicator
                        last_trigger["STATIC_LEFT_INDICATOR"] = now
                        last_trigger["MTD_LEFT_INDICATOR"] = now
                        latency_data["STATIC_LEFT_INDICATOR"] = "waiting..."
                        latency_data["MTD_LEFT_INDICATOR"] = "waiting..."
                    elif command == 0x05:  # Right Indicator
                        last_trigger["STATIC_RIGHT_INDICATOR"] = now
                        last_trigger["MTD_RIGHT_INDICATOR"] = now
                        latency_data["STATIC_RIGHT_INDICATOR"] = "waiting..."
                        latency_data["MTD_RIGHT_INDICATOR"] = "waiting..."

                # Handle ECU responses
                elif raw_id == STATUS_ID_HEADLAMP_ECU and last_trigger["STATIC_HEADLAMP"]:
                    latency = (now - last_trigger["STATIC_HEADLAMP"]) * 1000
                    latency_data["STATIC_HEADLAMP"] = f"{latency:.2f} ms"
                    last_trigger["STATIC_HEADLAMP"] = None
                elif decoded_id == STATUS_ID_HEADLAMP_ECU and last_trigger["MTD_HEADLAMP"]:
                    latency = (now - last_trigger["MTD_HEADLAMP"]) * 1000
                    latency_data["MTD_HEADLAMP"] = f"{latency:.2f} ms"
                    last_trigger["MTD_HEADLAMP"] = None
                elif raw_id == STATUS_ID_AIRBAG_ECU and last_trigger["STATIC_AIRBAG"]:
                    if msg.data[0] == 0x01:
                        latency = (now - last_trigger["STATIC_AIRBAG"]) * 1000
                        latency_data["STATIC_AIRBAG"] = f"{latency:.2f} ms"
                        last_trigger["STATIC_AIRBAG"] = None
                elif decoded_id == STATUS_ID_AIRBAG_ECU and last_trigger["MTD_AIRBAG"]:
                    if msg.data[0] == 0x01:
                        latency = (now - last_trigger["MTD_AIRBAG"]) * 1000
                        latency_data["MTD_AIRBAG"] = f"{latency:.2f} ms"
                        last_trigger["MTD_AIRBAG"] = None
                elif raw_id == STATUS_ID_LEFT_INDICATOR and last_trigger["STATIC_LEFT_INDICATOR"]:
                    if msg.data[0] == 0x01:
                        latency = (now - last_trigger["STATIC_LEFT_INDICATOR"]) * 1000
                        latency_data["STATIC_LEFT_INDICATOR"] = f"{latency:.2f} ms"
                        last_trigger["STATIC_LEFT_INDICATOR"] = None
                elif decoded_id == STATUS_ID_LEFT_INDICATOR and last_trigger["MTD_LEFT_INDICATOR"]:
                    if msg.data[0] == 0x01:
                        latency = (now - last_trigger["MTD_LEFT_INDICATOR"]) * 1000
                        latency_data["MTD_LEFT_INDICATOR"] = f"{latency:.2f} ms"
                        last_trigger["MTD_LEFT_INDICATOR"] = None
                elif raw_id == STATUS_ID_RIGHT_INDICATOR and last_trigger["STATIC_RIGHT_INDICATOR"]:
                    if msg.data[0] == 0x01:
                        latency = (now - last_trigger["STATIC_RIGHT_INDICATOR"]) * 1000
                        latency_data["STATIC_RIGHT_INDICATOR"] = f"{latency:.2f} ms"
                        last_trigger["STATIC_RIGHT_INDICATOR"] = None
                elif decoded_id == STATUS_ID_RIGHT_INDICATOR and last_trigger["MTD_RIGHT_INDICATOR"]:
                    if msg.data[0] == 0x01:
                        latency = (now - last_trigger["MTD_RIGHT_INDICATOR"]) * 1000
                        latency_data["MTD_RIGHT_INDICATOR"] = f"{latency:.2f} ms"
                        last_trigger["MTD_RIGHT_INDICATOR"] = None

def display_loop():
    print("[Logger] 🚀 Monitoring ECU memory + latency...\nPress Ctrl+C to stop.\n")
    time.sleep(1)
    while True:
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        with data_lock:
            os.system('clear')
            print(f"[{timestamp}] ECU Resource Monitor\n")

            # Static
            print(f"STATIC HEADLIGHT SWITCH ECU -> {memory_data.get('STATIC_SWITCH', 0):.2f} MB")
            print(f"STATIC HEADLAMP ECU         -> {memory_data.get('STATIC_HEADLAMP', 0):.2f} MB")
            print(f"STATIC FORCE SENSOR ECU     -> {memory_data.get('STATIC_FORCESENSOR', 0):.2f} MB")
            print(f"STATIC CRASH DETECTOR ECU   -> {memory_data.get('STATIC_CRASHDETECTOR', 0):.2f} MB")
            print(f"STATIC AIRBAG ECU           -> {memory_data.get('STATIC_AIRBAG', 0):.2f} MB")
            print(f"STATIC LEFT INDICATOR ECU   -> {memory_data.get('STATIC_LEFT_INDICATOR', 0):.2f} MB")
            print(f"STATIC RIGHT INDICATOR ECU  -> {memory_data.get('STATIC_RIGHT_INDICATOR', 0):.2f} MB")
            print(f"STATIC INDICATOR SWITCH ECU -> {memory_data.get('STATIC_INDICATOR_SWITCH', 0):.2f} MB\n")

            # MTD
            print(f"MTD HEADLIGHT SWITCH ECU    -> {memory_data.get('MTD_SWITCH', 0):.2f} MB")
            print(f"MTD HEADLAMP ECU            -> {memory_data.get('MTD_HEADLAMP', 0):.2f} MB")
            print(f"MTD FORCE SENSOR ECU        -> {memory_data.get('MTD_FORCESENSOR', 0):.2f} MB")
            print(f"MTD CRASH DETECTOR ECU      -> {memory_data.get('MTD_CRASHDETECTOR', 0):.2f} MB")
            print(f"MTD AIRBAG ECU              -> {memory_data.get('MTD_AIRBAG', 0):.2f} MB")
            print(f"MTD LEFT INDICATOR ECU      -> {memory_data.get('MTD_LEFT_INDICATOR', 0):.2f} MB")
            print(f"MTD RIGHT INDICATOR ECU     -> {memory_data.get('MTD_RIGHT_INDICATOR', 0):.2f} MB")
            print(f"MTD INDICATOR SWITCH ECU    -> {memory_data.get('MTD_INDICATOR_SWITCH', 0):.2f} MB\n")

            # Latency
            print(f"STATIC HEADLAMP LATENCY     -> {latency_data.get('STATIC_HEADLAMP', 'waiting...')}")
            print(f"MTD HEADLAMP LATENCY        -> {latency_data.get('MTD_HEADLAMP', 'waiting...')}\n")
            print(f"STATIC AIRBAG LATENCY       -> {latency_data.get('STATIC_AIRBAG', 'waiting...')}")
            print(f"MTD AIRBAG LATENCY          -> {latency_data.get('MTD_AIRBAG', 'waiting...')}\n")
            print(f"STATIC LEFT INDICATOR LATENCY -> {latency_data.get('STATIC_LEFT_INDICATOR', 'waiting...')}")
            print(f"MTD LEFT INDICATOR LATENCY    -> {latency_data.get('MTD_LEFT_INDICATOR', 'waiting...')}")
            print(f"STATIC RIGHT INDICATOR LATENCY -> {latency_data.get('STATIC_RIGHT_INDICATOR', 'waiting...')}")
            print(f"MTD RIGHT INDICATOR LATENCY   -> {latency_data.get('MTD_RIGHT_INDICATOR', 'waiting...')}")

        time.sleep(1)

if __name__ == "__main__":
    threading.Thread(target=monitor_memory, daemon=True).start()
    threading.Thread(target=monitor_latency, daemon=True).start()
    display_loop()
