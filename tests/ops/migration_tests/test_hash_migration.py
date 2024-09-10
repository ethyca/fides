import pytest
from sqlalchemy.orm import Session

from fides.api.migrations.hash_migration_job import (
    MODELS_TO_MIGRATE,
    is_migrated,
    migrate_table,
)
from fides.api.migrations.hash_migration_tracker import HashMigrationTracker
from fides.api.models.privacy_preference import (
    ConsentIdentitiesMixin,
    CurrentPrivacyPreference,
    PrivacyPreferenceHistory,
    ServedNoticeHistory,
    ServingComponent,
)
from fides.api.models.privacy_request import CustomPrivacyRequestField, ProvidedIdentity


@pytest.fixture
def unmigrated_current_privacy_preference(db: Session, privacy_notice):
    email = "test@email.com"
    phone_number = "+15555555555"
    fides_user_device_id = "165ad0ed-10fb-4a60-9810-e0749346ec16"
    external_id = "ext-123"

    current_privacy_preference = CurrentPrivacyPreference.create(
        db=db,
        data={
            "preferences": {
                "preferences": [
                    {
                        "privacy_notice_history_id": privacy_notice.translations[0]
                        .histories[0]
                        .id,
                        "preference": "opt_out",
                    }
                ],
            },
            "email": email,
            "hashed_email": CurrentPrivacyPreference.bcrypt_hash_value(email),
            "phone_number": phone_number,
            "hashed_phone_number": CurrentPrivacyPreference.bcrypt_hash_value(
                phone_number
            ),
            "fides_user_device": fides_user_device_id,
            "hashed_fides_user_device": CurrentPrivacyPreference.bcrypt_hash_value(
                fides_user_device_id
            ),
            "external_id": external_id,
            "hashed_external_id": CurrentPrivacyPreference.bcrypt_hash_value(
                external_id
            ),
            "is_hash_migrated": False,
        },
    )
    yield current_privacy_preference
    current_privacy_preference.delete(db)


@pytest.fixture
def unmigrated_provided_identity(db: Session):
    email = "test@email.com"
    provided_identity = ProvidedIdentity.create(
        db,
        data={
            "privacy_request_id": None,
            "field_name": "email",
            "hashed_value": ProvidedIdentity.bcrypt_hash_value(email),
            "encrypted_value": {"value": email},
            "is_hash_migrated": False,
        },
    )
    yield provided_identity
    provided_identity.delete(db)


@pytest.fixture
def unmigrated_custom_privacy_request_field(db: Session):
    loyalty_id = "CH-1"
    custom_privacy_request_field = CustomPrivacyRequestField.create(
        db=db,
        data={
            "field_name": "loyalty_id",
            "field_label": "Loyalty ID",
            "encrypted_value": {"value": loyalty_id},
            "hashed_value": CustomPrivacyRequestField.bcrypt_hash_value(loyalty_id),
            "is_hash_migrated": False,
        },
    )
    yield custom_privacy_request_field
    custom_privacy_request_field.delete(db)


@pytest.fixture
def unmigrated_privacy_preference_history(db: Session, privacy_notice):
    email = "test@email.com"
    phone_number = "+15555555555"
    fides_user_device_id = "165ad0ed-10fb-4a60-9810-e0749346ec16"
    external_id = "ext-123"

    privacy_preference_history = PrivacyPreferenceHistory.create(
        db=db,
        data={
            "preference": "opt_in",
            "privacy_notice_history_id": privacy_notice.translations[0].histories[0].id,
            "notice_key": "example_privacy_notice_1",
            "email": email,
            "hashed_email": PrivacyPreferenceHistory.bcrypt_hash_value(email),
            "phone_number": phone_number,
            "hashed_phone_number": PrivacyPreferenceHistory.bcrypt_hash_value(
                phone_number
            ),
            "fides_user_device": fides_user_device_id,
            "hashed_fides_user_device": PrivacyPreferenceHistory.bcrypt_hash_value(
                fides_user_device_id
            ),
            "external_id": external_id,
            "hashed_external_id": PrivacyPreferenceHistory.bcrypt_hash_value(
                external_id
            ),
            "is_hash_migrated": False,
        },
        check_name=False,
    )
    yield privacy_preference_history
    privacy_preference_history.delete(db)


@pytest.fixture
def unmigrated_served_notice_history(db: Session, privacy_notice):
    email = "test@email.com"
    phone_number = "+15555555555"
    fides_user_device_id = "165ad0ed-10fb-4a60-9810-e0749346ec16"
    external_id = "ext-123"

    served_notice_history = ServedNoticeHistory.create(
        db=db,
        data={
            "acknowledge_mode": False,
            "serving_component": ServingComponent.overlay,
            "privacy_notice_history_id": privacy_notice.translations[0].histories[0].id,
            "email": email,
            "hashed_email": ServedNoticeHistory.bcrypt_hash_value(email),
            "phone_number": phone_number,
            "hashed_phone_number": ServedNoticeHistory.bcrypt_hash_value(phone_number),
            "fides_user_device": fides_user_device_id,
            "hashed_fides_user_device": ServedNoticeHistory.bcrypt_hash_value(
                fides_user_device_id
            ),
            "external_id": external_id,
            "hashed_external_id": ServedNoticeHistory.bcrypt_hash_value(external_id),
            "served_notice_history_id": "ser_12345",
            "is_hash_migrated": False,
        },
        check_name=False,
    )
    yield served_notice_history
    served_notice_history.delete(db)


