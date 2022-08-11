import sys

# This is a hacky workaround to test the scripts in a subdir
sys.path.insert(0, "scripts")

from unittest import mock

import pytest
from create_superuser import collect_username_and_password, create_user_and_client
from fideslib.cryptography.cryptographic_util import str_to_b64_str
from fideslib.exceptions import KeyOrNameAlreadyExists
from fideslib.models.client import ADMIN_UI_ROOT, ClientDetail
from fideslib.models.fides_user import FidesUser
from fideslib.models.fides_user_permissions import FidesUserPermissions
from fideslib.oauth.schemas.user import UserCreate

from fidesops.ops.api.v1.scope_registry import CLIENT_CREATE


class TestCreateSuperuserScript:
    @mock.patch("create_superuser.get_username")
    @mock.patch("create_superuser.get_password")
    @mock.patch("create_superuser.get_input")
    def test_collect_username_and_password(
        self,
        mock_input,
        mock_pass,
        mock_user,
        db,
    ):
        GENERIC_INPUT = "some_input"
        mock_pass.return_value = str_to_b64_str("TESTP@ssword9")
        mock_user.return_value = "test_user"
        mock_input.return_value = GENERIC_INPUT
        user: UserCreate = collect_username_and_password(db)

        assert user.username == "test_user"
        assert user.password == "TESTP@ssword9"
        assert user.first_name == GENERIC_INPUT
        assert user.last_name == GENERIC_INPUT

    @mock.patch("create_superuser.get_username")
    @mock.patch("create_superuser.get_password")
    @mock.patch("create_superuser.get_input")
    def test_collect_username_and_password_user_exists(
        self,
        mock_input,
        mock_pass,
        mock_user,
        db,
    ):
        user = FidesUser.create(
            db=db,
            data={"username": "test_user", "password": "test_password"},
        )
        mock_pass.return_value = str_to_b64_str("TESTP@ssword9")
        mock_user.return_value = "test_user"
        mock_input.return_value = "some_input"

        with pytest.raises(Exception):
            collect_username_and_password(db)

        user.delete(db)

    @mock.patch("create_superuser.get_username")
    @mock.patch("create_superuser.get_password")
    @mock.patch("create_superuser.get_input")
    def test_collect_username_and_password_bad_data(
        self,
        mock_input,
        mock_pass,
        mock_user,
        db,
    ):
        mock_pass.return_value = str_to_b64_str("bad_password")
        mock_user.return_value = "test_user"
        mock_input.return_value = "some_input"

        with pytest.raises(ValueError):
            collect_username_and_password(db)

    @mock.patch("create_superuser.get_username")
    @mock.patch("create_superuser.get_password")
    @mock.patch("create_superuser.get_input")
    def test_create_user_and_client(
        self,
        mock_input,
        mock_pass,
        mock_user,
        db,
    ):
        mock_pass.return_value = str_to_b64_str("TESTP@ssword9")
        mock_user.return_value = "test_user"
        mock_input.return_value = "some_input"

        superuser = create_user_and_client(db)
        assert superuser.username == "test_user"
        assert superuser.credentials_valid("TESTP@ssword9")
        assert superuser.hashed_password != "TESTP@ssword9"

        client_detail = db.query(ClientDetail).filter_by(user_id=superuser.id).first()
        assert client_detail.user == superuser
        assert superuser.client == client_detail
        assert client_detail.fides_key == ADMIN_UI_ROOT
        assert CLIENT_CREATE not in client_detail.scopes

        user_permissions = FidesUserPermissions.get_by(
            db=db, field="user_id", value=superuser.id
        )
        assert user_permissions is not None

        with pytest.raises(KeyOrNameAlreadyExists):
            create_user_and_client(db)

        client_detail.delete(db)
        superuser.delete(db)
