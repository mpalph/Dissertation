# loggerlat.py
# 🚦 Smooth High-Precision ECU Latency Monitor (no flicker, clean updates)

import can
import time
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

def decrypt_id(arbitration_id):
    if arbitration_id == CONTROL_ID:
        return CONTROL_ID

    now = time.localtime()
    seed = (now.tm_min * 60 + now.tm_sec).to_bytes(16, byteorder='big')
    cipher = AES.new(AES_KEY, AES.MODE_ECB)
    encrypted = cipher.encrypt(seed)
    mask = int.from_bytes(encrypted[:2], byteorder='big') & 0x7FF
    return mask ^ arbitration_id

def monitor_latency():
    print("[LoggerLat] 🚀 Monitoring ECU latencies...\nPress Ctrl+C to stop.\n")

    bus = can.interface.Bus(channel="vcan0", interface="socketcan")

    # 🕑 Timing trackers
    last_triggers = {
        "STATIC_HEADLAMP": None,
        "MTD_HEADLAMP": None,
        "STATIC_AIRBAG": None,
        "MTD_AIRBAG": None,
        "STATIC_LEFT_INDICATOR": None,
        "MTD_LEFT_INDICATOR": None,
        "STATIC_RIGHT_INDICATOR": None,
        "MTD_RIGHT_INDICATOR": None,
    }

    # 📈 Latency displays
    latency_values = {
        "STATIC_HEADLAMP": "waiting...",
        "MTD_HEADLAMP": "waiting...",
        "STATIC_AIRBAG": "waiting...",
        "MTD_AIRBAG": "waiting...",
        "STATIC_LEFT_INDICATOR": "waiting...",
        "MTD_LEFT_INDICATOR": "waiting...",
        "STATIC_RIGHT_INDICATOR": "waiting...",
        "MTD_RIGHT_INDICATOR": "waiting...",
    }

    # 📋 Print the 8 constant lines once
    for key in ["MTD_HEADLAMP", "STATIC_HEADLAMP", "MTD_AIRBAG", "STATIC_AIRBAG",
                "MTD_LEFT_INDICATOR", "STATIC_LEFT_INDICATOR", "MTD_RIGHT_INDICATOR", "STATIC_RIGHT_INDICATOR"]:
        sys.stdout.write(f"{key.replace('_', ' ').title()} latency: {latency_values[key]}\n")
    sys.stdout.flush()

    try:
        while True:
            msg = bus.recv(timeout=0.01)
            updated = False

            if msg:
                raw_id = msg.arbitration_id
                decoded_id = decrypt_id(raw_id)
                now = time.perf_counter()

                # ➡️ Handle control inputs
                if raw_id == CONTROL_ID:
                    command = msg.data[0]

                    if command == 0x02:  # Headlamp toggle
                        last_triggers["STATIC_HEADLAMP"] = now
                        last_triggers["MTD_HEADLAMP"] = now
                        latency_values["STATIC_HEADLAMP"] = "waiting..."
                        latency_values["MTD_HEADLAMP"] = "waiting..."
                        updated = True

                    elif command == 0x03:  # Crash trigger
                        last_triggers["STATIC_AIRBAG"] = now
                        last_triggers["MTD_AIRBAG"] = now
                        latency_values["STATIC_AIRBAG"] = "waiting..."
                        latency_values["MTD_AIRBAG"] = "waiting..."
                        updated = True

                    elif command == 0x04:  # Left indicator toggle
                        last_triggers["STATIC_LEFT_INDICATOR"] = now
                        last_triggers["MTD_LEFT_INDICATOR"] = now
                        latency_values["STATIC_LEFT_INDICATOR"] = "waiting..."
                        latency_values["MTD_LEFT_INDICATOR"] = "waiting..."
                        updated = True

                    elif command == 0x05:  # Right indicator toggle
                        last_triggers["STATIC_RIGHT_INDICATOR"] = now
                        last_triggers["MTD_RIGHT_INDICATOR"] = now
                        latency_values["STATIC_RIGHT_INDICATOR"] = "waiting..."
                        latency_values["MTD_RIGHT_INDICATOR"] = "waiting..."
                        updated = True

                    elif command == 0x06:  # Hazard ON
                        last_triggers["STATIC_LEFT_INDICATOR"] = now
                        last_triggers["MTD_LEFT_INDICATOR"] = now
                        last_triggers["STATIC_RIGHT_INDICATOR"] = now
                        last_triggers["MTD_RIGHT_INDICATOR"] = now
                        latency_values["STATIC_LEFT_INDICATOR"] = "waiting..."
                        latency_values["MTD_LEFT_INDICATOR"] = "waiting..."
                        latency_values["STATIC_RIGHT_INDICATOR"] = "waiting..."
                        latency_values["MTD_RIGHT_INDICATOR"] = "waiting..."
                        updated = True

                # ➡️ Handle STATUS messages

                # Headlamp Static
                elif raw_id == STATUS_ID_HEADLAMP_ECU and last_triggers["STATIC_HEADLAMP"]:
                    latency_values["STATIC_HEADLAMP"] = f"{(now - last_triggers['STATIC_HEADLAMP']) * 1000:.2f} ms"
                    last_triggers["STATIC_HEADLAMP"] = None
                    updated = True

                # Headlamp MTD
                elif decoded_id == STATUS_ID_HEADLAMP_ECU and last_triggers["MTD_HEADLAMP"]:
                    latency_values["MTD_HEADLAMP"] = f"{(now - last_triggers['MTD_HEADLAMP']) * 1000:.2f} ms"
                    last_triggers["MTD_HEADLAMP"] = None
                    updated = True

                # Airbag Static
                elif raw_id == STATUS_ID_AIRBAG_ECU and last_triggers["STATIC_AIRBAG"]:
                    if msg.data[0] == 0x01:
                        latency_values["STATIC_AIRBAG"] = f"{(now - last_triggers['STATIC_AIRBAG']) * 1000:.2f} ms"
                        last_triggers["STATIC_AIRBAG"] = None
                        updated = True

                # Airbag MTD
                elif decoded_id == STATUS_ID_AIRBAG_ECU and last_triggers["MTD_AIRBAG"]:
                    if msg.data[0] == 0x01:
                        latency_values["MTD_AIRBAG"] = f"{(now - last_triggers['MTD_AIRBAG']) * 1000:.2f} ms"
                        last_triggers["MTD_AIRBAG"] = None
                        updated = True

                # Left Indicator Static
                elif raw_id == STATUS_ID_LEFT_INDICATOR and last_triggers["STATIC_LEFT_INDICATOR"]:
                    if msg.data[0] == 0x01:
                        latency_values["STATIC_LEFT_INDICATOR"] = f"{(now - last_triggers['STATIC_LEFT_INDICATOR']) * 1000:.2f} ms"
                        last_triggers["STATIC_LEFT_INDICATOR"] = None
                        updated = True

                # Left Indicator MTD
                elif decoded_id == STATUS_ID_LEFT_INDICATOR and last_triggers["MTD_LEFT_INDICATOR"]:
                    if msg.data[0] == 0x01:
                        latency_values["MTD_LEFT_INDICATOR"] = f"{(now - last_triggers['MTD_LEFT_INDICATOR']) * 1000:.2f} ms"
                        last_triggers["MTD_LEFT_INDICATOR"] = None
                        updated = True

                # Right Indicator Static
                elif raw_id == STATUS_ID_RIGHT_INDICATOR and last_triggers["STATIC_RIGHT_INDICATOR"]:
                    if msg.data[0] == 0x01:
                        latency_values["STATIC_RIGHT_INDICATOR"] = f"{(now - last_triggers['STATIC_RIGHT_INDICATOR']) * 1000:.2f} ms"
                        last_triggers["STATIC_RIGHT_INDICATOR"] = None
                        updated = True

                # Right Indicator MTD
                elif decoded_id == STATUS_ID_RIGHT_INDICATOR and last_triggers["MTD_RIGHT_INDICATOR"]:
                    if msg.data[0] == 0x01:
                        latency_values["MTD_RIGHT_INDICATOR"] = f"{(now - last_triggers['MTD_RIGHT_INDICATOR']) * 1000:.2f} ms"
                        last_triggers["MTD_RIGHT_INDICATOR"] = None
                        updated = True

            if updated:
                # 🖥️ Only if real update, move cursor up 8 lines and redraw cleanly
                sys.stdout.write("\033[8F")  # Move up 8 lines
                for key in ["MTD_HEADLAMP", "STATIC_HEADLAMP", "MTD_AIRBAG", "STATIC_AIRBAG",
                            "MTD_LEFT_INDICATOR", "STATIC_LEFT_INDICATOR", "MTD_RIGHT_INDICATOR", "STATIC_RIGHT_INDICATOR"]:
                    sys.stdout.write("\033[K")  # Clear line
                    sys.stdout.write(f"{key.replace('_', ' ').title()} latency: {latency_values[key]}\n")
                sys.stdout.flush()

    except KeyboardInterrupt:
        print("\n[LoggerLat] 🧯 Monitoring stopped.")

if __name__ == "__main__":
    monitor_latency()
