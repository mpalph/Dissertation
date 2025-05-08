# Listens for control commands (ID 0x001) from ignition.py
# Listens for headlamp status updates (ID 0x301) from Headlamp ECU
# Sends headlamp toggle commands (ID 0x201) to Headlamp ECU
# CAN IDs dynamically encrypted

import signal
import sys
import time
from can_node import CANNode
from mtd import encrypt_id, decrypt_id

# CAN payloads 
CONTROL_COMMAND = 0x02
TOGGLE_ON = [0x01, 0x55, 0xAA]
TOGGLE_OFF = [0x02, 0x55, 0xAA]
STATUS_ON = [0x10, 0x01, 0xF0]

class HeadlightSwitchECU(CANNode):
    def __init__(self, node_id, **kwargs):
        super().__init__(node_id, **kwargs)
        self.control_id = 0x001                  # Listen for ignition control messages
        self.listen_id = 0x301                   # Listen for headlamp ON/OFF status updates
        self.broadcast_id = 0x201                # Send toggle commands to Headlamp ECU
        self.running = True                      

    def on_message(self, msg):
        """
        Process incoming CAN messages:
        - Headlamp status updates (0x301) from Headlamp ECU
        - Control commands (0x001) from ignition.py
        """
        # Listens to headlamp status and defines when it is on
        if decrypt_id(msg.arbitration_id) == self.listen_id:
            self.headlight_state_on = list(msg.data[0:3]) == STATUS_ON
            return

        if decrypt_id(msg.arbitration_id) == self.control_id:
            if msg.data[0] == CONTROL_COMMAND:
                self.toggle()
                return

    def toggle(self):
        """
        Send a CAN message to toggle the headlamp ON or OFF based on known state.
        Encrypt ID
        """
        if self.headlight_state_on:
            self.send_message(encrypt_id(self.broadcast_id), TOGGLE_OFF)
        else:
            self.send_message(encrypt_id(self.broadcast_id), TOGGLE_ON)

    def shutdown(self):
        self.running = False
        self.stop()

if __name__ == "__main__":
    ecu = HeadlightSwitchECU("MTD HEADLIGHT SWITCH ECU", bus_name="vcan0")

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
