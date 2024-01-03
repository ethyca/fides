"""
This script is designed to help with testing the Data Migration script
for moving users to Fideslang 2.0, found in Fides release 2.20

The steps to run the script are as follows:
1. In a terminal, run `nox -s teardown -- volumes ; nox -s dev` to get the server running
2. In a separate terminal, run `nox -s shell`, and then `fides user login ; fides push`
3. You can run `python scripts/verify_fideslang_2_data_migration.py -h` to understand how to invoke script
"""
import argparse
import json
from functools import partial
from typing import Dict

import fideslang
import requests
from alembic import command

from fides.api.db.database import get_alembic_config
from fides.api.schemas.privacy_notice import PrivacyNoticeCreation, PrivacyNoticeRegion
from fides.config import CONFIG
from fides.core.api_helpers import get_server_resource
from fides.core.push import push
from fides.core.utils import get_db_engine

DATABASE_URL = CONFIG.database.sync_database_uri
AUTH_HEADER = CONFIG.user.auth_header
SERVER_URL = CONFIG.cli.server_url
DOWN_REVISION = "708a780b01ba"
PRIVACY_NOTICE_ID = ""  # Guido forgive me, this gets mutated later
CONSENT_REQUEST_ID = ""  # Guido forgive me, this gets mutated later
CONSENT_CODE = "1234"

data_category_upgrades: Dict[str, str] = {
    "user.financial.account_number": "user.financial.bank_account",
    "user.credentials": "user.authorization.credentials",
    "user.browsing_history": "user.behavior.browsing_history",
    "user.media_consumption": "user.behavior.media_consumption",
    "user.search_history": "user.behavior.search_history",
    "user.organization": "user.contact.organization",
    "user.non_specific_age": "user.demographic.age_range",
    "user.date_of_birth": "user.demographic.date_of_birth",
    "user.gender": "user.demographic.gender",
    "user.political_opinion": "user.demographic.political_opinion",
    "user.profiling": "user.demographic.profile",
    "user.race": "user.demographic.race_ethnicity",
    "user.religious_belief": "user.demographic.religious_belief",
    "user.sexual_orientation": "user.demographic.sexual_orientation",
    "user.genetic": "user.health_and_medical.genetic",
    "user.observed": "user.behavior",
}

print(f"Using Server URL: {SERVER_URL}")

assert (
    fideslang.__version__.split(".")[0] == "2"
), "Must have at least Fideslang version 2!"

# Test updating Datasets, including deeply nested ones
old_dataset = fideslang.models.Dataset(
    fides_key="old_dataset",
    data_categories=["user.observed"],  # new key = user.behavior
    collections=[
        fideslang.models.DatasetCollection(
            name="old_dataset_collection",
            data_categories=["user.observed"],  # new key = user.behavior
            fields=[
                fideslang.models.DatasetField(
                    name="old_dataset_field",
                    data_categories=["user.observed"],  # new key = user.behavior
                    fields=None,
                )
            ],
        )
    ],
)

# Test Privacy Declarations and Egress/Ingress updates
old_system = fideslang.models.System(
    fides_key="old_system",
    system_type="service",
    privacy_declarations=[
        fideslang.models.PrivacyDeclaration(
            name="old_privacy_declaration_1",
            data_categories=["user.observed"],  # new key = user.behavior
            data_subjects=["employee"],
            data_use="improve.system",  # new key = functional.service.improve
            shared_categories=["user.observed"],  # new key = user.behavior
        ),
    ],
    ingress=[
        fideslang.models.DataFlow(
            fides_key="privacy_annotations",
            type="system",
            data_categories=["user.observed"],  # new key = user.behavior
        ),
        fideslang.models.DataFlow(fides_key="test_key", type="system"),
    ],
    egress=[
        fideslang.models.DataFlow(
            type="system",
            fides_key="privacy_annotations",
            data_categories=["user.observed"],  # new key = user.behavior
        )
    ],
    dataset_references=["old_dataset"],
)

# This needs to exist for testing, since we can't switch back and
# forth between fideslang versions on the fly in a test script
fideslang_1_category = fideslang.models.DataCategory(
    fides_key="user.observed", parent_key="user"
)
# This needs to exist for testing, since we can't switch back and
# forth between fideslang versions on the fly in a test script
fideslang_1_use = fideslang.models.DataUse(
    fides_key="improve.system", parent_key="improve"
)

