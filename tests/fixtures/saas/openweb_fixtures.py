from typing import Any, Dict, Generator
import requests
import pydash
import pytest
import random
import string
import time

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
    random_pkv = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(10))
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
    
    x = openweb_erasure_external_references['primary_key']
   #baseurl = "https://www.spot.im/api/sso/v1/user?primary_key="
    pkval = x
    base_url = "https://" + openweb_secrets['domain'] + "/api/sso/v1/user?primary_key="
    spot_id = "&spot_id=" + openweb_secrets['x_spot_id'] 
    un = "&user_name="+pkval
    total_url = base_url + pkval + spot_id + un
    headers_add_user = {
        'x-spotim-sso-access-token': openweb_secrets['api_key']
    }
    response_add_user = requests.request("POST", total_url, headers=headers_add_user)
    print(response_add_user.status_code)

    check_url = base_url + pkval
    headers_check_user = {
        'content-type':'application/json',
        'x-spotim-sso-access-token': openweb_secrets['api_key']
    }


    time.sleep(10)

    response_check_user = requests.request("GET", check_url, headers=headers_check_user)
    print("add user \n", total_url, "\n", "chk user \n", check_url )
    print(response_check_user.status_code)
    #base_url = f"https://{openweb_secrets['domain']}"
    #spot_id_val = {openweb_secrets['x_spot_id']}  
    # import pdb; pdb.set_trace()
    return pkval
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