from fides.api.ops.util import logger
from fides.api.ops.util.logger import MASKED, Pii


def test_logger_masks_pii() -> None:
    some_data = "some_data"
    result = logger._mask_pii_for_logs(Pii(some_data))
    assert result == MASKED


def test_logger_does_not_mask_by_default() -> None:
    some_data = "some_data"
    result = logger._mask_pii_for_logs(some_data)
    assert result == some_data
