"""
Sample data to use for seeding the database. This are loaded & parsed from the
sample project at src/fides/data/sample_project.

See load_samples() in seed.py for usage.
"""
from importlib.resources import files
from typing import Any, Dict, List, TextIO, Union

import yaml
from expandvars import expandvars
from fideslang.models import Dataset, Organization, Policy, System

import fides.data.sample_project
from fides.api.ops.schemas.connection_configuration.connection_config import (
    CreateConnectionConfigurationWithSecrets,
)


def load_sample_resources_from_project(
    strict: bool = False,
) -> Dict[str, List[Union[Dataset, Organization, Policy, System]]]:
    """
    Loads all the sample resource YAML files from the sample project by
    traversing through the sample_resources/ folder, inspecting each file, and
    parsing them into fideslang models.

    Returns a dictionary, grouped by resource type (e.g. Dataset, System...)

    NOTE: This only implements parsing for types we _currently_ expect to use in
    the sample project. If new types are added to the project, this will quietly
    ignore them unless strict=True is provided, which throws an error. We test
    the "strict" version of this in the integration tests to ensure this code
    doesn't fall out of date.
    """
    sample_resources_path = files(fides.data.sample_project).joinpath(
        "sample_resources/"
    )
    sample_resources_dict = {
        "dataset": [],
        "organization": [],
        "policy": [],
        "system": [],
    }
    for yaml_path in sample_resources_path.iterdir():
        with yaml_path.open("r") as file:
            # TODO: expand ENV vars here, like load_sample_connectors() does?
            # ...probably not since fides push doesn't support that!
            yaml_dict = yaml.safe_load(file)

            # Parse the contents of the YAML into the respective Pydantic models
            if yaml_dict.get("dataset", []):
                datasets = [Dataset.parse_obj(e) for e in yaml_dict.get("dataset")]
                sample_resources_dict["dataset"].extend(datasets)
            elif yaml_dict.get("organization", []):
                organizations = [
                    Organization.parse_obj(e) for e in yaml_dict.get("organization")
                ]
                sample_resources_dict["organization"].extend(organizations)
            elif yaml_dict.get("policy", []):
                policies = [Policy.parse_obj(e) for e in yaml_dict.get("policy")]
                sample_resources_dict["policy"].extend(policies)
            elif yaml_dict.get("system", []):
                systems = [System.parse_obj(e) for e in yaml_dict.get("system")]
                sample_resources_dict["system"].extend(systems)
            else:
                if strict:
                    unknown_resource_keys = list(yaml_dict.keys())
                    raise NotImplementedError(
                        f"Unexpected sample resource type, keys={unknown_resource_keys}"
                    )
                # quietly ignore failures when strict=False, so we only fail during tests
    return sample_resources_dict


def load_sample_connectors_from_project() -> (
    List[CreateConnectionConfigurationWithSecrets]
):
    """
    Loads all the sample connector YAML files from the sample project by
    traversing through the sample_connectors/ folder, inspecting each file, and
    parsing them into "ConnectionConfig" models that would be suitable for the
    `PATCH /api/v1/connection` API.

    While parsing the YAML file, this also performs ENV variable expansion,
    similar to what Docker/Bash/etc. support. This allows secrets to be provided
    as ENV var names (e.g. $FIDES_DEPLOY__CONNECTORS__POSTGRES__PASSWORD) and
    replaced with "real" values at runtime.

    After parsing the models, this function then *excludes* any connector missing
    any of it's secrets. This prevents gotchas with failing connectors at runtime
    and also makes it easy to programmatically control which connectors should be
    enabled by simply adding/removing the secrets to the config file.

    Returns a list of models, ready to be upserted!

    NOTE: This function does quite a bit of magic that the CLI/API/etc. don't
    support today, so it is likely to fall out of sync or break surprisingly.
    We've added extra tests that are designed to be defensive and warn us if
    something drifts.
    """
    sample_connectors_path = files(fides.data.sample_project).joinpath(
        "sample_connectors/"
    )
    sample_connectors = []
    for yaml_path in sample_connectors_path.iterdir():
        with yaml_path.open("r") as file:
            # Expand ENV vars when reading the YAML, to handle secrets
            yaml_dict = load_sample_yaml_file(file, expand_vars=True)
            if yaml_dict.get("connector", []):
                connectors = [
                    CreateConnectionConfigurationWithSecrets.parse_obj(e)
                    for e in yaml_dict.get("connector")
                ]
                sample_connectors.extend(connectors)

    # Disable any connectors whose "secrets" dict has empty values
    for connector in sample_connectors:
        # If there are no secrets at all, disable!
        if not connector.secrets:
            connector.disabled = True
            continue

        # If any of the secret values are missing, disable!
        for key, value in connector.secrets.items():
            if not value or value == "":
                connector.disabled = True

    # Exclude any disabled connectors from the final results
    return [e for e in sample_connectors if not e.disabled]


def load_sample_yaml_file(file: TextIO, expand_vars: bool = True) -> Dict:
    yaml_str = file.read()
    if expand_vars:
        return yaml.safe_load(expandvars(yaml_str))
    else:
        return yaml.safe_load(file)
