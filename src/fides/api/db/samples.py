"""
Sample data to use for seeding the database. This are loaded & parsed from the
sample project at src/fides/data/sample_project.

See load_samples() in seed.py for usage.
"""

from typing import Dict, List, Optional, TextIO

import yaml
from expandvars import expandvars  # type: ignore
from fideslang.models import Taxonomy
from fideslang.validation import FidesKey

# DEFER: This can be changed to importlib.resources once we drop support for Python 3.8
from importlib_resources import files

from fides.api.schemas.connection_configuration.connection_config import (
    CreateConnectionConfigurationWithSecrets,
)
from fides.core.parse import parse


def load_sample_resources_from_project() -> Taxonomy:
    """
    Loads all the sample resource YAML files from the sample project by
    traversing through the sample_resources/ folder, inspecting each file, and
    parsing them into fideslang models.

    Returns a Taxonomy object, which has accessor for each resource type
    (system, dataset, etc.) and a list of models for each.
    """
    import fides.data.sample_project  # type: ignore

    sample_resources_path = files(fides.data.sample_project).joinpath(
        "sample_resources/"
    )
    resources: Taxonomy = parse(str(sample_resources_path))
    return resources


class SampleConnection(CreateConnectionConfigurationWithSecrets):
    """
    We use the `PATCH /api/v1/connection` endpoint function to instantiate the
    sample connections, which expects a ConnectionConfig-style model as input,
    so this model extends the CreateConnectionConfigurationWithSecrets model as
    a base.

    However, we also want to (optionally) support other fields in the sample
    connections YAML, such as a 'dataset' field which isn't supported in the
    ConnectionConfig APIs. Therefore, we extend that "base" model with our new
    fields and then reformat this source model as needed to suit those APIs.
    """

    dataset: Optional[FidesKey] = None
    """
    (Optional) Valid fides_key for an existing dataset that should be used
    for this ConnectionConfig. If a dataset does not exist for this key,
    creation will fail.
    """

    system_key: Optional[FidesKey] = None
    """
    (Optional) The connection config is linked to a system via the `system_id`,
    which is auto-generated when the system is created in the database.
    We include the system key here to be able to use a consistent identifier
    to query for a system and retrieve it's ID.
    """


def load_sample_connections_from_project() -> List[SampleConnection]:
    """
    Loads all the sample connection YAML files from the sample project by
    traversing through the sample_connections/ folder, inspecting each file, and
    parsing them into "ConnectionConfig" models that would be suitable for the
    `PATCH /api/v1/connection` API.

    While parsing the YAML file, this also performs ENV variable expansion,
    similar to what Docker/Bash/etc. support. This allows secrets to be provided
    as ENV var names (e.g. $FIDES_DEPLOY__CONNECTORS__POSTGRES__PASSWORD) and
    replaced with "real" values at runtime.

    After parsing the models, this function then *excludes* any connection missing
    any of it's secrets. This prevents gotchas with failing connections at runtime
    and also makes it easy to programmatically control which connections should be
    enabled by simply adding/removing the secrets to the config file.

    Returns a list of models, ready to be upserted!

    NOTE: This function does quite a bit of magic that the CLI/API/etc. don't
    support today, so it is likely to fall out of sync or break surprisingly.
    We've added extra tests that are designed to be defensive and warn us if
    something drifts.
    """
    import fides.data.sample_project  # type: ignore

    sample_connections_path = files(fides.data.sample_project).joinpath(
        "sample_connections/"
    )
    sample_connections = []
    for yaml_path in sample_connections_path.iterdir():
        with yaml_path.open("r") as file:
            # Expand ENV vars when reading the YAML, to handle secrets
            yaml_dict = load_sample_yaml_file(file, expand_vars=True)
            connections = yaml_dict.get("connection", [])
            sample_connections.extend(
                [SampleConnection.parse_obj(e) for e in connections]
            )

    # Exclude any connections whose "secrets" dict has empty values
    valid_connections = []
    for connection in sample_connections:
        # If there are no secrets at all, skip this connection
        if not connection.secrets:
            continue

        # Check if all secret values are present and non-empty
        if all(value and value != "" for value in connection.secrets.values()):  # type: ignore
            valid_connections.append(connection)

    # Exclude any invalid connections from the final results
    return valid_connections


def load_sample_yaml_file(file: TextIO, expand_vars: bool = True) -> Dict:
    yaml_str = file.read()
    if expand_vars:
        return yaml.safe_load(expandvars(yaml_str))
    return yaml.safe_load(file)
