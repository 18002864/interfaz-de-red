
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse as urlparse
import re
import requests

# ================== GLOBAL VARIABLES ==================
last_post_data = None
message = ""
message_elements = ""

# Define constants to avoid repetition
ALLOWED_METHODS = 'POST, OPTIONS'
ALLOWED_HEADERS = 'Content-Type'
PORT = 8080

reserved_one = "0"
reserved_two = "00"

# Protocol settings (simulated values)
sent_request = "304006011"

# ================== HTTP REQUEST HANDLER ==================
def handle_options_request(handler):
    '''Handle OPTIONS request to support CORS preflight.'''
    handler.send_response(200)
    handler.send_header('Access-Control-Allow-Origin', '*')
    handler.send_header('Access-Control-Allow-Methods', ALLOWED_METHODS)
    handler.send_header('Access-Control-Allow-Headers', ALLOWED_HEADERS)
    handler.end_headers()

def handle_post_request(handler):
    '''Handle POST requests, processing data and sending response.'''
    global last_post_data, message, message_elements

    content_length = int(handler.headers['Content-Length'])
    post_data = handler.rfile.read(content_length).decode('utf-8')
    
    # Update the global message and elements
    message = bytes.fromhex(post_data[24:]).decode('utf-8').upper()
    message_elements = message.split()
    
    # Process new message if it differs from the last
    if post_data != last_post_data:
        print(f"VD --> Operation: {post_data}")
        last_post_data = post_data
        print("VD --> Message Instruction: ", message)

        # Updated handling based on reordered parameters
        process_message_elements(message_elements)

    # Respond with the last received request
    response = last_post_data
    handler.send_response(200)
    handler.send_header('Content-type', 'text/plain')
    handler.send_header('Access-Control-Allow-Origin', '*')
    handler.end_headers()
    handler.wfile.write(response.encode('utf-8'))

def process_message_elements(elements):
    '''Process elements based on updated logical order and commands.'''
    for index, keyword in enumerate(elements):
        if keyword in keyword_list:
            target_device = elements[0]  # Adjusted order: device first
            if keyword == "ACT":
                device_activation_commands.get(target_device, lambda: None)()
            elif keyword == "DEACT":
                device_deactivation_commands.get(target_device, lambda: None)()
            elif keyword == "SET":
                device_set_commands.get(elements[index + 1], lambda: None)()
            elif keyword == "LCD":
                lcd_messaging_command.get("LCD", lambda: None)()

class CustomHandler(BaseHTTPRequestHandler):
    '''Custom HTTP request handler to manage POST and OPTIONS requests.'''
    def log_request(self, code='-', size='-'):
        pass

    def log_message(self, format, *args):
        pass

    def do_OPTIONS(self):
        handle_options_request(self)

    def do_POST(self):
        handle_post_request(self)

def run(server_class=HTTPServer, port=PORT):
    '''Run the HTTP server on the specified port.'''
    server_address = ('', port)
    httpd = server_class(server_address, CustomHandler)
    print(f'Starting server on port {port}...')
    httpd.serve_forever()

# ================== DEVICE COMMAND FUNCTIONS ==================
def DEVICE_ACTIVATION(device, target, command, extra_value=None):
    '''Activate a device with the new order: device, command, target.'''
    group_id, src_port, dst_port, device_code = 0x9, 8080, 9090, 0
    control = protocol_sent_request_dictionary[command][1]
    device_id = protocol_sent_request_dictionary[target][1]

    protocol_response = f"{group_id}{reserved_one}{dst_port}{reserved_two}{control}0{device_id}1"
    if extra_value:
        protocol_response += extra_value

    if 9 <= len(protocol_response) <= 17:
        print("APP --> Protocol Response:", protocol_response)

    # Send protocol
    payload_data = protocol_response
    protocol_message = create_protocol(group_id, src_port, dst_port, device_code, payload_data)
    send_protocol_message(protocol_message)

def DEVICE_DEACTIVATION(device, target):
    '''Deactivate a device with the new parameter order.'''
    group_id, src_port, dst_port, device_code = 0x9, 8080, 9090, 0
    control = protocol_sent_request_dictionary[device][1]
    device_id = protocol_sent_request_dictionary[target][1]

    protocol_response = f"{group_id}{reserved_one}{dst_port}{reserved_two}{control}1{device_id}0"
    if 9 <= len(protocol_response) <= 17:
        print("APP --> Protocol Response:", protocol_response)

