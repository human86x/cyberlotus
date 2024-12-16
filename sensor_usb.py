from pymodbus.client import ModbusSerialClient

# Initialize the Modbus client
client = ModbusSerialClient(
    method='rtu',
    port='/dev/ttyUSB0',  # Adjust this to your actual device
    baudrate=4800,
    stopbits=1,
    bytesize=8,
    parity='N',
    timeout=1
)

# Function to read a register
def read_register(register):
    try:
        result = client.read_holding_registers(address=register, count=1, unit=1)  # Unit 1 is the default slave ID
        if not result.isError():
            value = result.registers[0]
            return value
        else:
            print(f"Error reading register {register}: {result}")
            return None
    except Exception as e:
        print(f"Exception reading register {register}: {e}")
        return None

# Open connection to the sensor
if client.connect():
    try:
        # Read values from the respective registers
        nitrogen = read_register(2)
        phosphorus = read_register(3)
        potassium = read_register(4)
        ph = read_register(5)
        temperature = read_register(6)

        # Display the values
        print(f"Nitrogen (N): {nitrogen}")
        print(f"Phosphorus (P): {phosphorus}")
        print(f"Potassium (K): {potassium}")
        print(f"pH: {ph / 100:.2f}")  # Assuming pH is returned as 100x the actual value
        print(f"Temperature: {temperature / 100:.2f} °C")  # Assuming temperature is 100x the actual value

    finally:
        # Close the client connection
        client.close()
else:
    print("Failed to connect to the sensor.")
