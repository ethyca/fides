
import pytest

from fides.api.graph.graph import DatasetGraph
from fides.api.models.datasetconfig import convert_dataset_to_graph
from fides.api.models.privacy_request import ExecutionLogStatus, PrivacyRequestStatus
from fides.api.models.sql_models import Dataset
from fides.api.schemas.policy import ActionType
from fides.api.task.create_request_tasks import run_access_request
from fixtures.application_fixtures import example_datasets


@pytest.mark.integration_external
@pytest.mark.integration_bigquery
@pytest.skip(reason="Isolate test strategy to DSRs for now")
def test_bigquery_example_data(bigquery_enterprise_test_engine):
    """Confirm that we can connect to the bigquery enterprise db and get table names"""
    inspector = inspect(bigquery_enterprise_test_engine)
    assert sorted(inspector.get_table_names(schema="enterprise_dsr_testing")) == sorted(
        [
            "badges",
            "comments",
            "post_history",
            "post_links",
            "posts_answers",
            "posts_moderator_nomination",
            "posts_orphaned_tag_wiki",
            "posts_privilege_wiki",
            "posts_questions",
            "posts_tag_wiki",
            "posts_tag_wiki_excerpt",
            "posts_wiki_placeholder",
            "stackoverflow_posts",
            "tags",
            "users",
            "votes",
        ]
    )

class TestRunAccessRequestWithRequestTasks:
    @pytest.mark.timeout(5)
    @pytest.mark.integration
    @pytest.mark.integration_bigquery
    def test_run_access_request(
            self,
            db,
            privacy_request,
            policy,
            bigquery_connection_config,
    ):
        # uses a fixture that also creates the dataset config for more realistic testing
        dataset = Dataset(**example_datasets[16])  # todo- use secrets instead of hard-coded
        initial_graph = convert_dataset_to_graph(
            dataset, bigquery_connection_config.key
        )
        graph = DatasetGraph(*[initial_graph])

        identity = {"stackoverflow_user_id": 1754}  # this is a real (not generated) user id in the Stackoverflow dataset

        run_access_request(
            privacy_request,
            policy,
            graph,
            [
                bigquery_enterprise_test_dataset_config,
            ],
            identity,
            db,
            privacy_request_proceed=True,
        )
        wait_for_tasks_to_complete(db, privacy_request, ActionType.access)

        assert privacy_request.access_tasks.count() == 16
        assert privacy_request.erasure_tasks.count() == 0

        all_access_tasks = privacy_request.access_tasks.all()

        assert {t.collection_address for t in all_access_tasks} == {
            "__ROOT__:__ROOT__",
            "bigquery_enterprise_test_dataset:users",
            "bigquery_enterprise_test_dataset:comments",
            "bigquery_enterprise_test_dataset:post_history",
            "bigquery_enterprise_test_dataset:stackoverflow_posts",
            "__TERMINATE__:__TERMINATE__",
        }
        assert all(t.status == ExecutionLogStatus.complete for t in all_access_tasks)
        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.complete

        raw_access_results = privacy_request.get_raw_access_results()

        # 16 comments being found tests that our input_keys are working properly
        assert len([comment["id"] for comment in raw_access_results["bigquery_enterprise_test_dataset:comments"]]) == 16

        customer_details = raw_access_results["bigquery_enterprise_test_dataset:user"][0]
        assert customer_details["display_name"] == "David R. Longnecker"
        assert customer_details["location"] == "Kansas City, MO, USA"
        assert customer_details["profile_image_url"] == "https://i.stack.imgur.com/egFxf.jpg?s=128&g=1"


# todo- include util method (unused) to re-populate the relevant bigquery table(s) with data if data has been lost / corrupted