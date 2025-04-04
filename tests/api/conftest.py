import pytest
import requests
from pytest import MonkeyPatch


@pytest.fixture(scope="session")
def monkeysession():
    """
    Monkeypatch at the session level instead of the function level.
    Automatically undoes the monkeypatching when the session finishes.
    """
    mpatch = MonkeyPatch()
    yield mpatch
    mpatch.undo()


@pytest.fixture(autouse=True, scope="session")
def monkeypatch_requests(test_client, monkeysession) -> None:
    """
    Some places within the application, for example `fides.core.api`, use the `requests`
    library to interact with the webserver. This fixture patches those `requests` calls
    so that all of those tests instead interact with the test instance.
    """
    monkeysession.setattr(requests, "get", test_client.get)
    monkeysession.setattr(requests, "post", test_client.post)
    monkeysession.setattr(requests, "put", test_client.put)
    monkeysession.setattr(requests, "patch", test_client.patch)
    monkeysession.setattr(requests, "delete", test_client.delete)
