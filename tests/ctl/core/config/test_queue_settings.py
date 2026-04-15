import os
import pytest
from hypothesis import given, strategies as st, provisional as pst

from fides.config.queue_settings import QueueSettings

class TestQueueSettings:
    def test_default_values(self) -> None:
        settings = QueueSettings()
        assert settings.use_sqs_queue is False
        assert settings.sqs_url is None
        assert settings.aws_region == "us-east-1"
        assert settings.aws_access_key_id is None
        assert settings.aws_secret_access_key is None
        assert settings.sqs_queue_name_prefix == "fides-"

    @pytest.mark.parametrize(
        "env_var, value, expected",
        [
            ("FIDES__QUEUE__USE_SQS_QUEUE", "True", True),
            ("FIDES__QUEUE__USE_SQS_QUEUE", "False", False),
            ("FIDES__QUEUE__SQS_URL", "http://localhost:9324", "http://localhost:9324"),
            ("FIDES__QUEUE__AWS_REGION", "us-west-2", "us-west-2"),
            ("FIDES__QUEUE__AWS_ACCESS_KEY_ID", "my_key", "my_key"),
            ("FIDES__QUEUE__AWS_SECRET_ACCESS_KEY", "my_secret", "my_secret"),
            ("FIDES__QUEUE__SQS_QUEUE_NAME_PREFIX", "test-prefix-", "test-prefix-"),
        ],
    )
    def test_env_var_overrides(self, env_var: str, value: str, expected: any, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(env_var, value)
        settings = QueueSettings()
        
        attr_name = env_var.replace("FIDES__QUEUE__", "").lower()
        actual = getattr(settings, attr_name)
        assert actual == expected

@given(
    use_sqs_queue=st.booleans(),
    sqs_url=st.one_of(st.none(), pst.urls()),
    aws_region=st.text(min_size=1, max_size=20).filter(lambda s: "\x00" not in s),
    aws_access_key_id=st.one_of(st.none(), st.text(min_size=1, max_size=20).filter(lambda s: "\x00" not in s)),
    aws_secret_access_key=st.one_of(st.none(), st.text(min_size=1, max_size=40).filter(lambda s: "\x00" not in s)),
    sqs_queue_name_prefix=st.text(min_size=1, max_size=10).filter(lambda s: "\x00" not in s),
)
def test_queue_settings_env_var_round_trip(
    use_sqs_queue,
    sqs_url,
    aws_region,
    aws_access_key_id,
    aws_secret_access_key,
    sqs_queue_name_prefix,
):
    """
    Property 12: Config Env Var Round-Trip
    For any valid value assigned via FIDES__QUEUE__* env var, reading the resulting
    QueueSettings object returns the same value.
    """
    env_vars = {
        "FIDES__QUEUE__USE_SQS_QUEUE": str(use_sqs_queue),
        "FIDES__QUEUE__AWS_REGION": aws_region,
        "FIDES__QUEUE__SQS_QUEUE_NAME_PREFIX": sqs_queue_name_prefix,
    }
    if sqs_url is not None:
        env_vars["FIDES__QUEUE__SQS_URL"] = sqs_url
    if aws_access_key_id is not None:
        env_vars["FIDES__QUEUE__AWS_ACCESS_KEY_ID"] = aws_access_key_id
    if aws_secret_access_key is not None:
        env_vars["FIDES__QUEUE__AWS_SECRET_ACCESS_KEY"] = aws_secret_access_key

    old_environ = dict(os.environ)
    os.environ.update(env_vars)

    try:
        settings = QueueSettings()
        assert settings.use_sqs_queue == use_sqs_queue
        if sqs_url is not None:
            assert settings.sqs_url == sqs_url
        assert settings.aws_region == aws_region
        if aws_access_key_id is not None:
            assert settings.aws_access_key_id == aws_access_key_id
        if aws_secret_access_key is not None:
            assert settings.aws_secret_access_key == aws_secret_access_key
        assert settings.sqs_queue_name_prefix == sqs_queue_name_prefix
    finally:
        os.environ.clear()
        os.environ.update(old_environ)
