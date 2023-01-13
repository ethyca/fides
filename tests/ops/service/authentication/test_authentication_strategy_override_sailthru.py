import json
from urllib.parse import parse_qsl

from requests import PreparedRequest, Request

from fides.api.ops.models.connectionconfig import ConnectionConfig
from fides.api.ops.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)

# None of these are real secrets: these are just the same values
# used in the Sailthru API docs
from fides.api.ops.util.saas_util import format_body

api_key = "123key"
secret = "abcsecret"
expected_sig = "fa5c79189b708199f3cf69f1cf8f7928"
sailthru_email = "neil@example.com"


def test_generate_sig():
    body_format = "json"
    request_json = {"id": sailthru_email}
    str_body: str = json.dumps(request_json, separators=(",", ":"))

    strategy = AuthenticationStrategy.get_strategy(
        "sailthru", {"api_key": api_key, "secret": secret}
    )

    sig = strategy.generate_sailthru_sig(secret, api_key, body_format, str_body)
    assert sig == expected_sig


def test_api_key_auth_body():
    headers, output = format_body(
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        body=json.dumps(
            {
                "id": sailthru_email,
                "optout_email": "basic",
                "sms_marketing_status": "opt-out",
            }
        ),
    )
    req: PreparedRequest = Request(
        method="POST", url="https://localhost.com", data=output
    ).prepare()

    secrets = {"api_key": api_key, "secret": secret}

    authenticated_request = AuthenticationStrategy.get_strategy(
        "sailthru", {"api_key": "<api_key>", "secret": "<secret>"}
    ).add_authentication(req, ConnectionConfig(secrets=secrets))

    request_body = dict(parse_qsl(authenticated_request.body))

    assert request_body["api_key"] == api_key
    assert request_body["sig"] == "39dceb7dc2b551f823f2568350524260"
    json_body = json.loads(request_body["json"])
    assert json_body["id"] == sailthru_email
    assert json_body["optout_email"] == "basic"
    assert json_body["sms_marketing_status"] == "opt-out"
