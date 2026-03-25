import pytest
from sqlalchemy.orm import Session

from fides.api.models.data_purpose import DataPurpose
from fides.api.models.sql_models import System
from fides.api.models.system_purpose import SystemPurpose


class TestSystemPurposeModel:
    @pytest.fixture
    def purpose(self, db: Session) -> DataPurpose:
        return DataPurpose.create(
            db=db,
            data={
                "fides_key": "test_purpose",
                "name": "Test Purpose",
                "data_use": "analytics",
            },
        )

    def test_create_system_purpose(
        self, db: Session, system: System, purpose: DataPurpose
    ):
        sp = SystemPurpose.create(
            db=db,
            data={
                "system_id": system.id,
                "data_purpose_id": purpose.id,
            },
        )
        assert sp.system_id == system.id
        assert sp.data_purpose_id == purpose.id
        assert sp.assigned_by is None
        assert sp.created_at is not None

    def test_unique_constraint(self, db: Session, system: System, purpose: DataPurpose):
        SystemPurpose.create(
            db=db,
            data={
                "system_id": system.id,
                "data_purpose_id": purpose.id,
            },
        )
        with pytest.raises(Exception):
            SystemPurpose.create(
                db=db,
                data={
                    "system_id": system.id,
                    "data_purpose_id": purpose.id,
                },
            )

    def test_cascade_on_system_delete(
        self, db: Session, system: System, purpose: DataPurpose
    ):
        sp = SystemPurpose.create(
            db=db,
            data={
                "system_id": system.id,
                "data_purpose_id": purpose.id,
            },
        )
        sp_id = sp.id
        system.delete(db)
        assert db.query(SystemPurpose).filter_by(id=sp_id).first() is None
