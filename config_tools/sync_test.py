import serial
import time
from control_libs.system_stats import append_console_message
# Set the correct port and baud rate for Linux
arduino_port = '/dev/ttyACM0'  # Replace with your actual port if different
baud_rate = 9600

# Initialize serial connection
ser = serial.Serial(arduino_port, baud_rate, timeout=1)
time.sleep(2)  # Allow time for Arduino to reset

def activate_pump(pump_letter):
    ser.write(f"{pump_letter}o".encode())
    print(f"Pump {pump_letter.upper()} ON")

def deactivate_pump(pump_letter):
    ser.write(f"{pump_letter}f".encode())
    print(f"Pump {pump_letter.upper()} OFF")

def stop_all_pumps():
    ser.write(b'X')  # Send 'X' to Arduino to stop all pumps
    print("Stop command sent: All pumps OFF.")

def pump_menu():
    while True:
        print("\nPump Control Menu:")
        print("[1]: Activate/Deactivate Pump (A-T)")
        print("[2]: Stop All Pumps")
        print("[3]: Quit")
        
        choice = input("Select an option (1-3): ").strip()
        
        if choice == '1':
            pump_choice = input("Select pump (A-T): ").lower()
            if 'a' <= pump_choice <= 't':
                action = input("Turn ON or OFF? (o/f): ").lower()
                if action == 'o':
                    activate_pump(pump_choice)
                elif action == 'f':
                    deactivate_pump(pump_choice)
                else:
                    print("Invalid action. Enter 'o' for ON or 'f' for OFF.")
            else:
                print("Invalid pump selection. Enter a letter between A and T.")
        
        elif choice == '2':
            stop_all_pumps()
        
        elif choice == '3':
            print("Exiting pump control.")
            break
        
        else:
            print("Invalid selection. Please enter 1, 2, or 3.")

try:
    pump_menu()
except KeyboardInterrupt:
    print("\nInterrupted. Sending stop command to all pumps.")
    stop_all_pumps()
    ser.close()
