import serial
import time

# Update this with the correct port if different
WEMOS_PORT = '/dev/ttyUSB0'  # Linux/Mac
# WEMOS_PORT = 'COM3'        # Windows (example)
BAUD_RATE = 9600

def connect_to_wemos():
    try:
        print(f"[DEBUG] Connecting to Wemos on {WEMOS_PORT}...")
        ser = serial.Serial(WEMOS_PORT, BAUD_RATE, timeout=2)
        time.sleep(2)  # Allow connection to stabilize
        print("[DEBUG] Connected to Wemos D1 Mini.")
        return ser
    except serial.SerialException as e:
        print(f"[ERROR] Failed to connect to Wemos: {e}")
        return None

def send_command(ser, command):
    if ser and ser.is_open:
        ser.write(command.encode())
        print(f"[DEBUG] Sent command: {command}")
    else:
        print("[ERROR] Serial connection not open.")

def trigger_relay(ser):
    send_command(ser, 'X')
    print("[INFO] Relay turned ON.")

def deactivate_relay(ser):
    send_command(ser, 'Y')
    print("[INFO] Relay turned OFF.")

def reset_arduino(ser):
    send_command(ser, 'R')
    print("[INFO] Arduino Mega has been reset.")

def main():
    ser = connect_to_wemos()
    
    if not ser:
        return

    while True:
        print("\n[MENU] Select an action:")
        print("1. Turn Relay ON")
        print("2. Turn Relay OFF")
        print("3. Reset Arduino Mega")
        print("4. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            trigger_relay(ser)
        elif choice == '2':
            deactivate_relay(ser)
        elif choice == '3':
            reset_arduino(ser)
        elif choice == '4':
            print("[INFO] Exiting...")
            ser.close()
            break
        else:
            print("[ERROR] Invalid choice. Please select a valid option.")

if __name__ == "__main__":
    main()
