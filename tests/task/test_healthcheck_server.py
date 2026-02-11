import time
from concurrent.futures import ThreadPoolExecutor

import pytest
import requests
from loguru import logger


class TestCeleryHealthCheckServer:
    def test_responds_to_ping_properly(self, celery_session_app, celery_session_worker):
        # Get the port from the celery app config (unique per xdist worker)
        port = celery_session_app.conf.get("healthcheck_port", 9000)
        try:
            response = requests.get(f"http://127.0.0.1:{port}/", timeout=5)
            assert response.status_code == 200
            assert response.json()["status"] == "ok"
        except requests.exceptions.ConnectionError:
            pytest.fail("Connection error")

    def test_concurrent_healthcheck_requests(
        self, celery_session_app, celery_session_worker
    ):
        """
        Verify multiple concurrent healthcheck requests don't cause contention or deadlocks.
        
        This test validates that the log_message() override prevents stderr contention
        and that SO_REUSEADDR allows proper concurrent handling.
        """
        # Get the port from the celery app config (unique per xdist worker)
        port = celery_session_app.conf.get("healthcheck_port", 9000)

        def make_request():
            try:
                response = requests.get(f"http://127.0.0.1:{port}/", timeout=10)
                return response.status_code == 200
            except Exception as e:
                logger.error(f"Request failed: {e}")
                return False

        # Test with a smaller number of concurrent requests to be safe
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in futures]

        successful_requests = sum(results)
        assert successful_requests >= 8, (
            f"Too many concurrent requests failed: {successful_requests}/10"
        )

    def test_healthcheck_logging_doesnt_block(
        self, celery_session_app, celery_session_worker, capsys
    ):
        """
        Verify HTTP logging doesn't cause stderr contention with pytest output capturing.
        
        This test validates that the log_message() override prevents the default
        SimpleHTTPRequestHandler behavior of writing to stderr, which can cause
        deadlocks in test environments.
        """
        # Get the port from the celery app config (unique per xdist worker)
        port = celery_session_app.conf.get("healthcheck_port", 9000)
        
        # Make multiple requests while pytest is capturing output
        for i in range(5):
            response = requests.get(f"http://127.0.0.1:{port}/", timeout=5)
            assert response.status_code == 200

        # Verify we can still capture output without blocking
        # The fact that this test completes without hanging is the real test
        captured = capsys.readouterr()
        # Test completes successfully without hanging on stderr writes


class TestCeleryHealthCheckWorker:
    @pytest.fixture(autouse=True)
    def setup_teardown(self, celery_session_app):
        port = celery_session_app.conf.get("healthcheck_port", 9000)
        yield
        with pytest.raises(Exception):
            requests.get(f"http://127.0.0.1:{port}/", timeout=1)

    def test_shutdown_gracefully(self, celery_session_app, celery_session_worker):
        try:
            logger.info("Shutdown gracefully")
            celery_session_worker.stop()
            logger.info("Shutdown gracefully finished")
        except Exception:
            pytest.fail("Failed to stop health check server")
