import pytest
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from fides.api.models.detection_discovery import DiffStatus, StagedResource


class TestStagedResourceModel:
    @pytest.fixture
    def create_staged_resource(self, db: Session):
        urn = "bq_monitor_1.prj-bigquery-418515.test_dataset_1.consent-reports-20"
        resource = StagedResource.create(
            db=db,
            # the data below isn't realistic, just to exhaust all the fields
            data={
                "urn": urn,
                "user_assigned_data_categories": ["user.contact.email"],
                "name": "consent-reports-20",
                "resource_type": "Table",
                "description": "test description",
                "monitor_config_id": "bq_monitor_1",
                "source_modified": "2024-03-27T21:47:09.915000+00:00",
                "classifications": [
                    {
                        "label": "user.authorization.credentials",
                        "score": 0.4247,
                        "aggregated_score": 0.2336,
                        "classification_paradigm": "context",
                    },
                    {
                        "label": "system",
                        "score": 0.4,
                        "aggregated_score": 0.18,
                        "classification_paradigm": "content",
                    },
                ],
                "diff_status": DiffStatus.MONITORED.value,
                "child_diff_statuses": {DiffStatus.CLASSIFICATION_ADDITION.value: 9},
                "children": [
                    "bq_monitor_1.prj-bigquery-418515.test_dataset_1.consent-reports-20.Notice_title",
                    "bq_monitor_1.prj-bigquery-418515.test_dataset_1.consent-reports-20.Email",
                    "bq_monitor_1.prj-bigquery-418515.test_dataset_1.consent-reports-20.Method",
                    "bq_monitor_1.prj-bigquery-418515.test_dataset_1.consent-reports-20.Fides_user_device",
                    "bq_monitor_1.prj-bigquery-418515.test_dataset_1.consent-reports-20.Created",
                    "bq_monitor_1.prj-bigquery-418515.test_dataset_1.consent-reports-20.Preference",
                    "bq_monitor_1.prj-bigquery-418515.test_dataset_1.consent-reports-20.Request_origin",
                    "bq_monitor_1.prj-bigquery-418515.test_dataset_1.consent-reports-20.User_geography",
                    "bq_monitor_1.prj-bigquery-418515.test_dataset_1.consent-reports-20.Phone_number",
                ],
                "parent": "bq_monitor_1.prj-bigquery-418515.test_dataset_1",
                "meta": {"num_rows": 19},
            },
        )
        return resource

    def test_create_staged_resource(self, db: Session, create_staged_resource) -> None:
        """
        Creation fixture creates the resource, this tests that it was created successfully
        and that we can access its attributes as expected
        """
        saved_resource: StagedResource = StagedResource.get_urn(
            db, create_staged_resource.urn
        )
        assert saved_resource.user_assigned_data_categories == ["user.contact.email"]
        assert saved_resource.classifications == [
            {
                "label": "user.authorization.credentials",
                "score": 0.4247,
                "aggregated_score": 0.2336,
                "classification_paradigm": "context",
            },
            {
                "label": "system",
                "score": 0.4,
                "aggregated_score": 0.18,
                "classification_paradigm": "content",
            },
        ]
        assert saved_resource.meta == {"num_rows": 19}
        assert saved_resource.child_diff_statuses == {
            DiffStatus.CLASSIFICATION_ADDITION.value: 9
        }
        assert saved_resource.diff_status == DiffStatus.MONITORED.value

    def test_update_staged_resource(self, db: Session, create_staged_resource) -> None:
        """
        Tests that we can update a staged resource, specifically some of its more complex fields
        """
        saved_resource: StagedResource = StagedResource.get_urn(
            db, create_staged_resource.urn
        )
        saved_resource.user_assigned_data_categories.append("system")
        # needed to ensure array updates are persisted to the db
        flag_modified(saved_resource, "user_assigned_data_categories")

        saved_resource.classifications.append(
            {
                "label": "user.contact.email",
                "score": 0.2,
                "aggregated_score": 0.1,
                "classification_paradigm": "content",
            }
        )
        # needed to ensure array updates are persisted to the db
        flag_modified(saved_resource, "classifications")
        saved_resource.diff_status = DiffStatus.ADDITION.value

        saved_resource.save(db)
        updated_resource = StagedResource.get_urn(db, saved_resource.urn)
        assert updated_resource.diff_status == DiffStatus.ADDITION.value
        assert updated_resource.user_assigned_data_categories == [
            "user.contact.email",
            "system",
        ]
        assert updated_resource.classifications == [
            {
                "label": "user.authorization.credentials",
                "score": 0.4247,
                "aggregated_score": 0.2336,
                "classification_paradigm": "context",
            },
            {
                "label": "system",
                "score": 0.4,
                "aggregated_score": 0.18,
                "classification_paradigm": "content",
            },
            {
                "label": "user.contact.email",
                "score": 0.2,
                "aggregated_score": 0.1,
                "classification_paradigm": "content",
            },
        ]

    def test_staged_resource_helpers(self, db: Session, create_staged_resource):
        saved_resource: StagedResource = StagedResource.get_urn(
            db, create_staged_resource.urn
        )
        saved_resource.add_child_diff_status(diff_status=DiffStatus.REMOVAL)
        saved_resource.add_child_diff_status(
            diff_status=DiffStatus.CLASSIFICATION_ADDITION
        )
        saved_resource.save(db)

        updated_resource: StagedResource = StagedResource.get_urn(
            db, saved_resource.urn
        )
        assert updated_resource.child_diff_statuses == {
            DiffStatus.REMOVAL.value: 1,
            DiffStatus.CLASSIFICATION_ADDITION.value: 10,
        }
