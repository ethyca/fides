import pytest

import fidesctl.cli.utils as utils


@pytest.mark.unit
def test_check_server_bad_ping():
    "Check for an exception if the server isn't up."
    with pytest.raises(SystemExit):
        utils.check_server("foo", "http://fake_address:8080")
