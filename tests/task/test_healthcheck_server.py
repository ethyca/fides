import time

import pytest
import requests
from loguru import logger


class TestCeleryHealthCheckServer:
    def test_responds_to_ping_properly(self, celery_session_app, celery_session_worker):
        try:
            response = requests.get("http://127.0.0.1:9000/")
            assert response.status_code == 200
            assert response.json()["status"] == "ok"
        except requests.exceptions.ConnectionError:
            pytest.fail("Connection error")


class TestCeleryHealthCheckWorker:
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        yield
        with pytest.raises(Exception):
            requests.get("http://127.0.0.1:9000/", timeout=1)

    def test_shutdown_gracefully(self, celery_session_app, celery_session_worker):
        try:
            logger.info("Shutdown gracefully")
            celery_session_worker.stop()
            logger.info("Shutdown gracefully finished")
        except Exception:
            pytest.fail("Failed to stop health check server")





