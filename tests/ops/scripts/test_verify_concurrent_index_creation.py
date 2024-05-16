from scripts.verify_concurrent_index_creation import get_index_info
from sqlalchemy.orm import Session


class TestVerifyConcurrentIndexCreation:
    def test_both_indexes_exist(self, db: Session):
        table_index_map = {
            "privacypreferencehistory": ["ix_privacypreferencehistory_property_id"],
            "servednoticehistory": ["ix_servednoticehistory_property_id"],
        }
        index_info = get_index_info(db, table_index_map)
        assert index_info == {
            "ix_privacypreferencehistory_property_id": "complete",
            "ix_servednoticehistory_property_id": "complete",
        }

    def test_one_index_missing(self, db: Session):
        table_index_map = {
            "privacypreferencehistory": ["ix_privacypreferencehistory_property_id"],
            "servednoticehistory": ["ix_missing_index"],
        }
        index_info = get_index_info(db, table_index_map)
        assert index_info == {
            "ix_privacypreferencehistory_property_id": "complete",
            "ix_missing_index": "not found",
        }
