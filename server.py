from http.server import HTTPServer, BaseHTTPRequestHandler
import re
import requests
import subprocess

# Global Variables
last_post_data = None
response_list = list("000000000000000000000000")
device_state = {}  # Dictionary to track each device's state
SRC_PORT = 8080  # Source port for this application
DST_PORT = 9090  # Example destination port for the virtual device
TO = 0x04  # Example destination address, should match your actual `TO` in the C code
FROM = 0x02  # Example source address, should match your actual `FROM` in the C code
# Reserved fields
reserved_one = "0"
reserved_two = "0"
DEVICE_CODES = {
    "SW0": 0x1,
    "SW1": 0x2,
    "SLIDER0": 0x3,
    "PICKER": 0x4,
    "HEAT": 0x5,
    "LEDRED": 0x6,
    "LEDGRN": 0x7,
    "FAN": 0x8,
    "LEDRGB": 0x9,
    "LCD": 0xA
}

# Instruction Keywords
keywords = {
    "activate": "ON",
    "deactivate": "OFF",
    "set": "SET",
    "lcd": "LCD"
}

# Device Command Mappings
device_commands = {
    "SW0": {"activate": "ON", "deactivate": "OFF"},
    "SW1": {"activate": "ON", "deactivate": "OFF"},
    "LCD": {"set": "SET"}
}

# HTTP Request Handler
class RequestHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        global last_post_data
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length).decode("utf-8")

        # Parse incoming data and handle instructions
        if post_data != last_post_data:
            command = parse_command(post_data)
            process_command(command)
            last_post_data = post_data
        
        # Respond with the latest command for verification
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(last_post_data.encode("utf-8"))

def parse_command(post_data):
    """Parse incoming data to extract command details."""
    message = bytes.fromhex(post_data[24:]).decode("utf-8").upper()
    elements = message.split()
    
    # Extract the main keyword, device, destination group, and any parameters
    keyword = elements[0]
    device = elements[1] if len(elements) > 1 else None
    destination_group = elements[2] if len(elements) > 2 else None
    params = elements[3:] if len(elements) > 3 else []

    return {"keyword": keyword, "device": device, "destination_group": destination_group, "params": params}

def process_command(command):
    """Route command to the appropriate function based on keyword."""
    keyword = command["keyword"]
    device = command["device"]
    destination_group = command["destination_group"]
    
    if keyword == keywords["activate"]:
        activate_device(device, destination_group)
    elif keyword == keywords["deactivate"]:
        deactivate_device(device, destination_group)
    elif keyword == keywords["set"]:
        set_device_value(device, destination_group, command["params"])
    elif keyword == keywords["lcd"]:
        set_lcd_message(destination_group, command["params"])

def send_serial_command(to_group, from_group, device_code, payload):
    """Helper function to send a command over serial through the HTTP server."""
    url = 'http://localhost:8181'  # Replace with the actual endpoint for the serial driver
    headers = {'Content-Type': 'application/json'}
    
    # Construct protocol message format
    protocol_message = {
        "to": to_group,
        "from": from_group,
        "device_code": device_code,
        "payload": payload
    }
    
    # Send the request to the serial driver endpoint
    response = requests.post(url, json=protocol_message, headers=headers)
    print(f"Response from serial driver: {response.text}")
    return response

# Device functions
def activate_device(device, destination_group):
    print(f"Activating {device} in group {destination_group}")
    device_code = DEVICE_CODES.get(device)
    source_group = "G4"  # Example source group

    if device_code is not None:
        control = "ON"  # Example control for activation
        command_packet = build_command_packet(source_group, destination_group, control, device_code, "ACTIVATE")
        execute_driver_command(command_packet)
    else:
        print(f"Unknown device: {device}")

def deactivate_device(device, destination_group):
    print(f"Deactivating {device} in group {destination_group}")
    device_code = DEVICE_CODES.get(device)
    source_group = "G4"  # Example source group

    if device_code is not None:
        control = "OFF"  # Example control for deactivation
        command_packet = build_command_packet(source_group, destination_group, control, device_code, "DEACTIVATE")
        execute_driver_command(command_packet)
    else:
        print(f"Unknown device: {device}")

def set_device_value(device, destination_group, params):
    print(f"Setting {device} in group {destination_group} with parameters: {params}")
    device_code = DEVICE_CODES.get(device)
    source_group = "G4"  # Example source group

    if device_code is not None:
        control = "SET"  # Example control for setting values
        extra_value = params[0]  # Assuming params[0] is the value to set, such as "FF5733"
        # Pass extra_value to ensure it’s appended to protocol_response
        command_packet = build_command_packet(source_group, destination_group, control, device_code, extra_value=extra_value)
        execute_driver_command(command_packet)
    else:
        print(f"Unknown device: {device}")

def set_lcd_message(destination_group, params):
    print(f"Setting LCD message in group {destination_group} with params: {params}")
    device_code = DEVICE_CODES.get("LCD")
    source_group = "G4"  # Example source group

    if device_code is not None:
        control = "LCD"  # Example control for LCD message
        message_content = " ".join(params)
        command_packet = build_command_packet(source_group, destination_group, control, device_code, f"LCD {message_content}")
        execute_driver_command(command_packet)
    else:
        print("LCD device code not found.")

def calculate_checksum(to, from_addr, length):
    """Calculate checksum as per the C implementation."""
    return ((to + from_addr + length) ^ 0xFF) + 1

def build_command_packet(source_group, destination_group, control, device, action=None, extra_value=None):
    """Builds a command packet string with the header and payload."""
    # Extract and zero-pad `source_group` and `destination_group`
    source_group = re.match(r"G(\d+)", source_group).group(1).zfill(2)  # Example: "G0" -> "00"
    destination_group = re.match(r"G(\d+)", destination_group).group(1).zfill(2)  # Example: "G4" -> "04"

    # Build the core protocol response with the required fields
    protocol_response = f"{source_group}{reserved_one}{destination_group}{reserved_two}{control}0{device}1"

    # Append `extra_value` if provided
    if extra_value:
        protocol_response += extra_value  # Append color code or any additional parameter

    # Recalculate length after appending `extra_value`
    length = len(protocol_response)

    # Adjusted maximum length to 25 characters
    if not (9 <= length <= 25):
        raise ValueError(f"Protocol response length is out of bounds: {length} characters.")

    # Calculate checksum for the final packet
    checksum = calculate_checksum(TO, FROM, length)
    
    # Construct the final packet in the correct format
    packet = f"J {TO} {FROM} {length} {checksum} {protocol_response}"
    print("Constructed protocol_response:", protocol_response)  # Debugging step to check protocol structure
    return packet

def execute_driver_command(command_packet):
    """Executes the serial driver with the constructed packet."""
    try:
        # Run the serial driver binary with the packet as argument
        print("command_packet", command_packet)
        process = subprocess.Popen(["./serial_driver", command_packet], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()
        
        if process.returncode != 0:
            print(f"Error from driver: {error.decode('utf-8')}")
        else:
            print(f"Driver output: {output.decode('utf-8')}")
            
    except FileNotFoundError:
        print("Error: serial_driver binary not found. Make sure to compile it first with 'gcc serial_driver.c -o serial_driver'")
    except PermissionError:
        print("Error: Permission denied. Try running with sudo or check file permissions")
    except Exception as e:
        print(f"Error executing driver: {str(e)}")


# Run HTTP Server
def run(server_class=HTTPServer, handler_class=RequestHandler, port=8080):
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting server on port {port}...")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