class TestHashMigrationUtils:
    """General tests for various hash migration utils."""

    @pytest.mark.usefixtures(
        "unmigrated_current_privacy_preference",
        "unmigrated_provided_identity",
        "unmigrated_custom_privacy_request_field",
        "unmigrated_privacy_preference_history",
        "unmigrated_served_notice_history",
    )
    @pytest.mark.parametrize("model", MODELS_TO_MIGRATE)
    def test_is_migrated(self, db: Session, model):
        """
        Tests that each model can query its corresponding table for unmigrated rows.
        """
        assert is_migrated(db, model) is False

    @pytest.mark.usefixtures(
        "unmigrated_current_privacy_preference",
        "unmigrated_provided_identity",
        "unmigrated_custom_privacy_request_field",
        "unmigrated_privacy_preference_history",
        "unmigrated_served_notice_history",
    )
    @pytest.mark.parametrize("model", MODELS_TO_MIGRATE)
    def test_migrate_table(self, db: Session, model):
        """
        Tests that each model can be migrated to use the new SHA-256 hash.
        Migrate teach table/model and verify both the DB check and
        migration tracker both report the migration as complete afterwards.
        """

        migrate_table(db, model)
        assert is_migrated(db, model) is True
        assert HashMigrationTracker.is_migrated(model.__name__) is True

    @pytest.mark.parametrize("model", MODELS_TO_MIGRATE)
    def test_hash_value_for_search(self, model):
        """
        Tests that we only generate the SHA-256 hash for searches after migrating the table,
        instead of returning both the bcrypt and SHA-256 hashes.
        """
        email = "user@example.com"
        HashMigrationTracker.clear()
        assert model.hash_value_for_search(email) == {
            model.bcrypt_hash_value(email),
            model.hash_value(email),
        }
        HashMigrationTracker.set_migrated(model.__name__)
        assert model.hash_value_for_search(email) == {model.hash_value(email)}


class TestHashMigration:
    """More targeted tests for the actual migration for each model."""

    def test_current_privacy_preference(
        self,
        unmigrated_current_privacy_preference: CurrentPrivacyPreference,
    ):
        model = unmigrated_current_privacy_preference
        model.migrate_hashed_fields()
        assert model.hashed_email == CurrentPrivacyPreference.hash_value(model.email)
        assert model.hashed_phone_number == CurrentPrivacyPreference.hash_value(
            model.phone_number
        )
        assert model.hashed_fides_user_device == CurrentPrivacyPreference.hash_value(
            model.fides_user_device
        )
        assert model.hashed_external_id == CurrentPrivacyPreference.hash_value(
            model.external_id
        )
        assert model.is_hash_migrated is True

    def test_provided_identity(self, unmigrated_provided_identity: ProvidedIdentity):
        model = unmigrated_provided_identity
        model.migrate_hashed_fields()
        assert model.hashed_value == ProvidedIdentity.hash_value(
            model.encrypted_value.get("value")
        )
        assert model.is_hash_migrated is True

    def test_custom_privacy_request_field(
        self, unmigrated_custom_privacy_request_field: CustomPrivacyRequestField
    ):
        model = unmigrated_custom_privacy_request_field
        model.migrate_hashed_fields()
        assert model.hashed_value == ProvidedIdentity.hash_value(
            model.encrypted_value.get("value")
        )
        assert model.is_hash_migrated is True

    def test_privacy_preference_history(
        self, unmigrated_privacy_preference_history: PrivacyPreferenceHistory
    ):
        model = unmigrated_privacy_preference_history
        model.migrate_hashed_fields()
        assert model.hashed_email == PrivacyPreferenceHistory.hash_value(model.email)
        assert model.hashed_phone_number == PrivacyPreferenceHistory.hash_value(
            model.phone_number
        )
        assert model.hashed_fides_user_device == PrivacyPreferenceHistory.hash_value(
            model.fides_user_device
        )
        assert model.hashed_external_id == PrivacyPreferenceHistory.hash_value(
            model.external_id
        )
        assert model.is_hash_migrated is True

    def test_served_notice_history(
        self, unmigrated_served_notice_history: ServedNoticeHistory
    ):
        model = unmigrated_served_notice_history
        model.migrate_hashed_fields()
        assert model.hashed_email == ServedNoticeHistory.hash_value(model.email)
        assert model.hashed_phone_number == ServedNoticeHistory.hash_value(
            model.phone_number
        )
        assert model.hashed_fides_user_device == ServedNoticeHistory.hash_value(
            model.fides_user_device
        )
        assert model.hashed_external_id == ServedNoticeHistory.hash_value(
            model.external_id
        )
        assert model.is_hash_migrated is True
