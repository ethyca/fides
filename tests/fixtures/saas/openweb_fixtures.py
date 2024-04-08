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

@pytest.fixture
def openweb_erasure_identity_email() -> str:
    return generate_random_email()
'''
we do need a means of creating a random 'primay_key' and using that for the erasure request. THere is a difference in how the endpoint responds when sent an invalid (or already used) primary_key. A saved example of each is in postman.
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

    In this case we need to ensure that a user exists that can be deleted. We also need to ensure we reference the user we used here for the delete request as well.
    '''
    x = openweb_erasure_external_references['primary_key']
    primary_key_val = x
    spot_id = "&spot_id=" + openweb_secrets['x_spot_id'] 
    user_name = "&user_name=" + primary_key_val
    add_user_url = "https://" + openweb_secrets['domain'] + "/api/sso/v1/user?primary_key=" + primary_key_val + spot_id + user_name
    check_user_url = "https://" + openweb_secrets['domain'] + "/api/sso/v1/user/" +  primary_key_val
    payload = {}
    headers = {
        'x-spotim-sso-access-token': openweb_secrets['api_key']
    }
    response = requests.request("POST", add_user_url, headers=headers, data=payload)
    assert response.ok
    ''' Debugging
    print(response_add_user.content, " content ")
    print(response_add_user.json(), " json ")
    print(response_add_user.text, " text ")
    print(response_add_user.url, " url")
    print("")
    #print(response_add_user.request, " request itself")
    # print(response_add_user.headers, " headers")
    print(response_add_user.status_code, " status code")
    print(" ***************************************************")
    '''
    print("add user  \n", add_user_url)
    print("check user \n", check_user_url )
    response = requests.request("GET", check_user_url, headers=headers)
    '''Debugging
    print("add user \n", total_url, "\n", "chk user \n", check_url )
    print(response_check_user.status_code, " status code")
    print(response_check_user.content, " content ")
    # print(response_check_user.json(), " json ")
    print(response_check_user.text, " text")
    print(response_check_user.url, " url")
    print("")
    print(response_check_user.request, " request itself \n")
    print(response_check_user.reason, " reason \n")
    # print(response_check_user.headers, " headers \n")
    print(" ***************************************************")
    #spot_id_val = {openweb_secrets['x_spot_id']}  
    # import pdb; pdb.set_trace()
    return pkval
    '''
    assert response.ok

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