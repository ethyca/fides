from typing import Any, Dict, Generator
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import text

from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.privacy_preference import (
    ConsentIdentitiesMixin,
    CurrentPrivacyPreference,
)
from fides.api.models.sql_models import Dataset as CtlDataset
from fides.api.schemas.policy import ActionType
from fides.api.task.consent_identity_enrichment import enrich_identities_for_consent
from fides.config import CONFIG

pytestmark = pytest.mark.integration


@pytest.fixture()
def enable_identity_enrichment():
    CONFIG.consent.identity_enrichment = True
    yield CONFIG
    CONFIG.consent.identity_enrichment = False


IDENTITY_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS identity_lookup (
    id SERIAL PRIMARY KEY,
    email VARCHAR(100),
    external_id VARCHAR(100),
    phone VARCHAR(50)
);
"""

IDENTITY_TABLE_SEED = [
    {
        "id": 90001,
        "email": "enrichment-user@example.com",
        "external_id": "ext_enrich_001",
        "phone": "555-0199",
    },
    {
        "id": 90002,
        "email": "second-user@example.com",
        "external_id": "ext_enrich_002",
        "phone": "555-0200",
    },
]

IDENTITY_DATASET_DICT = {
    "fides_key": "consent_identity_db",
    "name": "consent_identity_db",
    "description": "Test dataset for consent identity enrichment",
    "collections": [
        {
            "name": "identity_lookup",
            "fields": [
                {
                    "name": "id",
                    "data_categories": ["system.operations"],
                    "fides_meta": {"primary_key": True, "data_type": "integer"},
                },
                {
                    "name": "email",
                    "data_categories": ["user.contact.email"],
                    "fides_meta": {"identity": "email", "data_type": "string"},
                },
                {
                    "name": "external_id",
                    "data_categories": ["user.unique_id"],
                    "fides_meta": {
                        "identity": "external_id",
                        "data_type": "string",
                    },
                },
                {
                    "name": "phone",
                    "data_categories": ["user.contact.phone_number"],
                    "fides_meta": {
                        "identity": "phone_number",
                        "data_type": "string",
                    },
                },
            ],
        }
    ],
}


@pytest.fixture(scope="function")
def identity_lookup_table(postgres_integration_db):
    """Create and seed the identity_lookup table in the test Postgres DB."""
    engine = postgres_integration_db.bind
    with engine.connect() as conn:
        conn.execute(text(IDENTITY_TABLE_SQL))
        for row in IDENTITY_TABLE_SEED:
            cols = ", ".join(row.keys())
            placeholders = ", ".join(f":{k}" for k in row.keys())
            conn.execute(
                text(f"INSERT INTO identity_lookup ({cols}) VALUES ({placeholders})"),
                row,
            )
    yield engine
    with engine.connect() as conn:
        conn.execute(
            text(
                f"DELETE FROM identity_lookup WHERE id IN ({', '.join(str(r['id']) for r in IDENTITY_TABLE_SEED)})"
            )
        )


@pytest.fixture(scope="function")
def consent_enrichment_connection_config(
    db, identity_lookup_table
) -> Generator[ConnectionConfig, None, None]:
    """Postgres ConnectionConfig with consent in enabled_actions."""
    from tests.fixtures.application_fixtures import integration_secrets

    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": "consent_identity_db",
            "name": "consent_identity_postgres",
            "connection_type": ConnectionType.postgres,
            "access": AccessLevel.read,
            "secrets": integration_secrets["postgres_example"],
            "disabled": False,
            "enabled_actions": [ActionType.consent],
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def consent_enrichment_dataset_config(
    db, consent_enrichment_connection_config
) -> Generator[DatasetConfig, None, None]:
    """DatasetConfig for the identity_lookup table with identity fields."""
    ctl_dataset = CtlDataset.create_from_dataset_dict(db, IDENTITY_DATASET_DICT)
    dataset_config = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": consent_enrichment_connection_config.id,
            "fides_key": "consent_identity_db",
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset_config
    dataset_config.delete(db)
    ctl_dataset.delete(db)


@pytest.mark.usefixtures("enable_identity_enrichment")
class TestConsentIdentityEnrichmentIntegration:
    @pytest.fixture(autouse=True)
    def mock_cache_store(self):
        with patch(
            "fides.api.task.consent_identity_enrichment.get_dsr_cache_store"
        ) as mock_store:
            mock_store.return_value = MagicMock()
            yield mock_store

    def test_enriches_email_from_external_id(
        self,
        db,
        consent_enrichment_connection_config,
        consent_enrichment_dataset_config,
    ):
        """Given only external_id, enrichment resolves email from the DB."""
        privacy_request = MagicMock()
        result = enrich_identities_for_consent(
            datasets=[consent_enrichment_dataset_config],
            connection_configs=[consent_enrichment_connection_config],
            identity_data={"external_id": "ext_enrich_001"},
            privacy_request=privacy_request,
            session=db,
        )
        assert result["external_id"] == "ext_enrich_001"
        assert result["email"] == "enrichment-user@example.com"
        assert result["phone_number"] == "555-0199"

    def test_enriches_external_id_from_email(
        self,
        db,
        consent_enrichment_connection_config,
        consent_enrichment_dataset_config,
    ):
        """Given only email, enrichment resolves external_id and phone from the DB."""
        privacy_request = MagicMock()
        result = enrich_identities_for_consent(
            datasets=[consent_enrichment_dataset_config],
            connection_configs=[consent_enrichment_connection_config],
            identity_data={"email": "second-user@example.com"},
            privacy_request=privacy_request,
            session=db,
        )
        assert result["email"] == "second-user@example.com"
        assert result["external_id"] == "ext_enrich_002"
        assert result["phone_number"] == "555-0200"

    def test_no_enrichment_when_all_identities_present(
        self,
        db,
        consent_enrichment_connection_config,
        consent_enrichment_dataset_config,
    ):
        """No DB query when all identity types are already present."""
        privacy_request = MagicMock()
        identity = {
            "email": "enrichment-user@example.com",
            "external_id": "ext_enrich_001",
            "phone_number": "555-0199",
        }
        result = enrich_identities_for_consent(
            datasets=[consent_enrichment_dataset_config],
            connection_configs=[consent_enrichment_connection_config],
            identity_data=identity,
            privacy_request=privacy_request,
            session=db,
        )
        assert result == identity

    def test_user_not_found_returns_original(
        self,
        db,
        consent_enrichment_connection_config,
        consent_enrichment_dataset_config,
    ):
        """User not in DB returns original identity data unchanged."""
        privacy_request = MagicMock()
        identity = {"external_id": "nonexistent_id"}
        result = enrich_identities_for_consent(
            datasets=[consent_enrichment_dataset_config],
            connection_configs=[consent_enrichment_connection_config],
            identity_data=identity,
            privacy_request=privacy_request,
            session=db,
        )
        assert result == identity

    def test_does_not_overwrite_existing_identity(
        self,
        db,
        consent_enrichment_connection_config,
        consent_enrichment_dataset_config,
    ):
        """Existing identities in the input are preserved even if DB has different values."""
        privacy_request = MagicMock()
        result = enrich_identities_for_consent(
            datasets=[consent_enrichment_dataset_config],
            connection_configs=[consent_enrichment_connection_config],
            identity_data={
                "email": "my-original@example.com",
                "external_id": "ext_enrich_001",
            },
            privacy_request=privacy_request,
            session=db,
        )
        assert result["email"] == "my-original@example.com"
        assert result["external_id"] == "ext_enrich_001"
        assert result["phone_number"] == "555-0199"

    def test_skipped_without_consent_enabled_actions(
        self, db, consent_enrichment_dataset_config
    ):
        """Postgres without consent in enabled_actions is excluded from enrichment."""
        from tests.fixtures.application_fixtures import integration_secrets

        non_consent_config = ConnectionConfig.create(
            db=db,
            data={
                "key": "non_consent_pg",
                "name": "non_consent_postgres",
                "connection_type": ConnectionType.postgres,
                "access": AccessLevel.read,
                "secrets": integration_secrets["postgres_example"],
                "disabled": False,
                "enabled_actions": [ActionType.access],
            },
        )
        try:
            privacy_request = MagicMock()
            identity = {"external_id": "ext_enrich_001"}
            result = enrich_identities_for_consent(
                datasets=[consent_enrichment_dataset_config],
                connection_configs=[non_consent_config],
                identity_data=identity,
                privacy_request=privacy_request,
                session=db,
            )
            assert result == identity
        finally:
            non_consent_config.delete(db)


@pytest.mark.usefixtures("enable_identity_enrichment")
class TestPreferenceBasedEnrichment:
    """Test the fast path: resolving missing identities from
    CurrentPrivacyPreference records before falling back to DB connectors."""

    @pytest.fixture(autouse=True)
    def mock_cache_store(self):
        with patch(
            "fides.api.task.consent_identity_enrichment.get_dsr_cache_store"
        ) as mock_store:
            mock_store.return_value = MagicMock()
            yield mock_store

    @pytest.fixture()
    def preference_with_both_identities(self, db):
        pref = CurrentPrivacyPreference.create(
            db=db,
            data={
                "email": "pref-user@example.com",
                "hashed_email": ConsentIdentitiesMixin.hash_value(
                    "pref-user@example.com"
                ),
                "external_id": "ext_pref_001",
                "hashed_external_id": ConsentIdentitiesMixin.hash_value("ext_pref_001"),
                "preferences": {},
            },
        )
        yield pref
        pref.delete(db)

    def test_resolves_external_id_from_email(self, db, preference_with_both_identities):
        privacy_request = MagicMock()
        result = enrich_identities_for_consent(
            datasets=[],
            connection_configs=[],
            identity_data={"email": "pref-user@example.com"},
            privacy_request=privacy_request,
            session=db,
        )
        assert result["email"] == "pref-user@example.com"
        assert result["external_id"] == "ext_pref_001"

    def test_resolves_email_from_external_id(self, db, preference_with_both_identities):
        privacy_request = MagicMock()
        result = enrich_identities_for_consent(
            datasets=[],
            connection_configs=[],
            identity_data={"external_id": "ext_pref_001"},
            privacy_request=privacy_request,
            session=db,
        )
        assert result["external_id"] == "ext_pref_001"
        assert result["email"] == "pref-user@example.com"

    def test_skips_when_both_present(self, db, preference_with_both_identities):
        privacy_request = MagicMock()
        identity = {
            "email": "pref-user@example.com",
            "external_id": "ext_pref_001",
        }
        result = enrich_identities_for_consent(
            datasets=[],
            connection_configs=[],
            identity_data=identity,
            privacy_request=privacy_request,
            session=db,
        )
        assert result == identity
        privacy_request.add_success_execution_log.assert_not_called()

    def test_no_match_returns_original(self, db):
        privacy_request = MagicMock()
        identity = {"email": "nonexistent@example.com"}
        result = enrich_identities_for_consent(
            datasets=[],
            connection_configs=[],
            identity_data=identity,
            privacy_request=privacy_request,
            session=db,
        )
        assert result == identity

    def test_skips_when_flag_disabled(self, db, enable_identity_enrichment):
        enable_identity_enrichment.consent.identity_enrichment = False
        privacy_request = MagicMock()
        identity = {"email": "pref-user@example.com"}
        result = enrich_identities_for_consent(
            datasets=[],
            connection_configs=[],
            identity_data=identity,
            privacy_request=privacy_request,
            session=db,
        )
        assert result == identity
        privacy_request.add_success_execution_log.assert_not_called()

    def test_preference_preferred_over_db_connector(
        self,
        db,
        preference_with_both_identities,
        consent_enrichment_connection_config,
        consent_enrichment_dataset_config,
        identity_lookup_table,
    ):
        """Preference lookup resolves the identity; DB connector is not queried."""
        privacy_request = MagicMock()
        result = enrich_identities_for_consent(
            datasets=[consent_enrichment_dataset_config],
            connection_configs=[consent_enrichment_connection_config],
            identity_data={"email": "pref-user@example.com"},
            privacy_request=privacy_request,
            session=db,
        )
        assert result["external_id"] == "ext_pref_001"
        log_call = privacy_request.add_success_execution_log.call_args
        assert "preferences" in log_call.kwargs.get(
            "message", log_call[1].get("message", "")
        )

    def test_falls_back_to_db_connector(
        self,
        db,
        consent_enrichment_connection_config,
        consent_enrichment_dataset_config,
        identity_lookup_table,
    ):
        """No preference match — falls back to DB connector enrichment."""
        privacy_request = MagicMock()
        result = enrich_identities_for_consent(
            datasets=[consent_enrichment_dataset_config],
            connection_configs=[consent_enrichment_connection_config],
            identity_data={"email": "enrichment-user@example.com"},
            privacy_request=privacy_request,
            session=db,
        )
        assert result["external_id"] == "ext_enrich_001"
        log_call = privacy_request.add_success_execution_log.call_args
        assert "DB connectors" in log_call.kwargs.get(
            "message", log_call[1].get("message", "")
        )
