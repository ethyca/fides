import json
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Any, Optional

from celery import bootsteps
from celery.worker import WorkController
from loguru import logger

HEALTHCHECK_DEFAULT_PORT = 9000
HEALTHCHECK_DEFAULT_PING_TIMEOUT = 2.0
HEALTHCHECK_DEFAULT_HTTP_SERVER_SHUTDOWN_TIMEOUT = 2.0


class HealthcheckHandler(SimpleHTTPRequestHandler):
    """HTTP request handler with additional properties and functions"""

    def __init__(
        self, parent: WorkController, healthcheck_ping_timeout: float, *args: Any
    ):
        self.parent = parent
        self.healthcheck_ping_timeout = healthcheck_ping_timeout
        super().__init__(*args)

    def do_GET(self) -> None:
        """Handle GET requests"""
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
    # ignore kwargs type
    def __init__(self, parent: WorkController, **kwargs):  # type: ignore [arg-type, no-untyped-def]
        self.thread: Optional[threading.Thread] = None
        self.http_server: Optional[HTTPServer] = None

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
                HEALTHCHECK_DEFAULT_HTTP_SERVER_SHUTDOWN_TIMEOUT,
            )
        )

        super().__init__(parent, **kwargs)

    # The mypy hints for an HTTP handler are strange, so ignoring them here
    def http_handler(self, *args) -> None:  # type: ignore [arg-type, no-untyped-def]
        HealthcheckHandler(self.parent, self.healthcheck_ping_timeout, *args)

    def start(self, parent: WorkController) -> None:
        # Ignore mypy hints here as the constructed object immediately handles the request
        # (if you look in the source code for SimpleHTTPRequestHandler, specifically the finalize request method)
        self.http_server = HTTPServer(
            ("0.0.0.0", self.healthcheck_port), self.http_handler  # type: ignore [arg-type]
        )

        self.thread = threading.Thread(
            target=self.http_server.serve_forever, daemon=True
        )
        self.thread.start()

    def stop(self, parent: WorkController) -> None:
        if self.http_server is None:
            logger.warning(
                "Requested stop of HTTP healthcheck server, but no server was started"
            )
        else:
            logger.info(
                f"Stopping health check server with a timeout of {self.shutdown_timeout} seconds"
            )
            self.http_server.shutdown()

        # Really this should not happen if the HTTP server is None, but just in case, we should check.
        if self.thread is None:
            logger.warning("No thread in HTTP healthcheck server to shutdown...")
        else:
            self.thread.join(self.shutdown_timeout)

        logger.info(f"Health check server stopped on port {self.healthcheck_port}")
