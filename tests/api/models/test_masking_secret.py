"""Tests for the MaskingSecret model and related functionality."""

from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from fides.api.common_exceptions import MaskingSecretsExpired
from fides.api.models.masking_secret import MaskingSecret
from fides.api.models.policy import Policy
from fides.api.schemas.masking.masking_secrets import MaskingSecretCache, SecretType
from fides.api.service.privacy_request.request_runner_service import (
    CurrentStep,
    _verify_masking_secrets,
)


class TestMaskingSecret:
    """Tests for the MaskingSecret model."""

    def test_masking_secret_create(self, db: Session, privacy_request):
        """Test creating a MaskingSecret record."""
        privacy_request_id = privacy_request.id
        secret_value = "test-secret-value"
        masking_strategy = "aes_encrypt"
        secret_type = SecretType.key

        masking_secret = MaskingSecret.create(
            db=db,
            data={
                "privacy_request_id": privacy_request_id,
                "secret": secret_value,
                "masking_strategy": masking_strategy,
                "secret_type": secret_type,
            },
        )
        db.commit()

        assert masking_secret.privacy_request_id == privacy_request_id
        assert masking_secret.masking_strategy == masking_strategy
        assert masking_secret.secret_type == secret_type

        retrieved_secret = masking_secret.get_secret()
        # Depending on DB encoding, could be str or bytes - accept either
        assert (
            retrieved_secret == secret_value
            or retrieved_secret == secret_value.encode("utf-8")
        )

    def test_set_secret_string(self, db: Session, privacy_request):
        """Test setting a string secret."""
        privacy_request_id = privacy_request.id
        masking_secret = MaskingSecret(
            privacy_request_id=privacy_request_id,
            masking_strategy="aes_encrypt",
            secret_type=SecretType.key,
        )

        masking_secret.set_secret("test-string-secret")
        db.add(masking_secret)
        db.commit()

        retrieved_secret = masking_secret.get_secret()
        # Could be returned as str or bytes depending on DB encoding
        assert (
            retrieved_secret == "test-string-secret"
            or retrieved_secret == b"test-string-secret"
        )

    def test_set_secret_bytes(self, db: Session, privacy_request):
        """Test setting a bytes secret."""
        privacy_request_id = privacy_request.id
        masking_secret = MaskingSecret(
            privacy_request_id=privacy_request_id,
            masking_strategy="aes_encrypt",
            secret_type=SecretType.key,
        )

        masking_secret.set_secret(b"test-bytes-secret")
        db.add(masking_secret)
        db.commit()

        retrieved_secret = masking_secret.get_secret()
        # Could be returned as str or bytes depending on DB encoding
        assert (
            retrieved_secret == b"test-bytes-secret"
            or retrieved_secret == "test-bytes-secret"
        )

    def test_set_secret_invalid_type(self):
        """Test setting an invalid secret type raises an error."""
        masking_secret = MaskingSecret(
            privacy_request_id="dummy-id",  # Not saved to DB so FK constraint not an issue
            masking_strategy="aes_encrypt",
            secret_type=SecretType.key,
        )

        with pytest.raises(ValueError, match="Secret must be either string or bytes"):
            masking_secret.set_secret(123)  # type: ignore

    def test_persist_masking_secrets(self, db: Session, privacy_request):
        """Test persisting masking secrets to the database."""
        masking_secrets = [
            MaskingSecretCache(
                secret="secret1",
                masking_strategy="strategy1",
                secret_type=SecretType.key,
            ),
            MaskingSecretCache(
                secret=b"secret2",
                masking_strategy="strategy2",
                secret_type=SecretType.key,
            ),
        ]

        privacy_request.persist_masking_secrets(masking_secrets)
        db.commit()

        saved_secrets = (
            db.query(MaskingSecret)
            .filter(MaskingSecret.privacy_request_id == privacy_request.id)
            .all()
        )
        assert len(saved_secrets) == 2

        # Create sets of saved strategies and expected strategies to verify without order dependency
        saved_strategies = {s.masking_strategy for s in saved_secrets}
        expected_strategies = {"strategy1", "strategy2"}
        assert saved_strategies == expected_strategies

        # Verify the secret values - order doesn't matter
        saved_secret_values = set()
        for secret in saved_secrets:
            value = secret.get_secret()
            # Normalize to string for comparison
            if isinstance(value, bytes):
                value = value.decode("utf-8") if value != b"secret2" else "secret2"
            saved_secret_values.add(value)

        assert saved_secret_values == {"secret1", "secret2"}


class TestMaskingSecretFallback:
    """
    Tests for the masking secret fallback functionality.

    TODO: Remove these tests once we fully move to the new DB based approach.
    """

    @patch(
        "fides.api.service.privacy_request.request_runner_service.get_all_masking_secret_keys"
    )
    def test_verify_masking_secrets_expired(
        self, mock_get_all_keys, db: Session, privacy_request
    ):
        """Test that _verify_masking_secrets raises appropriate exception."""
        # Mock to return empty list of keys
        mock_get_all_keys.return_value = []

        # Create a policy that requires masking secrets
        policy_mock = Mock(spec=Policy)
        policy_mock.generate_masking_secrets.return_value = [
            MaskingSecretCache(
                secret="test-secret",
                masking_strategy="test-strategy",
                secret_type=SecretType.key,
            )
        ]

        # Without any secrets in cache or DB
        with pytest.raises(MaskingSecretsExpired):
            _verify_masking_secrets(policy_mock, privacy_request, CurrentStep.erasure)

    def test_verify_masking_secrets_success_db(self, db: Session, privacy_request):
        """Test that _verify_masking_secrets succeeds when secrets are in DB."""
        # Create a policy that requires masking secrets
        policy_mock = Mock(spec=Policy)
        policy_mock.generate_masking_secrets.return_value = [
            MaskingSecretCache(
                secret="test-secret",
                masking_strategy="test-strategy",
                secret_type=SecretType.key,
            )
        ]

        # Add a secret to the database
        MaskingSecret.create(
            db=db,
            data={
                "privacy_request_id": privacy_request.id,
                "secret": "test-secret",
                "masking_strategy": "test-strategy",
                "secret_type": SecretType.key,
            },
        )
        db.commit()

        # Should not raise an exception
        _verify_masking_secrets(policy_mock, privacy_request, CurrentStep.erasure)

    @patch(
        "fides.api.service.privacy_request.request_runner_service.get_all_masking_secret_keys"
    )
    def test_verify_masking_secrets_success_cache(
        self, mock_get_all_keys, db: Session, privacy_request
    ):
        """Test that _verify_masking_secrets succeeds when secrets are in cache."""
        # Create a policy that requires masking secrets
        policy_mock = Mock(spec=Policy)
        policy_mock.generate_masking_secrets.return_value = [
            MaskingSecretCache(
                secret="test-secret",
                masking_strategy="test-strategy",
                secret_type=SecretType.key,
            )
        ]

        # Mock cache keys to return a non-empty list
        mock_get_all_keys.return_value = [
            f"id-{privacy_request.id}-masking-secret-test-strategy-key"
        ]

        # Should not raise an exception
        _verify_masking_secrets(policy_mock, privacy_request, CurrentStep.erasure)
