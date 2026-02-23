import pytest
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.sql_models import System
from fides.system_integration_link.models import (
    SystemConnectionConfigLink,
)
from fides.system_integration_link.repository import (
    SystemIntegrationLinkRepository,
)


@pytest.fixture()
def repo() -> SystemIntegrationLinkRepository:
    return SystemIntegrationLinkRepository()


@pytest.fixture()
def system_a(db: Session):
    system = System.create(
        db=db,
        data={
            "fides_key": "link_test_system_a",
            "name": "Link Test System A",
            "organization_fides_key": "test_organization",
            "system_type": "Service",
        },
    )
    yield system
    system.delete(db)


@pytest.fixture()
def system_b(db: Session):
    system = System.create(
        db=db,
        data={
            "fides_key": "link_test_system_b",
            "name": "Link Test System B",
            "organization_fides_key": "test_organization",
            "system_type": "Service",
        },
    )
    yield system
    system.delete(db)


@pytest.fixture()
def connection_config(db: Session):
    config = ConnectionConfig.create(
        db=db,
        data={
            "key": "link_test_connection",
            "connection_type": "manual",
            "access": "read",
        },
    )
    yield config
    config.delete(db)


@pytest.fixture()
def connection_config_b(db: Session):
    config = ConnectionConfig.create(
        db=db,
        data={
            "key": "link_test_connection_b",
            "connection_type": "manual",
            "access": "read",
        },
    )
    yield config
    config.delete(db)


@pytest.fixture(autouse=True)
def cleanup_links(db: Session):
    """Clean up any link records after each test."""
    yield
    db.query(SystemConnectionConfigLink).filter(
        SystemConnectionConfigLink.connection_config_id.in_(
            db.query(ConnectionConfig.id).filter(
                ConnectionConfig.key.like("link_test_%")
            )
        )
    ).delete(synchronize_session=False)
    db.commit()


class TestUpsertLink:
    def test_creates_new_link(self, repo, db, connection_config, system_a):
        entity = repo.upsert_link(
            connection_config_id=connection_config.id,
            system_id=system_a.id,
            session=db,
        )
        db.commit()

        assert entity.system_id == system_a.id
        assert entity.connection_config_id == connection_config.id
        assert entity.system_fides_key == "link_test_system_a"
        assert entity.system_name == "Link Test System A"

    def test_returns_existing_link_on_duplicate(
        self, repo, db, connection_config, system_a
    ):
        first = repo.upsert_link(
            connection_config_id=connection_config.id,
            system_id=system_a.id,
            session=db,
        )
        db.commit()

        second = repo.upsert_link(
            connection_config_id=connection_config.id,
            system_id=system_a.id,
            session=db,
        )
        db.commit()

        assert first.id == second.id


class TestGetLinksForConnection:
    def test_returns_links_with_system_info(
        self, repo, db, connection_config, system_a
    ):
        repo.upsert_link(
            connection_config_id=connection_config.id,
            system_id=system_a.id,
            session=db,
        )
        db.commit()

        links = repo.get_links_for_connection(connection_config.id, session=db)

        assert len(links) == 1
        assert links[0].system_fides_key == "link_test_system_a"

    def test_returns_empty_for_no_links(self, repo, db, connection_config):
        links = repo.get_links_for_connection(connection_config.id, session=db)
        assert links == []


class TestDeleteAllLinksForConnection:
    def test_deletes_link(self, repo, db, connection_config, system_a):
        repo.upsert_link(
            connection_config_id=connection_config.id,
            system_id=system_a.id,
            session=db,
        )
        db.commit()

        count = repo.delete_all_links_for_connection(connection_config.id, session=db)
        db.commit()

        assert count == 1
        remaining = repo.get_links_for_connection(connection_config.id, session=db)
        assert remaining == []

    def test_only_deletes_target_connection(
        self, repo, db, connection_config, connection_config_b, system_a, system_b
    ):
        """Deleting links for one connection doesn't affect another."""
        repo.upsert_link(
            connection_config_id=connection_config.id,
            system_id=system_a.id,
            session=db,
        )
        repo.upsert_link(
            connection_config_id=connection_config_b.id,
            system_id=system_b.id,
            session=db,
        )
        db.commit()

        count = repo.delete_all_links_for_connection(connection_config.id, session=db)
        db.commit()

        assert count == 1
        assert repo.get_links_for_connection(connection_config.id, session=db) == []
        remaining_b = repo.get_links_for_connection(connection_config_b.id, session=db)
        assert len(remaining_b) == 1
        assert remaining_b[0].system_fides_key == "link_test_system_b"

    def test_delete_then_create_in_same_session(
        self, repo, db, connection_config, system_a, system_b
    ):
        """Verifies the core set_links flow: delete all, then create new."""
        repo.upsert_link(
            connection_config_id=connection_config.id,
            system_id=system_a.id,
            session=db,
        )
        db.flush()

        repo.delete_all_links_for_connection(connection_config.id, session=db)
        db.flush()

        entity = repo.upsert_link(
            connection_config_id=connection_config.id,
            system_id=system_b.id,
            session=db,
        )
        db.commit()

        assert entity.system_fides_key == "link_test_system_b"

        links = repo.get_links_for_connection(connection_config.id, session=db)
        assert len(links) == 1
        assert links[0].system_fides_key == "link_test_system_b"

    def test_returns_zero_when_no_links_exist(self, repo, db, connection_config):
        count = repo.delete_all_links_for_connection(connection_config.id, session=db)
        assert count == 0


class TestDeleteLinks:
    def test_deletes_specific_system_link(
        self, repo, db, connection_config, connection_config_b, system_a, system_b
    ):
        repo.upsert_link(
            connection_config_id=connection_config.id,
            system_id=system_a.id,
            session=db,
        )
        repo.upsert_link(
            connection_config_id=connection_config_b.id,
            system_id=system_b.id,
            session=db,
        )
        db.commit()

        count = repo.delete_links(
            connection_config_id=connection_config.id,
            system_id=system_a.id,
            session=db,
        )
        db.commit()

        assert count == 1
        assert repo.get_links_for_connection(connection_config.id, session=db) == []
        remaining_b = repo.get_links_for_connection(connection_config_b.id, session=db)
        assert len(remaining_b) == 1
        assert remaining_b[0].system_fides_key == "link_test_system_b"


class TestResolveHelpers:
    def test_resolve_connection_config(self, repo, db, connection_config):
        result = repo.resolve_connection_config("link_test_connection", session=db)
        assert result is not None
        assert result.id == connection_config.id

    def test_resolve_connection_config_not_found(self, repo, db):
        result = repo.resolve_connection_config("nonexistent_key", session=db)
        assert result is None

    def test_resolve_system(self, repo, db, system_a):
        result = repo.resolve_system("link_test_system_a", session=db)
        assert result is not None
        assert result.id == system_a.id

    def test_resolve_system_not_found(self, repo, db):
        result = repo.resolve_system("nonexistent_system", session=db)
        assert result is None
