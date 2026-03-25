import pytest
from sqlalchemy.orm import Session

from fides.api.models.data_producer import DataProducer, DataProducerMember


class TestDataProducerModel:
    def test_create_data_producer(self, db: Session):
        producer = DataProducer.create(
            db=db,
            data={
                "name": "Analytics Engineering Team",
                "description": "Responsible for analytics pipelines",
                "external_id": "analytics-eng-okta-group",
                "contact_email": "analytics-eng@example.com",
                "contact_slack_channel": "#analytics-eng",
            },
        )
        assert producer.name == "Analytics Engineering Team"
        assert producer.external_id == "analytics-eng-okta-group"
        assert producer.contact_email == "analytics-eng@example.com"

    def test_create_minimal_producer(self, db: Session):
        producer = DataProducer.create(
            db=db,
            data={"name": "Minimal Producer"},
        )
        assert producer.name == "Minimal Producer"
        assert producer.monitor_id is None

    def test_delete_producer(self, db: Session):
        producer = DataProducer.create(
            db=db,
            data={"name": "Delete Me"},
        )
        producer_id = producer.id
        producer.delete(db)
        assert db.query(DataProducer).filter_by(id=producer_id).first() is None


class TestDataProducerMemberModel:
    @pytest.fixture
    def producer(self, db: Session) -> DataProducer:
        return DataProducer.create(
            db=db,
            data={"name": "Test Producer"},
        )

    def test_add_member(self, db: Session, producer: DataProducer, user):
        member = DataProducerMember.create(
            db=db,
            data={
                "data_producer_id": producer.id,
                "user_id": user.id,
            },
        )
        assert member.data_producer_id == producer.id
        assert member.user_id == user.id

    def test_unique_constraint(self, db: Session, producer: DataProducer, user):
        DataProducerMember.create(
            db=db,
            data={
                "data_producer_id": producer.id,
                "user_id": user.id,
            },
        )
        with pytest.raises(Exception):
            DataProducerMember.create(
                db=db,
                data={
                    "data_producer_id": producer.id,
                    "user_id": user.id,
                },
            )

    def test_cascade_on_producer_delete(
        self, db: Session, producer: DataProducer, user
    ):
        member = DataProducerMember.create(
            db=db,
            data={
                "data_producer_id": producer.id,
                "user_id": user.id,
            },
        )
        member_id = member.id
        producer.delete(db)
        assert db.query(DataProducerMember).filter_by(id=member_id).first() is None
