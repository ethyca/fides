import pytest
from fideslib.db.base_class import KeyOrNameAlreadyExists, KeyValidationError
from sqlalchemy.orm import Session

from fidesops.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.ops.schemas.saas.saas_config import SaaSConfig
from fidesops.ops.util.text import to_snake_case


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

    def test_setting_disabled_at(self, db, connection_config):
        assert connection_config.disabled_at is None

        connection_config.disabled = True
        connection_config.save(db)
        original_disabled_time = connection_config.disabled_at
        assert original_disabled_time is not None

        connection_config.disabled = True
        connection_config.save(db)
        assert connection_config.disabled_at is not None
        assert connection_config.disabled_at == original_disabled_time

        connection_config.disabled = False
        connection_config.save(db)
        assert connection_config.disabled_at is None

        connection_config.disabled = True
        connection_config.save(db)
        assert connection_config.disabled_at is not None
        assert connection_config.disabled_at > original_disabled_time

    def test_default_value_saas_config(
        self, db, saas_example_config, saas_example_secrets
    ):
        connection_config: ConnectionConfig = ConnectionConfig.create(
            db=db,
            data={
                "key": "not_configured",
                "name": "not_configured",
                "connection_type": ConnectionType.saas,
                "access": AccessLevel.read,
            },
        )
        saas_config = SaaSConfig(**saas_example_config)
        assert connection_config.secrets is None

        # verify that setting the SaaS config for the first time populates
        # the secrets with default values
        connection_config.update_saas_config(db, saas_config=saas_config)
        assert connection_config.secrets == {"domain": "localhost"}

        # verify that a user-defined secret overrides the default value
        connection_config.update(db, data={"secrets": saas_example_secrets})
        assert connection_config.secrets["domain"] == saas_example_secrets["domain"]

        # verify that updating the SaaS config after configuring the secrets
        # does not override any user-defined values
        connection_config.update_saas_config(db, saas_config=saas_config)
        assert connection_config.secrets["domain"] == saas_example_secrets["domain"]

    def test_default_value_saas_config_invalid_type(
        self, db, saas_example_config, saas_example_secrets
    ):
        saas_example_config["type"] = "invalid"
        with pytest.raises(ValueError):
            SaaSConfig(**saas_example_config)

    def test_connection_type_human_readable(self):
        for connection in ConnectionType:
            connection.human_readable  # Makes sure all ConnectionTypes have been added to human_readable mapping

    def test_connection_type_human_readable_invalid(self):
        with pytest.raises(ValueError):
            ConnectionType("nonmapped_type").human_readable()
