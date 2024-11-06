import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse as urlparse

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
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
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8').strip()  # Strip any extra whitespace
        print(f"Received POST request: {post_data}")
        
        # Map actions to responses
        response_map = {
            "switch_0_on": "00F0FF000000000000000000",
            "switch_1_on": "4000000000000000000000000000000000000000",
            "fan_on": "1000000000000000000000000000000000000000",
            "heat_on": "0100000000000000000000000000000000000000",
            "led_red_on": "0400000000000000000000000000000000000000",
            "led_green_on": "0200000000000000000000000000000000000000",
            "slider_0_max": "0000FF0000000000000000000000000000000000",
        }
        
        print(f"Action received: '{post_data}'")
        
        # Create reverse mapping
        reverse_map = {value: key for key, value in response_map.items()}
        
        # Try to find the command in both the original map and reverse map
        response = response_map.get(post_data, None)  # Try original mapping first
        if response is None:
            # If not found in original map, check reverse map
            command = reverse_map.get(post_data, None)
            if command:
                response = post_data  # If found in reverse map, use the original input as response
            else:
                response = "Unknown command"
        
        print(f"Response to send: '{response}'")
        
        if response != "Unknown command":
            # Call the driver to send this response to the Pico
            execute_driver_command(response)
        
        # Send the response to the client
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

def execute_driver_command(command):
    try:
        # Use the compiled binary, not the .c file
        process = subprocess.Popen(["./serial_driver", command], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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

# Server setup
def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting server on port {port}...')
    httpd.serve_forever()

if __name__ == "__main__":
    run()
