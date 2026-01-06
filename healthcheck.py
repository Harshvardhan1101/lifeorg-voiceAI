"""Simple HTTP health check server for Kubernetes probes."""

import asyncio
import logging
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

logger = logging.getLogger("health-check")

HEALTH_PORT = int(os.environ.get("HEALTH_PORT", "8080"))


class HealthHandler(BaseHTTPRequestHandler):
    """HTTP handler for health check endpoints."""
    
    def do_GET(self):
        """Handle GET requests for health checks."""
        if self.path == "/health" or self.path == "/healthz":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "healthy"}')
        elif self.path == "/ready" or self.path == "/readyz":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "ready"}')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress default logging to reduce noise."""
        pass


def start_health_server():
    """Start the health check HTTP server in a background thread."""
    try:
        server = HTTPServer(("0.0.0.0", HEALTH_PORT), HealthHandler)
        logger.info(f"Health check server started on port {HEALTH_PORT}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Failed to start health check server: {e}")


def run_health_server_background():
    """Run health server in a daemon thread."""
    thread = threading.Thread(target=start_health_server, daemon=True)
    thread.start()
    return thread
