## Responds to startup command from Ignition ECU 
# If OFF: Waits 2.0s, sends readiness signal, then starts fuel level broadcasts
# If ON: Waits 2.0s, sends shutdown signal, then stops broadcasting
# CAN IDs dynamically encrypted

import threading
import signal
import sys
import time
import random
from can_node import CANNode
from mtd import encrypt_id, decrypt_id 

#CAN Payloads
COMMAND_CONTROL = 0x07
STARTUP = [0xF1, 0x55, 0x8F, 0x01]
SHUTDOWN = [0xF1, 0x55, 0x8F, 0x00]

class FuelECU(CANNode):
    def __init__(self, node_id, **kwargs):
        super().__init__(node_id, **kwargs)
        self.broadcast_id = 0x702           # ID for readiness and fuel level
        self.control_id = 0x001             # Ignition command ID
        self.running = True
        self.started = False

    def start(self):
        super().start()
        self.start_fuel_broadcast_loop()

    def on_message(self, msg):
        """
        Toggle between startup and shutdown
        """
        if decrypt_id(msg.arbitration_id) == self.control_id and msg.data[0] == COMMAND_CONTROL:
            if not self.started:
                threading.Timer(2.0, self._handle_startup).start()
            else:
                threading.Timer(2.0, self._handle_shutdown).start()

    def _handle_startup(self):
        """
        Send readiness signal, begin fuel level broadcasting.
        """
        self.started = True
        self.send_message(encrypt_id(self.broadcast_id), STARTUP)
        print(f"[MTD FUEL ECU] System started")

    def _handle_shutdown(self):
        """
        Send shutdown signal, and stop fuel level broadcasting.
        """
        self.started = False
        self.send_message(encrypt_id(self.broadcast_id), SHUTDOWN)
        print(f"[MTD FUEL ECU] System stopped")

    def start_fuel_broadcast_loop(self):
        """
        Broadcasts simulated fuel level every second,
        """
        def loop():
            if self.running:
                if self.started:
                    fuel_level = random.randint(30, 100)  # Simulate fuel
                    self.send_message(encrypt_id(self.broadcast_id), [0x0F]*2 + [fuel_level])
                threading.Timer(1.0, loop).start()

        loop()

    def shutdown(self):
        self.running = False
        self.stop()

if __name__ == "__main__":
    ecu = FuelECU("MTD FUEL ECU", bus_name="vcan0")

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
