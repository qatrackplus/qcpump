"""Simple server for testing 307 redirects"""

from http.server import HTTPServer, BaseHTTPRequestHandler


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(307)
        self.end_headers()
        self.wfile.write(b'Temporary Redirect')


httpd = HTTPServer(('127.0.0.1', 8000), SimpleHTTPRequestHandler)
httpd.serve_forever()
