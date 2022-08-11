from fidesops.ops.common_exceptions import FidesopsException
from fidesops.ops.graph.analytics_events import failed_graph_analytics_event


class TestFailedGraphAnalyticsEvent:
    def test_create_failed_privacy_request_event(self, privacy_request):
        fake_exception = FidesopsException("Graph Failed")
        analytics_event = failed_graph_analytics_event(privacy_request, fake_exception)

        assert analytics_event.docker is True
        assert analytics_event.event == "privacy_request_execution_failure"
        assert analytics_event.event_created_at is not None
        assert analytics_event.extra_data == {
            "privacy_request": privacy_request.id,
        }

        assert analytics_event.error == "FidesopsException"
        assert analytics_event.status_code == 500
        assert analytics_event.endpoint is None
        assert analytics_event.local_host is False
