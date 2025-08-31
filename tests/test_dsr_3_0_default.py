"""Test that DSR 3.0 is now the default scheduler with backward compatibility for existing DSR 2.0 requests."""

from fides.api.models.privacy_request import PrivacyRequest
from fides.api.models.privacy_request.request_task import RequestTask
from fides.api.schemas.policy import ActionType
from fides.api.task.scheduler_utils import use_dsr_3_0_scheduler


class TestDSR3DefaultScheduler:
    """Test that DSR 3.0 is now the default scheduler."""

    def test_dsr_3_0_is_default_for_new_requests(self, db, policy):
        """Test that new privacy requests use DSR 3.0 by default."""
        # Create a new privacy request without any previous processing
        privacy_request = PrivacyRequest.create(
            db=db,
            data={
                "policy_id": policy.id,
                "status": "pending",
            },
        )

        # The scheduler should default to DSR 3.0 for new requests
        result = use_dsr_3_0_scheduler(privacy_request, ActionType.access)
        assert result is True

        privacy_request.delete(db=db)

    def test_existing_dsr_2_0_requests_can_continue(self, db, policy, cache):
        """Test that existing DSR 2.0 requests can continue with DSR 2.0."""
        # Create a privacy request and simulate it having previous DSR 2.0 results
        privacy_request = PrivacyRequest.create(
            db=db,
            data={
                "policy_id": policy.id,
                "status": "in_processing",
            },
        )

        # Simulate having previous DSR 2.0 results by storing data in cache
        cache_key = (
            f"{privacy_request.id}__access_request__test_dataset:test_collection"
        )
        cache.set_encoded_object(cache_key, {"test": "data"})

        # The scheduler should allow existing DSR 2.0 requests to continue
        result = use_dsr_3_0_scheduler(privacy_request, ActionType.access)
        assert result is False  # Should continue using DSR 2.0

        privacy_request.delete(db=db)
        cache.delete(cache_key)

    def test_new_requests_without_cache_use_dsr_3_0(self, db, policy):
        """Test that new requests without existing cache data use DSR 3.0."""
        # Create a privacy request without any cache data
        privacy_request = PrivacyRequest.create(
            db=db,
            data={
                "policy_id": policy.id,
                "status": "pending",
            },
        )

        # Should use DSR 3.0 for new requests
        result = use_dsr_3_0_scheduler(privacy_request, ActionType.access)
        assert result is True

        privacy_request.delete(db=db)

    def test_cache_exists_but_tasks_exist_uses_dsr_3_0(self, db, policy, cache):
        """
        Test that when cache exists but tasks also exist, scheduler uses DSR 3.0.

        This verifies the existing_tasks_count condition in the scheduler decision.
        The scheduler only allows DSR 2.0 when cache exists AND no tasks exist.
        """
        # Create a privacy request
        privacy_request = PrivacyRequest.create(
            db=db,
            data={
                "policy_id": policy.id,
                "status": "in_processing",
            },
        )

        # Simulate having previous DSR 2.0 results by storing data in cache
        cache_key = (
            f"{privacy_request.id}__access_request__test_dataset:test_collection"
        )
        cache.set_encoded_object(cache_key, {"test": "data"})

        # Create an existing task to simulate partial processing with DSR 3.0
        RequestTask.create(
            db,
            data={
                "action_type": ActionType.access,
                "status": "pending",
                "privacy_request_id": privacy_request.id,
                "collection_address": "test_dataset:test_collection",
                "dataset_name": "test_dataset",
                "collection_name": "test_collection",
                "upstream_tasks": [],
                "downstream_tasks": [],
                "all_descendant_tasks": [],
            },
        )

        # Even though cache exists, because tasks exist, should use DSR 3.0
        result = use_dsr_3_0_scheduler(privacy_request, ActionType.access)
        assert result is True  # Should use DSR 3.0 because tasks exist
