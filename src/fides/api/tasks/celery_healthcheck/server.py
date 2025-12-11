import json
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler

from celery import bootsteps
from celery.worker import WorkController
from loguru import logger

HEALTHCHECK_DEFAULT_PORT = 9000
HEALTHCHECK_DEFAULT_PING_TIMEOUT = 2.0
DEFAULT_SHUTDOWN_TIMEOUT = 2.0


class HealthcheckHandler(SimpleHTTPRequestHandler):
    """HTTP request handler with additional properties and functions"""

    def __init__(self, parent: WorkController, healthcheck_ping_timeout: float, *args):
        self.parent = parent
        self.healthcheck_ping_timeout = healthcheck_ping_timeout
        super().__init__(*args)

    def do_GET(self):
        """Handle GET requests"""
        # Do something
        try:
            try:
                parent = self.parent
                insp = parent.app.control.inspect(
                    destination=[parent.hostname], timeout=self.healthcheck_ping_timeout
                )
                result = insp.ping()

                data = json.dumps({"status": "ok", "data": result})
                logger.debug(f"Healthcheck ping result: {data}")

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(bytes(data, "utf-8"))
            except Exception as e:
                logger.warning(f"Healthcheck ping exception: {e}")
                response = {"status": "error", "data": str(e)}
                self.send_response(503)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(bytes(json.dumps(response), "utf-8"))
        except Exception as ex:
            logger.exception("HealthcheckHandler exception", exc_info=ex)
            self.send_response(500)


class HealthCheckServer(bootsteps.StartStopStep):
    def __init__(self, parent: WorkController, **kwargs):
        self.thread = None
        self.parent = parent
        # config
        self.healthcheck_port = int(
            getattr(parent.app.conf, "healthcheck_port", HEALTHCHECK_DEFAULT_PORT)
        )
        self.healthcheck_ping_timeout = float(
            getattr(
                parent.app.conf,
                "healthcheck_ping_timeout",
                HEALTHCHECK_DEFAULT_PING_TIMEOUT,
            )
        )
        self.shutdown_timeout = float(
            getattr(
                parent.app.conf,
                "shutdown_timeout",
                DEFAULT_SHUTDOWN_TIMEOUT,
            )
        )

    def http_handler(self, *args):
        HealthcheckHandler(self.parent, self.healthcheck_ping_timeout, *args)

    def start(self, parent: WorkController):
        self.http_server = HTTPServer(
            ("0.0.0.0", self.healthcheck_port), self.http_handler
        )

        self.thread = threading.Thread(
            target=self.http_server.serve_forever, daemon=True
        )
        self.thread.start()

    def stop(self, parent: WorkController):
        logger.info(
            f"Stopping health check server with a timeout of {self.shutdown_timeout} seconds"
        )
        self.http_server.shutdown()
        self.thread.join(self.shutdown_timeout)
        logger.info(f"Health check server stopped on port {self.healthcheck_port}")
