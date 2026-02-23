from http.server import BaseHTTPRequestHandler
import socketserver
import threading
import ssl
from core.logger.logger_setup import setup_logging
import logging

setup_logging()
logger = logging.getLogger(__name__)

HTTP_PORT = 80
HTTPS_PORT = 443
DOMAIN = "trip-kzn.ru"

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile='fullchain.pem', keyfile='certificate.key')


class HTTPSHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.send_header('Content-Length', len(b"s4vaki"))
        self.end_headers()
        self.wfile.write(b"s4vaki")

    def do_POST(self):
        self.do_GET()

class HTTPRedirect(HTTPSHandler):
    def do_GET(self):
        self.send_response(301)
        self.send_header('Location', f'https://trip-kzn.ru:{HTTPS_PORT}{self.path}')
        self.end_headers()

def run_http():
    httpd = socketserver.TCPServer(("", HTTP_PORT), HTTPRedirect)
    logger.info("HTTP сервер запущен")
    httpd.serve_forever()



def simulate_user_creation():
    import requests
    import time
    
    # Wait for accounts service to start
    time.sleep(5) 
    
    try:
        response = requests.post(
            'http://accounts:5000/create_user',
            json={
                'email': 'test_from_web@example.com',
                'password': 'secure_password_123'
            }
        )
        logger.info(f"User creation response: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Failed to call accounts service: {e}")

if __name__ == '__main__':
    # Run user creation test in background
    test_thread = threading.Thread(target=simulate_user_creation, daemon=True)
    test_thread.start()

    http_thread = threading.Thread(target=run_http, daemon=True)
    http_thread.start()
    with socketserver.TCPServer(("", HTTPS_PORT), HTTPSHandler) as httpd:
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
        logger.info(f"Сайт запущен на https://trip-kzn.ru:{HTTPS_PORT}")
        httpd.serve_forever()
