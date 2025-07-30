# pylint: disable=protected-access
import os
from abc import ABC, abstractmethod
from typing import Dict, Iterable, List, Optional, Type
from zipfile import ZipFile

from fideslang.models import Dataset
from loguru import logger
from packaging.version import Version
from packaging.version import parse as parse_version
from sqlalchemy.orm import Session

from fides.api.api.deps import get_api_session
from fides.api.common_exceptions import ValidationError
from fides.api.cryptography.cryptographic_util import str_to_b64_str
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.custom_connector_template import CustomConnectorTemplate
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.schemas.connection_configuration.saas_config_template_values import (
    SaasConnectionTemplateValues,
)
from fides.api.schemas.saas.connector_template import ConnectorTemplate
from fides.api.schemas.saas.saas_config import SaaSConfig
from fides.api.service.authentication.authentication_strategy_oauth2_authorization_code import (
    OAuth2AuthorizationCodeAuthenticationStrategy,
)
from fides.api.util.saas_util import (
    encode_file_contents,
    load_config,
    load_config_from_string,
    load_dataset_from_string,
    load_yaml_as_string,
    replace_config_placeholders,
    replace_dataset_placeholders,
    replace_version,
)
from fides.api.util.unsafe_file_util import verify_svg, verify_zip


class ConnectorTemplateLoader(ABC):
    _instance: Optional["ConnectorTemplateLoader"] = None

    def __new__(cls: Type["ConnectorTemplateLoader"]) -> "ConnectorTemplateLoader":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._templates = {}  # type: ignore[attr-defined]
            cls._instance._load_connector_templates()
        return cls._instance

    @classmethod
    def get_connector_templates(cls) -> Dict[str, ConnectorTemplate]:
        """Returns a map of connection templates."""
        return cls()._instance._templates  # type: ignore[attr-defined, union-attr]

    @abstractmethod
    def _load_connector_templates(self) -> None:
        """Load connector templates into the _templates dictionary"""


class FileConnectorTemplateLoader(ConnectorTemplateLoader):
    """
    Loads SaaS connector templates from the data/saas directory.
    """

    def _load_connector_templates(self) -> None:
        logger.info("Loading connectors templates from the data/saas directory")
        for file in os.listdir("data/saas/config"):
            if file.endswith(".yml"):
                config_path = os.path.join("data/saas/config", file)
                config = SaaSConfig(**load_config(config_path))

                connector_type = config.type

                authentication = config.client_config.authentication
                authorization_required = (
                    authentication is not None
                    and authentication.strategy
                    == OAuth2AuthorizationCodeAuthenticationStrategy.name
                )

                try:
                    icon = encode_file_contents(f"data/saas/icon/{connector_type}.svg")
                except FileNotFoundError:
                    logger.debug(
                        f"Could not find the expected {connector_type}.svg in the data/saas/icon/ directory, using default icon"
                    )
                    icon = encode_file_contents("data/saas/icon/default.svg")

                # store connector template for retrieval
                try:
                    FileConnectorTemplateLoader.get_connector_templates()[
                        connector_type
                    ] = ConnectorTemplate(
                        config=load_yaml_as_string(config_path),
                        dataset=load_yaml_as_string(
                            f"data/saas/dataset/{connector_type}_dataset.yml"
                        ),
                        icon=icon,
                        human_readable=config.name,
                        authorization_required=authorization_required,
                        user_guide=config.user_guide,
                        supported_actions=config.supported_actions,
                    )
                except Exception:
                    logger.exception("Unable to load {} connector", connector_type)


