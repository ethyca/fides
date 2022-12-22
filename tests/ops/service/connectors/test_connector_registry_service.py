from typing import Callable, Dict
from unittest import mock
from unittest.mock import Mock

import yaml

from fides.api.ops.models.datasetconfig import DatasetConfig
from fides.api.ops.service.connectors.saas.connector_registry_service import (
    ConnectorTemplate,
    load_registry,
    registry_file,
    update_saas_configs,
)
from fides.api.ops.util.saas_util import load_config, load_dataset, load_yaml_as_string
from fides.core.config.helpers import load_file

NEW_CONFIG_DESCRIPTION = "new test config description"
NEW_DATASET_DESCRIPTION = "new test dataset description"
NEW_CONNECTOR_PARAM = {"name": "new_param", "default_value": "new_param_default_value"}
NEW_ENDPOINT = {
    "name": "new endpoint",
    "requests": {
        "read": {
            "method": "GET",
            "path": "/test/path",
            "param_values": [{"name": "test_param", "identity": "email"}],
        }
    },
}
NEW_FIELD = {
    "name": "new_field",
    "data_categories": ["system.operations"],
}
NEW_COLLECTION = {
    "name": "new_collection",
    "fields": [NEW_FIELD],
}


class TestConnectionRegistry:
    def test_get_connector_template(self):
        registry = load_registry(registry_file)

        assert "mailchimp" in registry.connector_types()

        assert registry.get_connector_template("bad_key") is None
        mailchimp_registry = registry.get_connector_template("mailchimp")

        assert mailchimp_registry == ConnectorTemplate(
            config="data/saas/config/mailchimp_config.yml",
            dataset="data/saas/dataset/mailchimp_dataset.yml",
            icon="data/saas/icon/mailchimp.svg",
            human_readable="Mailchimp",
        )

    @mock.patch(
        "fides.api.ops.service.connectors.saas.connector_registry_service.load_dataset_with_replacement"
    )
    @mock.patch(
        "fides.api.ops.service.connectors.saas.connector_registry_service.load_config_with_replacement"
    )
    @mock.patch(
        "fides.api.ops.service.connectors.saas.connector_registry_service.load_config"
    )
    def test_update_config_additions(
        self,
        load_config_mock_object: Mock,
        load_config_with_replacement_mock_object: Mock,
        load_dataset_with_replacement_mock_object: Mock,
        db,
        secondary_mailchimp_instance,
        tertiary_mailchimp_instance,
        secondary_sendgrid_instance,
    ):
        update_config(
            load_config_mock_object,
            load_config_mocked_additions_function,
            load_config_with_replacement_mock_object,
            load_config_with_replacement_mocked_additions_function,
            load_dataset_with_replacement_mock_object,
            load_dataset_with_replacement_mocked_additions_function,
            validate_updated_instances_additions,
            db,
            secondary_mailchimp_instance,
            tertiary_mailchimp_instance,
            secondary_sendgrid_instance,
        )

    @mock.patch(
        "fides.api.ops.service.connectors.saas.connector_registry_service.load_dataset_with_replacement"
    )
    @mock.patch(
        "fides.api.ops.service.connectors.saas.connector_registry_service.load_config_with_replacement"
    )
    @mock.patch(
        "fides.api.ops.service.connectors.saas.connector_registry_service.load_config"
    )
    def test_update_config_removals(
        self,
        load_config_mock_object: Mock,
        load_config_with_replacement_mock_object: Mock,
        load_dataset_with_replacement_mock_object: Mock,
        db,
        secondary_mailchimp_instance,
        tertiary_mailchimp_instance,
        secondary_sendgrid_instance,
    ):
        update_config(
            load_config_mock_object,
            load_config_mocked_removals_function,
            load_config_with_replacement_mock_object,
            load_config_with_replacement_mocked_removals_function,
            load_dataset_with_replacement_mock_object,
            load_dataset_with_replacement_mocked_removals_function,
            validate_updated_instances_removals,
            db,
            secondary_mailchimp_instance,
            tertiary_mailchimp_instance,
            secondary_sendgrid_instance,
        )


