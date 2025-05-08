# Listens for toggle commands from Switch ECU (ID 0x201)
# Changes headlamp ON/OFF state accordingly
# Periodically broadcasts headlamp status (ID 0x301) using:
# CAN IDs dynamically encrypted

import threading
import signal
import sys
import time
from can_node import CANNode
from mtd import encrypt_id, decrypt_id

#CAN payloads
TOGGLE_ON = [0x01, 0x55, 0xAA]
TOGGLE_OFF = [0x02, 0x55, 0xAA]

STATUS_ON = [0x10, 0x01, 0xF0]
STATUS_OFF = [0x11, 0x00, 0xF0]

class HeadlampECU(CANNode):
    def __init__(self, node_id, **kwargs):
        super().__init__(node_id, **kwargs)
        self.headlight_state = False       # Headlight initially OFF
        self.listen_id = 0x201              # Listen for headlamp toggle commands
        self.broadcast_id = 0x301           # Broadcast headlamp status
        self.running = True                 

    def start(self):
        """
        Updates "start" to include status broadcasting.
        """
        super().start()
        self.start_status_broadcast()

    def on_message(self, msg):
        """
        Process incoming CAN messages:
        - Headlamp toggle commands
        """
        if decrypt_id(msg.arbitration_id) == self.listen_id:
            # Handle toggle headlamp commands
            cmd = msg.data[0]

            if list(msg.data[0:3]) == TOGGLE_ON and not self.headlight_state:
                self.headlight_state = True
                print(f"[MTD HEADLAMP ECU] Headlights turned ON")

            elif list(msg.data[0:3]) == TOGGLE_OFF and self.headlight_state:
                self.headlight_state = False
                print(f"[MTD HEADLAMP ECU] Headlights turned OFF")

    def start_status_broadcast(self):
        """
        Broadcast headlamp ON/OFF status
        """
        def loop():
            if self.running:
                if self.headlight_state:
                    payload = STATUS_ON
                else:
                    payload = STATUS_OFF

                self.send_message(encrypt_id(self.broadcast_id), payload)
                threading.Timer(1.0, loop).start()

        loop()

    def shutdown(self):
        self.running = False
        self.stop()

if __name__ == "__main__":
    ecu = HeadlampECU("MTD HEADLAMP ECU", bus_name="vcan0")

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
