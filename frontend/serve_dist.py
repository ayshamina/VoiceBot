#!/usr/bin/env python3
"""
Development server for serving the built React frontend.
Serves the compiled dist/ folder on http://localhost:5173
Proxies API requests to the backend on http://localhost:8000
"""
import http.server
import socketserver
import os
import mimetypes
import urllib.request
import urllib.error
import json

PORT = 5173
DIST_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist')
BACKEND_URL = 'http://localhost:8000'

# Register MIME types for bundled assets
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/css', '.css')
mimetypes.add_type('image/svg+xml', '.svg')
mimetypes.add_type('application/json', '.json')

class ProxyServerHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIST_DIRECTORY, **kwargs)
    
    def do_GET(self):
        """Handle GET requests - proxy API calls, serve static files."""
        # Proxy API requests to backend
        if self.path.startswith('/api/'):
            self._proxy_request('GET')
            return
        
        # Serve static files
        super().do_GET()
    
    def do_POST(self):
        """Handle POST requests - proxy to backend."""
        if self.path.startswith('/api/'):
            self._proxy_request('POST')
        else:
            super().do_POST()
    
    def do_PUT(self):
        """Handle PUT requests - proxy to backend."""
        if self.path.startswith('/api/'):
            self._proxy_request('PUT')
        else:
            self.send_error(405)
    
    def do_DELETE(self):
        """Handle DELETE requests - proxy to backend."""
        if self.path.startswith('/api/'):
            self._proxy_request('DELETE')
        else:
            self.send_error(405)
    
    def _proxy_request(self, method):
        """Proxy request to backend."""
        target_url = BACKEND_URL + self.path
        
        # Get request body if present
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else None
        
        # Copy headers
        headers = {}
        for header, value in self.headers.items():
            if header.lower() not in ('host', 'connection', 'content-length'):
                headers[header] = value
        
        try:
            # Make request to backend
            req = urllib.request.Request(
                target_url,
                data=body,
                headers=headers,
                method=method
            )
            
            with urllib.request.urlopen(req) as response:
                # Copy response status
                self.send_response(response.status)
                
                # Copy response headers
                for header, value in response.getheaders():
                    if header.lower() not in ('server', 'date', 'content-encoding'):
                        self.send_header(header, value)
                
                # Copy response body
                response_body = response.read()
                self.send_header('Content-Length', len(response_body))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(response_body)
                
        except urllib.error.HTTPError as e:
            # Forward HTTP errors from backend
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            error_body = json.dumps({'error': str(e.reason)}).encode()
            self.send_header('Content-Length', len(error_body))
            self.end_headers()
            self.wfile.write(error_body)
        except Exception as e:
            # Handle connection errors
            self.send_response(503)
            self.send_header('Content-Type', 'application/json')
            error_body = json.dumps({'error': f'Backend connection failed: {str(e)}'}).encode()
            self.send_header('Content-Length', len(error_body))
            self.end_headers()
            self.wfile.write(error_body)
    
    def end_headers(self):
        """Add headers for development."""
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()
    
    def log_message(self, format, *args):
        """Log requests to console."""
        print(f'[{self.client_address[0]}] {format % args}')

if __name__ == '__main__':
    os.chdir(DIST_DIRECTORY)
    Handler = ProxyServerHandler
    
    print(f"Serving built frontend from: {DIST_DIRECTORY}")
    print(f"Proxying API requests to: {BACKEND_URL}")
    print(f"Development server running at http://localhost:{PORT}/")
    print(f"Press Ctrl+C to stop")
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
