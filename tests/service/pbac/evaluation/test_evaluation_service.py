"""Integration tests for InProcessPBACEvaluationService.evaluate().

Covers the full pipeline through the public interface:
- Consumer resolution via Redis (registered vs unregistered)
- Dataset purpose lookup from the init-time map
- Collection-level purpose inheritance end-to-end
- Interaction between dataset_purpose_overrides and the init map
"""

from datetime import datetime, timezone

import pytest

from fides.service.pbac.consumers.entities import DataConsumerEntity
from fides.service.pbac.consumers.repository import DataConsumerRedisRepository
from fides.service.pbac.purposes.repository import DataPurposeRedisRepository
from fides.service.pbac.service import InProcessPBACEvaluationService
from fides.service.pbac.types import (
    DatasetPurposes,
    GapType,
    RawQueryLogEntry,
    TableRef,
)


@pytest.fixture
def purpose_repo(cache):
    return DataPurposeRedisRepository(cache)


@pytest.fixture
def consumer_repo(cache, purpose_repo):
    return DataConsumerRedisRepository(cache, purpose_repo)


@pytest.fixture
def registered_consumer(consumer_repo):
    """A consumer registered in Redis with billing + analytics purposes."""
    now = datetime.now(timezone.utc)
    entity = DataConsumerEntity(
        id="consumer-integ-1",
        name="Billing Pipeline",
        type="group",
        contact_email="billing@example.com",
        purpose_fides_keys=["billing", "analytics"],
        created_at=now,
        updated_at=now,
    )
    consumer_repo.save(entity)
    yield entity
    # Cleanup
    try:
        consumer_repo.delete(entity.id)
    except Exception:
        pass


@pytest.fixture
def dataset_purposes_map():
    return {
        "billing_db": DatasetPurposes(
            dataset_key="billing_db",
            purpose_keys=frozenset({"billing"}),
            collection_purposes={
                "invoices": frozenset({"accounting"}),
            },
        ),
        "analytics_db": DatasetPurposes(
            dataset_key="analytics_db",
            purpose_keys=frozenset({"analytics"}),
        ),
        "marketing_db": DatasetPurposes(
            dataset_key="marketing_db",
            purpose_keys=frozenset({"marketing"}),
        ),
    }


def _make_entry(
    identity: str,
    tables: list[TableRef],
) -> RawQueryLogEntry:
    return RawQueryLogEntry(
        source_id="test",
        external_job_id="job-1",
        identity=identity,
        query_text="SELECT 1",
        statement_type="SELECT",
        referenced_tables=tables,
        timestamp=datetime.now(timezone.utc),
    )


# --- Registered consumer + dataset purposes from init map ---


@pytest.mark.integration
class TestRegisteredConsumerWithDatasetPurposes:
    def test_compliant_when_purposes_overlap(
        self, cache, registered_consumer, dataset_purposes_map
    ):
        service = InProcessPBACEvaluationService(
            cache=cache,
            dataset_purposes=dataset_purposes_map,
        )
        entry = _make_entry(
            "billing@example.com",
            [TableRef(catalog="", schema="billing_db", table="invoices")],
        )

        output = service.evaluate(entry)

        assert output.is_compliant
        assert output.consumer.id == "consumer-integ-1"
        assert output.consumer.type == "group"

    def test_violation_when_purposes_do_not_overlap(
        self, cache, registered_consumer, dataset_purposes_map
    ):
        service = InProcessPBACEvaluationService(
            cache=cache,
            dataset_purposes=dataset_purposes_map,
        )
        entry = _make_entry(
            "billing@example.com",
            [TableRef(catalog="", schema="marketing_db", table="campaigns")],
        )

        output = service.evaluate(entry)

        assert not output.is_compliant
        assert len(output.violations) == 1
        assert output.violations[0].dataset_key == "marketing_db"
        assert output.violations[0].control == "purpose_restriction"

    def test_mixed_compliance_across_datasets(
        self, cache, registered_consumer, dataset_purposes_map
    ):
        service = InProcessPBACEvaluationService(
            cache=cache,
            dataset_purposes=dataset_purposes_map,
        )
        entry = _make_entry(
            "billing@example.com",
            [
                TableRef(catalog="", schema="billing_db", table="invoices"),
                TableRef(catalog="", schema="marketing_db", table="campaigns"),
            ],
        )

        output = service.evaluate(entry)

        assert not output.is_compliant
        assert output.total_accesses == 2
        assert len(output.violations) == 1
        assert output.violations[0].dataset_key == "marketing_db"


# --- Unregistered consumer ---


@pytest.mark.integration
class TestUnregisteredConsumer:
    def test_unregistered_consumer_produces_gaps(self, cache, dataset_purposes_map):
        service = InProcessPBACEvaluationService(
            cache=cache,
            dataset_purposes=dataset_purposes_map,
        )
        entry = _make_entry(
            "unknown@example.com",
            [TableRef(catalog="", schema="billing_db", table="invoices")],
        )

        output = service.evaluate(entry)

        assert output.consumer is None
        assert len(output.gaps) >= 1
        assert output.gaps[0].gap_type == GapType.UNRESOLVED_IDENTITY
        assert "no declared purposes" in output.gaps[0].reason


# --- Dataset not in the purposes map ---


@pytest.mark.integration
class TestDatasetNotInMap:
    def test_unknown_dataset_produces_gap_for_registered_consumer(
        self, cache, registered_consumer, dataset_purposes_map
    ):
        """A dataset with no entry in the map has no declared purposes -> gap."""
        service = InProcessPBACEvaluationService(
            cache=cache,
            dataset_purposes=dataset_purposes_map,
        )
        entry = _make_entry(
            "billing@example.com",
            [TableRef(catalog="", schema="unknown_db", table="things")],
        )

        output = service.evaluate(entry)

        assert output.is_compliant
        assert len(output.gaps) >= 1


# --- dataset_purpose_overrides takes precedence ---


@pytest.mark.integration
class TestDatasetPurposeOverrides:
    def test_overrides_take_precedence_over_init_map(
        self, cache, registered_consumer, dataset_purposes_map
    ):
        """Explicit overrides passed to evaluate() override the init-time map."""
        service = InProcessPBACEvaluationService(
            cache=cache,
            dataset_purposes=dataset_purposes_map,
        )
        entry = _make_entry(
            "billing@example.com",
            [TableRef(catalog="", schema="marketing_db", table="campaigns")],
        )

        # marketing_db would normally violate, but override gives it billing purpose
        output = service.evaluate(
            entry,
            dataset_purpose_overrides={"marketing_db": ["billing"]},
        )

        assert output.is_compliant


# --- No dataset purposes provided (backward compat) ---


@pytest.mark.integration
class TestNoDatasetPurposes:
    def test_no_map_means_all_datasets_unrestricted(self, cache, registered_consumer):
        """Without a dataset_purposes map, all datasets fall back to empty
        purposes -> gap (compliant for registered consumers)."""
        service = InProcessPBACEvaluationService(cache=cache)
        entry = _make_entry(
            "billing@example.com",
            [TableRef(catalog="", schema="billing_db", table="invoices")],
        )

        output = service.evaluate(entry)

        assert output.is_compliant
