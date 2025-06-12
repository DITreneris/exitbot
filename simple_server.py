#!/usr/bin/env python
"""
A very simple HTTP server to test connectivity
"""
import http.server
import socketserver
import json
import socket
import sys

PORT = 3000  # Changed to a different port


class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        # Different responses based on path
        if self.path == "/":
            response = {
                "status": "ok",
                "message": "Simple server is running",
                "version": "1.0.0",
            }
        elif self.path == "/test":
            response = {
                "status": "ok",
                "message": "Test endpoint is working",
                "data": {"test_id": 12345, "is_functional": True},
            }
        else:
            response = {
                "status": "not_found",
                "message": f"Endpoint {self.path} not found",
            }

        # Send the response
        self.wfile.write(json.dumps(response).encode())

    def log_message(self, format, *args):
        """Override log method to print to stdout"""
        print(f"{self.client_address[0]} - {format % args}")


if __name__ == "__main__":
    print(f"Starting simple server on port {PORT}")
    print(f"Access at: http://localhost:{PORT} or http://127.0.0.1:{PORT}")

    # Get ip address for local network access
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"Or from other devices on your network: http://{local_ip}:{PORT}")

    # Create and start the server
    try:
        with socketserver.TCPServer(("", PORT), SimpleHTTPRequestHandler) as httpd:
            print("Server running... press Ctrl+C to stop")
            httpd.serve_forever()
    except socket.error as e:
        if e.errno == 10048:  # Windows-specific error code for "Address already in use"
            print(f"ERROR: Port {PORT} is already in use. Try a different port.")
            print("You may have another server running on this port.")
            sys.exit(1)
        else:
            print(f"Socket error: {e}")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
