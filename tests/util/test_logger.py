from fidesops.util import logger
from fidesops.util.logger import NotPii, MASKED


def test_logger_masks_pii() -> None:
    some_data = "some_data"
    result = logger._mask_pii_for_logs(some_data)
    assert result == MASKED


def test_logger_does_not_mask_whitelist() -> None:
    some_data = NotPii("some_data")
    result = logger._mask_pii_for_logs(some_data)
    assert result == some_data
