import json
from typing import Dict, List

from sqlalchemy import inspect, text
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.orm import Session

from fides.api.db.session import get_db_session
from fides.config import get_config

CONFIG = get_config()


def check_index_exists(inspector: Inspector, table_name: str, index_name: str) -> bool:
    indexes = inspector.get_indexes(table_name)
    return any(index["name"] == index_name for index in indexes)


def get_index_progress(db: Session, table_name: str, index_name: str) -> str:
    progress_query = text(
        """
        SELECT
            c.phase AS progress
        FROM
            pg_stat_progress_create_index c
            JOIN pg_index i ON c.index_relid = i.indexrelid
        WHERE
            i.indrelid::regclass::text = :table_name
            AND i.indexrelid::regclass::text = :index_name
        """
    )
    result = db.execute(
        progress_query, {"table_name": table_name, "index_name": index_name}
    ).fetchone()
    return result[0] if result else "complete"


def get_index_info(
    db: Session, table_index_map: Dict[str, List[str]]
) -> Dict[str, str]:
    inspector: Inspector = inspect(db.bind)
    index_info: Dict[str, str] = {}
    for table_name, index_names in table_index_map.items():
        for index_name in index_names:
            exists = check_index_exists(inspector, table_name, index_name)
            progress = (
                get_index_progress(db, table_name, index_name)
                if exists
                else "not found"
            )
            index_info[index_name] = progress
    return index_info


if __name__ == "__main__":
    SessionLocal = get_db_session(CONFIG)
    db: Session = SessionLocal()

    table_index_map: Dict[str, List[str]] = {
        "privacypreferencehistory": ["ix_privacypreferencehistory_property_id"],
        "servednoticehistory": ["ix_servednoticehistory_property_id"],
    }

    index_info: Dict[str, str] = get_index_info(db, table_index_map)
    print(json.dumps(index_info))