# ================== PROTOCOL CONSTRUCTION ==================
def create_protocol(group_id, src_port, dst_port, device_code, payload_data):
    '''Create protocol message with header and payload.'''
    header = f"{group_id:04b}{src_port:016b}{dst_port:016b}{device_code:04b}"
    header_hex = hex(int(header, 2))[2:].zfill(len(header) // 4)
    full_message = header_hex + payload_data
    return full_message

def send_protocol_message(protocol_message):
    '''Send protocol message to external server.'''
    url = 'http://localhost:8181'
    headers = {'Content-Type': 'application/json'}
    data = {'protocol_message': protocol_message}
    response = requests.post(url, json=data, headers=headers)
    print("Response from server:", response.text)

# ================== LCD MESSAGE HANDLING ==================
def MESSAGE_LCD(target, content):
    '''Send message to LCD based on target and content.'''
    lcd = device_vd_dictionary["LCD"]
    position, hex_value = lcd
    response_list[position] = str(hex_value)
    message_hex = content.encode('utf-8').hex()
    partial_response = ''.join(response_list) + message_hex.upper()
    response = partial_response + "0" * (66 - len(partial_response)) if len(partial_response) < 66 else partial_response
    print("Response:", response)

# ================== HELPER DATA STRUCTURES ==================
keyword_list = ["ACT", "DEACT", "SET", "LCD"]

protocol_sent_request_dictionary = {
    "LCD": [5, 0], "SW0": [2, 1], "SW1": [2, 2], "SLIDERS": [2, 3],
    "PICKER": [2, 4], "HEAT": [5, 5], "LEDRED": [5, 6], "LEDGRN": [5, 7],
    "FAN": [5, 8], "LEDRGB": [5, 9]
}

device_vd_dictionary = {
    "LCD": [0, 8], "SW0": [0, 4], "SW1": [0, 2], "FAN": [0, 1],
    "LEDRGB": [1, 8], "LEDRED": [1, 4], "LEDGRN": [1, 2], "HEAT": [1, 1],
    "SPEED": [2, list(range(16))], "SPACE1": [3, 0], "SLIDER0": [[4, 5], list(range(16))],
    "SLIDER1": [[6, 7], list(range(16))], "SLIDER2": [[8, 9], list(range(16))],
    "SPACE2": [10, 0], "LED RGB": [[11, 12, 13, 14, 15, 16], list(range(16))],
    "SPACE3": [17, 0], "ColorPicker": [[18, 19, 20, 21, 22, 23], list(range(16))]
}

# Command mappings
device_set_commands = {
    "SLIDER0": lambda: SET_SLIDER0(True, message.split("> ", 1)[1]),
    "SLIDER1": lambda: SET_SLIDER1(True, message.split("> ", 1)[1]),
    "SLIDER2": lambda: SET_SLIDER2(True, message.split("> ", 1)[1]),
    "PickColor": lambda: SET_COLORPICKER(True, message.split("> ", 1)[1]),
    "SW0": lambda: SET_SW0(True, message.split("> ", 1)[1]),
    "SW1": lambda: SET_SW1(True, message.split("> ", 1)[1]),
    "HEAT": lambda: SET_HEAT(True, message.split("> ", 1)[1]),
    "LEDRED": lambda: SET_LEDRED(True, message.split("> ", 1)[1]),
    "LEDGRN": lambda: SET_LEDGRN(True, message.split("> ", 1)[1]),
    "FAN": lambda: SET_FAN(True, message.split("> ", 1)[1]),
    "LEDRGB": lambda: SET_LEDRGB(True, message.split("> ", 1)[1]),
    "LCD": lambda: SET_LCD(True, message.split("> ", 1)[1])
}

# Mapping for LCD command
lcd_messaging_command = {
    "LCD": lambda: MESSAGE_LCD(
        message_elements[0], 
        " ".join(message_elements[2:])
    )
}

if __name__ == "__main__":
    run()
