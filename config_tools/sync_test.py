import serial
import time

# Set the correct port and baud rate for Linux
arduino_port = '/dev/ttyACM1'  # Replace with your actual port if different
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
    for i in range(20):  # Loop through pumps A to T
        ser.write(f"{chr(ord('a') + i)}f".encode())
    print("All pumps OFF.")

def pump_menu():
    while True:
        print("\nPump Control Menu:")
        print("[a-t]: Activate/Deactivate Pump A-T")
        print("[x]: Stop all pumps")
        print("[q]: Quit")
        
        choice = input("Enter pump letter, 'x' to stop all, or 'q' to quit: ").lower()
        
        if choice == 'q':
            print("Exiting pump control.")
            break
        elif choice == 'x':
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
            print("Invalid pump selection. Please enter a letter between 'a' and 't'.")

try:
    pump_menu()
except KeyboardInterrupt:
    print("\nInterrupted. Turning off all pumps.")
    stop_all_pumps()
    ser.close()
