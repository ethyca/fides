from fidesops.service.client_data_strategies.https_helper import (
    create_authorization_headers,
    create_identity_parameters,
)


def test__create_authorization_headers__happy_path():
    auth = "Please let me in. I said please."

    headers = create_authorization_headers(auth)

    assert headers["Authorization"] == auth


def test__create_identity_parameters__happy_path():
    identity = "me@test.com"

    parameters = create_identity_parameters(identity)

    assert parameters["identity"] == identity