def update_config(
    load_config_mock_object,
    load_config_mock_function: Callable,
    load_config_with_replacement_mock_object,
    load_config_with_replacement_mock_function: Callable,
    load_dataset_with_replacement_mock_object,
    load_dataset_with_replacement_mock_function: Callable,
    validation_function: Callable,
    db,
    secondary_mailchimp_instance,
    tertiary_mailchimp_instance,
    secondary_sendgrid_instance,
):
    """
    Helper function to test config updates.

    First, load the original templates for `mailchimp` and `sendgrid`,
    and instantiate two `mailchimp` instances and one `sendgrid` instance
    by means of fixtures. We use these 3 instances to test functionality
    across multiple instances of the same type, as well as multiple types.

    Then, based on the provided mock objects and functions to override,
    "updates" are made to connector templates for `mailchimp` and `sendgrid`.
    The nature of those updates are "plugged in" via the override functions.

    Then, perform the update "script", i.e. invoke `update_saas_configs`.

    Then, confirm that the instances have been updated as expected, by
    invoking a plugged-in `validation_function`
    """
    registry = load_registry(registry_file)
    assert "mailchimp" in registry.connector_types()

    mailchimp_template_config = load_config(
        registry.get_connector_template("mailchimp").config
    )
    mailchimp_template_dataset = load_dataset(
        registry.get_connector_template("mailchimp").dataset
    )[0]
    mailchimp_version = mailchimp_template_config["version"]

    sendgrid_template_config = load_config(
        registry.get_connector_template("sendgrid").config
    )
    sendgrid_template_dataset = load_dataset(
        registry.get_connector_template("sendgrid").dataset
    )[0]
    sendgrid_version = sendgrid_template_config["version"]

    # confirm original version of template works as expected
    (
        secondary_mailchimp_config,
        secondary_mailchimp_dataset,
    ) = secondary_mailchimp_instance
    secondary_mailchimp_saas_config = secondary_mailchimp_config.saas_config
    secondary_mailchimp_dataset.ctl_dataset.description = mailchimp_template_dataset[
        "description"
    ]
    assert secondary_mailchimp_saas_config["version"] == mailchimp_version
    assert (
        secondary_mailchimp_saas_config["description"]
        == mailchimp_template_config["description"]
    )

    (
        tertiary_mailchimp_config,
        tertiary_mailchimp_dataset,
    ) = tertiary_mailchimp_instance
    tertiary_mailchimp_saas_config = tertiary_mailchimp_config.saas_config
    tertiary_mailchimp_dataset.ctl_dataset.description = mailchimp_template_dataset[
        "description"
    ]
    tertiary_mailchimp_saas_config = (
        tertiary_mailchimp_dataset.connection_config.saas_config
    )
    assert tertiary_mailchimp_saas_config["version"] == mailchimp_version
    assert (
        tertiary_mailchimp_saas_config["description"]
        == mailchimp_template_config["description"]
    )

    (
        secondary_sendgrid_config,
        secondary_sendgrid_dataset,
    ) = secondary_sendgrid_instance
    secondary_sendgrid_saas_config = secondary_sendgrid_config.saas_config
    secondary_sendgrid_dataset.ctl_dataset.description = sendgrid_template_dataset[
        "description"
    ]
    assert secondary_sendgrid_saas_config["version"] == sendgrid_version
    assert (
        secondary_sendgrid_saas_config["description"]
        == sendgrid_template_config["description"]
    )

    # mock methods within template instantiation workflow
    # to produce an updated saas config template
    # this mimics "updates" made to SaaS config and dataset templates
    # for mailchimp and sendgrid
    load_config_mock_object.side_effect = load_config_mock_function
    load_config_with_replacement_mock_object.side_effect = (
        load_config_with_replacement_mock_function
    )
    load_dataset_with_replacement_mock_object.side_effect = (
        load_dataset_with_replacement_mock_function
    )

    # run update "script"
    update_saas_configs(registry, db)

    # confirm updates applied successfully
    secondary_mailchimp_dataset: DatasetConfig = DatasetConfig.filter(
        db=db,
        conditions=DatasetConfig.fides_key == secondary_mailchimp_dataset.fides_key,
    ).first()
    validation_function(
        secondary_mailchimp_dataset,
        mailchimp_template_config,
        mailchimp_template_dataset,
        secondary_mailchimp_config.key,
        secondary_mailchimp_dataset.fides_key,
    )

    tertiary_mailchimp_dataset: DatasetConfig = DatasetConfig.filter(
        db=db,
        conditions=DatasetConfig.fides_key == tertiary_mailchimp_dataset.fides_key,
    ).first()
    validation_function(
        tertiary_mailchimp_dataset,
        mailchimp_template_config,
        mailchimp_template_dataset,
        tertiary_mailchimp_config.key,
        tertiary_mailchimp_dataset.fides_key,
    )

    secondary_sendgrid_dataset: DatasetConfig = DatasetConfig.filter(
        db=db,
        conditions=DatasetConfig.fides_key == secondary_sendgrid_dataset.fides_key,
    ).first()
    validation_function(
        secondary_sendgrid_dataset,
        sendgrid_template_config,
        sendgrid_template_dataset,
        secondary_sendgrid_config.key,
        secondary_sendgrid_dataset.fides_key,
    )

    # clean up after ourselves
    secondary_mailchimp_config.delete(db)
    tertiary_mailchimp_config.delete(db)
    secondary_sendgrid_config.delete(db)


