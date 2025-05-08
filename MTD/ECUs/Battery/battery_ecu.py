# Responds to startup command from Ignition ECU 
# If OFF: Waits 1.0s, sends readiness signal, then starts voltage broadcast
# If ON: Waits 1.0s, stops voltage broadcast and signals shutdown
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
STARTUP = [0xB1, 0x55, 0x8F, 0x01]
SHUTDOWN = [0xB1, 0x55, 0x8F, 0x00]

class BatteryECU(CANNode):
    def __init__(self, node_id, **kwargs):
        super().__init__(node_id, **kwargs)
        self.broadcast_id = 0x701           # ID for readiness and voltage
        self.control_id = 0x001             # Ignition startup/shutdown command
        self.running = True
        self.started = False

    def start(self):
        super().start()
        self.start_voltage_broadcast_loop()

    def on_message(self, msg):
        """
       Toggle between startup and shutdown
        """
        if decrypt_id(msg.arbitration_id) == self.control_id and msg.data[0] == COMMAND_CONTROL:
            if not self.started:
                threading.Timer(1.0, self._handle_startup).start()
            else:
                threading.Timer(1.0, self._handle_shutdown).start()

    def _handle_startup(self):
        """
        Send readiness signal, and allow voltage broadcasts.
        """
        self.started = True
        self.send_message(encrypt_id(self.broadcast_id), STARTUP)
        print(f"[MTD BATTERY ECU] System started")

    def _handle_shutdown(self):
        """
        Send shutdown signal, and block voltage broadcast.
        """
        self.started = False
        self.send_message(encrypt_id(self.broadcast_id), SHUTDOWN)
        print(f"[MTD BATTERY ECU] System stopped")

    def start_voltage_broadcast_loop(self):
        """
        Broadcasts voltage only when system is 'started'.
        """
        def loop():
            if self.running:
                if self.started:
                    voltage = random.randint(115, 125)  # Random voltage
                    encrypted_id = encrypt_id(self.broadcast_id)
                    self.send_message(encrypted_id, [0]*3 + [voltage])
                threading.Timer(1.0, loop).start()

        loop()

    def shutdown(self):
        self.running = False
        self.stop()

if __name__ == "__main__":
    ecu = BatteryECU("MTD BATTERY ECU", bus_name="vcan0")

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
