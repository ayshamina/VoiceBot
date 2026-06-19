#!/usr/bin/env python3
"""
Flask-based development server for serving the React frontend.
Serves on http://localhost:5173
"""
from flask import Flask, send_from_directory, send_file
import os
import mimetypes

app = Flask(__name__, static_folder='.', static_url_path='')

# Register MIME types for modern web assets
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('application/javascript', '.mjs')
mimetypes.add_type('application/javascript', '.jsx')
mimetypes.add_type('text/css', '.css')
mimetypes.add_type('image/svg+xml', '.svg')

@app.route('/')
@app.route('/<path:path>')
def serve(path='index.html'):
    """Serve static files with proper MIME types."""
    # Try to serve the requested file
    if path and os.path.isfile(path):
        return send_from_directory('.', path)
    
    # For SPA routing - serve index.html
    if path and not '.' in path:
        return send_file('index.html', mimetype='text/html')
    
    # Default to index.html
    return send_file('index.html', mimetype='text/html')

if __name__ == '__main__':
    print("Development server running at http://localhost:5173/")
    print("Press Ctrl+C to stop")
    app.run(host='localhost', port=5173, debug=False)