# This is used to test what happens to Taxonomy items that extended off of now-updated default items
orphaned_data_category = fideslang.models.DataCategory(
    fides_key="user.observed.custom", parent_key="user.observed"
)

# This is used to test Privacy Notices
old_notice = PrivacyNoticeCreation(
    name="old_notice",
    data_uses=["improve.system"],
    regions=[PrivacyNoticeRegion("lu")],
    consent_mechanism="opt_in",
    displayed_in_overlay=True,
    enforcement_level="system_wide",
)

# This is used to test updating Policy Rules
old_policy = fideslang.models.Policy(
    fides_key="old_policy",
    rules=[
        fideslang.models.PolicyRule(
            name="old_policy_rule",
            data_subjects=fideslang.models.PrivacyRule(
                matches=fideslang.models.MatchesEnum.ALL, values=["employee"]
            ),
            data_uses=fideslang.models.PrivacyRule(
                matches=fideslang.models.MatchesEnum.ALL,
                values=["improve.system"],  # new key = function.service.improve
            ),
            data_categories=fideslang.models.PrivacyRule(
                matches=fideslang.models.MatchesEnum.ALL,
                values=["user.observed"],  # new key = user.behavior
            ),
        )
    ],
)


def reload_objects() -> None:
    """
    Good luck :D

    Downgrades the database to the previous migration,
    loads the "outdated" objects into the database, and then
    migrates back up to 'head'
    """
    alembic_config = get_alembic_config(DATABASE_URL)

    print(f"> Rolling back one migration to: {DOWN_REVISION}")
    command.downgrade(alembic_config, DOWN_REVISION)

    print("> Seeding the database with 'outdated' Taxonomy objects")
    create_outdated_objects()

    print("Upgrading database to migration revision: head")
    command.upgrade(alembic_config, "head")


def create_outdated_objects() -> None:
    """
    Make a smattering of requests to get our DB into the state
    we want for testing the migration.
    """

    # The push order is deliberate here!
    push(
        url=SERVER_URL,
        headers=AUTH_HEADER,
        taxonomy=fideslang.models.Taxonomy(
            data_category=[orphaned_data_category, fideslang_1_category],
            data_use=[fideslang_1_use],
        ),
    )
    push(
        url=SERVER_URL,
        headers=AUTH_HEADER,
        taxonomy=fideslang.models.Taxonomy(
            system=[old_system],
        ),
    )
    push(
        url=SERVER_URL,
        headers=AUTH_HEADER,
        taxonomy=fideslang.models.Taxonomy(
            dataset=[old_dataset],
            policy=[old_policy],
        ),
    )

    # Create Privacy Notice
    # response = requests.post(
    #     url=f"{SERVER_URL}/api/v1/privacy-notice",
    #     headers=AUTH_HEADER,
    #     allow_redirects=True,
    #     data=json.dumps([old_notice.dict()]),
    # )
    # assert response.ok, f"Failed to Create Privacy Notice: {response.text}"
    # global PRIVACY_NOTICE_ID  # I'm so sorry
    # PRIVACY_NOTICE_ID = response.json()[0]["id"]  # Please forgive me

    # Create a Consent Request
    # response = requests.post(
    #     url=f"{SERVER_URL}/api/v1/consent-request",
    #     allow_redirects=True,
    #     data=json.dumps({"email": "user@example.com"}),
    # )
    # global CONSENT_REQUEST_ID
    # CONSENT_REQUEST_ID = response.json()["consent_request_id"]

    # Create a Privacy Request from a Consent request?
    # response = requests.patch(
    #     url=f"{SERVER_URL}/api/v1/consent-request/{CONSENT_REQUEST_ID}/preferences",
    #     allow_redirects=True,
    #     data=json.dumps(
    #         {
    #             "code": CONSENT_CODE,
    #             "consent": [
    #                 {
    #                     "data_use": "improve.system",
    #                     "opt_in": True,
    #                     "has_gpc_flag": False,
    #                     "conflicts_with_gpc": False,
    #                 }
    #             ],
    #             "executable_options": [
    #                 {"data_use": "improve.system", "executable": True}
    #             ],
    #         }
    #     ),
    # )
    # assert response.ok, response.text


