import pytest

from fides.api.db.system import get_system
from fides.api.models.sql_models import Organization, PrivacyDeclaration


def test_system_privacy_declarations_in_alphabetical_order(db, system):
    """
    Ensure that the system privacy declarations are in alphabetical order by name
    """
    # Add more privacy declarations to the system
    new_privacy_declarations = [
        {
            "data_use": "marketing.advertising.profiling",
            "name": "Declaration Name",
            "system_id": system.id,
        },
        {
            "data_use": "essential",
            "name": "Another Declaration Name",
            "system_id": system.id,
        },
    ]
    for data in new_privacy_declarations:
        PrivacyDeclaration.create(db=db, data=data)
        db.commit()

    db.refresh(system)
    updated_system = get_system(db, system.fides_key)

    privacy_declarations = updated_system.privacy_declarations
    sorted_privacy_declarations = sorted(privacy_declarations, key=lambda x: x.name)

    assert privacy_declarations == sorted_privacy_declarations, (
        "Privacy declarations are not in alphabetical order by name"
    )


class TestOrganizationEncryptedFields:
    """Verify that Organization encrypted columns round-trip correctly
    through StringEncryptedType(AesGcmEngine)."""

    @pytest.fixture()
    def contact_details(self):
        return {
            "name": "Jane Controller",
            "address": "123 Privacy Lane",
            "email": "user@example.com",
            "phone": "+1-555-0100",
        }

    def test_encrypted_fields_round_trip(self, db, contact_details):
        org = Organization.create(
            db=db,
            data={
                "fides_key": "test_encryption_org",
                "name": "Test Encryption Org",
                "controller": contact_details,
                "data_protection_officer": contact_details,
                "representative": contact_details,
            },
        )
        db.expire(org)
        reloaded = (
            db.query(Organization).filter_by(fides_key="test_encryption_org").first()
        )

        assert reloaded.controller == contact_details
        assert reloaded.data_protection_officer == contact_details
        assert reloaded.representative == contact_details

        reloaded.delete(db)

    def test_null_encrypted_fields(self, db):
        org = Organization.create(
            db=db,
            data={
                "fides_key": "test_null_encryption_org",
                "name": "Test Null Encryption Org",
                "controller": None,
                "data_protection_officer": None,
                "representative": None,
            },
        )
        db.expire(org)
        reloaded = (
            db.query(Organization)
            .filter_by(fides_key="test_null_encryption_org")
            .first()
        )

        assert reloaded.controller is None
        assert reloaded.data_protection_officer is None
        assert reloaded.representative is None

        reloaded.delete(db)
