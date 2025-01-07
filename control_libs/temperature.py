def read_solution_temperature():
    response = send_command_and_get_response(b'T')
    if response is not None:
        try:
            return float(response)
        except ValueError:
            print(f"Error reading temperature: {response}")
    return None