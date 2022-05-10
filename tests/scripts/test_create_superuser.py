import pytest
from unittest import mock

from create_superuser import (
    collect_username_and_password,
    create_user_and_client,
)
from fidesops.common_exceptions import KeyOrNameAlreadyExists
from fidesops.models.client import ClientDetail, ADMIN_UI_ROOT
from fidesops.models.fidesops_user import FidesopsUser
from fidesops.models.fidesops_user_permissions import FidesopsUserPermissions
from fidesops.schemas.user import UserCreate
from fidesops.api.v1.scope_registry import CLIENT_CREATE


class TestCreateSuperuserScript:
    @mock.patch("create_superuser.get_username")
    @mock.patch("create_superuser.get_password")
    def test_collect_username_and_password(self, mock_pass, mock_user, db):
        mock_pass.return_value = "TESTP@ssword9"
        mock_user.return_value = "test_user"
        user: UserCreate = collect_username_and_password(db)

        assert user.username == "test_user"
        assert user.password == "TESTP@ssword9"

    @mock.patch("create_superuser.get_username")
    @mock.patch("create_superuser.get_password")
    def test_collect_username_and_password_user_exists(self, mock_pass, mock_user, db):
        user = FidesopsUser.create(
            db=db,
            data={"username": "test_user", "password": "test_password"},
        )
        mock_pass.return_value = "TESTP@ssword9"
        mock_user.return_value = "test_user"

        with pytest.raises(Exception):
            collect_username_and_password(db)

        user.delete(db)

    @mock.patch("create_superuser.get_username")
    @mock.patch("create_superuser.get_password")
    def test_collect_username_and_password_bad_data(self, mock_pass, mock_user, db):
        mock_pass.return_value = "bad_password"
        mock_user.return_value = "test_user"

        with pytest.raises(ValueError):
            collect_username_and_password(db)

    @mock.patch("create_superuser.get_username")
    @mock.patch("create_superuser.get_password")
    def test_create_user_and_client(self, mock_pass, mock_user, db):
        mock_pass.return_value = "TESTP@ssword9"
        mock_user.return_value = "test_user"

        superuser = create_user_and_client(db)
        assert superuser.username == "test_user"
        assert superuser.credentials_valid("TESTP@ssword9")
        assert superuser.hashed_password != "TESTP@ssword9"

        client_detail = db.query(ClientDetail).filter_by(user_id=superuser.id).first()
        assert client_detail.user == superuser
        assert superuser.client == client_detail
        assert client_detail.fides_key == ADMIN_UI_ROOT
        assert CLIENT_CREATE not in client_detail.scopes

        user_permissions = FidesopsUserPermissions.get_by(
            db=db, field="user_id", value=superuser.id
        )
        assert user_permissions is not None

        with pytest.raises(KeyOrNameAlreadyExists):
            create_user_and_client(db)

        client_detail.delete(db)
        superuser.delete(db)
