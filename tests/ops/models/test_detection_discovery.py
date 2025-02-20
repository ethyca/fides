from datetime import datetime, timezone
from typing import List

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.detection_discovery import (
    DiffStatus,
    MonitorConfig,
    MonitorFrequency,
    StagedResource,
    fetch_staged_resources_by_type_query,
)


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

    @pytest.fixture
    def create_staged_database(self, db: Session):
        urn = "bq_monitor_1.prj-bigquery-418515.test_dataset_1"
        resource = StagedResource.create(
            db=db,
            data={
                "urn": urn,
                "user_assigned_data_categories": ["user.contact.email"],
                "name": "test_dataset_1",
                "resource_type": "Database",
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
                    "bq_monitor_1.prj-bigquery-418515.test_dataset_1.consent-reports-20",
                    "bq_monitor_1.prj-bigquery-418515.test_dataset_1.consent-reports-21",
                ],
                "parent": "bq_monitor_1.prj-bigquery-418515",
                "meta": {"num_rows": 19},
            },
        )
        return resource

    @pytest.fixture
    def create_staged_schema(self, db: Session):
        urn = "bq_monitor_1.prj-bigquery-418515"
        resource = StagedResource.create(
            db=db,
            data={
                "urn": urn,
                "user_assigned_data_categories": ["user.contact.email"],
                "name": "prj-bigquery-418515",
                "resource_type": "Schema",
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
                    "bq_monitor_1.prj-bigquery-418515.test_dataset_1",
                    "bq_monitor_1.prj-bigquery-418515.test_dataset_2",
                ],
                "parent": "bq_monitor_1",
                "meta": {"num_rows": 19},
            },
        )
        return resource

    def test_get_urn(self, db: Session, create_staged_resource) -> None:
        urn_list = [create_staged_resource.urn]
        from_db = StagedResource.get_urn_list(db, urn_list)
        assert len(from_db) == len(urn_list)
        assert from_db[0].urn == urn_list[0]

        # single urn
        from_db_single = StagedResource.get_urn(db, urn_list[0])
        assert from_db_single.urn == urn_list[0]

    async def test_get_urn_async(
        self, async_session_temp: AsyncSession, create_staged_resource
    ) -> None:
        urn_list: List[str] = [str(create_staged_resource.urn)]

        from_db_single = await StagedResource.get_urn_async(
            async_session_temp, urn_list[0]
        )
        assert from_db_single.urn == urn_list[0]

        from_db = await StagedResource.get_urn_list_async(async_session_temp, urn_list)
        assert len(from_db) == len(urn_list)
        assert from_db[0].urn == urn_list[0]

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

    def test_fetch_staged_resources_by_type_query(
        self,
        db: Session,
        create_staged_resource,
        create_staged_database,
        create_staged_schema,
    ) -> None:
        """
        Tests that the fetch_staged_resources_by_type_query works as expected
        """
        query = fetch_staged_resources_by_type_query("Table")
        resources = db.execute(query).all()
        assert len(resources) == 1
        assert resources[0][0].resource_type == "Table"
        assert resources[0][0].urn == create_staged_resource.urn

        query = fetch_staged_resources_by_type_query("Schema")
        resources = db.execute(query).all()
        assert len(resources) == 1

        query = fetch_staged_resources_by_type_query("Database")
        resources = db.execute(query).all()
        assert len(resources) == 1
        assert resources[0][0].urn == create_staged_database.urn

        database = StagedResource.get_urn(db, create_staged_database.urn)
        database.diff_status = None
        database.save(db)
        query = fetch_staged_resources_by_type_query("Database")
        resources = db.execute(query).all()
        assert len(resources) == 1

    def test_fetch_staged_resources_by_type_query(
        self,
        db: Session,
        create_staged_resource,
        create_staged_schema,
    ):
        """
        Tests that the fetch_staged_resources_by_type_query works as expected
        """
        query = fetch_staged_resources_by_type_query("Table")
        resources = db.execute(query).all()
        assert len(resources) == 1
        assert resources[0][0].resource_type == "Table"
        assert resources[0][0].urn == create_staged_resource.urn

        query = fetch_staged_resources_by_type_query("Schema")
        resources = db.execute(query).all()
        assert len(resources) == 1
        assert resources[0][0].urn == create_staged_schema.urn

        query = fetch_staged_resources_by_type_query("Table", ["bq_monitor_1"])
        resources = db.execute(query).all()
        assert len(resources) == 1

        query = fetch_staged_resources_by_type_query("Table", ["bq_monitor_2"])
        resources = db.execute(query).all()
        assert len(resources) == 0


SAMPLE_START_DATE = datetime(2024, 5, 20, 0, 42, 5, 17137, tzinfo=timezone.utc)


