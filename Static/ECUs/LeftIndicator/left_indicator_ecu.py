# Listens for left indicator commands (ID 0x601)
# Interprets toggle ON/OFF and hazard ON/OFF
# Broadcasts current status (ID 0x602)

import threading
import signal
import sys
import time
from can_node import CANNode

LEFT_ON = [0x10, 0x00, 0xC1]
LEFT_OFF = [0x10, 0x00, 0xC0]
HAZARD_ON = [0x11, 0x00, 0xC1]
HAZARD_OFF = [0x11, 0x00, 0xC0]
STATUS_ON = [0x6F, 0x8A]
STATUS_OFF = [0x6F, 0x88]

class LeftIndicatorECU(CANNode):
    def __init__(self, node_id, **kwargs):
        super().__init__(node_id, **kwargs)
        self.active = False                 
        self.hazard_mode = False             
        self.listen_id = 0x601               # Receive commands on this ID
        self.broadcast_id = 0x602            # Broadcast status on this ID
        self.running = True                  

    def start(self):
        super().start()
        self.start_status_broadcast()

    def on_message(self, msg):
        """
        Process incoming CAN messages:
        - Listen for indicator or hazard control commands (ID 0x601)
        """
        if msg.arbitration_id == self.listen_id:
            if list(msg.data[0:3]) == LEFT_ON:
                self.active = True
                self.hazard_mode = False
                print(f"[STATIC LEFT INDICATOR ECU] Left Indicator ON")

            elif list(msg.data[0:3]) == LEFT_OFF:
                self.active = False
                self.hazard_mode = False
                print(f"[STATIC LEFT INDICATOR ECU] Left Indicator OFF")

            elif list(msg.data[0:3]) == HAZARD_ON:
                self.active = True
                self.hazard_mode = True
                print(f"[STATIC LEFT INDICATOR ECU] Hazard Lights (Left) ON")

            elif list(msg.data[0:3]) == HAZARD_OFF:
                self.active = False
                self.hazard_mode = False
                print(f"[STATIC LEFT INDICATOR ECU] Hazard Lights (Left) OFF")

    def start_status_broadcast(self):
        """
        Broadcast indicator status every 1 second.
        """
        def loop():
            if self.running:
                status = STATUS_ON if self.active else STATUS_OFF
                self.send_message(self.broadcast_id, status + [0]*2)
                threading.Timer(1.0, loop).start()

        loop()

    def shutdown(self):
        self.running = False
        self.stop()

if __name__ == "__main__":
    ecu = LeftIndicatorECU("STATIC LEFT INDICATOR ECU", bus_name="vcan0")

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
