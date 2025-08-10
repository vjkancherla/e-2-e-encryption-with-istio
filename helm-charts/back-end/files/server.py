#!/usr/bin/env python3

import http.server
import socketserver
import json
import os
import socket
from datetime import datetime
from urllib.parse import urlparse, parse_qs

PORT = int(os.environ.get('PORT', 8080))

class SimpleBackendHandler(http.server.BaseHTTPRequestHandler):
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/health':
            self.send_health_response()
        elif self.path == '/info':
            self.send_info_response()
        elif self.path.startswith('/echo/'):
            # Extract message from path
            message = self.path[6:]  # Remove '/echo/' prefix
            self.send_echo_response(message)
        else:
            self.send_not_found()
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/echo':
            self.handle_echo_post()
        else:
            self.send_not_found()
    
    def send_health_response(self):
        """Send health check response"""
        health_data = {
            'status': 'healthy',
            'service': 'backend-app',
            'timestamp': datetime.now().isoformat(),
            'hostname': socket.gethostname(),
            'port': PORT
        }
        
        self.send_json_response(200, health_data)
    
    def send_info_response(self):
        """Send service information"""
        info_data = {
            'service': 'Simple Backend Demo',
            'version': '1.0',
            'description': 'Simple backend for E2E encryption testing',
            'hostname': socket.gethostname(),
            'port': PORT,
            'endpoints': [
                'GET /health - Health check',
                'GET /info - Service information',
                'GET /echo/{message} - Echo a message',
                'POST /echo - Echo JSON payload'
            ],
            'timestamp': datetime.now().isoformat()
        }
        
        self.send_json_response(200, info_data)
    
    def handle_echo_post(self):
        """Handle POST echo requests"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                request_data = json.loads(post_data.decode('utf-8'))
            else:
                request_data = {}
            
            response_data = {
                'echo': request_data,
                'received_at': datetime.now().isoformat(),
                'from_hostname': socket.gethostname(),
                'headers': dict(self.headers)
            }
            
            self.send_json_response(200, response_data)
            
        except json.JSONDecodeError:
            error_data = {
                'error': 'Invalid JSON payload',
                'timestamp': datetime.now().isoformat()
            }
            self.send_json_response(400, error_data)
        except Exception as e:
            error_data = {
                'error': f'Server error: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
            self.send_json_response(500, error_data)
    
    def send_echo_response(self, message):
        """Send echo response for GET requests"""
        echo_data = {
            'echo': message,
            'length': len(message),
            'timestamp': datetime.now().isoformat(),
            'from_hostname': socket.gethostname()
        }
        
        self.send_json_response(200, echo_data)
    
    def send_json_response(self, status_code, data):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        json_data = json.dumps(data, indent=2)
        self.wfile.write(json_data.encode('utf-8'))
    
    def send_not_found(self):
        """Send 404 response"""
        error_data = {
            'error': 'Endpoint not found',
            'path': self.path,
            'available_endpoints': [
                '/health',
                '/info', 
                '/echo/{message}',
                'POST /echo'
            ],
            'timestamp': datetime.now().isoformat()
        }
        
        self.send_json_response(404, error_data)
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Custom log format"""
        print(f"[{datetime.now().isoformat()}] {format % args}")

def run_server():
    """Start the HTTP server"""
    with socketserver.TCPServer(("", PORT), SimpleBackendHandler) as httpd:
        print(f"Starting simple backend server...")
        print(f"Server running on port {PORT}")
        print(f"Hostname: {socket.gethostname()}")
        print(f"Available endpoints:")
        print(f"  GET  /health          - Health check")
        print(f"  GET  /info            - Service information") 
        print(f"  GET  /echo/{{message}} - Echo a message")
        print(f"  POST /echo            - Echo JSON payload")
        print("-" * 50)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.shutdown()

if __name__ == "__main__":
    run_server()