import time
from typing import Any, Callable, Dict, List

DEFAULT_POLLING_ERROR_MESSAGE = (
    "The endpoint did not return the required data for testing during the time limit"
)


def poll_for_existence(
    poller: Callable,
    args: List[Any] = (),
    kwargs: Dict[str, Any] = {},
    error_message: str = DEFAULT_POLLING_ERROR_MESSAGE,
    retries: int = 10,
    interval: int = 5,
    existence_desired=True,
) -> Any:
    # we continue polling if poller is None OR if poller is not None but we don't desire existence, i.e. we are polling for removal
    while (return_val := poller(*args, **kwargs) is None) is existence_desired:
        if not retries:
            raise Exception(error_message)
        retries -= 1
        time.sleep(interval)

    return return_val
