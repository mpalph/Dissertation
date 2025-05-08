
import can
import threading

class CANNode:
    def __init__(self, node_id, bus_name='vcan0'):
        self.node_id = node_id
        self.bus = can.interface.Bus(bus_name, bustype='socketcan')
        self.running = False

    def start(self):
        """Start background thread to listen for CAN messages."""
        self.running = True
        threading.Thread(target=self.receive_loop, daemon=True).start()

    def stop(self):
        """Stop the receive loop and shut down the CAN bus."""
        self.running = False
        try:
            self.bus.shutdown()
        except Exception as e:
            print(f"[{self.node_id}] Warning: Bus shutdown failed — {e}")

    def send_message(self, target_id, data):
        """Send a CAN message to the given arbitration ID."""
        msg = can.Message(arbitration_id=target_id, data=data, is_extended_id=False)
        self.bus.send(msg)

    def receive_loop(self):
        """Background message receiving loop."""
        while self.running:
            try:
                msg = self.bus.recv(timeout=1.0)
                if msg:
                    self.on_message(msg)
            except (OSError, can.CanError):
                break

    def on_message(self, msg):
        """Override in subclasses to process incoming messages."""
        pass
