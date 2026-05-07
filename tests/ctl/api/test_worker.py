from unittest.mock import MagicMock, patch

import pytest

from fides.api.worker import _parse_prefetch_map, start_worker
from fides.config.celery_settings import CelerySettings


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


class TestQueuePrefetchMultiplierValidator:
    """Tests for CelerySettings.validate_queue_prefetch_multiplier.

    The validator runs at construction time and either passes the string through
    unchanged (all values are valid integers) or returns None (any value is not
    a parseable integer, or an entry is missing '=').
    """

    def test_none_is_accepted(self):
        settings = CelerySettings(queue_prefetch_multiplier=None)
        assert settings.queue_prefetch_multiplier is None

    def test_valid_single_entry(self):
        settings = CelerySettings(queue_prefetch_multiplier="fides.dsr=8")
        assert settings.queue_prefetch_multiplier == "fides.dsr=8"

    def test_valid_multiple_entries(self):
        settings = CelerySettings(
            queue_prefetch_multiplier="fides.dsr=8,fidesops.messaging=4"
        )
        assert settings.queue_prefetch_multiplier == "fides.dsr=8,fidesops.messaging=4"

    def test_non_integer_value_rejects_entire_string(self):
        settings = CelerySettings(queue_prefetch_multiplier="fides.dsr=8,foo=asd")
        assert settings.queue_prefetch_multiplier is None

    def test_single_bad_value_among_valid_rejects_all(self):
        """One bad entry causes the entire string to be discarded."""
        settings = CelerySettings(
            queue_prefetch_multiplier="fides.dsr=123,fidesops.messaging=4,bad.queue=notanint"
        )
        assert settings.queue_prefetch_multiplier is None

    def test_missing_equals_sign_rejects_entire_string(self):
        settings = CelerySettings(queue_prefetch_multiplier="nodequals")
        assert settings.queue_prefetch_multiplier is None

    def test_whitespace_around_value_is_tolerated(self):
        """int() strips surrounding whitespace, so 'queue= 8 ' passes validation."""
        settings = CelerySettings(queue_prefetch_multiplier="fides.dsr= 8 ")
        assert settings.queue_prefetch_multiplier == "fides.dsr= 8 "

    def test_unknown_queue_names_pass_validation(self):
        """The validator only checks integer-ness; unknown queue names are not its concern."""
        settings = CelerySettings(
            queue_prefetch_multiplier="nonexistent.queue=5,another.unknown=10"
        )
        assert (
            settings.queue_prefetch_multiplier
            == "nonexistent.queue=5,another.unknown=10"
        )


class TestParsePrefetchMap:
    """Tests for _parse_prefetch_map — the function that converts the validated
    config string into a {queue: int} dict at worker startup."""

    KNOWN_QUEUES = ["fides.dsr", "fidesops.messaging", "fides.privacy_preferences"]

    def _mock_config(self, value):
        """Return a mock CONFIG with queue_prefetch_multiplier set to *value*."""
        mock_config = MagicMock()
        mock_config.celery.queue_prefetch_multiplier = value
        return mock_config

    def test_returns_empty_dict_when_not_set(self):
        with patch("fides.api.worker.CONFIG", self._mock_config(None)):
            result = _parse_prefetch_map(self.KNOWN_QUEUES)
        assert result == {}

    def test_returns_empty_dict_for_empty_string(self):
        with patch("fides.api.worker.CONFIG", self._mock_config("")):
            result = _parse_prefetch_map(self.KNOWN_QUEUES)
        assert result == {}

    def test_parses_single_known_queue(self):
        with patch("fides.api.worker.CONFIG", self._mock_config("fides.dsr=8")):
            result = _parse_prefetch_map(self.KNOWN_QUEUES)
        assert result == {"fides.dsr": 8}

    def test_parses_multiple_known_queues(self):
        with patch(
            "fides.api.worker.CONFIG",
            self._mock_config("fides.dsr=8,fidesops.messaging=4"),
        ):
            result = _parse_prefetch_map(self.KNOWN_QUEUES)
        assert result == {"fides.dsr": 8, "fidesops.messaging": 4}

    def test_unknown_queue_is_included_despite_warning(self):
        """An unknown queue name is still inserted into the map (it simply never
        matches an active worker queue). The warning is tested elsewhere."""
        with patch(
            "fides.api.worker.CONFIG",
            self._mock_config("fides.dsr=8,nonexistent.queue=16"),
        ):
            result = _parse_prefetch_map(self.KNOWN_QUEUES)
        assert result == {"fides.dsr": 8, "nonexistent.queue": 16}

    def test_all_unknown_queues_still_returns_populated_map(self):
        with patch(
            "fides.api.worker.CONFIG",
            self._mock_config("totally.unknown=99"),
        ):
            result = _parse_prefetch_map(self.KNOWN_QUEUES)
        assert result == {"totally.unknown": 99}


class TestPrefetchMultiplierWorkerArgv:
    """Integration tests verifying that _run_celery_worker appends (or omits)
    --prefetch-multiplier in the argv it passes to celery_app.worker_main."""

    @pytest.fixture(autouse=True)
    def mock_celery_config(self):
        mock_config = MagicMock()
        mock_config.celery.worker_disable_heartbeat = False
        mock_config.celery.worker_disable_gossip = False
        mock_config.celery.worker_disable_mingle = False
        mock_config.celery.worker_concurrency = 2
        mock_config.celery.task_always_eager = False
        mock_config.celery.queue_prefetch_multiplier = None
        with patch("fides.api.worker.CONFIG", mock_config):
            yield mock_config

    @pytest.fixture
    def worker_main_mock(self):
        with patch("fides.api.worker.celery_app.worker_main") as mock:
            yield mock

    def test_prefetch_arg_added_when_queue_matches(
        self, mock_celery_config, worker_main_mock
    ):
        mock_celery_config.celery.queue_prefetch_multiplier = "fides.dsr=8"
        start_worker(queues="fides.dsr")
        argv = worker_main_mock.call_args.kwargs["argv"]
        assert "--prefetch-multiplier=8" in argv

    def test_prefetch_arg_absent_when_queue_does_not_match(
        self, mock_celery_config, worker_main_mock
    ):
        mock_celery_config.celery.queue_prefetch_multiplier = "fides.dsr=8"
        start_worker(queues="fidesops.messaging")
        argv = worker_main_mock.call_args.kwargs["argv"]
        assert not any(arg.startswith("--prefetch-multiplier") for arg in argv)

    def test_prefetch_arg_absent_when_setting_not_set(
        self, mock_celery_config, worker_main_mock
    ):
        mock_celery_config.celery.queue_prefetch_multiplier = None
        start_worker(queues="fides.dsr")
        argv = worker_main_mock.call_args.kwargs["argv"]
        assert not any(arg.startswith("--prefetch-multiplier") for arg in argv)

    def test_first_matching_queue_wins(self, mock_celery_config, worker_main_mock):
        """When a worker handles multiple queues, the first one with a prefetch
        entry in the map is used; subsequent matches are ignored."""
        mock_celery_config.celery.queue_prefetch_multiplier = (
            "fides.dsr=8,fidesops.messaging=4"
        )
        # fides.dsr appears first in the comma-separated queues arg
        start_worker(queues="fides.dsr,fidesops.messaging")
        argv = worker_main_mock.call_args.kwargs["argv"]
        assert "--prefetch-multiplier=8" in argv
        assert "--prefetch-multiplier=4" not in argv
