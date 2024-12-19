from fides.api.models.db_cache import DBCache, DBCacheNamespace


class TestDBCacheModel:
    def test_get_nonexisting_entry(self, db):
        cache_value = DBCache.get_cache_value(
            db, DBCacheNamespace.LIST_PRIVACY_EXPERIENCE, "nonexisting"
        )
        assert cache_value is None

    def test_set_and_get_cache_value(self, db):
        cache_value = DBCache.set_cache_value(
            db,
            DBCacheNamespace.LIST_PRIVACY_EXPERIENCE,
            "some-key",
            '{"some": "value", "another": "value"}'.encode(),
        )
        assert (
            cache_value.cache_value.decode() == '{"some": "value", "another": "value"}'
        )

        cache_value = DBCache.get_cache_value(
            db, DBCacheNamespace.LIST_PRIVACY_EXPERIENCE, "some-key"
        )
        assert cache_value.decode() == '{"some": "value", "another": "value"}'

    def test_update_cache_value(self, db):
        # First we set a value
        cache_value = DBCache.set_cache_value(
            db,
            DBCacheNamespace.LIST_PRIVACY_EXPERIENCE,
            "some-key",
            "value 1".encode(),
        )
        assert cache_value.cache_value.decode() == "value 1"
        assert (
            DBCache.get_cache_value(
                db, DBCacheNamespace.LIST_PRIVACY_EXPERIENCE, "some-key"
            ).decode()
            == "value 1"
        )

        # Update the cache value
        cache_value = DBCache.set_cache_value(
            db, DBCacheNamespace.LIST_PRIVACY_EXPERIENCE, "some-key", "value 2".encode()
        )
        assert cache_value.cache_value.decode() == "value 2"

        # Check the value was actually updated
        updated_value = DBCache.get_cache_value(
            db, DBCacheNamespace.LIST_PRIVACY_EXPERIENCE, "some-key"
        )
        assert updated_value.decode() == "value 2"
