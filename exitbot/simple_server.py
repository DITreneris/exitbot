"""
Ultra simple HTTP server for testing
"""
from http.server import HTTPServer, BaseHTTPRequestHandler


class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            # Root endpoint
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"""
            <html>
            <head><title>ExitBot</title></head>
            <body>
                <h1>ExitBot Deployment Test</h1>
                <p>Status: Running</p>
                <ul>
                    <li><a href="/test">Test Endpoint</a></li>
                    <li><a href="/health">Health Endpoint</a></li>
                </ul>
            </body>
            </html>
            """
            )
        elif self.path == "/test":
            # Test endpoint
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok","test":"successful"}')
        elif self.path == "/health":
            # Health endpoint
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        else:
            # 404 for anything else
            self.send_response(404)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>404: Not Found</h1></body></html>")


if __name__ == "__main__":
    server_address = ("", 8000)  # Empty string means all interfaces
    httpd = HTTPServer(server_address, SimpleHandler)
    print("Starting basic HTTP server on port 8000...")
    print("Access at: http://127.0.0.1:8000")
    print("Test endpoint: http://127.0.0.1:8000/test")
    print("Health endpoint: http://127.0.0.1:8000/health")
    httpd.serve_forever()
