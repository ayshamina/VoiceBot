import http.server
import os
import socketserver
import urllib.request
import urllib.error
import urllib.parse

PORT = 8080
BACKEND = 'http://127.0.0.1:8001'

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def _proxy(self):
        target_url = BACKEND + self.path
        method = self.command
        headers = {k: v for k, v in self.headers.items() if k.lower() != 'host'}
        body = None
        if method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length) if length else None

        req = urllib.request.Request(target_url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                self.send_response(resp.status)
                for header, value in resp.getheaders():
                    if header.lower() in ('content-length', 'transfer-encoding', 'connection'):
                        continue
                    self.send_header(header, value)
                response_body = resp.read()
                self.send_header('Content-Length', str(len(response_body)))
                self.end_headers()
                self.wfile.write(response_body)
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            for header, value in e.headers.items():
                if header.lower() in ('content-length', 'transfer-encoding', 'connection'):
                    continue
                self.send_header(header, value)
            error_body = e.read()
            self.send_header('Content-Length', str(len(error_body)))
            self.end_headers()
            self.wfile.write(error_body)
        except Exception as e:
            self.send_error(502, str(e))

    def do_GET(self):
        if self.path.startswith('/api/v1'):
            self._proxy()
            return

        parsed = urllib.parse.urlparse(self.path)
        local_path = self.translate_path(parsed.path)
        if parsed.path != '/' and not parsed.path.startswith('/assets') and not os.path.exists(local_path):
            self.path = '/index.html'
        super().do_GET()

    def do_POST(self):
        if self.path.startswith('/api/v1'):
            self._proxy()
        else:
            super().do_POST()

    def do_PUT(self):
        if self.path.startswith('/api/v1'):
            self._proxy()
        else:
            super().do_PUT()

    def do_DELETE(self):
        if self.path.startswith('/api/v1'):
            self._proxy()
        else:
            super().do_DELETE()

    def do_PATCH(self):
        if self.path.startswith('/api/v1'):
            self._proxy()
        else:
            super().do_PATCH()

    def do_OPTIONS(self):
        if self.path.startswith('/api/v1'):
            self._proxy()
        else:
            super().do_OPTIONS()

if __name__ == '__main__':
    os.chdir(os.path.join(os.path.dirname(__file__), 'dist'))
    with socketserver.TCPServer(('', PORT), ProxyHandler) as httpd:
        print(f'Serving proxy on http://127.0.0.1:{PORT}')
        httpd.serve_forever()
