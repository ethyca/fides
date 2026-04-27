from unittest.mock import MagicMock, patch

import pytest

from fides.api.worker import start_worker


@patch("fides.api.worker.celery_app.worker_main")
class TestStartWorker:
    """
    Unit tests for the start_worker function. Does not test the actual worker functionality,
    since we mock the worker_main method.
    """

    def test_cannot_provide_both_queues_and_exclude_queues(self, worker_main_mock):
        with pytest.raises(AssertionError):
            start_worker(queues="fidesops.messaging", exclude_queues="fides.dsr")

        worker_main_mock.assert_not_called()

    def test_start_worker_unknown_queue(self, worker_main_mock):
        with pytest.raises(ValueError):
            start_worker(queues="fidesops.messaging,unknown_queue")

        worker_main_mock.assert_not_called()

    @pytest.mark.parametrize(
        "queues, exclude_queues, expected_queues",
        [
            (
                None,
                None,
                "fidesops.messaging,fides.privacy_preferences,fides.privacy_request_exports,fides.privacy_request_ingestion,fides.dsr,fidesplus.consent_webhooks,fidesplus.discovery_monitors_detection,fidesplus.discovery_monitors_classification,fidesplus.discovery_monitors_promotion,fides",
            ),
            ("fides.dsr", None, "fides.dsr"),
            (
                None,
                "fides.dsr,fides.privacy_preferences,fides.privacy_request_exports,fides.privacy_request_ingestion,fidesplus.discovery_monitors_detection",
                "fidesops.messaging,fidesplus.consent_webhooks,fidesplus.discovery_monitors_classification,fidesplus.discovery_monitors_promotion,fides",
            ),
            ("fides,fides.dsr", None, "fides,fides.dsr"),
            (
                None,
                "fides,fides.dsr",
                "fidesops.messaging,fides.privacy_preferences,fides.privacy_request_exports,fides.privacy_request_ingestion,fidesplus.consent_webhooks,fidesplus.discovery_monitors_detection,fidesplus.discovery_monitors_classification,fidesplus.discovery_monitors_promotion",
            ),
        ],
    )
    def test_start_worker_with_arguments(
        self,
        worker_main_mock,
        queues,
        exclude_queues,
        expected_queues,
    ):
        start_worker(queues=queues, exclude_queues=exclude_queues)

        worker_main_mock.assert_called_once_with(
            argv=[
                "--quiet",
                "worker",
                "--loglevel=info",
                "--concurrency=2",
                f"--queues={expected_queues}",
            ]
        )


@patch("fides.api.worker.celery_app.worker_main")
class TestStartWorkerReload:
    """Tests for the --reload functionality of start_worker."""

    @patch("fides.api.worker.run_process")
    def test_reload_calls_run_process_with_defaults(
        self, run_process_mock: MagicMock, worker_main_mock: MagicMock
    ):
        """When reload=True and no reload_dirs, uses default watch dirs."""
        start_worker(reload=True)

        run_process_mock.assert_called_once()
        call_args = run_process_mock.call_args
        # Default watch dirs are "src" and "data"
        assert call_args.args == ("src", "data")
        assert call_args.kwargs["target"].__name__ == "_run_celery_worker"
        assert callable(call_args.kwargs["watch_filter"])
        # worker_main should NOT be called directly (run_process handles it)
        worker_main_mock.assert_not_called()

    @patch("fides.api.worker.run_process")
    def test_reload_uses_custom_dirs(
        self, run_process_mock: MagicMock, worker_main_mock: MagicMock
    ):
        """When reload_dirs are provided, they override defaults."""
        start_worker(reload=True, reload_dirs=["/custom/src", "/other/data"])

        call_args = run_process_mock.call_args
        assert call_args.args == ("/custom/src", "/other/data")

    @patch("fides.api.worker.run_process")
    def test_reload_filter_accepts_python_and_yaml(
        self, run_process_mock: MagicMock, worker_main_mock: MagicMock
    ):
        """The watch filter accepts .py, .yml, and .yaml files."""
        from watchfiles import Change

        start_worker(reload=True)

        watch_filter = run_process_mock.call_args.kwargs["watch_filter"]
        assert watch_filter(Change.modified, "/app/src/module.py") is True
        assert watch_filter(Change.modified, "/app/data/config.yml") is True
        assert watch_filter(Change.modified, "/app/data/config.yaml") is True
        assert watch_filter(Change.modified, "/app/src/readme.md") is False
        assert watch_filter(Change.modified, "/app/src/data.json") is False

    @patch("fides.api.worker.run_process")
    def test_reload_filter_ignores_noise_dirs(
        self, run_process_mock: MagicMock, worker_main_mock: MagicMock
    ):
        """The watch filter ignores __pycache__, .git, etc."""
        from watchfiles import Change

        start_worker(reload=True)

        watch_filter = run_process_mock.call_args.kwargs["watch_filter"]
        assert watch_filter(Change.modified, "/app/__pycache__/module.py") is False
        assert watch_filter(Change.modified, "/app/.git/hooks/pre-commit.py") is False
        assert watch_filter(Change.modified, "/app/node_modules/pkg/index.py") is False
        assert watch_filter(Change.modified, "/app/.mypy_cache/module.py") is False

    def test_no_reload_calls_worker_main_directly(self, worker_main_mock: MagicMock):
        """When reload=False (default), worker_main is called directly."""
        start_worker()

        worker_main_mock.assert_called_once()
