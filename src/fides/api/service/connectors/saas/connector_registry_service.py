# pylint: disable=protected-access
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Type
from zipfile import ZipFile

from fideslang.models import Dataset
from loguru import logger
from packaging.version import parse as parse_version
from sqlalchemy.orm import Session

from fides.api.api.deps import get_api_session
from fides.api.common_exceptions import ValidationError
from fides.api.cryptography.cryptographic_util import str_to_b64_str
from fides.api.models.custom_connector_template import CustomConnectorTemplate
from fides.api.schemas.saas.connector_template import ConnectorTemplate
from fides.api.schemas.saas.saas_config import SaaSConfig
from fides.api.service.authentication.authentication_strategy_oauth2_authorization_code import (
    OAuth2AuthorizationCodeAuthenticationStrategy,
)
from fides.api.util.saas_util import (
    encode_file_contents,
    extract_display_info_from_config,
    load_config,
    load_config_from_string,
    load_dataset_from_string,
    load_yaml_as_string,
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

                display_info = extract_display_info_from_config(config)

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
                        **display_info,
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

        display_info = extract_display_info_from_config(config)

        connector_template = ConnectorTemplate(
            config=template.config,
            dataset=template.dataset,
            icon=template.icon,
            human_readable=template.name,
            authorization_required=authorization_required,
            user_guide=config.user_guide,
            supported_actions=config.supported_actions,
            **display_info,
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
