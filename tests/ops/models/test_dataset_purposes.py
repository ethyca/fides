import pytest
from sqlalchemy.orm import Session

from fides.api.models.data_producer import DataProducer
from fides.api.models.data_purpose import DataPurpose
from fides.api.models.sql_models import Dataset


class TestDatasetPurposes:
    def test_dataset_with_purposes(self, db: Session):
        dataset = Dataset.create(
            db=db,
            data={
                "fides_key": "test_dataset_purposes",
                "name": "Test Dataset",
                "data_categories": [],
                "collections": [],
                "data_purposes": ["marketing_email", "analytics_basic"],
            },
        )
        assert dataset.data_purposes == ["marketing_email", "analytics_basic"]

    def test_dataset_without_purposes(self, db: Session):
        dataset = Dataset.create(
            db=db,
            data={
                "fides_key": "test_dataset_no_purposes",
                "name": "Test Dataset No Purposes",
                "data_categories": [],
                "collections": [],
            },
        )
        assert dataset.data_purposes == [] or dataset.data_purposes is None

    def test_dataset_with_producer(self, db: Session):
        producer = DataProducer.create(
            db=db,
            data={"name": "Test Producer"},
        )
        dataset = Dataset.create(
            db=db,
            data={
                "fides_key": "test_dataset_producer",
                "name": "Test Dataset With Producer",
                "data_categories": [],
                "collections": [],
                "data_producer_id": producer.id,
            },
        )
        assert dataset.data_producer_id == producer.id

    def test_producer_set_null_on_delete(self, db: Session):
        producer = DataProducer.create(
            db=db,
            data={"name": "Delete Producer"},
        )
        dataset = Dataset.create(
            db=db,
            data={
                "fides_key": "test_dataset_producer_delete",
                "name": "Test Dataset",
                "data_categories": [],
                "collections": [],
                "data_producer_id": producer.id,
            },
        )
        dataset_id = dataset.id
        producer.delete(db)
        db.expire_all()
        refreshed = db.query(Dataset).filter_by(id=dataset_id).first()
        assert refreshed.data_producer_id is None
