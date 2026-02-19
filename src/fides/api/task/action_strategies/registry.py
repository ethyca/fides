from fides.api.schemas.policy import ActionType
from fides.api.task.action_strategies.access_strategy import AccessStrategy
from fides.api.task.action_strategies.base import ActionStrategy
from fides.api.task.action_strategies.consent_strategy import ConsentStrategy
from fides.api.task.action_strategies.erasure_strategy import ErasureStrategy

ACTION_STRATEGIES: dict[ActionType, ActionStrategy] = {
    ActionType.access: AccessStrategy(),
    ActionType.erasure: ErasureStrategy(),
    ActionType.consent: ConsentStrategy(),
}
