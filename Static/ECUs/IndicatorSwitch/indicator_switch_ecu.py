# Listens for control commands (ID 0x001)
# Sends indicator control instructions (ID 0x601)

import signal
import sys
import time
from can_node import CANNode

#CAN Payloads
CONTROL_COMMAND_LEFT = 0x04
CONTROL_COMMAND_RIGHT = 0x05
CONTROL_COMMAND_HAZARD = 0x06
LEFT_ON = [0x10, 0x00, 0xC1]
LEFT_OFF = [0x10, 0x00, 0xC0]
RIGHT_ON = [0x01, 0x00, 0xC1]
RIGHT_OFF = [0x01, 0x00, 0xC0]
HAZARD_ON = [0x11, 0x00, 0xC1]
HAZARD_OFF = [0x11, 0x00, 0xC0]

class IndicatorSwitchECU(CANNode):
    def __init__(self, node_id, **kwargs):
        super().__init__(node_id, **kwargs)
        self.left_on = False
        self.right_on = False
        self.hazards_on = False
        self.control_id = 0x001               # Listen for ignition commands
        self.broadcast_id = 0x601             # Send instructions to indicators
        self.running = True                   

    def start(self):
        super().start()

    def on_message(self, msg):
        """
        Process incoming CAN messages:
        - Listen for user control commands (ID 0x001)
        """
        if msg.arbitration_id == self.control_id:
            command = msg.data[0]

            if command == 0x04:
                self.toggle_left()

            elif command == 0x05:
                self.toggle_right()

            elif command == 0x06:
                self.toggle_hazard()

    def toggle_left(self):
        """
        Toggle left indicator ON/OFF.
        Turns OFF right indicator if active.
        """
        if self.hazards_on:
            self.toggle_hazard()
            return

        self.left_on = not self.left_on
        self.right_on = False  # Disable right if switching left
        cmd = LEFT_ON if self.left_on else LEFT_OFF
        self.send_message(self.broadcast_id, cmd)

    def toggle_right(self):
        """
        Toggle right indicator ON/OFF.
        Turns OFF left indicator if active.
        """
        if self.hazards_on:
            self.toggle_hazard()
            return

        self.right_on = not self.right_on
        self.left_on = False  # Disable left if switching right
        cmd = RIGHT_ON if self.right_on else RIGHT_OFF
        self.send_message(self.broadcast_id, cmd)

    def toggle_hazard(self):
        """
        Toggle hazard lights ON/OFF.
        """
        self.hazards_on = not self.hazards_on
        cmd = HAZARD_ON if self.hazards_on else HAZARD_OFF
        self.send_message(self.broadcast_id, cmd)

    def shutdown(self):
        self.running = False
        self.stop()

if __name__ == "__main__":
    ecu = IndicatorSwitchECU("STATIC INDICATOR SWITCH ECU", bus_name="vcan0")

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
