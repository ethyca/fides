from fides.api.task.task_resources import TaskResources


class TestTaskResources:
    def test_cache_object(self, db, privacy_request, policy, integration_manual_config):
        resources = TaskResources(
            privacy_request, policy, [integration_manual_config], db
        )

        assert resources.get_all_cached_objects() == {}

        resources.cache_object(
            "access_request__postgres_example:customer", [{"id": 1, "last_name": "Doe"}]
        )
        resources.cache_object(
            "access_request__postgres_example:payment",
            [{"id": 2, "ccn": "111-111-1111-1111", "customer_id": 1}],
        )
        resources.cache_erasure("manual_example:filing-cabinet", 2)

        # Only access results from "cache_object" are returned
        assert resources.get_all_cached_objects() == {
            "postgres_example:payment": [
                {"id": 2, "ccn": "111-111-1111-1111", "customer_id": 1}
            ],
            "postgres_example:customer": [{"id": 1, "last_name": "Doe"}],
        }

    def test_cache_erasure(
        self, db, privacy_request, policy, integration_manual_config
    ):
        resources = TaskResources(
            privacy_request, policy, [integration_manual_config], db
        )

        assert resources.get_all_cached_erasures() == {}

        resources.cache_erasure("manual_example:filing-cabinet", 2)
        resources.cache_erasure("manual_example:storage-unit", 3)

        assert resources.get_all_cached_erasures() == {
            "manual_example:filing-cabinet": 2,
            "manual_example:storage-unit": 3,
        }