class CustomConnectorTemplateLoader(ConnectorTemplateLoader):
    """
    Loads custom connector templates defined in the custom_connector_template database table.
    """

    def _load_connector_templates(self) -> None:
        logger.info("Loading connectors templates from the database.")
        db = get_api_session()
        for template in CustomConnectorTemplate.all(db=db):
            if (
                template.replaceable
                and CustomConnectorTemplateLoader._replacement_available(template)
            ):
                logger.info(
                    f"Replacing {template.key} connector template with newer version."
                )
                template.delete(db=db)
                continue
            try:
                CustomConnectorTemplateLoader._register_template(template)
            except Exception:
                logger.exception("Unable to load {} connector", template.key)

    @staticmethod
    def _replacement_available(template: CustomConnectorTemplate) -> bool:
        """
        Check the connector templates in the FileConnectorTemplateLoader and return if a newer version is available.
        """
        replacement_connector = (
            FileConnectorTemplateLoader.get_connector_templates().get(template.key)
        )
        if not replacement_connector:
            return False

        custom_saas_config = SaaSConfig(**load_config_from_string(template.config))
        replacement_saas_config = SaaSConfig(
            **load_config_from_string(replacement_connector.config)
        )
        return parse_version(replacement_saas_config.version) > parse_version(
            custom_saas_config.version
        )

    @classmethod
    def _register_template(
        cls,
        template: CustomConnectorTemplate,
    ) -> None:
        """
        Registers a custom connector template by converting it to a ConnectorTemplate
        and adding it to the loader's template dictionary.
        """

        config = SaaSConfig(**load_config_from_string(template.config))
        authentication = config.client_config.authentication
        authorization_required = (
            authentication is not None
            and authentication.strategy
            == OAuth2AuthorizationCodeAuthenticationStrategy.name
        )

        connector_template = ConnectorTemplate(
            config=template.config,
            dataset=template.dataset,
            icon=template.icon,
            human_readable=template.name,
            authorization_required=authorization_required,
            user_guide=config.user_guide,
            supported_actions=config.supported_actions,
        )

        # register the template in the loader's template dictionary
        CustomConnectorTemplateLoader.get_connector_templates()[
            template.key
        ] = connector_template

    # pylint: disable=too-many-branches
    @classmethod
    def save_template(cls, db: Session, zip_file: ZipFile) -> None:
        """
        Extracts and validates the contents of a zip file containing a
        custom connector template, registers the template, and saves it to the database.
        """

        # verify the zip file before we use it
        verify_zip(zip_file)

        config_contents = None
        dataset_contents = None
        icon_contents = None
        function_contents = None

        for info in zip_file.infolist():
            try:
                file_contents = zip_file.read(info).decode()
            except UnicodeDecodeError:
                # skip any hidden metadata files that can't be decoded with UTF-8
                logger.debug(f"Unable to decode the file: {info.filename}")
                continue

            if info.filename.endswith("config.yml"):
                if not config_contents:
                    config_contents = file_contents
                else:
                    raise ValidationError(
                        "Multiple files ending with config.yml found, only one is allowed."
                    )
            elif info.filename.endswith("dataset.yml"):
                if not dataset_contents:
                    dataset_contents = file_contents
                else:
                    raise ValidationError(
                        "Multiple files ending with dataset.yml found, only one is allowed."
                    )
            elif info.filename.endswith(".svg"):
                if not icon_contents:
                    verify_svg(file_contents)
                    icon_contents = str_to_b64_str(file_contents)
                else:
                    raise ValidationError(
                        "Multiple svg files found, only one is allowed."
                    )

        if not config_contents:
            raise ValidationError("Zip file does not contain a config.yml file.")

        if not dataset_contents:
            raise ValidationError("Zip file does not contain a dataset.yml file.")

        # early validation of SaaS config and dataset
        saas_config = SaaSConfig(**load_config_from_string(config_contents))
        Dataset(**load_dataset_from_string(dataset_contents))

        # extract connector_type, human_readable, and replaceable values from the SaaS config
        connector_type = saas_config.type
        human_readable = saas_config.name
        replaceable = saas_config.replaceable

        # if the incoming connector is flagged as replaceable we will update the version to match
        # that of the existing connector template this way the custom connector template can be
        # removed once a newer version is bundled with Fides
        if replaceable:
            existing_connector = (
                FileConnectorTemplateLoader.get_connector_templates().get(
                    connector_type
                )
            )
            if existing_connector:
                existing_config = SaaSConfig(
                    **load_config_from_string(existing_connector.config)
                )
                config_contents = replace_version(
                    config_contents, existing_config.version
                )

        template = CustomConnectorTemplate(
            key=connector_type,
            name=human_readable,
            config=config_contents,
            dataset=dataset_contents,
            icon=icon_contents,
            replaceable=replaceable,
        )

        # attempt to register the template, raises an exception if validation fails
        CustomConnectorTemplateLoader._register_template(template)

        # save the custom connector to the database if it passed validation
        CustomConnectorTemplate.create_or_update(
            db=db,
            data={
                "key": connector_type,
                "name": human_readable,
                "config": config_contents,
                "dataset": dataset_contents,
                "icon": icon_contents,
                "functions": function_contents,
                "replaceable": replaceable,
            },
        )


