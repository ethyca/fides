from typing import Dict

from setup.database_connector import (
    create_database_connector,
    update_database_connector_secrets,
)
from setup.dataset import create_dataset


def create_fides_connector(
    auth_header: Dict[str, str],
    key: str = "fides_connector",
    verify: bool = True,
):
    create_database_connector(
        auth_header=auth_header,
        key=key,
        connection_type="fides",
    )
    update_database_connector_secrets(
        auth_header=auth_header,
        key=key,
        secrets={
            "uri": "http://fides-child:8080",
            "username": "parent",
            "password": "parentpassword1!",
        },
        verify=verify,
    )
    create_dataset(
        auth_header=auth_header,
        connection_key=key,
        yaml_path="data/dataset/remote_fides_example_test_dataset.yml",
    )
