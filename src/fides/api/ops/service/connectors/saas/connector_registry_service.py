# pylint: disable=protected-access
import os
from abc import ABC, abstractmethod
from ast import AST, AnnAssign
from operator import getitem
from typing import Any, Dict, Iterable, List, Optional, Tuple
from zipfile import ZipFile

from AccessControl.ZopeGuards import safe_builtins
from loguru import logger
from packaging.version import Version
from packaging.version import parse as parse_version
from RestrictedPython import compile_restricted
from RestrictedPython.transformer import RestrictingNodeTransformer
from sqlalchemy.orm import Session

from fides.api.ops.api.deps import get_api_session
from fides.api.ops.common_exceptions import FidesopsException, ValidationError
from fides.api.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.ops.models.custom_connector_template import CustomConnectorTemplate
from fides.api.ops.models.datasetconfig import DatasetConfig
from fides.api.ops.schemas.connection_configuration.connection_config import (
    SaasConnectionTemplateValues,
)
from fides.api.ops.schemas.saas.connector_template import ConnectorTemplate
from fides.api.ops.schemas.saas.saas_config import SaaSConfig
from fides.api.ops.util.saas_util import (
    encode_file_contents,
    load_config,
    load_config_from_string,
    load_yaml_as_string,
    replace_config_placeholders,
    replace_dataset_placeholders,
)
from fides.core.config import CONFIG
from fides.lib.cryptography.cryptographic_util import bytes_to_b64_str, str_to_b64_str


class ConnectorTemplateLoader(ABC):
    @classmethod
    @abstractmethod
    def get_connector_templates(cls) -> Dict[str, ConnectorTemplate]:
        """Returns a map of connection templates"""


class FileConnectorTemplateLoader(ConnectorTemplateLoader):
    """
    Loads SaaS connector templates from the data/saas directory.
    """

    _instance = None
    _templates: Dict[str, ConnectorTemplate] = {}

    @classmethod
    def get_instance(cls) -> "FileConnectorTemplateLoader":
        if cls._instance is None:
            logger.info("Loading connectors templates from the data/saas directory")
            cls._instance = cls()
            for file in os.listdir("data/saas/config"):
                if file.endswith(".yml"):
                    config_file = os.path.join("data/saas/config", file)
                    config_dict = load_config(config_file)
                    connector_type = config_dict["type"]
                    human_readable = config_dict["name"]

                    try:
                        icon = encode_file_contents(
                            f"data/saas/icon/{connector_type}.svg"
                        )
                    except FileNotFoundError:
                        logger.debug(
                            f"Could not find the expected {connector_type}.svg in the data/saas/icon/ directory, using default icon"
                        )
                        icon = encode_file_contents("data/saas/icon/default.svg")

                    # store connector template for retrieval
                    try:
                        cls._templates[connector_type] = ConnectorTemplate(
                            config=load_yaml_as_string(config_file),
                            dataset=load_yaml_as_string(
                                f"data/saas/dataset/{connector_type}_dataset.yml"
                            ),
                            icon=icon,
                            functions=None,
                            human_readable=human_readable,
                        )
                    except Exception:
                        logger.exception("Unable to load {} connector", connector_type)
        return cls._instance

    @classmethod
    def get_connector_templates(cls) -> Dict[str, ConnectorTemplate]:
        return cls.get_instance()._templates


class CustomConnectorTemplateLoader(ConnectorTemplateLoader):
    """
    Loads custom connector templates defined in the custom_connector_template database table.
    """

    _instance = None
    _templates: Dict[str, ConnectorTemplate] = {}

    @classmethod
    def get_instance(cls) -> "CustomConnectorTemplateLoader":
        if cls._instance is None:
            logger.info("Loading connectors templates from the database")
            cls._instance = cls()
            for template in CustomConnectorTemplate.all(db=get_api_session()):
                try:
                    cls._register_template(template)
                except Exception:
                    logger.exception("Unable to load {} connector", template.key)
        return cls._instance

    @classmethod
    def _register_template(
        cls,
        template: CustomConnectorTemplate,
    ) -> None:
        """
        Registers a custom connector template by converting it to a ConnectorTemplate,
        registering any custom functions, and adding it to the loader's template dictionary.
        """
        connector_template = ConnectorTemplate(
            config=template.config,
            dataset=template.dataset,
            icon=template.icon,
            functions=template.functions,
            human_readable=template.name,
        )

        # register custom functions if available
        if template.functions:
            register_custom_functions(template.functions)
            logger.info(
                f"Loaded functions from the custom connector template '{template.key}'"
            )

        # register the template in the loader's template dictionary
        cls.get_instance()._templates[template.key] = connector_template  # type: ignore

    @classmethod
    def save_template(cls, db: Session, zip_file: ZipFile) -> None:
        """
        Extracts and validates the contents of a zip file containing a
        custom connector template, registers the template, and saves it to the database.
        """

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
                    icon_contents = str_to_b64_str(file_contents)
                else:
                    raise ValidationError(
                        "Multiple svg files found, only one is allowed."
                    )
            elif info.filename.endswith(".py"):
                if not function_contents:
                    function_contents = file_contents
                else:
                    raise ValidationError(
                        "Multiple Python (.py) files found, only one is allowed."
                    )

        if not config_contents:
            raise ValidationError("Zip file does not contain a config.yml file.")

        if not dataset_contents:
            raise ValidationError("Zip file does not contain a dataset.yml file.")

        # extract connector_type and human_readable values from the SaaS config
        config = load_config_from_string(config_contents)
        connector_type = config["type"]
        human_readable = config["name"]

        template = CustomConnectorTemplate(
            key=connector_type,
            name=human_readable,
            config=config_contents,
            dataset=dataset_contents,
            icon=icon_contents,
            functions=function_contents,
        )

        # attempt to register the template, raises an exception if validation fails
        cls._register_template(template)

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
            },
        )

    @classmethod
    def get_connector_templates(cls) -> Dict[str, ConnectorTemplate]:
        return cls.get_instance()._templates