class ConnectorRegistry:
    @classmethod
    def _get_combined_templates(cls) -> Dict[str, ConnectorTemplate]:
        """
        Returns a combined map of connector templates from all registered loaders.
        The resulting map is an aggregation of templates from the file loader and the custom loader,
        with custom loader templates taking precedence in case of conflicts.
        """
        return {
            **FileConnectorTemplateLoader.get_connector_templates(),  # type: ignore
            **CustomConnectorTemplateLoader.get_connector_templates(),  # type: ignore
        }

    @classmethod
    def connector_types(cls) -> List[str]:
        """List of registered SaaS connector types"""
        return list(cls._get_combined_templates().keys())

    @classmethod
    def get_connector_template(cls, connector_type: str) -> Optional[ConnectorTemplate]:
        """
        Returns an object containing the various SaaS connector artifacts
        """
        return cls._get_combined_templates().get(connector_type)


def create_connection_config_from_template_no_save(
    db: Session,
    template: ConnectorTemplate,
    template_values: SaasConnectionTemplateValues,
    system_id: Optional[str] = None,
) -> ConnectionConfig:
    """Creates a SaaS connection config from a template without saving it."""
    # Load SaaS config from template and replace every instance of "<instance_fides_key>" with the fides_key
    # the user has chosen
    config_from_template: Dict = replace_config_placeholders(
        template.config, "<instance_fides_key>", template_values.instance_key
    )

    data = template_values.generate_config_data_from_template(
        config_from_template=config_from_template
    )

    if system_id:
        data["system_id"] = system_id

    # Create SaaS ConnectionConfig
    connection_config = ConnectionConfig.create_without_saving(db, data=data)

    return connection_config


def merge_dataset_dicts(
    existing_dataset: Dict,
    template_dataset: Dict,
    preserved_properties: Optional[List[str]] = None,
) -> Dict:
    """
    Merges an existing dataset with a template dataset, preserving specific properties
    from the existing dataset while adopting the structure and other properties from the template.

    Args:
        existing_dataset: The current dataset configuration
        template_dataset: The new template dataset configuration
        preserved_properties: List of properties to preserve from existing dataset. Defaults to ['data_categories'] but can be extended.

    Returns:
        A merged dataset with template structure and preserved properties from existing dataset
    """
    if preserved_properties is None:
        preserved_properties = ["data_categories"]

    # Start with the template dataset as the base (adopts new structure)
    merged_dataset = template_dataset.copy()

    def merge_collections(
        existing_collections: List[Dict], template_collections: List[Dict]
    ) -> List[Dict]:
        """Merge collections, preserving specified properties from existing collections."""
        # Create a mapping of existing collections by name for fast lookup
        existing_collections_map = {
            coll.get("name"): coll for coll in existing_collections
        }

        merged_collections = []
        for template_coll in template_collections:
            template_coll_name = template_coll.get("name")
            existing_coll = existing_collections_map.get(template_coll_name)

            if existing_coll:
                # Collection exists - merge it
                merged_coll = template_coll.copy()

                # Preserve collection-level properties
                for prop in preserved_properties:
                    if prop in existing_coll:
                        merged_coll[prop] = existing_coll[prop]

                # Merge fields if they exist
                if "fields" in template_coll and "fields" in existing_coll:
                    merged_coll["fields"] = merge_fields(
                        existing_coll["fields"], template_coll["fields"]
                    )

                merged_collections.append(merged_coll)
            else:
                # New collection from template - keep as is
                merged_collections.append(template_coll)

        return merged_collections

    def merge_fields(
        existing_fields: List[Dict], template_fields: List[Dict]
    ) -> List[Dict]:
        """Merge fields, preserving specified properties from existing fields."""
        # Create a mapping of existing fields by name for fast lookup
        existing_fields_map = {field.get("name"): field for field in existing_fields}

        merged_fields = []
        for template_field in template_fields:
            template_field_name = template_field.get("name")
            existing_field = existing_fields_map.get(template_field_name)

            if existing_field:
                # Field exists - merge it
                merged_field = template_field.copy()

                # Preserve field-level properties
                for prop in preserved_properties:
                    if prop in existing_field:
                        merged_field[prop] = existing_field[prop]

                # Preserve fides_meta properties
                if (
                    "fides_meta" in existing_field
                    and existing_field["fides_meta"] is not None
                ):
                    if "fides_meta" not in merged_field:
                        merged_field["fides_meta"] = {}

                    for prop in preserved_properties:
                        if prop in existing_field["fides_meta"]:
                            merged_field["fides_meta"][prop] = existing_field[
                                "fides_meta"
                            ][prop]

                # Handle nested fields recursively
                if "fields" in template_field and "fields" in existing_field:
                    merged_field["fields"] = merge_fields(
                        existing_field["fields"], template_field["fields"]
                    )

                merged_fields.append(merged_field)
            else:
                # New field from template - keep as is
                merged_fields.append(template_field)

        return merged_fields

    # Merge the collections
    if "collections" in existing_dataset and "collections" in template_dataset:
        merged_dataset["collections"] = merge_collections(
            existing_dataset["collections"], template_dataset["collections"]
        )

    return merged_dataset


