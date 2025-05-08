# Listens for startup command from Ignition ECU 
# Tracks timing of readiness messages:
#     - Battery ECU expected at 1.0s
#     - Fuel ECU expected at 2.0s
#     - Engine ECU expected at 3.0s
# Verifies timing and correct order
# On valid sequence: broadcasts startup
# On invalid timing or order: broadcasts failure
# CAN IDs dynamically encrypted

import time
import signal
import sys
from can_node import CANNode
from mtd import encrypt_id, decrypt_id 

# CAN Payloads
COMMAND_CONTROL = 0x07
BATTERY_STARTUP = [0xB1, 0x55, 0x8F, 0x01]
FUEL_STARTUP =    [0xF1, 0x55, 0x8F, 0x01]
ENGINE_STARTUP =  [0xEC, 0x55, 0x8F, 0x01]
STARTUP = [0xAA, 0x11]
FAILURE = [0xFF, 0xFF]

class StarterMotorECU(CANNode):
    def __init__(self, node_id, **kwargs):
        super().__init__(node_id, **kwargs)
        self.control_id = 0x001
        self.battery_id = 0x701
        self.fuel_id = 0x702
        self.engine_id = 0x703
        self.broadcast_id = 0x704
        self.running = True
        self.reset_state()

    def start(self):
        super().start()

    def reset_state(self):
        """
        This resets the system state
        """
        self.start_time = None
        self.received = {
            self.battery_id: None,
            self.fuel_id: None,
            self.engine_id: None
        }

    def on_message(self, msg):
        now = time.perf_counter()

        if decrypt_id(msg.arbitration_id) == self.control_id and msg.data[0] == COMMAND_CONTROL:
            self.reset_state()
            self.start_time = now

        # If the timer has started and we receive a message from one of the expected ECUs
        elif self.start_time and decrypt_id(msg.arbitration_id) in self.received:
            if self.received[decrypt_id(msg.arbitration_id)] is None:
                self.received[decrypt_id(msg.arbitration_id)] = (now - self.start_time, list(msg.data[:4])) # record how long it took to arrive

            # Check timing
            if all(self.received.values()):
                self.evaluate_sequence()

    def evaluate_sequence(self):
        r = self.received

        valid = (
            r[self.battery_id][1] == BATTERY_STARTUP and abs(r[self.battery_id][0] - 1.0) <= 0.5 and
            r[self.fuel_id][1]    == FUEL_STARTUP    and abs(r[self.fuel_id][0]    - 2.0) <= 0.5 and
            r[self.engine_id][1]  == ENGINE_STARTUP  and abs(r[self.engine_id][0]  - 3.0) <= 0.5 and
            r[self.battery_id][0] < r[self.fuel_id][0] < r[self.engine_id][0]
        )

        time.sleep(1.0)

        if valid:
            print(f"[STARTER MOTOR ECU] Valid startup sequence — engine starting")
            payload = STARTUP
        else:
            print(f"[STARTER MOTOR ECU] Invalid startup sequence")
            payload = FAILURE
            
        self.send_message(encrypt_id(self.broadcast_id), payload)
        self.reset_state()


    def shutdown(self):
        self.running = False
        self.stop()

if __name__ == "__main__":
    ecu = StarterMotorECU("STARTER MOTOR ECU", bus_name="vcan0")

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
