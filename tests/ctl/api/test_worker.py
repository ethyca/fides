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
                "fides,fidesops.messaging,fides.privacy_preferences,fides.privacy_request_exports,fides.privacy_request_ingestion,fides.dsr,fidesplus.consent_webhooks,fidesplus.discovery_monitors_detection,fidesplus.discovery_monitors_classification,fidesplus.discovery_monitors_promotion,fidesplus.bulk_consent_import",
            ),
            ("fides.dsr", None, "fides.dsr"),
            (
                None,
                "fides.dsr,fides.privacy_preferences,fides.privacy_request_exports,fides.privacy_request_ingestion,fidesplus.discovery_monitors_detection",
                "fides,fidesops.messaging,fidesplus.consent_webhooks,fidesplus.discovery_monitors_classification,fidesplus.discovery_monitors_promotion,fidesplus.bulk_consent_import",
            ),
            ("fides,fides.dsr", None, "fides,fides.dsr"),
            (
                None,
                "fides,fides.dsr",
                "fidesops.messaging,fides.privacy_preferences,fides.privacy_request_exports,fides.privacy_request_ingestion,fidesplus.consent_webhooks,fidesplus.discovery_monitors_detection,fidesplus.discovery_monitors_classification,fidesplus.discovery_monitors_promotion,fidesplus.bulk_consent_import",
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


class TestWorkerDisableFlags:
    """Tests for the individual worker_disable_heartbeat/gossip/mingle config flags."""

    @pytest.fixture(autouse=True)
    def mock_celery_config(self):
        """Provide a mock CONFIG.celery with the three disable flags."""
        mock_config = MagicMock()
        mock_config.celery.worker_disable_heartbeat = False
        mock_config.celery.worker_disable_gossip = False
        mock_config.celery.worker_disable_mingle = False
        mock_config.celery.worker_concurrency = 2
        with patch("fides.api.worker.CONFIG", mock_config):
            yield mock_config

    @pytest.fixture
    def worker_main_mock(self):
        with patch("fides.api.worker.celery_app.worker_main") as mock:
            yield mock

    def test_no_without_flags_when_all_disabled_false(
        self, mock_celery_config, worker_main_mock: MagicMock
    ):
        """Default: no --without-* flags when all flags are False."""
        start_worker()

        call_args = worker_main_mock.call_args
        argv = call_args.kwargs["argv"]
        assert "--without-heartbeat" not in argv
        assert "--without-gossip" not in argv
        assert "--without-mingle" not in argv

    @pytest.mark.parametrize(
        "flag_name",
        [
            "worker_disable_heartbeat",
            "worker_disable_gossip",
            "worker_disable_mingle",
        ],
    )
    def test_single_flag_enabled(
        self, mock_celery_config, worker_main_mock: MagicMock, flag_name: str
    ):
        """When a disable flag is True, the matching --without-* appears in argv."""
        setattr(mock_celery_config.celery, flag_name, True)
        start_worker()

        call_args = worker_main_mock.call_args
        argv = call_args.kwargs["argv"]
        flag_to_arg = {
            "worker_disable_heartbeat": "--without-heartbeat",
            "worker_disable_gossip": "--without-gossip",
            "worker_disable_mingle": "--without-mingle",
        }
        assert flag_to_arg[flag_name] in argv

    def test_all_three_flags_enabled(
        self, mock_celery_config, worker_main_mock: MagicMock
    ):
        """All three flags together produces all --without-* flags."""
        mock_celery_config.celery.worker_disable_heartbeat = True
        mock_celery_config.celery.worker_disable_gossip = True
        mock_celery_config.celery.worker_disable_mingle = True

        start_worker()

        call_args = worker_main_mock.call_args
        argv = call_args.kwargs["argv"]
        assert "--without-heartbeat" in argv
        assert "--without-gossip" in argv
        assert "--without-mingle" in argv


class TestWorkerConcurrency:
    """Tests for CONFIG.celery.worker_concurrency."""

    @pytest.fixture(autouse=True)
    def mock_celery_config(self):
        mock_config = MagicMock()
        mock_config.celery.worker_disable_heartbeat = False
        mock_config.celery.worker_disable_gossip = False
        mock_config.celery.worker_disable_mingle = False
        mock_config.celery.worker_concurrency = 2
        with patch("fides.api.worker.CONFIG", mock_config):
            yield mock_config

    @pytest.fixture
    def worker_main_mock(self):
        with patch("fides.api.worker.celery_app.worker_main") as mock:
            yield mock

    def test_default_concurrency_in_argv(
        self, mock_celery_config: MagicMock, worker_main_mock: MagicMock
    ):
        start_worker()
        argv = worker_main_mock.call_args.kwargs["argv"]
        assert "--concurrency=2" in argv

    @pytest.mark.parametrize("concurrency", [1, 4, 16])
    def test_custom_concurrency_in_argv(
        self,
        mock_celery_config: MagicMock,
        worker_main_mock: MagicMock,
        concurrency: int,
    ):
        mock_celery_config.celery.worker_concurrency = concurrency
        start_worker()
        argv = worker_main_mock.call_args.kwargs["argv"]
        assert f"--concurrency={concurrency}" in argv
