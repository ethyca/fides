"""Tests for the IdentityDefinition model."""

from sqlalchemy.orm import Session

from fides.api.models.fides_user import FidesUser
from fides.api.models.identity_definition import (
    IdentityDefinition,
    IdentityDefinitionType,
)


class TestIdentityDefinition:
    """Tests for the IdentityDefinition model."""

    def test_create_identity_definition(self, db: Session, user: FidesUser):
        """Test creating an IdentityDefinition record with all fields."""
        identity_key = "customer_id"
        name = "Customer ID"
        description = "Unique identifier for customers in the system"
        identity_type = IdentityDefinitionType.UUID

        identity_definition = IdentityDefinition.create(
            db=db,
            data={
                "identity_key": identity_key,
                "name": name,
                "description": description,
                "type": identity_type,
                "created_by": user.id,
            },
        )
        db.commit()

        assert identity_definition.identity_key == identity_key
        assert identity_definition.name == name
        assert identity_definition.description == description
        assert identity_definition.type == identity_type
        assert identity_definition.created_by == user.id

        # Verify persistence by retrieving from database
        retrieved = (
            db.query(IdentityDefinition)
            .filter(IdentityDefinition.identity_key == identity_key)
            .first()
        )
        assert retrieved is not None
        assert retrieved.identity_key == identity_key
        assert retrieved.name == name
        assert retrieved.description == description
        assert retrieved.type == identity_type
        assert retrieved.created_by == user.id
