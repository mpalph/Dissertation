# Central controller for launching and managing ECUs

import subprocess
import time
import signal
import readchar
import can

ecu_processes = []
running = True
bus = None 

def launch_all_ecus():
    """
    Launch both Static and MTD ECU subprocesses.
    """
    # Static ECUs
    ecu_processes.append(subprocess.Popen(["python3", "Static/ECUs/HeadlampSwitch/headlamp_switch_ecu.py"]))
    ecu_processes.append(subprocess.Popen(["python3", "Static/ECUs/Headlamp/headlamp_ecu.py"]))
    ecu_processes.append(subprocess.Popen(["python3", "Static/ECUs/ForceSensor/force_sensor_ecu.py"]))
    ecu_processes.append(subprocess.Popen(["python3", "Static/ECUs/CrashDetector/crash_detector_ecu.py"]))
    ecu_processes.append(subprocess.Popen(["python3", "Static/ECUs/Airbag/airbag_ecu.py"]))
    ecu_processes.append(subprocess.Popen(["python3", "Static/ECUs/IndicatorSwitch/indicator_switch_ecu.py"]))
    ecu_processes.append(subprocess.Popen(["python3", "Static/ECUs/LeftIndicator/left_indicator_ecu.py"]))
    ecu_processes.append(subprocess.Popen(["python3", "Static/ECUs/RightIndicator/right_indicator_ecu.py"]))
    ecu_processes.append(subprocess.Popen(["python3", "Static/ECUs/Battery/battery_ecu.py"]))
    ecu_processes.append(subprocess.Popen(["python3", "Static/ECUs/FuelSystem/fuel_system_ecu.py"]))
    ecu_processes.append(subprocess.Popen(["python3", "Static/ECUs/EngineControl/engine_control_ecu.py"]))
    ecu_processes.append(subprocess.Popen(["python3", "Static/ECUs/StarterMotor/starter_motor_ecu.py"]))

    # MTD ECUs
    ecu_processes.append(subprocess.Popen(["python3", "MTD/ECUs/HeadlampSwitch/headlamp_switch_ecu.py"]))
    ecu_processes.append(subprocess.Popen(["python3", "MTD/ECUs/Headlamp/headlamp_ecu.py"]))
    ecu_processes.append(subprocess.Popen(["python3", "MTD/ECUs/ForceSensor/force_sensor_ecu.py"]))
    ecu_processes.append(subprocess.Popen(["python3", "MTD/ECUs/CrashDetector/crash_detector_ecu.py"]))
    ecu_processes.append(subprocess.Popen(["python3", "MTD/ECUs/Airbag/airbag_ecu.py"]))
    ecu_processes.append(subprocess.Popen(["python3", "MTD/ECUs/IndicatorSwitch/indicator_switch_ecu.py"]))
    ecu_processes.append(subprocess.Popen(["python3", "MTD/ECUs/LeftIndicator/left_indicator_ecu.py"]))
    ecu_processes.append(subprocess.Popen(["python3", "MTD/ECUs/RightIndicator/right_indicator_ecu.py"]))
    ecu_processes.append(subprocess.Popen(["python3", "MTD/ECUs/Battery/battery_ecu.py"]))
    ecu_processes.append(subprocess.Popen(["python3", "MTD/ECUs/FuelSystem/fuel_system_ecu.py"]))
    ecu_processes.append(subprocess.Popen(["python3", "MTD/ECUs/EngineControl/engine_control_ecu.py"]))
    ecu_processes.append(subprocess.Popen(["python3", "MTD/ECUs/StarterMotor/starter_motor_ecu.py"]))
    

def terminate_ecus():
    for proc in ecu_processes:
        try:
            proc.send_signal(signal.SIGINT)
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
    print("[Ignition] All ECUs terminated.")

def input_loop():
    """
    Handles user input and sends CAN messages accordingly.
    """
    global running
    global bus

    bus = can.interface.Bus(channel="vcan0", interface="socketcan")
    print("\nEnter Input — [1] Toggle Headlights, [2] Trigger Crash, [3] Start Engine, [←] Left Indicator, [→] Right Indicator, [↑] Hazard, [q] Quit:")

    while running:
        try:
            key = readchar.readkey()

            if key == '1':
                # Toggle headlights
                msg = can.Message(arbitration_id=0x001, data=[0x02], is_extended_id=False)
                bus.send(msg)

            elif key == '2':
                # Trigger crash
                msg = can.Message(arbitration_id=0x001, data=[0x03], is_extended_id=False)
                bus.send(msg)

            elif key == '3':
                # Initiate engine start-up sequence
                msg = can.Message(arbitration_id=0x001, data=[0x07], is_extended_id=False)
                bus.send(msg)

            elif key == readchar.key.LEFT:
                # Toggle left indicator
                msg = can.Message(arbitration_id=0x001, data=[0x04], is_extended_id=False)
                bus.send(msg)

            elif key == readchar.key.RIGHT:
                # Toggle right indicator
                msg = can.Message(arbitration_id=0x001, data=[0x05], is_extended_id=False)
                bus.send(msg)

            elif key == readchar.key.UP:
                # Toggle hazards
                msg = can.Message(arbitration_id=0x001, data=[0x06], is_extended_id=False)
                bus.send(msg)

            elif key == 'q':
                print("[Ignition] Exit simulation")
                running = False
                break


        except KeyboardInterrupt:
            running = False
            break

def shutdown_bus():
    """
    Properly shutdown CAN bus.
    """
    global bus
    if bus is not None:
        bus.shutdown()


if __name__ == "__main__":
    try:
        launch_all_ecus()
        time.sleep(1.0)  # Let ECUs boot
        input_loop()
    finally:
        shutdown_bus()
        terminate_ecus()