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
    MonitorExecution,
    MonitorFrequency,
    SharedMonitorConfig,
    StagedResource,
    StagedResourceAncestor,
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
        self, async_session: AsyncSession, create_staged_resource
    ) -> None:
        urn_list: List[str] = [str(create_staged_resource.urn)]

        from_db_single = await StagedResource.get_urn_async(async_session, urn_list[0])
        assert from_db_single.urn == urn_list[0]

        from_db = await StagedResource.get_urn_list_async(async_session, urn_list)
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

    def test_fetch_staged_resources_by_type_query_with_monitor_config_ids(
        self,
        db: Session,
        create_staged_resource,
        create_staged_schema,
    ):
        """
        Tests that the fetch_staged_resources_by_type_query works as expected with monitor config IDs
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


class TestStagedResourceModelWebMonitorResults:
    """Tests for the StagedResource model related to web monitor result applications"""

    @pytest.fixture
    def create_web_monitor_staged_resource(self, db: Session, system):
        urn = "my_web_monitor_1.GET.td.doubleclick.net.https://td.doubleclick.net/td/ga/rul"
        resource = StagedResource.create(
            db=db,
            # the data below is representative of a web monitor result staged resource
            data={
                "urn": urn,
                "user_assigned_data_categories": ["user.contact.email"],
                "name": "rul",
                "resource_type": "Browser request",
                "monitor_config_id": "my_web_monitor_1",
                "diff_status": DiffStatus.ADDITION.value,
                "system_id": system.id,
                "vendor_id": "sample_compass_vendor_id",
                "meta": {
                    "domain": "td.doubleclick.net",
                    "method": "GET",
                    "parent": "https://www.googletagmanager.com/gtag/js?id=G-B356CF15GS",
                    "cookies": [
                        "test_cookie=CheckForPermission; expires=Fri, 13-Dec-2024 15:25:18 GMT; path=/; domain=.doubleclick.net; Secure; SameSite=none"
                    ],
                    "base_url": "https://td.doubleclick.net/td/ga/rul",
                    "data_uses": [],
                    "locations": ["USA"],
                    "mime_type": "text/html",
                    "parent_domain": "www.googletagmanager.com",
                },
            },
        )
        yield resource
        db.delete(resource)

    def test_create_staged_resource(
        self, db: Session, system, create_web_monitor_staged_resource
    ) -> None:
        """
        Creation fixture creates the resource, this tests that it was created successfully
        and that we can access its attributes as expected
        """
        saved_resource: StagedResource = StagedResource.get_urn(
            db, create_web_monitor_staged_resource.urn
        )
        assert saved_resource.system_id == system.id
        assert saved_resource.meta == {
            "domain": "td.doubleclick.net",
            "method": "GET",
            "parent": "https://www.googletagmanager.com/gtag/js?id=G-B356CF15GS",
            "cookies": [
                "test_cookie=CheckForPermission; expires=Fri, 13-Dec-2024 15:25:18 GMT; path=/; domain=.doubleclick.net; Secure; SameSite=none"
            ],
            "base_url": "https://td.doubleclick.net/td/ga/rul",
            "data_uses": [],
            "locations": ["USA"],
            "mime_type": "text/html",
            "parent_domain": "www.googletagmanager.com",
        }
        assert saved_resource.diff_status == DiffStatus.ADDITION.value
        assert saved_resource.vendor_id == "sample_compass_vendor_id"

    def test_update_staged_resource(
        self,
        db: Session,
        create_web_monitor_staged_resource,
        system,
        system_hidden,
    ) -> None:
        """
        Tests that we can update a staged resource, specifically its web-monitor related properties
        """
        saved_resource: StagedResource = StagedResource.get_urn(
            db, create_web_monitor_staged_resource.urn
        )

        # check system initially
        assert saved_resource.system_id == system.id

        saved_resource.system_id = system_hidden.id
        # needed to ensure array updates are persisted to the db
        flag_modified(saved_resource, "system_id")

        saved_resource.save(db)
        updated_resource = StagedResource.get_urn(db, saved_resource.urn)
        assert updated_resource.system_id == system_hidden.id


SAMPLE_START_DATE = datetime(2024, 5, 20, 0, 42, 5, 17137, tzinfo=timezone.utc)


class TestMonitorConfigModel:

    @pytest.fixture(scope="function")
    def shared_monitor_config(self, db: Session) -> SharedMonitorConfig:
        """Fixture for creating a test SharedMonitorConfig"""
        shared_config = SharedMonitorConfig.create(
            db=db,
            data={
                "name": "test shared config",
                "key": "test_shared_config",
                "description": "Test shared monitor configuration",
                "classify_params": {
                    "context_regex_pattern_mapping": [
                        [".*([e|E]mail|[e|E]mail_address).*", "user.contact.email"],
                        [".*[P|p]hone_number.*", "user.contact.phone_number"],
                    ]
                },
            },
        )
        return shared_config

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
            (
                MonitorFrequency.QUARTERLY,
                {
                    "start_date": SAMPLE_START_DATE,
                    "timezone": str(timezone.utc),
                    "day": 20,
                    "hour": 0,
                    "minute": 42,
                    "second": 5,
                    "month": "2,5,8,11",  # May is month 5, so it will run in May, Aug, Nov, Feb
                },
            ),
            (
                MonitorFrequency.YEARLY,
                {
                    "start_date": SAMPLE_START_DATE,
                    "timezone": str(timezone.utc),
                    "day": 20,
                    "month": 5,  # May
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
            (
                MonitorFrequency.QUARTERLY,
                {
                    "start_date": SAMPLE_START_DATE,
                    "timezone": str(timezone.utc),
                    "day": 20,
                    "hour": 0,
                    "minute": 42,
                    "second": 5,
                    "month": "2,5,8,11",  # May is month 5, so it will run in May, Aug, Nov, Feb
                },
            ),
            (
                MonitorFrequency.YEARLY,
                {
                    "start_date": SAMPLE_START_DATE,
                    "timezone": str(timezone.utc),
                    "day": 20,
                    "month": 5,  # May
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

    def test_monitor_config_with_shared_config(
        self,
        db: Session,
        connection_config: ConnectionConfig,
        shared_monitor_config: SharedMonitorConfig,
    ) -> None:
        """
        Test creating a MonitorConfig with a reference to a SharedMonitorConfig
        """
        mc = MonitorConfig.create(
            db=db,
            data={
                "name": "monitor with shared config",
                "key": "monitor_with_shared_config",
                "connection_config_id": connection_config.id,
                "classify_params": {
                    "context_regex_pattern_mapping": [],  # This will be overridden by shared config
                },
                "shared_config_id": shared_monitor_config.id,
            },
        )

        # Verify it was created with the shared config relationship
        mc_from_db = MonitorConfig.get(db=db, object_id=mc.id)
        assert mc_from_db.shared_config_id == shared_monitor_config.id
        assert mc_from_db.shared_config.name == "test shared config"

        # Verify the classify_params contains the pattern mapping from the shared config
        assert mc_from_db.classify_params["context_regex_pattern_mapping"] == [
            [".*([e|E]mail|[e|E]mail_address).*", "user.contact.email"],
            [".*[P|p]hone_number.*", "user.contact.phone_number"],
        ]

    def test_classify_params_merging(
        self,
        db: Session,
        connection_config: ConnectionConfig,
        shared_monitor_config: SharedMonitorConfig,
    ) -> None:
        """
        Test the classify_params property that merges parameters from both sources
        """
        mc = MonitorConfig.create(
            db=db,
            data={
                "name": "monitor for testing params merge",
                "key": "monitor_params_merge",
                "connection_config_id": connection_config.id,
                "classify_params": {
                    "num_samples": 25,  # Local parameter, not in shared config
                    "custom_param": "local value",  # Not in shared config
                    "context_regex_pattern_mapping": None,  # This should be overridden by shared config
                },
                "shared_config_id": shared_monitor_config.id,
            },
        )

        # Verify merged parameters
        mc_from_db = MonitorConfig.get(db=db, object_id=mc.id)
        merged_params = mc_from_db.classify_params

        # Params from shared config should be present
        assert "context_regex_pattern_mapping" in merged_params
        assert merged_params["context_regex_pattern_mapping"] == [
            [".*([e|E]mail|[e|E]mail_address).*", "user.contact.email"],
            [".*[P|p]hone_number.*", "user.contact.phone_number"],
        ]

        # Local params not in shared config should be preserved
        assert merged_params["custom_param"] == "local value"
        assert merged_params["num_samples"] == 25

    def test_shared_config_override_priority(
        self,
        db: Session,
        connection_config: ConnectionConfig,
        shared_monitor_config: SharedMonitorConfig,
    ) -> None:
        """
        Test that non-falsy shared config values override local config values
        """
        mc = MonitorConfig.create(
            db=db,
            data={
                "name": "monitor for testing priority",
                "key": "monitor_priority_test",
                "connection_config_id": connection_config.id,
                "classify_params": {
                    "context_regex_pattern_mapping": None,  # Should be overridden by shared config
                    "num_samples": 25,  # Should NOT be overridden (not in shared)
                },
                "shared_config_id": shared_monitor_config.id,
            },
        )

        # Update shared config with some falsy values that shouldn't override
        shared_monitor_config.update(
            db=db,
            data={
                "classify_params": {
                    "context_regex_pattern_mapping": [
                        [".*([e|E]mail|[e|E]mail_address).*", "user.contact.email"],
                        [".*[P|p]hone_number.*", "user.contact.phone_number"],
                    ],
                    "custom_field": None,  # This should not override local value since it's falsy
                },
            },
        )

        # Verify priority behavior in merged params
        mc_from_db = MonitorConfig.get(db=db, object_id=mc.id)
        merged_params = mc_from_db.classify_params

        # None local value should be overridden
        assert merged_params["context_regex_pattern_mapping"] == [
            [".*([e|E]mail|[e|E]mail_address).*", "user.contact.email"],
            [".*[P|p]hone_number.*", "user.contact.phone_number"],
        ]

        # Local value should not be overridden
        assert merged_params["num_samples"] == 25  # Local value

    def test_update_monitor_config_with_shared_config(
        self,
        db: Session,
        connection_config: ConnectionConfig,
        shared_monitor_config: SharedMonitorConfig,
    ) -> None:
        """
        Test updating a MonitorConfig to add or change shared config reference
        """
        # Create monitor without shared config
        mc = MonitorConfig.create(
            db=db,
            data={
                "name": "monitor to update",
                "key": "monitor_to_update",
                "connection_config_id": connection_config.id,
                "classify_params": {
                    "num_samples": 25,
                    "custom_param": "original value",
                },
            },
        )

        # Verify initial state
        assert mc.shared_config_id is None
        assert mc.classify_params == {
            "num_samples": 25,
            "custom_param": "original value",
        }

        # Update to add shared config reference
        mc.update(
            db=db,
            data={
                "shared_config_id": shared_monitor_config.id,
            },
        )

        # Verify updated state
        mc_from_db = MonitorConfig.get(db=db, object_id=mc.id)
        assert mc_from_db.shared_config_id == shared_monitor_config.id

        # Verify merged params
        merged_params = mc_from_db.classify_params
        assert merged_params["num_samples"] == 25  # Local value preserved
        assert (
            merged_params["custom_param"] == "original value"
        )  # Local value preserved
        assert merged_params["context_regex_pattern_mapping"] == [
            [".*([e|E]mail|[e|E]mail_address).*", "user.contact.email"],
            [".*[P|p]hone_number.*", "user.contact.phone_number"],
        ]


class TestMonitorExecutionModel:
    """Tests for the MonitorExecution model"""

    @pytest.fixture
    def monitor_config_key(self, db: Session, monitor_config) -> str:
        """Returns a monitor config key for testing"""
        return monitor_config.key

    def test_started_timestamp_is_set_on_creation(
        self, db: Session, monitor_config_key
    ) -> None:
        """Test that the started timestamp is set correctly when creating a new record"""
        # Create first record
        first_execution = MonitorExecution.create(
            db=db,
            data={
                "monitor_config_key": monitor_config_key,
                "status": "running",
            },
        )

        # Small delay to ensure timestamps would be different
        import time

        time.sleep(0.1)

        # Create second record
        second_execution = MonitorExecution.create(
            db=db,
            data={
                "monitor_config_key": monitor_config_key,
                "status": "running",
            },
        )

        # Verify timestamps are different (not a constant default)
        assert first_execution.started != second_execution.started

        # Verify timestamps are recent
        now = datetime.now(timezone.utc)
        assert (now - first_execution.started).total_seconds() < 5
        assert (now - second_execution.started).total_seconds() < 5

        # Verify second timestamp is later than first
        assert second_execution.started > first_execution.started


class TestStagedResourceAncestorModel:
    @pytest.fixture
    def staged_resource_1(self, db: Session) -> StagedResource:
        resource = StagedResource.create(
            db=db,
            data={
                "urn": "test_urn_1",
                "name": "Test Resource 1",
                "resource_type": "Table",  # not realistic, Table would not be ancestor of Table
            },
        )
        return resource

    @pytest.fixture
    def staged_resource_2(self, db: Session) -> StagedResource:
        resource = StagedResource.create(
            db=db,
            data={
                "urn": "test_urn_2",
                "name": "Test Resource 2",
                "resource_type": "Table",  # not realistic, Table would not be ancestor of Table
            },
        )
        return resource

    @pytest.fixture
    def staged_resource_3(self, db: Session) -> StagedResource:
        resource = StagedResource.create(
            db=db,
            data={
                "urn": "test_urn_3",
                "name": "Test Resource 3",
                "resource_type": "Table",  # not realistic # not realistic, Table would not be ancestor of Table
            },
        )
        return resource

    def test_create_staged_resource_ancestor_links(
        self,
        db: Session,
        staged_resource_1: StagedResource,
        staged_resource_2: StagedResource,
        staged_resource_3: StagedResource,
    ):
        """Test creating ancestor links for a staged resource."""
        descendant_urn = staged_resource_3.urn
        ancestor_urns = {staged_resource_1.urn, staged_resource_2.urn}

        StagedResourceAncestor.create_staged_resource_ancestor_links(
            db=db, resource_urn=descendant_urn, ancestor_urns=ancestor_urns
        )

        links = (
            db.query(StagedResourceAncestor)
            .filter_by(descendant_urn=descendant_urn)
            .all()
        )
        assert len(links) == 2
        created_ancestor_urns = {link.ancestor_urn for link in links}
        assert created_ancestor_urns == ancestor_urns

        # Verify relationships
        sr3 = StagedResource.get_urn(db, staged_resource_3.urn)
        assert len(sr3.ancestors()) == 2
        ancestor_resources_from_descendant = {
            ancestor.urn for ancestor in sr3.ancestors()
        }
        assert ancestor_resources_from_descendant == ancestor_urns

        sr1 = StagedResource.get_urn(db, staged_resource_1.urn)
        assert len(sr1.descendants()) == 1
        assert sr1.descendants()[0].urn == descendant_urn

    def test_create_staged_resource_ancestor_links_empty_ancestors(
        self, db: Session, staged_resource_1: StagedResource
    ):
        """Test creating links when the ancestor set is empty."""
        descendant_urn = staged_resource_1.urn
        ancestor_urns = set()

        StagedResourceAncestor.create_staged_resource_ancestor_links(
            db=db, resource_urn=descendant_urn, ancestor_urns=ancestor_urns
        )

        links = (
            db.query(StagedResourceAncestor)
            .filter_by(descendant_urn=descendant_urn)
            .all()
        )
        assert len(links) == 0

    def test_create_staged_resource_ancestor_links_idempotent(
        self,
        db: Session,
        staged_resource_1: StagedResource,
        staged_resource_2: StagedResource,
    ):
        """Test that creating the same links multiple times is idempotent."""
        descendant_urn = staged_resource_2.urn
        ancestor_urns = {staged_resource_1.urn}

        # Create links for the first time
        StagedResourceAncestor.create_staged_resource_ancestor_links(
            db=db, resource_urn=descendant_urn, ancestor_urns=ancestor_urns
        )
        links_first_call = (
            db.query(StagedResourceAncestor)
            .filter_by(descendant_urn=descendant_urn)
            .all()
        )
        assert len(links_first_call) == 1

        # Create links for the second time with the same data
        StagedResourceAncestor.create_staged_resource_ancestor_links(
            db=db, resource_urn=descendant_urn, ancestor_urns=ancestor_urns
        )
        links_second_call = (
            db.query(StagedResourceAncestor)
            .filter_by(descendant_urn=descendant_urn)
            .all()
        )
        assert (
            len(links_second_call) == 1
        )  # Should still be 1 due to ON CONFLICT DO NOTHING

        # Verify the link is correct
        assert links_second_call[0].ancestor_urn == staged_resource_1.urn
        assert links_second_call[0].descendant_urn == staged_resource_2.urn

    def test_cascade_delete_when_descendant_is_deleted(
        self,
        db: Session,
        staged_resource_1: StagedResource,  # Ancestor
        staged_resource_2: StagedResource,  # Descendant to be deleted
        staged_resource_3: StagedResource,  # Another descendant
    ):
        """Test ancestor links and ORM relationships after descendant resource deletion."""
        ancestor_urn = staged_resource_1.urn
        descendant_to_delete_urn = staged_resource_2.urn
        other_descendant_urn = staged_resource_3.urn

        # Link ancestor to both descendants
        StagedResourceAncestor.create_staged_resource_ancestor_links(
            db=db, resource_urn=descendant_to_delete_urn, ancestor_urns={ancestor_urn}
        )
        StagedResourceAncestor.create_staged_resource_ancestor_links(
            db=db, resource_urn=other_descendant_urn, ancestor_urns={ancestor_urn}
        )
        db.commit()  # Commit to ensure links are queryable for relationship loading

        # Refresh to ensure relationships are loaded from DB state
        db.refresh(staged_resource_1)
        db.refresh(staged_resource_2)
        db.refresh(staged_resource_3)

        # Verify initial links and relationships
        assert (
            db.query(StagedResourceAncestor)
            .filter_by(
                descendant_urn=descendant_to_delete_urn, ancestor_urn=ancestor_urn
            )
            .first()
            is not None
        )
        assert (
            db.query(StagedResourceAncestor)
            .filter_by(descendant_urn=other_descendant_urn, ancestor_urn=ancestor_urn)
            .first()
            is not None
        )
        assert {desc.urn for desc in staged_resource_1.descendants()} == {
            descendant_to_delete_urn,
            other_descendant_urn,
        }
        assert {anc.urn for anc in staged_resource_2.ancestors()} == {ancestor_urn}
        assert {anc.urn for anc in staged_resource_3.ancestors()} == {ancestor_urn}

        # Delete one descendant resource
        db.delete(staged_resource_2)
        db.commit()

        # Verify link to deleted descendant is gone
        assert (
            db.query(StagedResourceAncestor)
            .filter_by(
                descendant_urn=descendant_to_delete_urn, ancestor_urn=ancestor_urn
            )
            .first()
            is None
        )
        # Verify link to other descendant still exists
        assert (
            db.query(StagedResourceAncestor)
            .filter_by(descendant_urn=other_descendant_urn, ancestor_urn=ancestor_urn)
            .first()
            is not None
        )

        # Refresh remaining resources to update relationships
        db.refresh(staged_resource_1)
        db.refresh(staged_resource_3)

        # Verify relationships are updated
        assert {desc.urn for desc in staged_resource_1.descendants()} == {
            other_descendant_urn
        }
        assert {anc.urn for anc in staged_resource_3.ancestors()} == {ancestor_urn}

    def test_cascade_delete_when_ancestor_is_deleted(
        self,
        db: Session,
        staged_resource_1: StagedResource,  # Ancestor to be deleted
        staged_resource_2: StagedResource,  # Another ancestor
        staged_resource_3: StagedResource,  # Descendant
    ):
        """Test ancestor links and ORM relationships after ancestor resource deletion."""
        ancestor_to_delete_urn = staged_resource_1.urn
        other_ancestor_urn = staged_resource_2.urn
        descendant_urn = staged_resource_3.urn

        # Link both ancestors to the descendant
        StagedResourceAncestor.create_staged_resource_ancestor_links(
            db=db,
            resource_urn=descendant_urn,
            ancestor_urns={ancestor_to_delete_urn, other_ancestor_urn},
        )
        db.commit()  # Commit to ensure links are queryable for relationship loading

        # Refresh to ensure relationships are loaded from DB state
        db.refresh(staged_resource_1)
        db.refresh(staged_resource_2)
        db.refresh(staged_resource_3)

        # Verify initial links and relationships
        assert (
            db.query(StagedResourceAncestor)
            .filter_by(
                descendant_urn=descendant_urn, ancestor_urn=ancestor_to_delete_urn
            )
            .first()
            is not None
        )
        assert (
            db.query(StagedResourceAncestor)
            .filter_by(descendant_urn=descendant_urn, ancestor_urn=other_ancestor_urn)
            .first()
            is not None
        )
        assert {anc.urn for anc in staged_resource_3.ancestors()} == {
            ancestor_to_delete_urn,
            other_ancestor_urn,
        }
        assert {desc.urn for desc in staged_resource_1.descendants()} == {
            descendant_urn
        }
        assert {desc.urn for desc in staged_resource_2.descendants()} == {
            descendant_urn
        }

        # Delete one ancestor resource
        db.delete(staged_resource_1)
        db.commit()

        # Verify link from deleted ancestor is gone
        assert (
            db.query(StagedResourceAncestor)
            .filter_by(
                descendant_urn=descendant_urn, ancestor_urn=ancestor_to_delete_urn
            )
            .first()
            is None
        )
        # Verify link from other ancestor still exists
        assert (
            db.query(StagedResourceAncestor)
            .filter_by(descendant_urn=descendant_urn, ancestor_urn=other_ancestor_urn)
            .first()
            is not None
        )

        # Refresh remaining resources to update relationships
        db.refresh(staged_resource_2)
        db.refresh(staged_resource_3)

        # Verify relationships are updated
        assert {anc.urn for anc in staged_resource_3.ancestors()} == {
            other_ancestor_urn
        }
        assert {desc.urn for desc in staged_resource_2.descendants()} == {
            descendant_urn
        }
