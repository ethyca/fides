import pytest

from fides.api.alembic.migrations.helpers.database_functions import generate_record_id
from fides.api.alembic.migrations.helpers.fideslang_migration_functions import (
    remove_conflicting_rule_targets,
)
from fides.api.common_exceptions import KeyOrNameAlreadyExists, PolicyValidationError
from fides.api.db import seed
from fides.api.db.seed import DEFAULT_ERASURE_POLICY_RULE
from fides.api.models.policy import Rule, RuleTarget


class TestDataCategoryMigrationFunctions:

    def test_remove_conflicting_rule_targets(self, db):
        # prep the default erasure rule for testing by inserting a conflicting data category
        # directly into the database and bypassing the checks on RuleTarget.create
        seed.load_default_dsr_policies()
        erasure_rule = Rule.get_by(db, field="key", value=DEFAULT_ERASURE_POLICY_RULE)
        erasure_rule_id = erasure_rule.id
        db.execute(
            "INSERT INTO ruletarget (id, name, key, data_category, rule_id) VALUES (:id, :name, :key, :data_category, :rule_id)",
            {
                "id": generate_record_id("rul"),
                "name": f"{erasure_rule_id}-user.biometric.health",
                "key": f"{erasure_rule_id}-userbiometrichealth",
                "data_category": "user.biometric.health",
                "rule_id": erasure_rule_id,
            },
        )
        db.commit()

        with pytest.raises(PolicyValidationError) as exc:
            RuleTarget.create(
                db=db,
                data={
                    "data_category": "user.biometric",
                    "rule_id": erasure_rule_id,
                },
            )
        assert (
            "Policy rules are invalid, action conflict in erasure rules detected for categories user.biometric.health and user.biometric"
            in str(exc)
        )

        remove_conflicting_rule_targets(db.connection())

        db.commit()

        # verify we no longer get a validation error and have moved
        # instead to a KeyOrNameAlreadyExists exception
        with pytest.raises(KeyOrNameAlreadyExists):
            RuleTarget.create(
                db=db,
                data={
                    "data_category": "user.biometric",
                    "rule_id": erasure_rule_id,
                },
            )
