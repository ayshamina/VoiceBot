#!/usr/bin/env python3
"""
Simple development HTTP server with proper MIME types for modern web assets.
Serves the frontend on http://localhost:5173
"""
import http.server
import socketserver
import os

PORT = 5173
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class DevServerHandler(http.server.SimpleHTTPRequestHandler):
    # MIME types for modern web assets
    MIME_TYPES = {
        '.js': 'application/javascript; charset=utf-8',
        '.mjs': 'application/javascript; charset=utf-8',
        '.jsx': 'application/javascript; charset=utf-8',
        '.ts': 'application/typescript',
        '.tsx': 'application/typescript',
        '.json': 'application/json; charset=utf-8',
        '.css': 'text/css; charset=utf-8',
        '.html': 'text/html; charset=utf-8',
        '.svg': 'image/svg+xml',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.woff': 'font/woff',
        '.woff2': 'font/woff2',
        '.ttf': 'font/ttf',
        '.eot': 'application/vnd.ms-fontobject',
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        """Add headers for development."""
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()
    
    def send_response(self, code, message=None):
        """Override send_response to handle custom MIME types."""
        super().send_response(code, message)
    
    def do_GET(self):
        """Override GET to set proper MIME types."""
        # Map the request path to file
        path = self.translate_path(self.path)
        
        # Check if file exists
        if os.path.exists(path) and os.path.isfile(path):
            # Get file extension
            _, ext = os.path.splitext(path)
            
            # Get MIME type
            if ext in self.MIME_TYPES:
                mime_type = self.MIME_TYPES[ext]
            else:
                mime_type = 'application/octet-stream'
            
            # Send file with correct MIME type
            try:
                with open(path, 'rb') as f:
                    self.send_response(200)
                    self.send_header('Content-type', mime_type)
                    self.send_header('Content-Length', os.path.getsize(path))
                    self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                    self.send_header('Pragma', 'no-cache')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(f.read())
                    return
            except Exception as e:
                self.send_error(500, f"Error reading file: {e}")
                return
        
        # Fall back to default handler for directories
        super().do_GET()
    
    def log_message(self, format, *args):
        """Log request to console."""
        print(f'[{self.client_address[0]}] {format % args}')

if __name__ == '__main__':
    os.chdir(DIRECTORY)
    Handler = DevServerHandler
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Development server running at http://localhost:{PORT}/")
        print(f"Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
