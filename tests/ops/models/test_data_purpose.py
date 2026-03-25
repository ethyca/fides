import pytest
from sqlalchemy.orm import Session

from fides.api.models.data_purpose import DataPurpose


class TestDataPurposeModel:
    def test_create_data_purpose(self, db: Session):
        purpose = DataPurpose.create(
            db=db,
            data={
                "fides_key": "marketing_email",
                "name": "Email Marketing",
                "description": "Processing for email marketing campaigns",
                "data_use": "marketing.advertising",
                "data_subject": "customer",
                "data_categories": ["user.contact.email"],
                "legal_basis_for_processing": "Consent",
                "flexible_legal_basis_for_processing": True,
                "retention_period": "90 days",
                "features": ["email_targeting"],
            },
        )
        assert purpose.fides_key == "marketing_email"
        assert purpose.data_use == "marketing.advertising"
        assert purpose.data_subject == "customer"
        assert purpose.data_categories == ["user.contact.email"]
        assert purpose.flexible_legal_basis_for_processing is True
        assert purpose.features == ["email_targeting"]
        assert purpose.id is not None
        assert purpose.created_at is not None

    def test_create_minimal_data_purpose(self, db: Session):
        """Only fides_key, name, and data_use are required."""
        purpose = DataPurpose.create(
            db=db,
            data={
                "fides_key": "analytics_basic",
                "name": "Basic Analytics",
                "data_use": "analytics",
            },
        )
        assert purpose.fides_key == "analytics_basic"
        assert purpose.data_subject is None
        assert purpose.data_categories == []
        assert purpose.legal_basis_for_processing is None

    def test_fides_key_uniqueness(self, db: Session):
        DataPurpose.create(
            db=db,
            data={
                "fides_key": "unique_purpose",
                "name": "Purpose A",
                "data_use": "analytics",
            },
        )
        with pytest.raises(Exception):
            DataPurpose.create(
                db=db,
                data={
                    "fides_key": "unique_purpose",
                    "name": "Purpose B",
                    "data_use": "marketing",
                },
            )

    def test_delete_data_purpose(self, db: Session):
        purpose = DataPurpose.create(
            db=db,
            data={
                "fides_key": "to_delete",
                "name": "Delete Me",
                "data_use": "analytics",
            },
        )
        purpose_id = purpose.id
        purpose.delete(db)
        assert db.query(DataPurpose).filter_by(id=purpose_id).first() is None
