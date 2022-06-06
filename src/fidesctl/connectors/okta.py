"""Module that adds interactions with okta"""
from typing import List, Optional

from fideslang.models import Dataset, DatasetMetadata
from okta.client import Client as OktaClient
from okta.models import Application as OktaApplication

from fidesctl.connectors.models import OktaConfig
from fidesctl.core.utils import echo_red


def get_okta_client(okta_config: Optional[OktaConfig]) -> OktaClient:
    """
    Returns an Okta client for the given okta config. Authentication can
    also be handled through environment variables that the okta python sdk support.
    """
    config_dict = okta_config.dict() if okta_config else {}
    okta_client = OktaClient(config_dict)
    return okta_client


async def list_okta_applications(okta_client: OktaClient) -> List[OktaApplication]:
    """
    Returns a list of Okta applications. Iterates through each page returned by
    the client.
    """
    applications = []
    current_applications, resp, err = await okta_client.list_applications()
    while True:
        if err:
            echo_red(f"Failed to list Okta applications: {err}")
            raise SystemExit(1)
        applications.extend(current_applications)
        if resp.has_next():
            current_applications, err = await resp.next()
        else:
            break
    return applications


def create_okta_datasets(okta_applications: List[OktaApplication]) -> List[Dataset]:
    """
    Returns a list of dataset objects given a list of Okta applications
    """
    datasets = [
        Dataset(
            fides_key=application.id,
            name=application.name,
            fidesctl_meta=DatasetMetadata(
                resource_id=application.id,
            ),
            description=f"Fides Generated Description for Okta Application: {application.label}",
            data_categories=[],
            collections=[],
        )
        for application in okta_applications
        if application.status and application.status == "ACTIVE"
    ]
    return datasets
