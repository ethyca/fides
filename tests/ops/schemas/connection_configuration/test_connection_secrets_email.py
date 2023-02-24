from fides.api.ops.schemas.connection_configuration.connection_secrets_email import (
    EmailSchema,
)
import pytest


class TestEmailSchema:
    def test_email_schema_valid(self) -> None:
        email_schema = EmailSchema(
            to_email="to_email",
            test_email="valid_email@ethyca.com",
        )

    def test_email_schema_invalid(self) -> None:
        with pytest.raises(ValueError):
            EmailSchema(
                to_email="to_email",
                test_email="notanemail",
            )
