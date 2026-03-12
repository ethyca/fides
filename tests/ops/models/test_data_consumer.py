import pytest
from sqlalchemy.orm import Session

from fides.api.models.data_consumer import DataConsumer, DataConsumerPurpose
from fides.api.models.data_purpose import DataPurpose


class TestDataConsumerModel:
    def test_create_group_consumer(self, db: Session):
        consumer = DataConsumer.create(
            db=db,
            data={
                "name": "Marketing Team",
                "description": "Marketing department Google Group",
                "type": "group",
                "external_id": "marketing@example.com",
                "contact_email": "marketing-lead@example.com",
                "tags": ["marketing", "internal"],
            },
        )
        assert consumer.name == "Marketing Team"
        assert consumer.type == "group"
        assert consumer.external_id == "marketing@example.com"
        assert consumer.tags == ["marketing", "internal"]

    def test_create_project_consumer(self, db: Session):
        consumer = DataConsumer.create(
            db=db,
            data={
                "name": "Analytics Pipeline",
                "type": "project",
                "external_id": "bigquery-project-123",
            },
        )
        assert consumer.type == "project"

    def test_system_type_rejected(self, db: Session):
        """CHECK constraint prevents type='system' rows."""
        with pytest.raises(Exception):
            DataConsumer.create(
                db=db,
                data={
                    "name": "Should Fail",
                    "type": "system",
                },
            )

    def test_custom_type_allowed(self, db: Session):
        consumer = DataConsumer.create(
            db=db,
            data={
                "name": "Custom Consumer",
                "type": "data_warehouse",
            },
        )
        assert consumer.type == "data_warehouse"


class TestDataConsumerPurposeModel:
    @pytest.fixture
    def purpose(self, db: Session) -> DataPurpose:
        return DataPurpose.create(
            db=db,
            data={
                "fides_key": "consumer_test_purpose",
                "name": "Test Purpose",
                "data_use": "analytics",
            },
        )

    @pytest.fixture
    def consumer(self, db: Session) -> DataConsumer:
        return DataConsumer.create(
            db=db,
            data={
                "name": "Test Group",
                "type": "group",
            },
        )

    def test_link_purpose_to_consumer(
        self, db: Session, consumer: DataConsumer, purpose: DataPurpose
    ):
        link = DataConsumerPurpose.create(
            db=db,
            data={
                "data_consumer_id": consumer.id,
                "data_purpose_id": purpose.id,
            },
        )
        assert link.data_consumer_id == consumer.id
        assert link.data_purpose_id == purpose.id

    def test_unique_constraint(
        self, db: Session, consumer: DataConsumer, purpose: DataPurpose
    ):
        DataConsumerPurpose.create(
            db=db,
            data={
                "data_consumer_id": consumer.id,
                "data_purpose_id": purpose.id,
            },
        )
        with pytest.raises(Exception):
            DataConsumerPurpose.create(
                db=db,
                data={
                    "data_consumer_id": consumer.id,
                    "data_purpose_id": purpose.id,
                },
            )

    def test_cascade_on_consumer_delete(
        self, db: Session, consumer: DataConsumer, purpose: DataPurpose
    ):
        link = DataConsumerPurpose.create(
            db=db,
            data={
                "data_consumer_id": consumer.id,
                "data_purpose_id": purpose.id,
            },
        )
        link_id = link.id
        consumer.delete(db)
        assert db.query(DataConsumerPurpose).filter_by(id=link_id).first() is None
