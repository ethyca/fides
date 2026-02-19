from __future__ import annotations

from typing import Optional

from fides.api.common_exceptions import MaskingSecretsExpired
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import ActionType, CurrentStep
from fides.api.service.privacy_request.pipeline.base import PipelineStep, StepResult
from fides.api.service.privacy_request.pipeline.context import PipelineContext
from fides.api.task.action_strategies.registry import ACTION_STRATEGIES
from fides.api.util.cache import get_all_masking_secret_keys


def _verify_masking_secrets(
    policy: Policy, privacy_request: PrivacyRequest, resume_step: Optional[CurrentStep]
) -> None:
    """
    Checks that the required masking secrets are still cached for the given request.
    Raises an exception if masking secrets are needed for the given policy but they don't exist.
    """
    if resume_step is None:
        return

    if (
        policy.generate_masking_secrets()
        and not get_all_masking_secret_keys(privacy_request.id)
        and not privacy_request.masking_secrets
    ):
        raise MaskingSecretsExpired(
            f"The masking secrets for privacy request ID '{privacy_request.id}' have expired. Please submit a new erasure request."
        )


class ErasureStep(PipelineStep):
    @property
    def checkpoint(self) -> Optional[CurrentStep]:
        return CurrentStep.erasure

    @property
    def required_action_types(self) -> Optional[set[ActionType]]:
        return {ActionType.erasure}

    def execute(self, ctx: PipelineContext) -> StepResult:
        _verify_masking_secrets(ctx.policy, ctx.privacy_request, ctx.resume_step)
        ACTION_STRATEGIES[ActionType.erasure].run_pipeline_action(ctx)
        return StepResult.HALT
