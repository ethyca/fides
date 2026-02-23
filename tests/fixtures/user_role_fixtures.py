import pytest

from fides.api.models.client import ClientDetail
from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_permissions import FidesUserPermissions
from fides.api.oauth.roles import (
    APPROVER,
    CONTRIBUTOR,
    OWNER,
    VIEWER,
    VIEWER_AND_APPROVER,
)
from fides.common.scope_registry import USER_READ_OWN
from tests.helpers.auth import generate_role_header_for_user


@pytest.fixture
def owner_user(db):
    user = FidesUser.create(
        db=db,
        data={
            "username": "test_fides_owner_user",
            "password": "TESTdcnG@wzJeu0&%3Qe2fGo7",
            "email_address": "owner.user@ethyca.com",
        },
    )
    client = ClientDetail(
        hashed_secret="thisisatest",
        salt="thisisstillatest",
        scopes=[],
        roles=[OWNER],
        user_id=user.id,
    )

    FidesUserPermissions.create(db=db, data={"user_id": user.id, "roles": [OWNER]})

    db.add(client)
    db.commit()
    db.refresh(client)
    yield user
    user.delete(db)


@pytest.fixture
def approver_user(db):
    user = FidesUser.create(
        db=db,
        data={
            "username": "test_fides_viewer_user",
            "password": "TESTdcnG@wzJeu0&%3Qe2fGo7",
            "email_address": "approver.user@ethyca.com",
        },
    )
    client = ClientDetail(
        hashed_secret="thisisatest",
        salt="thisisstillatest",
        scopes=[],
        roles=[APPROVER],
        user_id=user.id,
    )

    FidesUserPermissions.create(db=db, data={"user_id": user.id, "roles": [APPROVER]})

    db.add(client)
    db.commit()
    db.refresh(client)
    yield user
    user.delete(db)


@pytest.fixture
def viewer_user(db):
    user = FidesUser.create(
        db=db,
        data={
            "username": "test_fides_viewer_user",
            "password": "TESTdcnG@wzJeu0&%3Qe2fGo7",
            "email_address": "viewer2.user@ethyca.com",
        },
    )
    client = ClientDetail(
        hashed_secret="thisisatest",
        salt="thisisstillatest",
        roles=[VIEWER],
        user_id=user.id,
    )

    FidesUserPermissions.create(db=db, data={"user_id": user.id, "roles": [VIEWER]})

    db.add(client)
    db.commit()
    db.refresh(client)
    yield user
    user.delete(db)


@pytest.fixture
def contributor_user(db):
    user = FidesUser.create(
        db=db,
        data={
            "username": "test_fides_contributor_user",
            "password": "TESTdcnG@wzJeu0&%3Qe2fGo7",
            "email_address": "contributor.user@ethyca.com",
        },
    )
    client = ClientDetail(
        hashed_secret="thisisatest",
        salt="thisisstillatest",
        scopes=[],
        roles=[CONTRIBUTOR],
        user_id=user.id,
    )

    FidesUserPermissions.create(
        db=db, data={"user_id": user.id, "roles": [CONTRIBUTOR]}
    )

    db.add(client)
    db.commit()
    db.refresh(client)
    yield user
    user.delete(db)


@pytest.fixture
def respondent(db):
    """Create a respondent user with USER_READ_OWN scope"""
    from fides.api.oauth.roles import RESPONDENT

    user = FidesUser.create(
        db=db,
        data={
            "username": "test_respondent_user",
            "password": "TESTdcnG@wzJeu0&%3Qe2fGo7",
            "email_address": "respondent.user@ethyca.com",
        },
    )
    client = ClientDetail(
        hashed_secret="thisisatest",
        salt="thisisstillatest",
        scopes=[USER_READ_OWN],
        roles=[RESPONDENT],
        user_id=user.id,
    )

    FidesUserPermissions.create(db=db, data={"user_id": user.id, "roles": [RESPONDENT]})

    db.add(client)
    db.commit()
    db.refresh(client)
    db.refresh(user)  # Refresh user to load the client relationship
    yield user
    user.delete(db)


@pytest.fixture
def viewer_and_approver_user(db):
    user = FidesUser.create(
        db=db,
        data={
            "username": "test_fides_viewer_and_approver_user",
            "password": "TESTdcnG@wzJeu0&%3Qe2fGo7",
            "email_address": "viewerapprover.user@ethyca.com",
        },
    )
    client = ClientDetail(
        hashed_secret="thisisatest",
        salt="thisisstillatest",
        scopes=[],
        roles=[VIEWER_AND_APPROVER],
        user_id=user.id,
    )

    FidesUserPermissions.create(
        db=db, data={"user_id": user.id, "roles": [VIEWER_AND_APPROVER]}
    )

    db.add(client)
    db.commit()
    db.refresh(client)
    yield user
    user.delete(db)


@pytest.fixture
def owner_auth_header(owner_user):
    return generate_role_header_for_user(owner_user, owner_user.client.roles)


@pytest.fixture
def contributor_auth_header(contributor_user):
    return generate_role_header_for_user(
        contributor_user, contributor_user.client.roles
    )


@pytest.fixture
def viewer_auth_header(viewer_user):
    return generate_role_header_for_user(viewer_user, viewer_user.client.roles)


@pytest.fixture
def approver_auth_header(approver_user):
    return generate_role_header_for_user(approver_user, approver_user.client.roles)


@pytest.fixture
def viewer_and_approver_auth_header(viewer_and_approver_user):
    return generate_role_header_for_user(
        viewer_and_approver_user, viewer_and_approver_user.client.roles
    )
