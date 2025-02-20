from unittest.mock import patch

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
                "fides,fidesops.messaging,fides.privacy_preferences,fides.dsr",
            ),
            ("fides.dsr", None, "fides.dsr"),
            (None, "fides.dsr,fides.privacy_preferences", "fides,fidesops.messaging"),
            ("fides,fides.dsr", None, "fides,fides.dsr"),
            (None, "fides,fides.dsr", "fidesops.messaging,fides.privacy_preferences"),
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
