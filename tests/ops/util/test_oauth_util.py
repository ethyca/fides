from fides.api.ops.util.oauth_util import get_root_client


def test_get_root_client() -> None:
    client = get_root_client()
    assert client
