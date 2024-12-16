from pymodbus.client import ModbusSerialClient
import logging

# Enable verbose logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

# Initialize the Modbus client
client = ModbusSerialClient(
    method='rtu',
    port='/dev/ttyUSB0',
    baudrate=4800,
    stopbits=1,
    bytesize=8,
    parity='N',
    timeout=1
)

if client.connect():
    try:
        # Attempt to read from register 0x0002 (Nitrogen)
        response = client.read_holding_registers(address=2, count=1, slave=1)
        if not response.isError():
            print(f"Response: {response.registers}")
        else:
            print(f"Error: {response}")
    finally:
        client.close()
else:
    print("Failed to connect to the sensor.")
