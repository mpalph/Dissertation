# Deploys on crash trigger (0x402)
# Cooldown of 5s where airbag cannot deploy
# Periodically broadcasts 0x501 airbag status every 1s
# CAN IDs dynamically encrypted

import threading
import signal
import sys
import time
from can_node import CANNode
from mtd import encrypt_id, decrypt_id

DEPLOY = [0xDE, 0x99]

class AirbagECU(CANNode):
    def __init__(self, node_id, **kwargs):
        super().__init__(node_id, **kwargs)
        self.status = 0x00                  # 0x00 = ready, 0x01 = deployed
        self.last_deploy_time = 0           # Last deployment timestamp
        self.cooldown = 5                   # Seconds to auto-reset after deployment
        self.running = True                 
        self.listen_crash = 0x402
        self.listen_status = 0x501
        self.broadcast_status = 0x501

    def start(self):
        """
        Start CAN listener and periodic status broadcasting.
        """
        super().start()
        self.start_status_broadcast()

    def on_message(self, msg):
        """
        Process incoming CAN messages:
        - Crash detector trigger (0x402)
        - Status update messages (0x501)
        """
        if decrypt_id(msg.arbitration_id) == self.listen_crash and list(msg.data[0:2]) == DEPLOY:
            if self.status == 0x01:
                print(f"[MTD AIRBAG ECU] Airbag already deployed.")
                return

            self.status = 0x01
            self.last_deploy_time = time.time()
            print(f"[MTD AIRBAG ECU] AIRBAG DEPLOYED!")

        # This is for demonstration purposes to allow spoofing
        elif decrypt_id(msg.arbitration_id) == self.listen_status:
            incoming_status = msg.data[0]
            self.status = incoming_status

    def start_status_broadcast(self):
        """
        Periodically broadcast airbag status
        """
        def loop():
            while self.running:
                # Auto-reset status after cooldown
                if self.status == 0x01 and (time.time() - self.last_deploy_time > self.cooldown):
                    self.status = 0x00

                self.send_message(encrypt_id(self.broadcast_status), [self.status] + [0xDE])
                time.sleep(1.0)

        threading.Thread(target=loop, daemon=True).start()

    def shutdown(self):
        self.running = False
        self.stop()

if __name__ == "__main__":
    ecu = AirbagECU("MTD AIRBAG ECU", bus_name="vcan0")

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
