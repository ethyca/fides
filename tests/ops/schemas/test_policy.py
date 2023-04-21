from pydantic.error_wrappers import ValidationError
import pytest

from fides.api.ops.schemas.policy import RuleTarget


def test_rule_target_schema():
    with pytest.raises(ValidationError):
        RuleTarget(data_category="not_a_real_data_category")

    rt = RuleTarget(data_category="user")
    assert rt.data_category == "user"