class ConnectorRegistry:
    _instance = None

    @classmethod
    def get_instance(cls) -> "ConnectorRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

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
    # Load saas config from template and replace every instance of "<instance_fides_key>" with the fides_key
    # the user has chosen
    config_from_template: Dict = replace_config_placeholders(
        template.config, "<instance_fides_key>", template_values.instance_key
    )

    data = {
        "name": template_values.name,
        "key": template_values.key,
        "description": template_values.description,
        "connection_type": ConnectionType.saas,
        "access": AccessLevel.write,
        "saas_config": config_from_template,
    }

    if system_id:
        data["system_id"] = system_id

    # Create SaaS ConnectionConfig
    connection_config = ConnectionConfig.create_without_saving(db, data=data)

    return connection_config


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
    data = {
        "connection_config_id": connection_config.id,
        "fides_key": template_values.instance_key,
        "dataset": dataset_from_template,  # Currently used for upserting a CTL Dataset
    }
    dataset_config = DatasetConfig.upsert_with_ctl_dataset(db, data=data)
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
            saas_config_instance = SaaSConfig.parse_obj(connection_config.saas_config)
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


def register_custom_functions(script: str) -> None:
    """
    Registers custom functions by executing the given script in a restricted environment.

    The script is compiled and executed with RestrictedPython, which is designed to reduce
    the risk of executing untrusted code. It provides a set of safe builtins to prevent
    malicious or unintended behavior.

    Args:
        script (str): The Python script containing the custom functions to be registered.

    Raises:
        FidesopsException: If allow_custom_connector_functions is disabled.
        SyntaxError: If the script contains a syntax error or uses restricted language features.
        Exception: If an exception occurs during the execution of the script.
    """

    if CONFIG.security.allow_custom_connector_functions:
        restricted_code = compile_restricted(
            script, "<string>", "exec", policy=CustomRestrictingNodeTransformer
        )
        safe_builtins["__import__"] = custom_guarded_import
        safe_builtins["_getitem_"] = getitem
        safe_builtins["staticmethod"] = staticmethod

        # pylint: disable=exec-used
        exec(
            restricted_code,
            {
                "__metaclass__": type,
                "__name__": "restricted_module",
                "__builtins__": safe_builtins,
            },
        )
    else:
        raise FidesopsException(
            message="The import of connector templates with custom functions is disabled by the 'security.allow_custom_connector_functions' setting."
        )


class CustomRestrictingNodeTransformer(RestrictingNodeTransformer):
    """
    Custom node transformer class that extends RestrictedPython's RestrictingNodeTransformer
    to allow the use of type annotations (AnnAssign) in restricted code.
    """

    def visit_AnnAssign(self, node: AnnAssign) -> AST:
        return self.node_contents_visit(node)


def custom_guarded_import(
    name: str,
    _globals: Optional[dict] = None,
    _locals: Optional[dict] = None,
    fromlist: Optional[Tuple[str, ...]] = None,
    level: int = 0,
) -> Any:
    """
    A custom import function that prevents the import of certain potentially unsafe modules.
    """
    if name in [
        "os",
        "sys",
        "subprocess",
        "shutil",
        "socket",
        "importlib",
        "tempfile",
        "glob",
    ]:
        # raising SyntaxError to be consistent with exceptions thrown from other guarded functions
        raise SyntaxError(f"Import of '{name}' module is not allowed.")
    if fromlist is None:
        fromlist = ()
    return __import__(name, _globals, _locals, fromlist, level)
