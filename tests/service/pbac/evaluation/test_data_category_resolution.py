"""Tests for data category resolution through InProcessPBACEvaluationService.evaluate().

Verifies that when field_categories are configured, the service resolves
SQL columns to data categories and passes them to the policy evaluator.
Tests exercise the public evaluate() interface with a capturing policy
evaluator to inspect the AccessEvaluationRequest.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from fides.service.pbac.consumers.entities import DataConsumerEntity
from fides.service.pbac.consumers.repository import DataConsumerRedisRepository
from fides.service.pbac.policies.interface import (
    AccessEvaluationRequest,
    AccessPolicyEvaluator,
    PolicyDecision,
    PolicyEvaluationResult,
)
from fides.service.pbac.purposes.repository import DataPurposeRedisRepository
from fides.service.pbac.service import InProcessPBACEvaluationService
from fides.service.pbac.types import (
    DatasetPurposes,
    RawQueryLogEntry,
    TableRef,
)


class CapturingPolicyEvaluator:
    """Records every AccessEvaluationRequest for inspection."""

    def __init__(self):
        self.requests: list[AccessEvaluationRequest] = []

    def evaluate(self, request: AccessEvaluationRequest) -> PolicyEvaluationResult:
        self.requests.append(request)
        return PolicyEvaluationResult(decision=PolicyDecision.NO_DECISION)


def _make_entry(
    query_text: str,
    tables: list[TableRef],
    identity: str = "test@example.com",
) -> RawQueryLogEntry:
    return RawQueryLogEntry(
        source_id="test",
        external_job_id="job-1",
        identity=identity,
        query_text=query_text,
        statement_type="SELECT",
        referenced_tables=tables,
        timestamp=datetime.now(timezone.utc),
    )


@pytest.fixture
def registered_consumer(cache):
    """A consumer with analytics purpose — won't overlap marketing datasets."""
    purpose_repo = DataPurposeRedisRepository(cache)
    consumer_repo = DataConsumerRedisRepository(cache, purpose_repo)
    now = datetime.now(timezone.utc)
    entity = DataConsumerEntity(
        id="consumer-cat-test",
        name="Analytics Pipeline",
        type="group",
        contact_email="test@example.com",
        purpose_fides_keys=["analytics"],
        created_at=now,
        updated_at=now,
    )
    consumer_repo.save(entity)
    yield entity
    try:
        consumer_repo.delete(entity.id)
    except Exception:
        pass


@pytest.fixture
def field_categories():
    return {
        "users": {
            "email": ["user.contact.email"],
            "phone": ["user.contact.phone_number"],
            "ssn": ["user.government_id"],
            "id": ["system.operations"],
        },
    }


@pytest.fixture
def dataset_purposes():
    return {
        "crm": DatasetPurposes(
            dataset_key="crm",
            purpose_keys=frozenset({"marketing"}),
        ),
    }


@pytest.mark.integration
class TestDataCategoryResolution:
    def test_specific_columns_resolve_to_categories(
        self, cache, registered_consumer, field_categories, dataset_purposes
    ):
        evaluator = CapturingPolicyEvaluator()
        service = InProcessPBACEvaluationService(
            cache=cache,
            dataset_purposes=dataset_purposes,
            field_categories=field_categories,
            policy_evaluator=evaluator,
        )
        entry = _make_entry(
            query_text="SELECT email, ssn FROM users",
            tables=[TableRef(catalog="", schema="crm", table="users")],
        )

        service.evaluate(entry)

        assert len(evaluator.requests) == 1
        assert set(evaluator.requests[0].data_categories) == {
            "user.contact.email",
            "user.government_id",
        }

    def test_select_star_resolves_all_field_categories(
        self, cache, registered_consumer, field_categories, dataset_purposes
    ):
        evaluator = CapturingPolicyEvaluator()
        service = InProcessPBACEvaluationService(
            cache=cache,
            dataset_purposes=dataset_purposes,
            field_categories=field_categories,
            policy_evaluator=evaluator,
        )
        entry = _make_entry(
            query_text="SELECT * FROM users",
            tables=[TableRef(catalog="", schema="crm", table="users")],
        )

        service.evaluate(entry)

        assert len(evaluator.requests) == 1
        assert set(evaluator.requests[0].data_categories) == {
            "user.contact.email",
            "user.contact.phone_number",
            "user.government_id",
            "system.operations",
        }

    def test_empty_data_categories_when_no_field_categories_configured(
        self, cache, registered_consumer, dataset_purposes
    ):
        evaluator = CapturingPolicyEvaluator()
        service = InProcessPBACEvaluationService(
            cache=cache,
            dataset_purposes=dataset_purposes,
            policy_evaluator=evaluator,
        )
        entry = _make_entry(
            query_text="SELECT email FROM users",
            tables=[TableRef(catalog="", schema="crm", table="users")],
        )

        service.evaluate(entry)

        assert len(evaluator.requests) == 1
        assert evaluator.requests[0].data_categories == ()

    def test_unknown_columns_produce_empty_categories(
        self, cache, registered_consumer, field_categories, dataset_purposes
    ):
        evaluator = CapturingPolicyEvaluator()
        service = InProcessPBACEvaluationService(
            cache=cache,
            dataset_purposes=dataset_purposes,
            field_categories=field_categories,
            policy_evaluator=evaluator,
        )
        entry = _make_entry(
            query_text="SELECT nonexistent_col FROM users",
            tables=[TableRef(catalog="", schema="crm", table="users")],
        )

        service.evaluate(entry)

        assert len(evaluator.requests) == 1
        assert evaluator.requests[0].data_categories == ()

    def test_compliant_query_does_not_invoke_policy_evaluator(
        self, cache, field_categories
    ):
        evaluator = CapturingPolicyEvaluator()
        purposes = {
            "crm": DatasetPurposes(
                dataset_key="crm",
                purpose_keys=frozenset({"analytics"}),
            ),
        }
        service = InProcessPBACEvaluationService(
            cache=cache,
            dataset_purposes=purposes,
            field_categories=field_categories,
            policy_evaluator=evaluator,
        )
        entry = _make_entry(
            query_text="SELECT email FROM users",
            tables=[TableRef(catalog="", schema="crm", table="users")],
        )

        result = service.evaluate(entry)

        assert result.is_compliant
        assert len(evaluator.requests) == 0
