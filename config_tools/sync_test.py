import serial
import time

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
        print("[a-t]: Activate/Deactivate Pump A-T")
        print("[s]: Stop all pumps")
        print("[q]: Quit")
        
        choice = input("Enter pump letter, 's' to stop all, or 'q' to quit: ").lower()
        
        if choice == 'q':
            print("Exiting pump control.")
            break
        elif choice == 's':
            stop_all_pumps()
        elif 'a' <= choice <= 't':
            action = input("Turn ON or OFF? (o/f): ").lower()
            if action == 'o':
                activate_pump(choice)
            elif action == 'f':
                deactivate_pump(choice)
            else:
                print("Invalid action. Enter 'o' for ON or 'f' for OFF.")
        else:
            print("Invalid selection. Please enter a letter between 'a' and 't', 's' to stop all pumps, or 'q' to quit.")

try:
    pump_menu()
except KeyboardInterrupt:
    print("\nInterrupted. Sending stop command to all pumps.")
    stop_all_pumps()
    ser.close()
