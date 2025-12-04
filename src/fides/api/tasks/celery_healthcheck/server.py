import logging
import threading

import uvicorn
from celery import bootsteps
from celery.worker import WorkController
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

app = FastAPI()
logger = logging.getLogger("celery.ext.healthcheck")

HEALTHCHECK_DEFAULT_PORT = 9000
HEALTHCHECK_DEFAULT_PING_TIMEOUT = 2.0


class HealthCheckServer(bootsteps.StartStopStep):
    def __init__(self, parent: WorkController, **kwargs):
        self.thread = None

        # facilitates testing
        self.app = app

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

    def start(self, parent: WorkController):
        @self.app.get("/")
        async def celery_ping():
            insp = parent.app.control.inspect(
                destination=[parent.hostname], timeout=self.healthcheck_ping_timeout
            )
            result = insp.ping()

            if result:
                return JSONResponse(
                    content={"status": "ok", "result": result},
                    status_code=status.HTTP_200_OK,
                )
            else:
                return JSONResponse(
                    content={"status": "error", "result": result},
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

        def run_server():
            uvicorn.run(
                self.app,
                host="0.0.0.0",
                port=self.healthcheck_port,
            )

        self.thread = threading.Thread(target=run_server, daemon=True)
        self.thread.start()

        logger.info(f"Health check server started on port {self.healthcheck_port}")

    def stop(self, parent: WorkController):
        pass