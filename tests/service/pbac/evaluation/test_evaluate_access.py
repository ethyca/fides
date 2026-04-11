"""Tests for the PBAC purpose evaluation engine (evaluate_purpose).

Covers:
- Rule 1: consumer with no purposes -> gap for every dataset
- Rule 2: consumer purposes don't intersect dataset purposes -> violation
- Rule 3: dataset with no declared purposes -> gap
- Collection-level additive purpose inheritance
- Multiple datasets in a single query
"""

from datetime import datetime, timezone

import pytest

from fides.service.pbac.evaluate import evaluate_purpose
from fides.service.pbac.types import (
    ConsumerPurposes,
    DatasetPurposes,
)


@pytest.fixture
def now():
    return datetime.now(timezone.utc)


def _make_consumer(purpose_keys: frozenset[str]) -> ConsumerPurposes:
    return ConsumerPurposes(
        consumer_id="consumer-1",
        consumer_name="test-consumer",
        purpose_keys=purpose_keys,
    )


# --- Rule 1: consumer with no purposes ---


def test_no_consumer_purposes_produces_gap(now):
    consumer = _make_consumer(frozenset())
    datasets = {
        "ds_billing": DatasetPurposes(
            dataset_key="ds_billing",
            purpose_keys=frozenset({"billing"}),
        )
    }

    output = evaluate_purpose(consumer, datasets, query_id="q-1")

    assert len(output.violations) == 0
    assert len(output.gaps) == 1
    assert "no declared purposes" in output.gaps[0].reason


def test_no_consumer_purposes_with_unrestricted_dataset(now):
    """A consumer with no purposes accessing an unrestricted dataset
    produces a gap flagging the consumer as having no declared purposes."""
    consumer = _make_consumer(frozenset())
    datasets = {
        "ds_open": DatasetPurposes(
            dataset_key="ds_open",
            purpose_keys=frozenset(),
        )
    }

    output = evaluate_purpose(consumer, datasets, query_id="q-1")

    assert len(output.violations) == 0
    assert len(output.gaps) == 1
    assert "no declared purposes" in output.gaps[0].reason


# --- Rule 2: purpose mismatch ---


def test_purpose_mismatch_produces_violation(now):
    consumer = _make_consumer(frozenset({"analytics"}))
    datasets = {
        "ds_billing": DatasetPurposes(
            dataset_key="ds_billing",
            purpose_keys=frozenset({"billing"}),
        )
    }

    output = evaluate_purpose(consumer, datasets, query_id="q-1")

    assert len(output.violations) == 1
    assert "do not overlap" in output.violations[0].reason


def test_purpose_overlap_is_compliant(now):
    consumer = _make_consumer(frozenset({"billing", "analytics"}))
    datasets = {
        "ds_billing": DatasetPurposes(
            dataset_key="ds_billing",
            purpose_keys=frozenset({"billing"}),
        )
    }

    output = evaluate_purpose(consumer, datasets, query_id="q-1")

    assert len(output.violations) == 0


# --- Rule 3: dataset with no declared purposes ---


def test_unrestricted_dataset_produces_gap(now):
    consumer = _make_consumer(frozenset({"billing"}))
    datasets = {
        "ds_open": DatasetPurposes(
            dataset_key="ds_open",
            purpose_keys=frozenset(),
        )
    }

    output = evaluate_purpose(consumer, datasets, query_id="q-1")

    assert len(output.violations) == 0
    assert len(output.gaps) == 1


# --- Collection-level additive inheritance ---


def test_collection_inherits_dataset_purposes(now):
    """A collection with no extra purposes inherits dataset-level purposes."""
    consumer = _make_consumer(frozenset({"billing"}))
    datasets = {
        "ds_billing": DatasetPurposes(
            dataset_key="ds_billing",
            purpose_keys=frozenset({"billing"}),
            collection_purposes={},
        )
    }

    output = evaluate_purpose(
        consumer,
        datasets,
        query_id="q-1",
        collections={"ds_billing": ("users",)},
    )

    assert len(output.violations) == 0


def test_collection_adds_own_purposes(now):
    """Collection purposes are additive -- consumer matches collection-level purpose
    even if it doesn't match dataset-level."""
    consumer = _make_consumer(frozenset({"analytics"}))
    datasets = {
        "ds_billing": DatasetPurposes(
            dataset_key="ds_billing",
            purpose_keys=frozenset({"billing"}),
            collection_purposes={"events": frozenset({"analytics"})},
        )
    }

    output = evaluate_purpose(
        consumer,
        datasets,
        query_id="q-1",
        collections={"ds_billing": ("events",)},
    )

    assert len(output.violations) == 0


def test_collection_mismatch_produces_violation(now):
    """Consumer purpose doesn't overlap with either dataset or collection purposes."""
    consumer = _make_consumer(frozenset({"marketing"}))
    datasets = {
        "ds_billing": DatasetPurposes(
            dataset_key="ds_billing",
            purpose_keys=frozenset({"billing"}),
            collection_purposes={"events": frozenset({"analytics"})},
        )
    }

    output = evaluate_purpose(
        consumer,
        datasets,
        query_id="q-1",
        collections={"ds_billing": ("events",)},
    )

    assert len(output.violations) == 1


# --- Multiple datasets ---


def test_multiple_datasets_mixed_compliance(now):
    consumer = _make_consumer(frozenset({"billing"}))
    datasets = {
        "ds_billing": DatasetPurposes(
            dataset_key="ds_billing",
            purpose_keys=frozenset({"billing"}),
        ),
        "ds_analytics": DatasetPurposes(
            dataset_key="ds_analytics",
            purpose_keys=frozenset({"analytics"}),
        ),
    }

    output = evaluate_purpose(consumer, datasets, query_id="q-1")

    assert output.total_accesses == 2
    assert len(output.violations) == 1
    assert output.violations[0].dataset_key == "ds_analytics"
