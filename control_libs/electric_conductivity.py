

def get_ec(ser):
    response = send_command_and_get_response(ser, b'D')
    if response is not None:
        try:
            #print(f"------------Reading EC:{response}")
            #return float(response)
            return response
        except ValueError:
            print(f"Error reading EC: {response}")
    return None