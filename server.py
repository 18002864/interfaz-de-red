from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse as urlparse

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        # Responder a las solicitudes OPTIONS con los encabezados de CORS adecuados
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        # Parse query parameters
        parsed_path = urlparse.urlparse(self.path)
        query = urlparse.parse_qs(parsed_path.query)

        # Log the received GET request
        print(f"Received GET request: {self.path}")
        print(f"Query parameters: {query}")

        # Prepare response content
        response = f"<html><body><h1>GET Request Received</h1><p>Path: {self.path}</p></body></html>"

        # Send headers with CORS
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.send_header('Access-Control-Allow-Origin', '*')  # Permite acceso desde cualquier origen
        self.end_headers()

        # Send the response body
        self.wfile.write(response.encode('utf-8'))

    def do_POST(self):
        # Log the received POST request
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        print(f"Received POST request: {post_data}")

        # Prepare response content
        # response = "F000000000000000000000004D656E73616A652064652070727565626100000000"
        # responseTurnAll = "F F F F F F F 0 808080 000000 FF0000 000000 4D656E73616A652064652070727565626100000000"
        # response_switch_0_on = "4000000000000000000000000000000000000000"
        # response_switch_1_on = "4000000000000000000000000000000000000000"
        # response_fan_on = "1000000000000000000000000000000000000000"\
        # response_LEDRGB_On = "0800000000000000000000000000000000000000"
        # response led red  = "0400000000000000000000000000000000000000"
        # response led green = "0200000000000000000000000000000000000000"
        # response heat on = "0100000000000000000000000000000000000000"
        # response slider 0 a tope = "0000FF0000000000000000000000000000000000"
        # response slider 1 a tope = "000000FF00000000000000000000000000000000"
        # response slider 2 a tope = "00000000FF000000000000000000000000000000"
        # response Set LED RGB to Blue (0000FF) = "00000000000000FFF00000000000000000000000"
        # response set PickColor to Red (FF0000) = "000000000000000000FF00000000000000000000"

        # Set SPEED to Max (F) no funciona
        # response = "000F000000000000000000000000000000000000"

        response = "0000FF0000000000000000000000000000000000"

        # Send headers with CORS
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.send_header('Access-Control-Allow-Origin', '*')  # Permite acceso desde cualquier origen
        self.end_headers()

        # Send the response body
        self.wfile.write(response.encode('utf-8'))

# Server setup
def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting server on port {port}...')
    httpd.serve_forever()

if __name__ == "__main__":
    run()