def increment_ver(version):
    version = version.split(".")
    version[2] = str(int(version[2]) + 1)
    return ".".join(version)


### Additions helpers ###


def load_config_mocked_additions_function(filename: str) -> Dict:
    """
    Loads the saas config from the yaml file
    Mocked to make additions to mailchimp config template _only_ for testing
    """
    yaml_file = load_file([filename])
    with open(yaml_file, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file).get("saas_config", [])
        update_config_additions(config, filename)
        return config


def load_config_with_replacement_mocked_additions_function(
    filename: str, string_to_replace: str, replacement: str
) -> Dict:
    """
    Loads the saas config from the yaml file and replaces any string with the given value
    Mocked to make additions to mailchimp config template _only_ for testing
    """
    yaml_str: str = load_yaml_as_string(filename).replace(
        string_to_replace, replacement
    )
    config: Dict = yaml.safe_load(yaml_str).get("saas_config", [])
    update_config_additions(config, filename)
    return config


def update_config_additions(config: Dict, filename: str):
    if filename in (
        "data/saas/config/mailchimp_config.yml",
        "data/saas/config/sendgrid_config.yml",
    ):
        config["version"] = increment_ver(config["version"])
        config["description"] = NEW_CONFIG_DESCRIPTION
        config["connector_params"].append(NEW_CONNECTOR_PARAM)
        config["endpoints"].append(NEW_ENDPOINT)


def load_dataset_with_replacement_mocked_additions_function(
    filename: str, string_to_replace: str, replacement: str
) -> Dict:
    """
    Loads the dataset from the yaml file and replaces any string with the given value
    Mocked to make additions to mailchimp dataset template _only_ for testing
    """
    yaml_str: str = load_yaml_as_string(filename).replace(
        string_to_replace, replacement
    )
    dataset: Dict = yaml.safe_load(yaml_str).get("dataset", [])
    if filename in (
        "data/saas/dataset/mailchimp_dataset.yml",
        "data/saas/dataset/sendgrid_dataset.yml",
    ):
        dataset[0]["description"] = NEW_DATASET_DESCRIPTION
        dataset[0]["collections"][0]["fields"].append(NEW_FIELD)
        dataset[0]["collections"].append(NEW_COLLECTION)
    return dataset


