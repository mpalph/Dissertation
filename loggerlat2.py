# loggerlat2.py
# 🚦 Ultra-High Precision ECU Latency Logger (to File)

import can
import time
from Crypto.Cipher import AES

# 🛡️ AES Shared Key for MTD
AES_KEY = b'SecureECUSharedK'

# 📡 CAN IDs
CONTROL_ID = 0x001
STATUS_ID_HEADLAMP_ECU = 0x301
STATUS_ID_AIRBAG_ECU = 0x501

def decrypt_id(arbitration_id):
    if arbitration_id == CONTROL_ID:
        return CONTROL_ID

    now = time.localtime()
    seed = (now.tm_min * 60 + now.tm_sec).to_bytes(16, byteorder='big')
    cipher = AES.new(AES_KEY, AES.MODE_ECB)
    encrypted = cipher.encrypt(seed)
    mask = int.from_bytes(encrypted[:2], byteorder='big') & 0x7FF
    return mask ^ arbitration_id

def log_to_file(entry):
    """
    Appends a single latency log line to 'latency.txt'.
    """
    with open("latency.txt", "a") as f:
        f.write(entry + "\n")

def monitor_latency():
    print("[LoggerLat2] 🚀 Monitoring and logging latencies to 'latency.txt'...\nPress Ctrl+C to stop.\n")

    bus = can.interface.Bus(channel="vcan0", interface="socketcan")

    last_static_trigger_headlamp = None
    last_mtd_trigger_headlamp = None
    last_static_trigger_airbag = None
    last_mtd_trigger_airbag = None

    try:
        while True:
            msg = bus.recv(timeout=0.0001)
            if not msg:
                continue

            raw_id = msg.arbitration_id
            decrypted_id = decrypt_id(raw_id)
            now = time.perf_counter()

            if raw_id == CONTROL_ID:
                command = msg.data[0]
                if command == 0x02:
                    last_static_trigger_headlamp = now
                    last_mtd_trigger_headlamp = now
                elif command == 0x03:
                    last_static_trigger_airbag = now
                    last_mtd_trigger_airbag = now

            elif raw_id == STATUS_ID_HEADLAMP_ECU and last_static_trigger_headlamp is not None:
                latency_ms = (now - last_static_trigger_headlamp) * 1000
                log_to_file(f"[{time.strftime('%H:%M:%S')}] STATIC HEADLAMP ECU latency: {latency_ms:.3f} ms")
                last_static_trigger_headlamp = None

            elif decrypted_id == STATUS_ID_HEADLAMP_ECU and last_mtd_trigger_headlamp is not None:
                latency_ms = (now - last_mtd_trigger_headlamp) * 1000
                log_to_file(f"[{time.strftime('%H:%M:%S')}] MTD HEADLAMP ECU latency: {latency_ms:.3f} ms")
                last_mtd_trigger_headlamp = None

            elif raw_id == STATUS_ID_AIRBAG_ECU and last_static_trigger_airbag is not None:
                if msg.data[0] == 0x01:
                    latency_ms = (now - last_static_trigger_airbag) * 1000
                    log_to_file(f"[{time.strftime('%H:%M:%S')}] STATIC AIRBAG ECU latency: {latency_ms:.3f} ms")
                    last_static_trigger_airbag = None

            elif decrypted_id == STATUS_ID_AIRBAG_ECU and last_mtd_trigger_airbag is not None:
                if msg.data[0] == 0x01:
                    latency_ms = (now - last_mtd_trigger_airbag) * 1000
                    log_to_file(f"[{time.strftime('%H:%M:%S')}] MTD AIRBAG ECU latency: {latency_ms:.3f} ms")
                    last_mtd_trigger_airbag = None

    except KeyboardInterrupt:
        print("\n[LoggerLat2] 🧯 Logging stopped.")

if __name__ == "__main__":
    monitor_latency()