def verify_migration(server_url: str, auth_header: Dict[str, str]) -> None:
    """
    Run a battery of assertions to verify the data migration worked as intended.
    """
    partial_get = partial(get_server_resource, url=server_url, headers=auth_header)

    # Verify Dataset
    server_old_dataset: fideslang.models.Dataset = partial_get(
        resource_key="old_dataset", resource_type="dataset"
    )
    assert server_old_dataset.data_categories == [
        "user.behavior"
    ], server_old_dataset.data_categories
    assert server_old_dataset.collections[0].data_categories == ["user.behavior"]
    assert server_old_dataset.collections[0].fields[0].data_categories == [
        "user.behavior"
    ]
    print("> Verified Datasets.")

    # Verify Systems
    server_old_system: fideslang.models.System = partial_get(
        resource_key="old_system", resource_type="system"
    )
    assert server_old_system.privacy_declarations[0].data_categories == [
        "user.behavior"
    ]
    assert (
        server_old_system.privacy_declarations[0].data_use
        == "functional.service.improve"
    )
    assert server_old_system.privacy_declarations[0].shared_categories == [
        "user.behavior"
    ]
    assert server_old_system.ingress[0].data_categories == ["user.behavior"]
    assert server_old_system.egress[0].data_categories == ["user.behavior"]
    print("> Verified Systems.")

    # Verify Policies
    server_old_policy: fideslang.models.Policy = partial_get(
        resource_key="old_policy", resource_type="policy"
    )
    assert server_old_policy.rules[0].data_categories.values == ["user.behavior"]
    assert server_old_policy.rules[0].data_uses.values == ["functional.service.improve"]
    print("> Verified Policy Rules.")

    # Verify Data Category
    server_orphaned_category: fideslang.models.DataCategory = partial_get(
        resource_key="user.behavior.custom", resource_type="data_category"
    )
    assert server_orphaned_category, server_orphaned_category
    print("> Verified Data Categories.")

    # Verify Privacy Notices
    # NOTE: This only tests the `privacynotice` table explicitly because the other
    # tables appear to be carbon copies (inheritance)
    # privacy_notice_response = requests.get(
    #     url=f"{SERVER_URL}/api/v1/privacy-notice/{PRIVACY_NOTICE_ID}",
    #     headers=AUTH_HEADER,
    #     allow_redirects=True,
    # ).json()
    # assert privacy_notice_response["data_uses"] == ["functional.service.improve"]
    # print("> Verified Privacy Notices.")

    # Verify Consent
    # consent_response = requests.post(
    #     url=f"{SERVER_URL}/api/v1/consent-request/{CONSENT_REQUEST_ID}/verify",
    #     allow_redirects=True,
    #     data=json.dumps(
    #         {
    #             "code": CONSENT_CODE,
    #         }
    #     ),
    # )
    # assert (
    #     consent_response.json()["consent"][0]["data_use"]
    #     == "functional.service.improve"
    # )

    # consent_result = get_db_engine(DATABASE_URL).execute(
    #     "select id, data_use, opt_in from consent;"
    # )
    # for r in consent_result:
    #     result = r["data_use"]
    #     assert result == "functional.service.improve", result

    # privacy_request_result = get_db_engine(DATABASE_URL).execute(
    #     "select id, status, consent_preferences from privacyrequest;"
    # )
    # for r in privacy_request_result:
    #     result = r["consent_preferences"][0]["data_use"]
    #     assert result == "functional.service.improve", result

    # consent_request_result = get_db_engine(DATABASE_URL).execute(
    #     "select id, preferences, privacy_request_id from consentrequest;"
    # )
    # for r in consent_request_result:
    #     result = r["preferences"][0]["data_use"]
    #     assert result == "functional.service.improve", result
    # print("> Verified Consent.")

    # Verify Rule Target
    rule_target_result = get_db_engine(DATABASE_URL).execute(
        "select data_category from ruletarget;"
    )
    for res in rule_target_result:
        data_category = res["data_category"]
        assert data_category not in data_category_upgrades.keys()
    print("> Verified Rule Targets.")


if __name__ == "__main__":
    print("> Running Fideslang 2.0 Data Migration Test Script...")

    parser = argparse.ArgumentParser(
        description="Verify the Fideslang 2.0 Data Migrations"
    )
    parser.add_argument(
        "--reload",
        dest="reload",
        action="store_const",
        const=True,
        default=False,
        help="whether or not to redo the migrations and reload the objects",
    )

    args = parser.parse_args()
    if args.reload:
        reload_objects()

    print("> Verifying Data Migration Updates...")
    verify_migration(server_url=SERVER_URL, auth_header=AUTH_HEADER)

    print("> Data Verification Complete!")
