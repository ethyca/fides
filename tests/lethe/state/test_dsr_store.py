"""Postgres-backed DSRStore behavior (replaces Redis DSRCacheStore unit tests)."""

import pytest

from lethe.state import DSRStore


@pytest.mark.integration
class TestDSRStorePostgres:
    def test_encryption_round_trip(self, db, privacy_request):
        store = DSRStore(db, privacy_request.id)
        store.write_encryption("key", "0123456789abcdef", expire_seconds=3600)
        db.commit()
        db.refresh(privacy_request)
        assert DSRStore(db, privacy_request.id).get_encryption("key") == "0123456789abcdef"

    def test_drp_merge_and_get(self, db, privacy_request):
        store = DSRStore(db, privacy_request.id)
        store.merge_drp_request_body({"meta": {"version": "0.5"}}, expire_seconds=300)
        store.merge_drp_request_body({"regime": "ccpa"}, expire_seconds=300)
        db.commit()
        db.refresh(privacy_request)
        s2 = DSRStore(db, privacy_request.id)
        meta = s2.get_drp("meta")
        assert meta is not None
        assert '"version": "0.5"' in str(meta)
        assert s2.get_drp("regime") == "ccpa"

    def test_clear_privacy_request_state(self, db, privacy_request):
        store = DSRStore(db, privacy_request.id)
        store.write_encryption("key", "secret", expire_seconds=3600)
        store.merge_drp_request_body({"k": "v"}, expire_seconds=300)
        db.flush()
        store.clear_privacy_request_state()
        db.commit()
        db.refresh(privacy_request)
        assert privacy_request.encryption_key is None
        assert not privacy_request.drp_request_body