def validate_updated_instances_additions(
    updated_dataset_config: DatasetConfig,
    original_template_config: Dict,
    original_template_dataset: Dict,
    key: str,
    fides_key: str,
):
    # check for dataset additions to template
    assert updated_dataset_config.ctl_dataset.description == NEW_DATASET_DESCRIPTION
    assert (
        len(updated_dataset_config.ctl_dataset.collections)
        == len(original_template_dataset["collections"]) + 1
    )
    assert NEW_COLLECTION in updated_dataset_config.ctl_dataset.collections
    assert NEW_FIELD in updated_dataset_config.ctl_dataset.collections[0]["fields"]

    # check for config additions to template
    updated_saas_config = updated_dataset_config.connection_config.saas_config
    assert updated_saas_config["version"] == increment_ver(
        original_template_config["version"]
    )
    assert updated_saas_config["description"] == NEW_CONFIG_DESCRIPTION
    assert any(
        NEW_CONNECTOR_PARAM["name"] == param["name"]
        for param in updated_saas_config["connector_params"]
    )
    assert (
        len(updated_saas_config["endpoints"])
        == len(original_template_config["endpoints"]) + 1
    )
    assert any(
        NEW_ENDPOINT["name"] == endpoint["name"]
        for endpoint in updated_saas_config["endpoints"]
    )

    assert updated_dataset_config.connection_config.key == key
    assert updated_saas_config["fides_key"] == fides_key


### Removals helpers ###


def load_config_mocked_removals_function(filename: str) -> Dict:
    """
    Loads the saas config from the yaml file
    Mocked to make removals to mailchimp config template _only_ for testing
    """
    yaml_file = load_file([filename])
    with open(yaml_file, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file).get("saas_config", [])
        update_config_removals(config, filename)
        return config


def load_config_with_replacement_mocked_removals_function(
    filename: str, string_to_replace: str, replacement: str
) -> Dict:
    """
    Loads the saas config from the yaml file and replaces any string with the given value
    Mocked to make removals to mailchimp config template _only_ for testing
    """
    yaml_str: str = load_yaml_as_string(filename).replace(
        string_to_replace, replacement
    )
    config: Dict = yaml.safe_load(yaml_str).get("saas_config", [])
    update_config_removals(config, filename)
    return config


def update_config_removals(config: Dict, filename: str):
    if filename in (
        "data/saas/config/mailchimp_config.yml",
        "data/saas/config/sendgrid_config.yml",
    ):
        config["version"] = increment_ver(config["version"])
        config["endpoints"].pop()
        config["connector_params"].pop()


def load_dataset_with_replacement_mocked_removals_function(
    filename: str, string_to_replace: str, replacement: str
) -> Dict:
    """
    Loads the dataset from the yaml file and replaces any string with the given value
    Mocked to make removals to mailchimp dataset _only_ for testing
    """
    yaml_str: str = load_yaml_as_string(filename).replace(
        string_to_replace, replacement
    )
    dataset: Dict = yaml.safe_load(yaml_str).get("dataset", [])
    if filename in (
        "data/saas/dataset/mailchimp_dataset.yml",
        "data/saas/dataset/sendgrid_dataset.yml",
    ):
        dataset[0]["collections"].pop()
    return dataset


def validate_updated_instances_removals(
    updated_dataset_config: DatasetConfig,
    original_template_config: Dict,
    original_template_dataset: Dict,
    key: str,
    fides_key: str,
):
    # check for dataset removals to template
    assert (
        len(updated_dataset_config.ctl_dataset.collections)
        == len(original_template_dataset["collections"]) - 1
    )

    # check for config removals to template
    updated_saas_config = updated_dataset_config.connection_config.saas_config
    assert (
        len(updated_saas_config["endpoints"])
        == len(original_template_config["endpoints"]) - 1
    )
    assert (
        len(updated_saas_config["connector_params"])
        == len(original_template_config["connector_params"]) - 1
    )

    assert updated_dataset_config.connection_config.key == key
    assert updated_saas_config["fides_key"] == fides_key
