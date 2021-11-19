import pytest
from sqlalchemy.orm import Session

from fidesops.db.base_class import KeyValidationError, KeyOrNameAlreadyExists
from fidesops.models.connectionconfig import (
    ConnectionConfig,
    ConnectionType,
    AccessLevel,
)
from fidesops.util.text import to_snake_case


class TestConnectionConfigModel:
    def test_create_connection_config(self, db: Session) -> None:
        name = "my main database"
        config = ConnectionConfig.create(
            db=db,
            data={
                "name": name,
                "connection_type": ConnectionType.postgres,
                "access": AccessLevel.read,
            },
        )
        assert config.key == to_snake_case(name)

        secrets = {
            "host": "host.docker.internal",
            "port": "6432",
            "db_name": "postgres_example",
            "username": "postgres",
            "password": "postgres",
        }
        config.secrets = secrets
        db.add(config)
        db.commit()
        db.expunge_all()

        loaded_config = db.query(ConnectionConfig).filter_by(name=name).first()

        assert loaded_config.secrets == secrets
        assert loaded_config.key == "my_main_database"
        assert loaded_config.name == name
        assert loaded_config.connection_type.value == "postgres"
        assert loaded_config.access.value == "read"
        assert loaded_config.created_at is not None

        first_updated = loaded_config.updated_at
        assert first_updated is not None
        assert loaded_config.last_test_timestamp is None
        assert loaded_config.last_test_succeeded is None

        new_pass = "p@ssword"
        loaded_config.secrets["password"] = new_pass
        db.add(loaded_config)
        db.commit()
        db.expunge_all()

        loaded_config = db.query(ConnectionConfig).filter_by(name=name).first()
        assert loaded_config.secrets["password"] == new_pass
        assert loaded_config.created_at is not None
        assert loaded_config.updated_at > first_updated

        loaded_config.delete(db=db)

    def test_create_connection_config_errors(self, db: Session, connection_config):
        with pytest.raises(KeyValidationError) as exc:
            ConnectionConfig.create(
                db=db,
                data={
                    "connection_type": ConnectionType.postgres,
                    "access": AccessLevel.read,
                },
            )
        assert str(exc.value) == "ConnectionConfig requires a name."

        with pytest.raises(KeyOrNameAlreadyExists) as exc:
            ConnectionConfig.create(
                db=db,
                data={
                    "connection_type": ConnectionType.postgres,
                    "access": AccessLevel.read,
                    "key": connection_config.key,
                },
            )
        assert (
            str(exc.value)
            == "Key my_postgres_db_1 already exists in ConnectionConfig. Keys will be snake-cased names if not provided. "
            "If you are seeing this error without providing a key, please provide a key or a different name."
        )
