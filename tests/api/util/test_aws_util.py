"""Tests for build_aws_client factory."""

from unittest.mock import MagicMock, patch

import pytest
from fides.api.schemas.storage.storage import AWSAuthMethod

from fides.api.util.aws_util import build_aws_client


@pytest.fixture()
def secrets() -> MagicMock:
    """AWSSchema mock with assume_role_arn."""
    s = MagicMock()
    s.auth_method = AWSAuthMethod.SECRET_KEYS
    s.aws_access_key_id = "AKID"
    s.aws_secret_access_key = "secret"
    s.aws_assume_role_arn = "arn:aws:iam::123456789012:role/MyRole"
    s.model_dump.return_value = {
        "auth_method": "secret_keys",
        "aws_access_key_id": "AKID",
        "aws_secret_access_key": "secret",
    }
    return s


class TestBuildAWSClient:
    """Tests for the build_aws_client factory function."""

    @patch(
        "fides.api.util.aws_util.get_aws_session"
    )
    def test_delegates_to_get_aws_session(
        self, mock_get_session: MagicMock, secrets: MagicMock
    ) -> None:
        """Auth and role assumption are delegated to get_aws_session."""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        expected_secrets = secrets.model_dump.return_value

        build_aws_client("s3", secrets)

        mock_get_session.assert_called_once_with(
            auth_method="secret_keys",
            storage_secrets=expected_secrets,
            assume_role_arn="arn:aws:iam::123456789012:role/MyRole",
        )
        mock_session.client.assert_called_once_with("s3")

    @patch(
        "fides.api.util.aws_util.get_aws_session"
    )
    def test_region_override(
        self, mock_get_session: MagicMock, secrets: MagicMock
    ) -> None:
        """Explicit region_name is injected into the secrets dict."""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        build_aws_client("s3", secrets, region_name="eu-west-1")

        call_secrets = mock_get_session.call_args[1]["storage_secrets"]
        assert call_secrets["region_name"] == "eu-west-1"

    @patch(
        "fides.api.util.aws_util.get_aws_session"
    )
    def test_no_region_override(
        self, mock_get_session: MagicMock, secrets: MagicMock
    ) -> None:
        """Original secrets are preserved when no region override is given."""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        build_aws_client("s3", secrets)

        call_secrets = mock_get_session.call_args[1]["storage_secrets"]
        assert "region_name" not in call_secrets
