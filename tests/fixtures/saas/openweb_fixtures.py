from typing import Any, Dict, Generator
import requests
import pydash
import pytest
import random
import string

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("openweb")


@pytest.fixture(scope="session")
def openweb_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "openweb.domain")
        or secrets["domain"],
        "api_key": pydash.get(saas_config, "openweb.api_key")
        or secrets["api_key"],
        "x_spot_id": pydash.get(saas_config, "openweb.x_spot_id")
        or secrets["x_spot_id"],
        # add the rest of your secrets here
    }


# @pytest.fixture(scope="session")
# def openweb_identity_email(saas_config) -> str:
#     return (
#         pydash.get(saas_config, "openweb.identity_email") or secrets["identity_email"]
#     )


@pytest.fixture
def openweb_erasure_identity_email() -> str:
    return generate_random_email()
'''
we do need a means of creating a random 'primay_key' and using that for the erasure request. THere is a difference in how the endpoint responds when sent an invalid (or already used) primary_key. A saved example of each is in postman
@pytest.fixture
def openweb_external_references() -> Dict[str, Any]:
    return {"primary_key": "deletemetestwds"}
'''
@pytest.fixture
def openweb_erasure_external_references() -> Dict[str, Any]:
    random_pkv = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16))
    return {"primary_key": random_pkv}

@pytest.fixture
def openweb_create_erasure_data(
    openweb_erasure_external_references,
    openweb_secrets
    ) -> Generator:
    '''
    Create the data needed for erasure tests here

    In this case we need to ensure that a user exists that can be deleted. We also need to ensure we reference the user we used here for the delete request as well
    '''
    base_url = f"https://{openweb_secrets['domain']}"
    spot_id_val = {openweb_secrets['x_spot_id']}  

    headers = {
        'x-spotim-sso-access-token': openweb_secrets['api_key']
    }
    random_pkv = openweb_erasure_external_references["primary_key"]
    # random_pkv = str(random_pkv)
    # base_url = str(base_url)
    spot_id_val = str(spot_id_val)

    totalurl = base_url + "/api/sso/v1/user?primary_key=" + random_pkv + "&spot_id=" + spot_id_val + "&username=" + random_pkv
    
    
    ## "https://www.spot.im/api/sso/v1/user?primary_key=88deletemetest&spot_id=sp_XJw6mJCV&user_name=88deletemetest"

    create_user_response = requests.request("POST", totalurl, headers=headers)
    print(create_user_response)
    assert create_user_response.status_code == 200
    '''
    # example to follow 
    # create__response = requests.post(
    #     url=f"{base_url}/rest/api/v1.3/lists/{openweb_secrets['test_list']}/members", json=member_body, headers=headers
    # )
    assert create_user_response.ok
    # member_riid = create_member_response.json()['recordData']['records'][0]

    # I'm not sure I need to return anything in this case?
   # yield random_pkv
    '''

@pytest.fixture
def openweb_runner(
    db,
    cache,
    openweb_secrets,
    #openweb_external_references,
    openweb_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "openweb",
        openweb_secrets,
        # external_references=openweb_external_references,
        erasure_external_references=openweb_erasure_external_references,
    )