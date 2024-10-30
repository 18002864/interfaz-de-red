import serial
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse as urlparse

class MicrocontrollerDriver:
    def __init__(self, port='/dev/ttyUSB0', baudrate=115200):
        # Establish serial connection with the microcontroller
        self.ser = serial.Serial(port, baudrate, timeout=1)

    def format_data_to_protocol(self, data):
        """
        Format data according to the protocol provided.
        Convert the incoming command into the appropriate bit structure and hex format.
        """
        # Extract values from the incoming data dictionary
        lcd = data.get('LCD', 0)
        sw0 = data.get('SW0', 0)
        sw1 = data.get('SW1', 0)
        fan = data.get('FAN', 0)
        led_red = data.get('LEDRED', 0)
        led_green = data.get('LEDGRN', 0)
        speed = data.get('SPEED', 0)
        slider0 = data.get('SLIDER0', 0)
        slider1 = data.get('SLIDER1', 0)
        slider2 = data.get('SLIDER2', 0)
        message = data.get('Msg', "")

        # Format each field to hex
        formatted_data = ""
        formatted_data += format(lcd, '01X')  # 1-bit LCD
        formatted_data += format(sw0, '01X')  # 1-bit SW0
        formatted_data += format(sw1, '01X')  # 1-bit SW1
        formatted_data += format(fan, '01X')  # 1-bit FAN
        formatted_data += format(led_red, '01X')  # 1-bit LED Red
        formatted_data += format(led_green, '01X')  # 1-bit LED Green
        formatted_data += format(speed, '01X')  # 4-bit Speed
        formatted_data += "0000"  # 4-bit Space
        formatted_data += format(slider0, '02X')  # 8-bit Slider 0
        formatted_data += format(slider1, '02X')  # 8-bit Slider 1
        formatted_data += format(slider2, '02X')  # 8-bit Slider 2
        formatted_data += "0000"  # 4-bit Space
        # LED RGB and PickColor handling can be added here similarly if needed
        
        # Format the message, ensure it's in hex and is 32 bytes (64 hex chars)
        hex_message = message.encode('utf-8').hex()
        hex_message = hex_message.ljust(64, '0')[:64]

        # Append the message at the end
        formatted_data += hex_message
        
        return formatted_data

    def send_data(self, data):
        """
        Send the formatted protocol data to the microcontroller.
        """
        formatted_data = self.format_data_to_protocol(data)
        print(f"Sending formatted packet to microcontroller: {formatted_data}")
        self.ser.write(formatted_data.encode())  # Send the hex data over UART/USB

    def receive_data(self):
        """
        Receive data from the microcontroller.
        """
        response = self.ser.readline().decode().strip()  # Receive and decode the response
        print(f"Received from microcontroller: {response}")
        return response

    def close(self):
        self.ser.close()


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Create a driver instance that connects to the microcontroller
        self.driver = MicrocontrollerDriver(port='/dev/ttyUSB0')
        super().__init__(*args, **kwargs)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        # Handle GET requests (used for status checks or diagnostics)
        parsed_path = urlparse.urlparse(self.path)
        query = urlparse.parse_qs(parsed_path.query)
        print(f"Received GET request: {self.path}")
        print(f"Query parameters: {query}")
        response = f"<html><body><h1>GET Request Received</h1><p>Path: {self.path}</p></body></html>"
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

    def do_POST(self):
        # Handle POST requests (commands from the virtual device)
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        print(f"Received POST request: {post_data}")

        # Parse the incoming POST data as a dictionary
        parsed_data = urlparse.parse_qs(post_data)

        # Convert it to a dictionary with actual values for easier handling
        data = {
            "LCD": int(parsed_data.get('LCD', [0])[0]),
            "SW0": int(parsed_data.get('SW0', [0])[0]),
            "SW1": int(parsed_data.get('SW1', [0])[0]),
            "FAN": int(parsed_data.get('FAN', [0])[0]),
            "LEDRED": int(parsed_data.get('LEDRED', [0])[0]),
            "LEDGRN": int(parsed_data.get('LEDGRN', [0])[0]),
            "SPEED": int(parsed_data.get('SPEED', [0])[0]),
            "SLIDER0": int(parsed_data.get('SLIDER0', [0])[0]),
            "SLIDER1": int(parsed_data.get('SLIDER1', [0])[0]),
            "SLIDER2": int(parsed_data.get('SLIDER2', [0])[0]),
            "Msg": parsed_data.get('Msg', [""])[0],
        }

        # Send the formatted data to the microcontroller through the driver
        self.driver.send_data(data)

        # Wait for a response from the microcontroller
        mc_response = self.driver.receive_data()

        # Send headers with CORS
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        # Send the response back to the virtual device
        self.wfile.write(mc_response.encode('utf-8'))

    def __del__(self):
        # Ensure to close the driver when the handler is destroyed
        self.driver.close()

# Server setup
def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting server on port {port}...')
    httpd.serve_forever()

if __name__ == "__main__":
    run()
