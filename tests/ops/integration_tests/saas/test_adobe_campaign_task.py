import random

import pytest

from fidesops.ops.core.config import config
from fidesops.ops.graph.graph import DatasetGraph
from fidesops.ops.models.privacy_request import PrivacyRequest
from fidesops.ops.schemas.redis_cache import PrivacyRequestIdentity
from fidesops.ops.service.connectors import get_connector
from fidesops.ops.task import graph_task
from fidesops.ops.task.graph_task import get_cached_data_for_erasures
from tests.ops.graph.graph_test_util import assert_rows_match


@pytest.mark.skip(reason="Only staging credentials available")
@pytest.mark.integration_saas
@pytest.mark.integration_saas
def test_adobe_campaign_connection_test(adobe_campaign_connection_config) -> None:
    get_connector(adobe_campaign_connection_config).test_connection()


@pytest.mark.skip(reason="Only staging credentials available")
@pytest.mark.integration_saas
@pytest.mark.integration_adobe_campaign
def test_adobe_campaign_access_request_task(
    policy,
    adobe_campaign_identity_email,
    adobe_campaign_connection_config,
    adobe_campaign_dataset_config,
    db,
) -> None:
    """Full access request based on the Adobe Campaign SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_adobe_campaign_access_request_task_{random.randint(0, 1000)}"
    )
    identity = PrivacyRequestIdentity(**{"email": adobe_campaign_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = adobe_campaign_connection_config.get_saas_config().fides_key
    merged_graph = adobe_campaign_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [adobe_campaign_connection_config],
        {"email": adobe_campaign_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:profile"],
        min_size=1,
        keys=[
            "PKey",
            "age",
            "birthDate",
            "blackList",
            "blackListAllLastModified",
            "blackListEmail",
            "blackListEmailLastModified",
            "blackListFax",
            "blackListFaxLastModified",
            "blackListLastModified",
            "blackListMobile",
            "blackListMobileLastModified",
            "blackListPhone",
            "blackListPhoneLastModified",
            "blackListPostalMail",
            "blackListPostalMailLastModified",
            "blackListPushnotification",
            "ccpaOptOut",
            "ccpaOptOutLastModified",
            "created",
            "cryptedId",
            "domain",
            "email",
            "emailFormat",
            "externalId",
            "fax",
            "firstName",
            "gender",
            "href",
            "isExternal",
            "lastModified",
            "lastName",
            "location",
            "middleName",
            "mobilePhone",
            "phone",
            "postalAddress",
            "preferredLanguage",
            "salutation",
            "subscriptions",
            "thumbnail",
            "timeZone",
            "title",
        ],
    )
    assert_rows_match(
        v[f"{dataset_name}:marketing_history"],
        min_size=1,
        keys=[
            "PKey",
            "age",
            "birthDate",
            "blackList",
            "blackListAllLastModified",
            "blackListEmail",
            "blackListEmailLastModified",
            "blackListFax",
            "blackListFaxLastModified",
            "blackListLastModified",
            "blackListMobile",
            "blackListMobileLastModified",
            "blackListPhone",
            "blackListPhoneLastModified",
            "blackListPostalMail",
            "blackListPostalMailLastModified",
            "ccpaOptOut",
            "ccpaOptOutLastModified",
            "countBroadLogEvents",
            "countSubHistoEvents",
            "countryIsoA2",
            "created",
            "email",
            "events",
            "externalId",
            "fax",
            "firstName",
            "gender",
            "href",
            "isExternal",
            "kpisAndChart",
            "lastModified",
            "lastName",
            "location",
            "middleName",
            "minBroadLogEvents",
            "minSubHistoEvents",
            "mobilePhone",
            "phone",
            "preferredLanguage",
            "salutation",
            "thumbnail",
            "timeZone",
            "title",
        ],
    )

    profile = v[f"{dataset_name}:profile"][0]
    assert profile["email"] == adobe_campaign_identity_email

    marketing_history = v[f"{dataset_name}:marketing_history"][0]
    assert marketing_history["email"] == adobe_campaign_identity_email


@pytest.mark.skip(reason="Only staging credentials available")
@pytest.mark.integration_saas
@pytest.mark.integration_adobe_campaign
def test_adobe_campaign_saas_erasure_request_task(
    db,
    policy,
    adobe_campaign_connection_config,
    adobe_campaign_dataset_config,
    adobe_campaign_erasure_identity_email,
    adobe_campaign_erasure_data,
) -> None:
    """Full erasure request based on the Adobe Campaign SaaS config"""
    masking_strict = config.execution.masking_strict
    config.execution.masking_strict = False  # Allow GDPR Delete

    # Create user for GDPR delete
    erasure_email = adobe_campaign_erasure_identity_email
    privacy_request = PrivacyRequest(
        id=f"test_saas_access_request_task_{random.randint(0, 1000)}"
    )
    identity = PrivacyRequestIdentity(**{"email": erasure_email})
    privacy_request.cache_identity(identity)

    dataset_name = adobe_campaign_connection_config.get_saas_config().fides_key
    merged_graph = adobe_campaign_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [adobe_campaign_connection_config],
        {"email": erasure_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:profile"],
        min_size=1,
        keys=[
            "PKey",
            "age",
            "birthDate",
            "blackList",
            "blackListAllLastModified",
            "blackListEmail",
            "blackListEmailLastModified",
            "blackListFax",
            "blackListFaxLastModified",
            "blackListLastModified",
            "blackListMobile",
            "blackListMobileLastModified",
            "blackListPhone",
            "blackListPhoneLastModified",
            "blackListPostalMail",
            "blackListPostalMailLastModified",
            "blackListPushnotification",
            "ccpaOptOut",
            "ccpaOptOutLastModified",
            "created",
            "cryptedId",
            "domain",
            "email",
            "emailFormat",
            "externalId",
            "fax",
            "firstName",
            "gender",
            "href",
            "isExternal",
            "lastModified",
            "lastName",
            "location",
            "middleName",
            "mobilePhone",
            "phone",
            "postalAddress",
            "preferredLanguage",
            "salutation",
            "subscriptions",
            "thumbnail",
            "timeZone",
            "title",
        ],
    )
    assert_rows_match(
        v[f"{dataset_name}:marketing_history"],
        min_size=1,
        keys=[
            "PKey",
            "age",
            "birthDate",
            "blackList",
            "blackListAllLastModified",
            "blackListEmail",
            "blackListEmailLastModified",
            "blackListFax",
            "blackListFaxLastModified",
            "blackListLastModified",
            "blackListMobile",
            "blackListMobileLastModified",
            "blackListPhone",
            "blackListPhoneLastModified",
            "blackListPostalMail",
            "blackListPostalMailLastModified",
            "ccpaOptOut",
            "ccpaOptOutLastModified",
            "countBroadLogEvents",
            "countSubHistoEvents",
            "countryIsoA2",
            "created",
            "email",
            "events",
            "externalId",
            "fax",
            "firstName",
            "gender",
            "href",
            "isExternal",
            "kpisAndChart",
            "lastModified",
            "lastName",
            "location",
            "middleName",
            "minBroadLogEvents",
            "minSubHistoEvents",
            "mobilePhone",
            "phone",
            "preferredLanguage",
            "salutation",
            "thumbnail",
            "timeZone",
            "title",
        ],
    )

    x = graph_task.run_erasure(
        privacy_request,
        policy,
        graph,
        [adobe_campaign_connection_config],
        {"email": erasure_email},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    # Assert erasure request made to adobe_campaign_user
    assert x == {
        "adobe_instance:profile": 1,
        "adobe_instance:marketing_history": 0,
    }

    config.execution.masking_strict = masking_strict  # Reset
