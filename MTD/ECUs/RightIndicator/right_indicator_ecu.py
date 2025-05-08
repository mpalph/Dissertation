# Listens for right indicator commands (ID 0x601)
# Interprets toggle ON/OFF and hazard ON/OFF
# Broadcasts current status (ID 0x603) 
# CAN IDs dynamically encrypted

import threading
import signal
import sys
import time
from can_node import CANNode
from mtd import encrypt_id, decrypt_id

RIGHT_ON = [0x01, 0x00, 0xC1]
RIGHT_OFF = [0x01, 0x00, 0xC0]
HAZARD_ON = [0x11, 0x00, 0xC1]
HAZARD_OFF = [0x11, 0x00, 0xC0]
STATUS_ON = [0x3F, 0x8A]
STATUS_OFF = [0x3F, 0x88]

class RightIndicatorECU(CANNode):
    def __init__(self, node_id, **kwargs):
        super().__init__(node_id, **kwargs)
        self.active = False                 
        self.hazard_mode = False             
        self.listen_id = 0x601               # Receive commands on this ID
        self.broadcast_id = 0x603            # Broadcast status on this ID
        self.running = True                  

    def start(self):
        super().start()
        self.start_status_broadcast()

    def on_message(self, msg):
        """
        Process incoming encrypted CAN messages:
        - Listen for indicator or hazard control commands (ID 0x601)
        """
        if decrypt_id(msg.arbitration_id) == self.listen_id:

            if list(msg.data[0:3]) == RIGHT_ON:
                self.active = True
                self.hazard_mode = False
                print(f"[MTD RIGHT INDICATOR ECU] Right Indicator ON")

            elif list(msg.data[0:3]) == RIGHT_OFF:
                self.active = False
                self.hazard_mode = False
                print(f"[MTD RIGHT INDICATOR ECU] Right Indicator OFF")

            elif list(msg.data[0:3]) == HAZARD_ON:
                self.active = True
                self.hazard_mode = True
                print(f"[MTD RIGHT INDICATOR ECU] Hazard Lights (Right) ON")

            elif list(msg.data[0:3]) == HAZARD_OFF:
                self.active = False
                self.hazard_mode = False
                print(f"[MTD RIGHT INDICATOR ECU] Hazard Lights (Right) OFF")

    def start_status_broadcast(self):
        """
        Broadcast encrypted indicator status every 1 second.
        """
        def loop():
            if self.running:
                status = STATUS_ON if self.active else STATUS_OFF
                self.send_message(encrypt_id(self.broadcast_id), status + [0]*2)
                threading.Timer(1.0, loop).start()

        loop()

    def shutdown(self):
        self.running = False
        self.stop()

if __name__ == "__main__":
    ecu = RightIndicatorECU("MTD RIGHT INDICATOR ECU", bus_name="vcan0")

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
