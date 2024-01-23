import pytest

from fides.config.execution_settings import ExecutionSettings


@pytest.mark.unit
class TestExecutionSettings:
    """
    The disable_consent_identity_verification should be dynamic and based on subject_verification_required but only
    if a value for disable_consent_identity_verification is not provided. In order for this fallback to work as
    expected we don't derive the fallback value in the ExecutionSettings but in the ExecutionSettingsProxy.
    These tests just make sure that we leave disable_consent_identity_verification as is.
    """

    @pytest.mark.parametrize(
        "subject_verification_required, disable_consent_verification, expected",
        [
            (True, None, None),
            (None, None, None),
            (None, True, True),
            (True, False, False),
            (False, None, None),
        ],
    )
    def test_default_value_for_disable_consent_identity_verification(
        self, subject_verification_required, disable_consent_verification, expected
    ):
        kwargs = {}
        if subject_verification_required is not None:
            kwargs[
                "subject_identity_verification_required"
            ] = subject_verification_required
        if disable_consent_verification is not None:
            kwargs[
                "disable_consent_identity_verification"
            ] = disable_consent_verification

        settings = ExecutionSettings(**kwargs)
        assert settings.disable_consent_identity_verification is expected
