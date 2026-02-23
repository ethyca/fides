from enum import Enum

from fides.api.models.db_cache import DBCache, DBCacheNamespace


# enum used to test extra namespaces since right now DBCacheNamespace only has one value
# this can be removed once more namespaces are added
class TestDbCacheNamespace(Enum):
    TEST_NAMESPACE = "test-namespace"


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
        assert cache_value.updated_at is not None

        original_timestamp = cache_value.updated_at

        # Update the cache value
        cache_value = DBCache.set_cache_value(
            db, DBCacheNamespace.LIST_PRIVACY_EXPERIENCE, "some-key", "value 2".encode()
        )
        assert cache_value.cache_value.decode() == "value 2"
        assert cache_value.updated_at > original_timestamp

        # Check the value was actually updated
        updated_value = DBCache.get_cache_value(
            db, DBCacheNamespace.LIST_PRIVACY_EXPERIENCE, "some-key"
        )
        assert updated_value.decode() == "value 2"

        previous_timestamp = cache_value.updated_at

        # Updating the value with the same value should still update the timestamp
        cache_value = DBCache.set_cache_value(
            db, DBCacheNamespace.LIST_PRIVACY_EXPERIENCE, "some-key", "value 2".encode()
        )
        assert cache_value.cache_value.decode() == "value 2"
        assert cache_value.updated_at > previous_timestamp

    def test_delete_cache_entry(self, db):
        # Add two entries
        DBCache.set_cache_value(
            db,
            DBCacheNamespace.LIST_PRIVACY_EXPERIENCE,
            "some-key",
            "value 1".encode(),
        )
        DBCache.set_cache_value(
            db,
            DBCacheNamespace.LIST_PRIVACY_EXPERIENCE,
            "some-key-2",
            "value 2".encode(),
        )
        assert (
            DBCache.get_cache_value(
                db, DBCacheNamespace.LIST_PRIVACY_EXPERIENCE, "some-key"
            ).decode()
            == "value 1"
        )
        assert (
            DBCache.get_cache_value(
                db, DBCacheNamespace.LIST_PRIVACY_EXPERIENCE, "some-key-2"
            ).decode()
            == "value 2"
        )

        # Delete the first entry
        DBCache.delete_cache_entry(
            db, DBCacheNamespace.LIST_PRIVACY_EXPERIENCE, "some-key"
        )

        # Check the first entry was deleted
        assert (
            DBCache.get_cache_value(
                db, DBCacheNamespace.LIST_PRIVACY_EXPERIENCE, "some-key"
            )
            is None
        )

        # Check the second entry still exists
        assert (
            DBCache.get_cache_value(
                db, DBCacheNamespace.LIST_PRIVACY_EXPERIENCE, "some-key-2"
            ).decode()
            == "value 2"
        )

    def test_clear_cache_for_namespace(self, db):
        # Add three entries, two belonging to namespace LIST_PRIVACY_EXPERIENCE and one to another namespace
        DBCache.set_cache_value(
            db,
            DBCacheNamespace.LIST_PRIVACY_EXPERIENCE,
            "key-1",
            "value 1".encode(),
        )
        DBCache.set_cache_value(
            db,
            DBCacheNamespace.LIST_PRIVACY_EXPERIENCE,
            "key-2",
            "value 2".encode(),
        )
        DBCache.set_cache_value(
            db,
            TestDbCacheNamespace.TEST_NAMESPACE,
            "key-1",
            "value 3".encode(),
        )

        # Check all entries exist
        assert (
            DBCache.get_cache_value(
                db, DBCacheNamespace.LIST_PRIVACY_EXPERIENCE, "key-1"
            ).decode()
            == "value 1"
        )
        assert (
            DBCache.get_cache_value(
                db, DBCacheNamespace.LIST_PRIVACY_EXPERIENCE, "key-2"
            ).decode()
            == "value 2"
        )
        assert (
            DBCache.get_cache_value(
                db, TestDbCacheNamespace.TEST_NAMESPACE, "key-1"
            ).decode()
            == "value 3"
        )

        # Clear the cache for LIST_PRIVACY_EXPERIENCE namespace
        DBCache.clear_cache_for_namespace(db, DBCacheNamespace.LIST_PRIVACY_EXPERIENCE)

        # Check the entries belonging to LIST_PRIVACY_EXPERIENCE were deleted
        assert (
            DBCache.get_cache_value(
                db, DBCacheNamespace.LIST_PRIVACY_EXPERIENCE, "key-1"
            )
            is None
        )
        assert (
            DBCache.get_cache_value(
                db, DBCacheNamespace.LIST_PRIVACY_EXPERIENCE, "key-2"
            )
            is None
        )

        # Check the entry belonging to another namespace still exists
        assert (
            DBCache.get_cache_value(
                db, TestDbCacheNamespace.TEST_NAMESPACE, "key-1"
            ).decode()
            == "value 3"
        )

    def test_clear_cache(self, db):
        # Add three entries, two belonging to namespace LIST_PRIVACY_EXPERIENCE and one to another namespace
        DBCache.set_cache_value(
            db,
            DBCacheNamespace.LIST_PRIVACY_EXPERIENCE,
            "key-1",
            "value 1".encode(),
        )
        DBCache.set_cache_value(
            db,
            DBCacheNamespace.LIST_PRIVACY_EXPERIENCE,
            "key-2",
            "value 2".encode(),
        )
        DBCache.set_cache_value(
            db,
            TestDbCacheNamespace.TEST_NAMESPACE,
            "key-1",
            "value 3".encode(),
        )

        # Check all entries exist
        assert (
            DBCache.get_cache_value(
                db, DBCacheNamespace.LIST_PRIVACY_EXPERIENCE, "key-1"
            ).decode()
            == "value 1"
        )
        assert (
            DBCache.get_cache_value(
                db, DBCacheNamespace.LIST_PRIVACY_EXPERIENCE, "key-2"
            ).decode()
            == "value 2"
        )
        assert (
            DBCache.get_cache_value(
                db, TestDbCacheNamespace.TEST_NAMESPACE, "key-1"
            ).decode()
            == "value 3"
        )

        # Clear the cache
        DBCache.clear_cache(db)

        # Check all entries were deleted
        assert (
            DBCache.get_cache_value(
                db, DBCacheNamespace.LIST_PRIVACY_EXPERIENCE, "key-1"
            )
            is None
        )
        assert (
            DBCache.get_cache_value(
                db, DBCacheNamespace.LIST_PRIVACY_EXPERIENCE, "key-2"
            )
            is None
        )
        assert (
            DBCache.get_cache_value(db, TestDbCacheNamespace.TEST_NAMESPACE, "key-1")
            is None
        )
