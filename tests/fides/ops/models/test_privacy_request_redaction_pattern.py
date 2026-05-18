from sqlalchemy.orm import Session

from fides.api.models.privacy_request_redaction_pattern import (
    PrivacyRequestRedactionPattern,
)


class TestPrivacyRequestRedactionPatternModel:
    def test_create_single_pattern(self, db: Session) -> None:
        pattern = PrivacyRequestRedactionPattern.create(
            db=db, data={"pattern": "email.*"}
        )
        assert pattern.id is not None
        assert pattern.pattern == "email.*"
        assert pattern.created_at is not None
        assert pattern.updated_at is not None

    def test_pattern_uniqueness(self, db: Session) -> None:
        PrivacyRequestRedactionPattern.create(db=db, data={"pattern": "full_name"})

        # Duplicate insert should be prevented by unique constraint.
        # Depending on DB behavior, this may raise an IntegrityError; use replace_patterns for idempotency.
        updated = PrivacyRequestRedactionPattern.replace_patterns(
            db=db, patterns=["full_name"]
        )
        assert updated == ["full_name"]

        # Ensure only one row exists
        rows = db.query(PrivacyRequestRedactionPattern).all()
        assert len(rows) == 1

    def test_get_patterns_empty(self, db: Session) -> None:
        # Ensure table empty
        PrivacyRequestRedactionPattern.replace_patterns(db=db, patterns=[])
        assert PrivacyRequestRedactionPattern.get_patterns(db) == []

    def test_replace_patterns_adds_and_removes(self, db: Session) -> None:
        # Start with two
        result = PrivacyRequestRedactionPattern.replace_patterns(
            db=db, patterns=[r"user", r"email.*"]
        )
        assert result == ["email.*", "user"]

        # Replace with subset + new
        result = PrivacyRequestRedactionPattern.replace_patterns(
            db=db, patterns=[r"user", r"name"]
        )
        assert result == ["name", "user"]

        patterns_in_db = PrivacyRequestRedactionPattern.get_patterns(db)
        assert set(patterns_in_db) == {"user", "name"}

    def test_replace_patterns_normalizes_input(self, db: Session) -> None:
        result = PrivacyRequestRedactionPattern.replace_patterns(
            db=db, patterns=["  name  ", "", " ", "name", "NAME"]
        )

        # Normalization trims whitespace, removes empties; case-sensitivity is preserved
        # So we expect two distinct patterns: "NAME" and "name"
        assert sorted(result) == ["NAME", "name"]
