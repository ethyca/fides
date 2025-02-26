import secrets

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fides.api.cryptography.identity_salt import get_identity_salt
from fides.api.models.identity_salt import IdentitySalt


class TestIdentitySalt:
    def test_create_duplicate_identity_salt(self, db: Session):

        # delete the salt
        db.query(IdentitySalt).delete()
        db.commit()

        # verify a salt can be added once
        IdentitySalt.create(
            db, data={"encrypted_value": {"value": secrets.token_hex(32)}}
        )

        # but not twice
        with pytest.raises(IntegrityError) as exc:
            IdentitySalt.create(
                db, data={"encrypted_value": {"value": secrets.token_hex(32)}}
            )
        assert "duplicate key value violates unique constraint" in str(exc)


class TestGetIdentitySalt:
    def test_get_identity_salt(self):
        # Salt should be 64 characters long (256 bits/32 bytes)
        assert len(get_identity_salt()) == 64
