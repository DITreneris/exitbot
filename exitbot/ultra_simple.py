"""
Ultra simple HTTP server with advanced diagnostics
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import socket
import os
import sys
import platform
import subprocess

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print(f"Received request for: {self.path}")
        if self.path == '/' or self.path == '':
            # Root endpoint
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
            <html>
            <head><title>ExitBot</title></head>
            <body>
                <h1>ExitBot Deployment Test</h1>
                <p style="color: green; font-weight: bold;">Status: Running</p>
                <ul>
                    <li><a href="/test">Test Endpoint</a></li>
                    <li><a href="/health">Health Endpoint</a></li>
                </ul>
            </body>
            </html>
            """)
        elif self.path == '/test':
            # Test endpoint
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status":"ok","test":"successful"}')
        elif self.path == '/health':
            # Health endpoint
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        else:
            # 404 for anything else
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body><h1>404: Not Found</h1></body></html>')

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def check_port_available(port):
    """Check if a port is available."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) != 0

def run_diagnostics():
    """Run diagnostics to help troubleshoot server issues."""
    print("\nRunning diagnostics...")
    print(f"Python version: {sys.version}")
    print(f"Operating system: {platform.platform()}")
    
    # Check firewall
    if platform.system() == "Windows":
        try:
            output = subprocess.check_output("netsh advfirewall show allprofiles", shell=True).decode()
            print("\nFirewall Status:")
            print(output.split("State")[1].split("\n")[0])
        except Exception as e:
            print(f"Error checking firewall: {e}")
    
    # Check network connectivity
    try:
        socket.gethostbyname("www.google.com")
        print("\nInternet connectivity: OK")
    except Exception:
        print("\nInternet connectivity: Failed")
    
    print("\nAvailable ports:")
    for port in [8000, 8080, 5000, 9999]:
        status = "Available" if check_port_available(port) else "In use"
        print(f"Port {port}: {status}")

if __name__ == '__main__':
    # Use port 9999 which is rarely used
    PORT = 9999
    
    # Run network diagnostics
    run_diagnostics()
    
    # Check if the port is available
    if not check_port_available(PORT):
        print(f"\nERROR: Port {PORT} is already in use.")
        print("Please choose a different port or close the application using this port.")
        sys.exit(1)
    
    HOST = '127.0.0.1'  # Only listen on localhost for security
    
    server_address = (HOST, PORT)
    try:
        httpd = HTTPServer(server_address, SimpleHandler)
        
        local_ip = get_ip()
        
        print('\n' + '=' * 50)
        print(f'Starting HTTP server on {HOST} port {PORT}')
        print('=' * 50)
        print(f'You can access the server at:')
        print(f'- http://localhost:{PORT}')
        print(f'- http://127.0.0.1:{PORT}')
        print('=' * 50)
        print('Press Ctrl+C to stop the server')
        
        httpd.serve_forever()
    except OSError as e:
        print(f"\nERROR: Could not start server: {e}")
        print("This might be due to firewall settings or the port being in use.")
        print("Try using a different port or running with administrative privileges.")
    except KeyboardInterrupt:
        print("\nServer stopped.") 