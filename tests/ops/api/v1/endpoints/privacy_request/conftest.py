import pytest

from fides.common.api.v1.urn_registry import PRIVACY_REQUEST_APPROVE, V1_URL_PREFIX


@pytest.fixture(scope="function")
def url_approve():
    return V1_URL_PREFIX + PRIVACY_REQUEST_APPROVE
