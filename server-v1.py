import serial
from http.server import BaseHTTPRequestHandler, HTTPServer

class MicrocontrollerDriver:
    def __init__(self, port='/dev/ttyUSB0', baudrate=115200):
        self.ser = serial.Serial(port, baudrate, timeout=1)

    def send_data(self, address, data):
        """
        Send data to a specific microcontroller by its address.
        The address can be a MAC address or a device ID.
        """
        packet = f"{address}:{data}"  # Example custom protocol packet: [Address][Data]
        self.ser.write(packet.encode())  # Send the data

    def receive_data(self):
        """
        Receive data from the microcontroller.
        """
        response = self.ser.readline().decode().strip()  # Receive and decode the response
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
        # Log the received POST request
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        print(f"Received POST request: {post_data}")

        # Extract data and send it to the microcontroller via the driver
        # For example, sending a command to turn on LED on Microcontroller 1 (address '01')
        self.driver.send_data("01", post_data)

        # Wait for a response from the microcontroller
        mc_response = self.driver.receive_data()

        # Send headers with CORS
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.send_header('Access-Control-Allow-Origin', '*')  # Allow access from any origin
        self.end_headers()

        # Send the response body (microcontroller response)
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
