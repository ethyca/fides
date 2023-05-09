import pytest
from sqlalchemy.orm import Session

from fides.api.ctl.sql_models import System
from fides.api.ops.common_exceptions import SystemManagerException
from fides.api.ops.models.fides_user import FidesUser


class TestSystemManager:
    def test_add_and_remove_user_from_system(
        self, db: Session, user: FidesUser, system: System
    ):
        assert user.systems == []
        assert system.users == []
        assert user.client.systems == []

        user.set_as_system_manager(db, system)
        assert user.systems == [system]
        assert system.users == [user]
        assert user.client.systems == [system.id]

        user.remove_as_system_manager(db, system)
        assert user.systems == []
        assert system.users == []
        assert user.client.systems == []

    def test_add_as_manager_of_bad_resource_type(
        self, db: Session, connection_config, user
    ):
        with pytest.raises(SystemManagerException) as exc:
            user.set_as_system_manager(db, connection_config)
        assert str(exc.value) == "Must pass in a system to set user as system manager."

    def test_remove_manager_from_bad_resource_type(
        self, db: Session, connection_config, user
    ):
        with pytest.raises(SystemManagerException) as exc:
            user.remove_as_system_manager(db, connection_config)
        assert (
            str(exc.value) == "Must pass in a system to remove user as system manager."
        )

    def test_adding_as_manager_when_already_a_manager(
        self, db: Session, system_manager, system
    ):
        assert system_manager.systems == [system]
        assert system.users == [system_manager]

        with pytest.raises(SystemManagerException) as exc:
            system_manager.set_as_system_manager(db, system)

        assert (
            str(exc.value)
            == f"User '{system_manager.username}' is already a system manager of '{system.name}'."
        )

        assert system_manager.systems == [system]

    def test_removing_as_manager_when_not_a_manager(self, db: Session, system, user):
        assert user.systems == []
        assert user.system_ids == []
        assert system.users == []
        with pytest.raises(SystemManagerException) as exc:
            user.remove_as_system_manager(db, system)

        assert (
            str(exc.value)
            == f"User '{user.username}' is not a manager of system '{system.name}'."
        )

    def test_system_ids_property(self, system_manager, system):
        assert system_manager.system_ids == [system.id]

    def test_removing_system_removes_manager(
        self, db: Session, user: FidesUser, system: System
    ):
        assert user.systems == []
        assert system.users == []
        assert user.client.systems == []

        user.set_as_system_manager(db, system)
        assert user.systems == [system]
        assert system.users == [user]
        assert user.client.systems == [system.id]

        db.delete(system)
        db.commit()
        db.flush()

        db.refresh(user)
        assert user.systems == []
        assert (
            user.client.systems != []
        )  # This isn't automatically cascade deleted, but the system doesn't exist either.

    def test_removing_user_removes_manager(
        self, db: Session, user: FidesUser, system: System
    ):
        assert user.systems == []
        assert system.users == []
        assert user.client.systems == []

        user.set_as_system_manager(db, system)
        assert user.systems == [system]
        assert system.users == [user]
        assert user.client.systems == [system.id]

        db.delete(user)
        db.commit()
        db.flush()

        db.refresh(system)
        assert system.users == []
