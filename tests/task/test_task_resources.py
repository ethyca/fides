from fidesops.task.task_resources import TaskResources


class TestTaskResources:
    def test_cache_erasure(self, privacy_request, policy, integration_manual_config):
        resources = TaskResources(privacy_request, policy, [integration_manual_config])

        assert resources.get_all_cached_erasures() == {}

        resources.cache_erasure("manual_example:filing-cabinet", 2)
        resources.cache_erasure("manual_example:storage-unit", 3)

        assert resources.get_all_cached_erasures() == {
            "manual_example:filing-cabinet": 2,
            "manual_example:storage-unit": 3,
        }
