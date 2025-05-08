# Responds to startup command from Ignition ECU 
# If OFF: Waits 3.0s, sends readiness signal, then starts
# If ON: Waits 3.0s, sends shutdown signal, then shutdown

import threading
import signal
import sys
import time
from can_node import CANNode

#CAN Payloads
COMMAND_CONTROL = 0x07
STARTUP = [0xEC, 0x55, 0x8F, 0x01]
SHUTDOWN = [0xEC, 0x55, 0x8F, 0x00]

class EngineECU(CANNode):
    def __init__(self, node_id, **kwargs):
        super().__init__(node_id, **kwargs)
        self.broadcast_id = 0x703           # ID for readiness and status
        self.control_id = 0x001             # Ignition control command
        self.running = True                 
        self.started = False                

    def start(self):
        super().start()

    def on_message(self, msg):
        """
        Toggle between startup and shutdown
        """
        if msg.arbitration_id == self.control_id and msg.data[0] == COMMAND_CONTROL:
            if not self.started:
                threading.Timer(3.0, self._handle_startup).start()
            else:
                threading.Timer(3.0, self._handle_shutdown).start()

    def _handle_startup(self):
        """
        Send readiness signal, begin engine status broadcast.
        """
        self.started = True
        self.send_message(self.broadcast_id, STARTUP)
        print(f"[STATIC ENGINE ECU] System started")

    def _handle_shutdown(self):
        """
        Send shutdown signal and stop status broadcasting.
        """
        self.started = False
        self.send_message(self.broadcast_id, SHUTDOWN)
        print(f"[STATIC ENGINE ECU] System stopped")

    def shutdown(self):
        self.running = False
        self.stop()

if __name__ == "__main__":
    ecu = EngineECU("STATIC ENGINE ECU", bus_name="vcan0")

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