class TestMonitorConfigModel:
    def test_create_monitor_config(
        self, db: Session, monitor_config, connection_config: ConnectionConfig
    ) -> None:
        """
        Creation fixture creates the config, this tests that it was created successfully
        and that we can access its attributes as expected.
        """
        mc: MonitorConfig = MonitorConfig.get(db=db, object_id=monitor_config.id)
        assert mc.name == "test monitor config 1"
        assert mc.key == "test_monitor_config_1"
        assert mc.classify_params == {
            "num_samples": 25,
            "num_threads": 2,
        }
        assert mc.monitor_execution_trigger is None  # not set in our fixture
        assert mc.enabled  # should be True by default
        assert mc.last_monitored is None  # not set in our fixture

        mc_connection_config = mc.connection_config
        assert mc_connection_config.id == connection_config.id
        assert mc_connection_config.key == connection_config.key
        assert mc_connection_config.connection_type == connection_config.connection_type

        assert mc.databases == ["db1", "db2"]
        assert mc.excluded_databases == []

    def test_update_monitor_config_fails_with_conflicting_dbs(
        self, db: Session, monitor_config, connection_config: ConnectionConfig
    ) -> None:
        """ """
        with pytest.raises(ValueError):
            monitor_config.update(
                db=db,
                data={
                    "name": "updated test monitor config 1",
                    "key": "test_monitor_config_1",
                    "connection_config_id": connection_config.id,
                    "databases": ["db1", "db2"],
                    "excluded_databases": ["db1"],
                },
            )

    def test_create_monitor_config_with_excluded_databases(
        self, db: Session, connection_config: ConnectionConfig
    ) -> None:
        mc = MonitorConfig.create(
            db=db,
            data={
                "name": "test monitor config 1",
                "key": "test_monitor_config_1",
                "connection_config_id": connection_config.id,
                "excluded_databases": ["db3"],
            },
        )
        assert mc.excluded_databases == ["db3"]
        db.delete(mc)

    @pytest.mark.parametrize(
        "monitor_frequency,expected_dict",
        [
            (
                MonitorFrequency.NOT_SCHEDULED,
                None,
            ),
            (
                MonitorFrequency.DAILY,
                {
                    "start_date": SAMPLE_START_DATE,
                    "timezone": str(timezone.utc),
                    "hour": 0,
                    "minute": 42,
                    "second": 5,
                },
            ),
            (
                MonitorFrequency.WEEKLY,
                {
                    "start_date": SAMPLE_START_DATE,
                    "timezone": str(timezone.utc),
                    "day_of_week": 0,  # sample start day is a Monday (day 0 in cron)
                    "hour": 0,
                    "minute": 42,
                    "second": 5,
                },
            ),
            (
                MonitorFrequency.MONTHLY,
                {
                    "start_date": SAMPLE_START_DATE,
                    "timezone": str(timezone.utc),
                    "day": 20,
                    "hour": 0,
                    "minute": 42,
                    "second": 5,
                },
            ),
        ],
    )
    def test_create_monitor_config_execution_trigger_logic(
        self,
        db: Session,
        connection_config: ConnectionConfig,
        monitor_frequency,
        expected_dict,
    ):
        """Tests that execution_trigger logic works as expected during within `create`"""
        mc = MonitorConfig.create(
            db=db,
            data={
                "name": "test monitor config 1",
                "key": "test_monitor_config_1",
                "connection_config_id": connection_config.id,
                "classify_params": {
                    "num_samples": 25,
                    "num_threads": 2,
                },
                "execution_start_date": SAMPLE_START_DATE,
                "execution_frequency": monitor_frequency,
            },
        )
        # this dict should have been derived from input fields in the data dict
        assert mc.monitor_execution_trigger == expected_dict
        # these fields on the object should be re-calculated based on the `monitor_execution_trigger` value
        assert mc.execution_frequency == monitor_frequency
        expected_date = (
            None
            if monitor_frequency == MonitorFrequency.NOT_SCHEDULED
            else SAMPLE_START_DATE
        )
        assert mc.execution_start_date == expected_date

        db.delete(mc)

    @pytest.mark.parametrize(
        "monitor_frequency,expected_dict",
        [
            (
                MonitorFrequency.NOT_SCHEDULED,
                None,
            ),
            (
                MonitorFrequency.DAILY,
                {
                    "start_date": SAMPLE_START_DATE,
                    "timezone": str(timezone.utc),
                    "hour": 0,
                    "minute": 42,
                    "second": 5,
                },
            ),
            (
                MonitorFrequency.WEEKLY,
                {
                    "start_date": SAMPLE_START_DATE,
                    "timezone": str(timezone.utc),
                    "day_of_week": 0,  # sample start day is a Tuesday (day 0 in cron)
                    "hour": 0,
                    "minute": 42,
                    "second": 5,
                },
            ),
            (
                MonitorFrequency.MONTHLY,
                {
                    "start_date": SAMPLE_START_DATE,
                    "timezone": str(timezone.utc),
                    "day": 20,
                    "hour": 0,
                    "minute": 42,
                    "second": 5,
                },
            ),
        ],
    )
    def test_update_monitor_config_execution_trigger_logic(
        self,
        db: Session,
        connection_config: ConnectionConfig,
        monitor_config: MonitorConfig,
        monitor_frequency,
        expected_dict,
    ):
        """Tests that execution_trigger logic works as expected during within `update`"""
        monitor_config.update(
            db=db,
            data={
                "name": "updated test monitor config 1",
                "key": "test_monitor_config_1",
                "connection_config_id": connection_config.id,
                "classify_params": {
                    "num_samples": 25,
                    "num_threads": 2,
                },
                "execution_start_date": SAMPLE_START_DATE,
                "execution_frequency": monitor_frequency,
            },
        )
        mc: MonitorConfig = MonitorConfig.get(db=db, object_id=monitor_config.id)

        # first ensure update works as expected on a "normal" field
        assert mc.name == "updated test monitor config 1"

        # then ensure update applies execution trigger logic as expected on the update

        # this dict should have been derived from input fields in the data dict
        assert mc.monitor_execution_trigger == expected_dict
        # these fields on the object should be re-calculated based on the `monitor_execution_trigger` value
        assert mc.execution_frequency == monitor_frequency
        expected_date = (
            None
            if monitor_frequency == MonitorFrequency.NOT_SCHEDULED
            else SAMPLE_START_DATE
        )
        assert mc.execution_start_date == expected_date
        db.delete(mc)
