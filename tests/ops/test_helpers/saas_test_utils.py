import time
from io import BytesIO
from typing import Any, Callable, Dict, List
from zipfile import ZipFile

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
    verification_count=1,
) -> Any:
    # we continue polling if poller is None OR if poller is not None but we don't desire existence, i.e. we are polling for removal
    original_retries = retries
    for _ in range(verification_count):
        while (return_val := poller(*args, **kwargs) is None) is existence_desired:
            if not retries:
                raise Exception(error_message)
            retries -= 1
            time.sleep(interval)
        retries = original_retries
    return return_val


def create_zip_file(file_data: Dict[str, str]) -> BytesIO:
    """
    Create a zip file in memory with the given files.

    Args:
        files (Dict[str, str]): A mapping of filenames to their contents

    Returns:
        io.BytesIO: An in-memory zip file with the specified files.
    """
    zip_buffer = BytesIO()

    with ZipFile(zip_buffer, "w") as zip_file:
        for filename, file_content in file_data.items():
            zip_file.writestr(filename, file_content)

    # resetting the file position pointer to the beginning of the stream
    # so the tests can read the zip file from the beginning
    zip_buffer.seek(0)
    return zip_buffer
