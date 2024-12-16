from pymodbus.client import ModbusSerialClient as ModbusClient

# Configure Modbus client
client = ModbusClient(
    method='rtu',
    port='/dev/ttyUSB0',  # Update to your actual port
    baudrate=4800,
    stopbits=1,
    bytesize=8,
    parity='N',
    timeout=2
)

# Connect to the client
if client.connect():
    try:
        # Read multiple registers (humidity, temperature, conductivity, pH, N, P, K)
        result = client.read_holding_registers(address=0, count=7, slave=1)
        if result.isError():
            print(f"Error reading registers: {result}")
        else:
            # Parse results
            data = result.registers
            humidity = data[0] * 0.1  # Convert to %
            temperature = data[1] * 0.1  # Convert to °C
            conductivity = data[2]  # μS/cm
            ph = data[3] * 0.1  # Convert to actual pH
            nitrogen = data[4]  # mg/kg
            phosphorus = data[5]  # mg/kg
            potassium = data[6]  # mg/kg

            print(f"Humidity: {humidity}%")
            print(f"Temperature: {temperature}°C")
            print(f"Conductivity: {conductivity} μS/cm")
            print(f"pH: {ph}")
            print(f"Nitrogen: {nitrogen} mg/kg")
            print(f"Phosphorus: {phosphorus} mg/kg")
            print(f"Potassium: {potassium} mg/kg")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()
else:
    print("Unable to connect to the Modbus device")
