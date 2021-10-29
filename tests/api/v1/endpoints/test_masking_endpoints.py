import json

from starlette.testclient import TestClient

from fidesops.api.v1.urn_registry import MASKING, MASKING_STRATEGY, V1_URL_PREFIX
from fidesops.service.masking.strategy.masking_strategy_aes_encrypt import AES_ENCRYPT
from fidesops.service.masking.strategy.masking_strategy_hash import HASH
from fidesops.service.masking.strategy.masking_strategy_hmac import HMAC
from fidesops.service.masking.strategy.masking_strategy_nullify import NULL_REWRITE
from fidesops.service.masking.strategy.masking_strategy_random_string_rewrite import (
    RANDOM_STRING_REWRITE,
)
from fidesops.service.masking.strategy.masking_strategy_string_rewrite import (
    STRING_REWRITE,
)
from fidesops.schemas.masking.masking_response import MaskingAPIResponse
from fidesops.service.masking.strategy.masking_strategy_factory import get_strategies


class TestGetMaskingStrategies:
    def test_read_strategies(self, api_client: TestClient):
        expected_response = []
        for strategy in get_strategies():
            expected_response.append(strategy.get_description())

        response = api_client.get(V1_URL_PREFIX + MASKING_STRATEGY)
        response_body = json.loads(response.text)

        assert 200 == response.status_code
        assert expected_response == response_body


class TestMaskValues:
    def test_mask_value_string_rewrite(self, api_client: TestClient):
        value = "check"
        rewrite_val = "mate"
        masking_strategy = {
            "strategy": STRING_REWRITE,
            "configuration": {"rewrite_value": rewrite_val},
        }
        expected_response = MaskingAPIResponse(plain=value, masked_value=rewrite_val)

        response = api_client.put(
            f"{V1_URL_PREFIX}{MASKING}?value={value}", json=masking_strategy
        )

        assert 200 == response.status_code
        assert expected_response == json.loads(response.text)

    def test_mask_value_random_string_rewrite(self, api_client: TestClient):
        value = "my email"
        length = 20

        masking_strategy = {
            "strategy": RANDOM_STRING_REWRITE,
            "configuration": {"length": length},
        }
        response = api_client.put(
            f"{V1_URL_PREFIX}{MASKING}?value={value}", json=masking_strategy
        )
        assert 200 == response.status_code
        json_response = json.loads(response.text)
        assert value == json_response["plain"]
        assert length == len(json_response["masked_value"])

    def test_mask_value_hmac(self, api_client: TestClient):
        value = "867-5309"
        hmac_key = "my_super_secret_key"
        masking_strategy = {
            "strategy": HMAC,
            "configuration": {"hmac_key": hmac_key},
        }
        response = api_client.put(
            f"{V1_URL_PREFIX}{MASKING}?value={value}", json=masking_strategy
        )
        assert 200 == response.status_code
        json_response = json.loads(response.text)
        assert value == json_response["plain"]
        assert (
            "bf4f5048cc2daf518311f55154dd68c372cf41304e3c439cba62e99fde57333c"
            == json_response["masked_value"]
        )

    def test_mask_value_hash(self, api_client: TestClient):
        value = "867-5309"
        salt = "my_test_salt"
        masking_strategy = {
            "strategy": HASH,
            "configuration": {"salt": salt},
        }
        response = api_client.put(
            f"{V1_URL_PREFIX}{MASKING}?value={value}", json=masking_strategy
        )
        assert 200 == response.status_code
        json_response = json.loads(response.text)
        assert value == json_response["plain"]
        assert (
            "c67e2f74843b247b72aae44b6d28bc63ead8bc1f125a4074be2c49941772c142"
            == json_response["masked_value"]
        )

    def test_mask_value_aes_encrypt(self, api_client: TestClient):
        value = "last name"
        masking_strategy = {
            "strategy": AES_ENCRYPT,
            "configuration": {
                "mode": "GCM",
                "key": "4838f838d9g939f9",
                "nonce": "939f929dajr2",
            },
        }
        response = api_client.put(
            f"{V1_URL_PREFIX}{MASKING}?value={value}", json=masking_strategy
        )
        assert 200 == response.status_code
        json_response = json.loads(response.text)
        assert value == json_response["plain"]
        assert "nG0BmcgF2VTqn36mNxdW/uMixR/Zz002EA==" == json_response["masked_value"]

    def test_mask_value_no_such_strategy(self, api_client: TestClient):
        value = "check"
        rewrite_val = "mate"
        masking_strategy = {
            "strategy": "No Such Strategy",
            "configuration": {"rewrite_value": rewrite_val},
        }

        response = api_client.put(
            f"{V1_URL_PREFIX}{MASKING}?value={value}", json=masking_strategy
        )

        assert 404 == response.status_code

    def test_mask_value_invalid_config(self, api_client: TestClient):
        value = "check"
        masking_strategy = {
            "strategy": STRING_REWRITE,
            "configuration": {"wrong": "config"},
        }

        response = api_client.put(
            f"{V1_URL_PREFIX}{MASKING}?value={value}", json=masking_strategy
        )

        assert 400 == response.status_code

    def test_mask_value_aes_invalid_key_len(self, api_client: TestClient):
        value = "check"
        masking_strategy = {
            "strategy": AES_ENCRYPT,
            "configuration": {
                "mode": "GCM",
                "key": "shortkey",
                "nonce": "939f929dajr2",
            },
        }

        response = api_client.put(
            f"{V1_URL_PREFIX}{MASKING}?value={value}", json=masking_strategy
        )
        assert 400 == response.status_code
        assert (
            "Encryption key must be 16 bytes long"
            == json.loads(response.text)["detail"]
        )

    def test_masking_value_null(self, api_client: TestClient):
        value = "my_email"

        masking_strategy = {
            "strategy": NULL_REWRITE,
            "configuration": {},
        }
        response = api_client.put(
            f"{V1_URL_PREFIX}{MASKING}?value=my_email", json=masking_strategy
        )
        assert 200 == response.status_code
        json_response = json.loads(response.text)
        assert value == json_response["plain"]
        assert json_response["masked_value"] is None