def upsert_dataset_config_from_template(
    db: Session,
    connection_config: ConnectionConfig,
    template: ConnectorTemplate,
    template_values: SaasConnectionTemplateValues,
) -> DatasetConfig:
    """
    Creates a `DatasetConfig` from a template
    and associates it with a ConnectionConfig.
    If the `DatasetConfig` already exists in the db,
    then the existing record is updated.
    """
    # Load the dataset config from template and replace every instance of "<instance_fides_key>" with the fides_key
    # the user has chosen
    dataset_from_template: Dict = replace_dataset_placeholders(
        template.dataset, "<instance_fides_key>", template_values.instance_key
    )

    # Check if there's an existing dataset to merge with
    existing_dataset_config = DatasetConfig.filter(
        db=db,
        conditions=(
            (DatasetConfig.connection_config_id == connection_config.id)
            & (DatasetConfig.fides_key == template_values.instance_key)
        ),
    ).first()

    final_dataset = dataset_from_template
    if existing_dataset_config and existing_dataset_config.ctl_dataset:
        # Get the existing dataset structure
        # Convert SQLAlchemy model to dict for merging
        ctl_dataset = existing_dataset_config.ctl_dataset
        existing_dataset = {
            "fides_key": ctl_dataset.fides_key,
            "name": ctl_dataset.name,
            "description": ctl_dataset.description,
            "data_categories": ctl_dataset.data_categories,
            "collections": ctl_dataset.collections,
            "fides_meta": ctl_dataset.fides_meta,
        }
        # Merge datasets, preserving data_categories from existing dataset
        final_dataset = merge_dataset_dicts(existing_dataset, dataset_from_template)

    data = {
        "connection_config_id": connection_config.id,
        "fides_key": template_values.instance_key,
        "dataset": final_dataset,  # Use merged dataset that preserves data_categories
    }
    dataset_config = DatasetConfig.create_or_update(db, data=data)
    return dataset_config


def update_saas_configs(db: Session) -> None:
    """
    Updates SaaS config instances currently in the DB if to the
    corresponding template in the registry are found.

    Effectively an "update script" for SaaS config instances,
    to be run on server bootstrap.
    """
    for connector_type in ConnectorRegistry.connector_types():
        logger.debug(
            "Determining if any updates are needed for connectors of type {} based on templates...",
            connector_type,
        )
        template: ConnectorTemplate = ConnectorRegistry.get_connector_template(  # type: ignore
            connector_type
        )
        saas_config = SaaSConfig(**load_config_from_string(template.config))
        template_version: Version = parse_version(saas_config.version)

        connection_configs: Iterable[ConnectionConfig] = ConnectionConfig.filter(
            db=db,
            conditions=(ConnectionConfig.saas_config["type"].astext == connector_type),
        ).all()
        for connection_config in connection_configs:
            saas_config_instance = SaaSConfig.model_validate(
                connection_config.saas_config
            )
            if parse_version(saas_config_instance.version) < template_version:
                logger.info(
                    "Updating SaaS config instance '{}' of type '{}' as its version, {}, was found to be lower than the template version {}",
                    saas_config_instance.fides_key,
                    connector_type,
                    saas_config_instance.version,
                    template_version,
                )
                try:
                    update_saas_instance(
                        db,
                        connection_config,
                        template,
                        saas_config_instance,
                    )
                except Exception:
                    logger.exception(
                        "Encountered error attempting to update SaaS config instance {}",
                        saas_config_instance.fides_key,
                    )


def update_saas_instance(
    db: Session,
    connection_config: ConnectionConfig,
    template: ConnectorTemplate,
    saas_config_instance: SaaSConfig,
) -> None:
    """
    Replace in the DB the existing SaaS instance configuration data
    (SaaSConfig, DatasetConfig) associated with the given ConnectionConfig
    with new instance configuration data based on the given ConnectorTemplate
    """
    template_vals = SaasConnectionTemplateValues(
        name=connection_config.name,
        key=connection_config.key,
        description=connection_config.description,
        secrets=connection_config.secrets,
        instance_key=saas_config_instance.fides_key,
    )

    config_from_template: Dict = replace_config_placeholders(
        template.config, "<instance_fides_key>", template_vals.instance_key
    )

    connection_config.update_saas_config(db, SaaSConfig(**config_from_template))

    upsert_dataset_config_from_template(db, connection_config, template, template_vals)
