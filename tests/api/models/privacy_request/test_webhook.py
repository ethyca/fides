import pytest

from fides.api.models.privacy_request.webhook import (
    generate_request_callback_pre_approval_jwe,
    generate_request_callback_resume_jwe,
    generate_request_task_callback_jwe,
)
from fides.api.oauth.jwt import decrypt_jwe
from fides.config import CONFIG


@pytest.mark.parametrize(
    "jwe_generator",
    [
        generate_request_callback_pre_approval_jwe,
        generate_request_task_callback_jwe,
        generate_request_callback_resume_jwe,
    ],
    ids=[
        "pre_approval_jwe",
        "task_callback_jwe",
        "resume_callback_jwe",
    ],
)
def test_generate_valid_jwe(jwe_generator, policy_pre_execution_webhooks):
    for webhook in policy_pre_execution_webhooks:
        jwe = jwe_generator(webhook)
        assert isinstance(jwe, str)
        assert jwe
        assert len(jwe.split(".")) == 5


@pytest.mark.parametrize(
    "jwe_generator",
    [
        generate_request_callback_pre_approval_jwe,
        generate_request_task_callback_jwe,
        generate_request_callback_resume_jwe,
    ],
    ids=[
        "pre_approval_jwe",
        "task_callback_jwe",
        "resume_callback_jwe",
    ],
)
def test_generate_jwe_round_trip(jwe_generator, policy_pre_execution_webhooks):
    for webhook in policy_pre_execution_webhooks:
        jwe = jwe_generator(webhook)
        decrypted_payload = decrypt_jwe(jwe, CONFIG.security.app_encryption_key)
        assert decrypted_payload  # Ensure the payload is not empty
        assert isinstance(decrypted_payload, str)  # Ensure the payload is a string
        assert (
            "webhook_id" in decrypted_payload or "request_task_id" in decrypted_payload
        )  # Verify expected fields in the payload
        assert "scopes" in decrypted_payload
        assert "iat" in decrypted_payload


@pytest.mark.parametrize(
    "jwe_generator",
    [
        generate_request_callback_pre_approval_jwe,
        generate_request_task_callback_jwe,
        generate_request_callback_resume_jwe,
    ],
    ids=[
        "pre_approval_jwe",
        "task_callback_jwe",
        "resume_callback_jwe",
    ],
)
def test_generate_jwe_invalid_input(jwe_generator):
    with pytest.raises(AttributeError):
        jwe_generator(None)

    with pytest.raises(AttributeError):
        jwe_generator({})


@pytest.mark.parametrize(
    "jwe_generator",
    [
        generate_request_callback_pre_approval_jwe,
        generate_request_task_callback_jwe,
        generate_request_callback_resume_jwe,
    ],
    ids=[
        "pre_approval_jwe",
        "task_callback_jwe",
        "resume_callback_jwe",
    ],
)
def test_generate_jwe_replay_protection(jwe_generator, policy_pre_execution_webhooks):
    for webhook in policy_pre_execution_webhooks:
        jwe1 = jwe_generator(webhook)
        jwe2 = jwe_generator(webhook)
        assert jwe1 != jwe2  # Ensure the JWEs are different
