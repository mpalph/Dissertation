
# Crash Detector ECU (MTD Version)
# ─────────────────────────────────────────────────────
# Listens to G-force (0x401)
# Sends deploy signal (0x402) if threshold exceeded
# CAN IDs dynamically encrypted

import time
import threading
import signal
import sys
from can_node import CANNode
from mtd import encrypt_id, decrypt_id

class CrashDetectorECU(CANNode):
    def __init__(self, node_id, threshold=50, **kwargs):
        super().__init__(node_id, **kwargs)
        self.threshold = threshold
        self.latest_force = 0
        self.running = True
        self.listen_force = 0x401
        self.broadcast_id = 0x402

    def start(self):
        """
        Start CAN listener and background force monitoring thread.
        """
        super().start()
        self.start_force_monitor()

    def on_message(self, msg):
        """
        Process incoming CAN messages:
        - G-force readings (ID 0x401)
        """
        if decrypt_id(msg.arbitration_id) == self.listen_force:
            self.latest_force = msg.data[0]

    def start_force_monitor(self):
        """
        Checks the latest G-force. 
        Sends deploy command if threshold exceeded.
        """
        def monitor():
            while self.running:
                if self.latest_force > self.threshold:
                    self.send_message(encrypt_id(self.broadcast_id), [0xDE] + [0x99])
                    time.sleep(1.0)  # Cooldown to avoid rapid redeploys
                time.sleep(0.1)

        threading.Thread(target=monitor, daemon=True).start()

    def shutdown(self):
        self.running = False
        self.stop()

if __name__ == "__main__":
    ecu = CrashDetectorECU("MTD CRASH DETECTOR ECU", bus_name="vcan0")

    def handle_sigint(sig, frame):
        ecu.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)

    ecu.start()

    try:
        while ecu.running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        ecu.shutdown()
