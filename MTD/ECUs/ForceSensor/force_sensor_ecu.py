# Continuously broadcasts safe G-force 
# Listens for control messages (ID 0x001) to trigger crash simulation
# Sends one high G-force value to simulate crash on demand
# CAN IDs dynamically encrypted

import random
import threading
import signal
import sys
import time
from can_node import CANNode
from mtd import encrypt_id, decrypt_id

# CAN payloads
CONTROL_COMMAND = 0x03

class ForceSensorECU(CANNode):
    def __init__(self, node_id, **kwargs):
        super().__init__(node_id, **kwargs)
        self.control_id = 0x001                  # Listen for ignition control messages
        self.broadcast_id = 0x401                 # G-force readings broadcast ID
        self.running = True                       
        self._loop_thread = None                  

    def start(self):
        """
        Start CAN listener and safe G-force simulation.
        """
        super().start()
        self._start_safe_force_loop()

    def on_message(self, msg):
        """
        Process incoming CAN messages:
        - Control messages (ID 0x001) to trigger a crash.
        """
        if decrypt_id(msg.arbitration_id) == self.control_id:
            command = msg.data[0]

            if msg.data[0] == CONTROL_COMMAND:
                self.simulate_crash()

    def _start_safe_force_loop(self):
        """
        Broadcast random safe G-force readings.
        """
        def loop():
            while self.running:
                safe_force = random.randint(5, 40)  # Normal forces
                self.send_message(encrypt_id(self.broadcast_id), [safe_force] + [0x2A])
                time.sleep(1.0)

        self._loop_thread = threading.Thread(target=loop, daemon=True)
        self._loop_thread.start()

    def simulate_crash(self):
        """
        Inject a high G-force value to simulate crash.
        """
        crash_force = random.randint(70, 100)
        print(f"[MTD FORCE SENSOR ECU] Crash force injected: {crash_force}")
        self.send_message(encrypt_id(self.broadcast_id), [crash_force] + [0x2A])

    def shutdown(self):
        self.running = False
        self.stop()

if __name__ == "__main__":
    ecu = ForceSensorECU("MTD FORCE SENSOR ECU", bus_name="vcan0")

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
