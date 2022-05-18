"""This module handles finding and parsing fides configuration files."""

# pylint: disable=C0115,C0116, E0213
import os
import re
from typing import Dict, List, Type

from pydantic import create_model

from .fides_settings import FidesSettings


class DatabaseCredentials(FidesSettings):
    """Class used to store values from the 'credentials.database.custom_key' section of the config."""

    connection_string: str = ""


class OktaCredentials(FidesSettings):
    """Class used to store values from the 'credentials.okta.custom_key' section of the config."""

    client_token: str = ""


class AwsCredentials(FidesSettings):
    """Class used to store values from the 'credentials.aws.custom_key' section of the config."""

    access_key_id: str = ""
    secret_access_key: str = ""
    region: str = ""


def create_dynamic_credentials_settings_model(settings: Dict) -> Type[FidesSettings]:
    """
    Returns a credentials settings model which contains dynamic keys to
    take advantage of pydantic features of model fields without knowing keys
    ahead of time.

    This allows a user to create a config with a custom key which is a field in our model.

    Example Config:
    [credentials.database]
    my_redshift = {connection_string="my_redshift_connection_string"}

    Exampe Model:
    credentials=(
        database=(
            my_redshift=(
                connection_string="my_redshift_connection_string"
            )
        )
    )
    """
    database_config_keys = get_credentials_config_keys(
        settings=settings, category="database"
    )
    database_dynamic_model = create_dynamic_key_model(
        config_keys=database_config_keys,
        base_model=DatabaseCredentials,
        model_name="DatabaseCredentialsWrapper",
    )
    aws_config_keys = get_credentials_config_keys(settings=settings, category="aws")
    aws_dynamic_model = create_dynamic_key_model(
        config_keys=aws_config_keys,
        base_model=AwsCredentials,
        model_name="AwsCredentialsWrapper",
    )

    okta_config_keys = get_credentials_config_keys(settings=settings, category="okta")
    okta_dynamic_model = create_dynamic_key_model(
        config_keys=okta_config_keys,
        base_model=OktaCredentials,
        model_name="OktaCredentialsWrapper",
    )

    credentials_dynamic_model = create_model(
        "CredentialsSettings",
        database=(
            database_dynamic_model,
            database_dynamic_model(),
        ),
        aws=(aws_dynamic_model, aws_dynamic_model()),
        okta=(okta_dynamic_model, okta_dynamic_model()),
        __base__=FidesSettings,
    )
    return credentials_dynamic_model


def create_dynamic_key_model(
    config_keys: List[str], base_model: Type[FidesSettings], model_name: str
) -> Type[FidesSettings]:
    """
    Given a list of config keys, creates a pydantic model with those fields
    """
    custom_credentials_fields = {key: (base_model, base_model()) for key in config_keys}

    dynamic_key_model = create_model(  # type: ignore
        __model_name=model_name,
        **custom_credentials_fields,
        __base__=FidesSettings,
    )
    return dynamic_key_model


def get_credentials_config_keys(settings: Dict, category: str) -> List[str]:
    """
    Gathers a list of config keys which are defined in config or environment variables
    for a given credentials category.
    """
    credentials_settings_dict = settings.get("credentials")
    config_keys = (
        credentials_settings_dict.get(category, {}).keys()
        if credentials_settings_dict
        else []
    )

    pattern = f"FIDESCTL_CREDENTIALS__{category}__(.*?)__".upper()
    environment_keys = []
    for key in os.environ:
        search = re.search(pattern, key)
        if search:
            environment_keys.append(search.group(1).lower())

    credentials_keys = list(set(config_keys).union(set(environment_keys)))
    return credentials_keys
