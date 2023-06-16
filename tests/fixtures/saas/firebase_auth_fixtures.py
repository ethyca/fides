from random import randint
from typing import Any, Dict, Generator

import pydash
import pytest
from firebase_admin import auth
from firebase_admin.auth import UserNotFoundError
from firebase_admin.exceptions import FirebaseError
from sqlalchemy.orm import Session

from fides.api.cryptography import cryptographic_util
from fides.api.db import session
from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.service.saas_request.override_implementations.firebase_auth_request_overrides import (
    initialize_firebase,
)
from fides.api.util.saas_util import (
    load_config_with_replacement,
    load_dataset_with_replacement,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("firebase_auth")
from fides.api.models.sql_models import Dataset as CtlDataset


@pytest.fixture
def firebase_auth_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/firebase_auth_config.yml",
        "<instance_fides_key>",
        "firebase_auth_instance",
    )


@pytest.fixture
def firebase_auth_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/firebase_auth_dataset.yml",
        "<instance_fides_key>",
        "firebase_auth_instance",
    )[0]


@pytest.fixture(scope="session")
def firebase_auth_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "firebase_auth.domain") or secrets["domain"],
        "type": pydash.get(saas_config, "firebase_auth.type") or secrets["type"],
        "project_id": pydash.get(saas_config, "firebase_auth.project_id")
        or secrets["project_id"],
        "private_key_id": pydash.get(saas_config, "firebase_auth.private_key_id")
        or secrets["private_key_id"],
        "private_key": pydash.get(saas_config, "firebase_auth.private_key")
        or secrets["private_key"],
        "client_email": pydash.get(saas_config, "firebase_auth.client_email")
        or secrets["client_email"],
        "client_id": pydash.get(saas_config, "firebase_auth.client_id")
        or secrets["client_id"],
        "auth_uri": pydash.get(saas_config, "firebase_auth.auth_uri")
        or secrets["auth_uri"],
        "token_uri": pydash.get(saas_config, "firebase_auth.token_uri")
        or secrets["token_uri"],
        "auth_provider_x509_cert_url": pydash.get(
            saas_config, "firebase_auth.auth_provider_x509_cert_url"
        )
        or secrets["auth_provider_x509_cert_url"],
        "client_x509_cert_url": pydash.get(
            saas_config, "firebase_auth.client_x509_cert_url"
        )
        or secrets["client_x509_cert_url"],
    }


@pytest.fixture(scope="function")
def firebase_auth_user(firebase_auth_secrets) -> Generator:
    app = initialize_firebase(firebase_auth_secrets)

    # create a user provider
    uid = cryptographic_util.generate_secure_random_string(28)
    email = f"{cryptographic_util.generate_secure_random_string(13)}@email.com"
    provider_id = "facebook.com"
    display_name = "John Doe #1"
    photo_url = "http://www.facebook.com/12345678/photo.png"
    up1 = auth.UserProvider(
        uid,
        email=email,
        provider_id=provider_id,
        display_name=display_name,
        photo_url=photo_url,
    )

    # create another user provider
    uid = cryptographic_util.generate_secure_random_string(28)
    email = f"{cryptographic_util.generate_secure_random_string(13)}@email.com"
    provider_id = "google.com"
    display_name = "John Doe #2"
    up2 = auth.UserProvider(
        uid,
        email=email,
        provider_id=provider_id,
        display_name=display_name,
    )
    # create the user
    email = f"{cryptographic_util.generate_secure_random_string(13)}@email.com"
    uid = cryptographic_util.generate_secure_random_string(28)
    user = auth.ImportUserRecord(
        uid=uid,
        email=email,
        email_verified=False,
        display_name="John Doe",
        photo_url="http://www.example.com/12345678/photo.png",
        phone_number="+1" + str(randint(1000000000, 9999999999)),
        disabled=False,
        provider_data=[up1, up2],
    )
    auth.import_users([user], app=app)

    yield user

    try:
        auth.delete_user(user.uid, app=app)
    except FirebaseError as e:
        # user may have already been deleted, so catch the possible exception
        if not isinstance(e, UserNotFoundError):
            raise e


@pytest.fixture(scope="function")
def firebase_auth_connection_config(
    db: session, firebase_auth_config, firebase_auth_secrets
) -> Generator:
    fides_key = firebase_auth_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": firebase_auth_secrets,
            "saas_config": firebase_auth_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def firebase_auth_dataset_config(
    db: Session,
    firebase_auth_connection_config: ConnectionConfig,
    firebase_auth_dataset: Dict[str, Any],
) -> Generator:
    fides_key = firebase_auth_dataset["fides_key"]
    firebase_auth_connection_config.name = fides_key
    firebase_auth_connection_config.key = fides_key
    firebase_auth_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, firebase_auth_dataset)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": firebase_auth_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)
