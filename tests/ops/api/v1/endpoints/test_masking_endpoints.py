import json

from starlette.testclient import TestClient

from fides.api.schemas.masking.masking_api import MaskingAPIResponse
from fides.api.schemas.masking.masking_configuration import (
    AesEncryptionMaskingConfiguration,
)
from fides.api.service.masking.strategy.masking_strategy import MaskingStrategy
from fides.api.service.masking.strategy.masking_strategy_aes_encrypt import (
    AesEncryptionMaskingStrategy,
)
from fides.api.service.masking.strategy.masking_strategy_hash import HashMaskingStrategy
from fides.api.service.masking.strategy.masking_strategy_hmac import HmacMaskingStrategy
from fides.api.service.masking.strategy.masking_strategy_nullify import (
    NullMaskingStrategy,
)
from fides.api.service.masking.strategy.masking_strategy_random_string_rewrite import (
    RandomStringRewriteMaskingStrategy,
)
from fides.api.service.masking.strategy.masking_strategy_string_rewrite import (
    StringRewriteMaskingStrategy,
)
from fides.common.api.scope_registry import MASKING_EXEC, MASKING_READ
from fides.common.api.v1.urn_registry import MASKING, MASKING_STRATEGY, V1_URL_PREFIX


class TestGetMaskingStrategies:
    def test_read_strategies(self, api_client: TestClient, generate_auth_header):
        auth_header = generate_auth_header(scopes=[MASKING_READ])
        expected_response = []
        for strategy in MaskingStrategy.get_strategies():
            expected_response.append(strategy.get_description().model_dump(mode="json"))

        response = api_client.get(V1_URL_PREFIX + MASKING_STRATEGY, headers=auth_header)
        response_body = response.json()

        assert 200 == response.status_code
        assert expected_response == response_body


class TestMaskValues:
    def test_no_strategies_specified(
        self, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[MASKING_EXEC])
        value = "my_email"
        request = {
            "values": [value],
        }

        response = api_client.put(
            f"{V1_URL_PREFIX}{MASKING}", json=request, headers=auth_header
        )
        assert 422 == response.status_code

    def test_mask_nothing(self, api_client: TestClient, generate_auth_header):
        auth_header = generate_auth_header(scopes=[MASKING_EXEC])
        request = {
            "values": None,
            "masking_strategy": {
                "strategy": StringRewriteMaskingStrategy.name,
                "configuration": {"rewrite_value": "MASKED"},
            },
        }

        response = api_client.put(
            f"{V1_URL_PREFIX}{MASKING}", json=request, headers=auth_header
        )
        assert 422 == response.status_code

    def test_mask_value_string_rewrite(
        self, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[MASKING_EXEC])
        value = "check"
        rewrite_val = "mate"
        request = {
            "values": [value],
            "masking_strategy": {
                "strategy": StringRewriteMaskingStrategy.name,
                "configuration": {"rewrite_value": rewrite_val},
            },
        }
        expected_response = MaskingAPIResponse(
            plain=[value], masked_values=[rewrite_val]
        )

        response = api_client.put(
            f"{V1_URL_PREFIX}{MASKING}", json=request, headers=auth_header
        )

        assert 200 == response.status_code
        assert expected_response.model_dump(mode="json") == response.json()

    def test_mask_value_random_string_rewrite(
        self, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[MASKING_EXEC])
        value = "my email"
        length = 20
        request = {
            "values": [value],
            "masking_strategy": {
                "strategy": RandomStringRewriteMaskingStrategy.name,
                "configuration": {"length": length},
            },
        }
        response = api_client.put(
            f"{V1_URL_PREFIX}{MASKING}", json=request, headers=auth_header
        )
        assert 200 == response.status_code
        json_response = json.loads(response.text)
        assert value == json_response["plain"][0]
        assert length == len(json_response["masked_values"][0])

    def test_mask_value_hmac(self, api_client: TestClient, generate_auth_header):
        auth_header = generate_auth_header(scopes=[MASKING_EXEC])
        value = "867-5309"
        request = {
            "values": [value],
            "masking_strategy": {
                "strategy": HmacMaskingStrategy.name,
                "configuration": {},
            },
        }
        response = api_client.put(
            f"{V1_URL_PREFIX}{MASKING}", json=request, headers=auth_header
        )
        assert 200 == response.status_code
        json_response = json.loads(response.text)
        assert value == json_response["plain"][0]
        assert json_response["masked_values"][0] != value

    def test_mask_value_hash(self, api_client: TestClient, generate_auth_header):
        auth_header = generate_auth_header(scopes=[MASKING_EXEC])
        value = "867-5309"
        request = {
            "values": [value],
            "masking_strategy": {
                "strategy": HashMaskingStrategy.name,
                "configuration": {},
            },
        }
        response = api_client.put(
            f"{V1_URL_PREFIX}{MASKING}", json=request, headers=auth_header
        )
        assert 200 == response.status_code
        json_response = json.loads(response.text)
        assert value == json_response["plain"][0]
        assert json_response["masked_values"][0] != value

    def test_mask_value_hash_multi_value(
        self, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[MASKING_EXEC])
        value = "867-5309"
        value2 = "844-5205"
        request = {
            "values": [value, value2],
            "masking_strategy": {
                "strategy": HashMaskingStrategy.name,
                "configuration": {},
            },
        }
        response = api_client.put(
            f"{V1_URL_PREFIX}{MASKING}", json=request, headers=auth_header
        )
        assert 200 == response.status_code
        json_response = json.loads(response.text)
        assert value == json_response["plain"][0]
        assert value2 == json_response["plain"][1]
        assert json_response["masked_values"][0] != value
        assert json_response["masked_values"][1] != value2

    def test_mask_value_hash_multi_value_same_value(
        self, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[MASKING_EXEC])
        value = "867-5309"
        request = {
            "values": [value, value],
            "masking_strategy": {
                "strategy": HashMaskingStrategy.name,
                "configuration": {},
            },
        }
        response = api_client.put(
            f"{V1_URL_PREFIX}{MASKING}", json=request, headers=auth_header
        )
        assert 200 == response.status_code
        json_response = json.loads(response.text)
        assert value == json_response["plain"][0]
        assert value == json_response["plain"][1]
        assert json_response["masked_values"][0] != value
        assert json_response["masked_values"][1] != value

    def test_mask_value_aes_encrypt(self, api_client: TestClient, generate_auth_header):
        auth_header = generate_auth_header(scopes=[MASKING_EXEC])
        value = "last name"
        request = {
            "values": [value],
            "masking_strategy": {
                "strategy": AesEncryptionMaskingStrategy.name,
                "configuration": {
                    "mode": AesEncryptionMaskingConfiguration.Mode.GCM.value
                },
            },
        }
        response = api_client.put(
            f"{V1_URL_PREFIX}{MASKING}", json=request, headers=auth_header
        )
        assert 200 == response.status_code
        json_response = json.loads(response.text)
        assert value == json_response["plain"][0]
        assert json_response["masked_values"][0] != value

    def test_mask_value_no_such_strategy(
        self, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[MASKING_EXEC])
        value = "check"
        rewrite_val = "mate"
        request = {
            "values": [value],
            "masking_strategy": {
                "strategy": "No Such Strategy",
                "configuration": {"rewrite_value": rewrite_val},
            },
        }

        response = api_client.put(
            f"{V1_URL_PREFIX}{MASKING}", json=request, headers=auth_header
        )

        assert 404 == response.status_code

    def test_mask_value_invalid_config(
        self, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[MASKING_EXEC])
        value = "check"
        request = {
            "values": [value],
            "masking_strategy": {
                "strategy": StringRewriteMaskingStrategy.name,
                "configuration": {"wrong": "config"},
            },
        }

        response = api_client.put(
            f"{V1_URL_PREFIX}{MASKING}", json=request, headers=auth_header
        )

        assert 400 == response.status_code

    def test_masking_value_null(self, api_client: TestClient, generate_auth_header):
        auth_header = generate_auth_header(scopes=[MASKING_EXEC])
        value = "my_email"
        request = {
            "values": [value],
            "masking_strategy": {
                "strategy": NullMaskingStrategy.name,
                "configuration": {},
            },
        }

        response = api_client.put(
            f"{V1_URL_PREFIX}{MASKING}", json=request, headers=auth_header
        )
        assert 200 == response.status_code
        json_response = json.loads(response.text)
        assert value == json_response["plain"][0]
        assert json_response["masked_values"][0] is None

    def test_masking_values_multiple_strategies(
        self, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[MASKING_EXEC])
        value = "check"
        rewrite_val = "mate"
        request = {
            "values": [value],
            "masking_strategy": [
                {
                    "strategy": StringRewriteMaskingStrategy.name,
                    "configuration": {"rewrite_value": rewrite_val},
                },
                {
                    "strategy": HashMaskingStrategy.name,
                    "configuration": {},
                },
            ],
        }

        response = api_client.put(
            f"{V1_URL_PREFIX}{MASKING}", json=request, headers=auth_header
        )
        assert 200 == response.status_code
        assert response.json()["plain"] == ["check"]
        assert response.json()["masked_values"] != [
            rewrite_val
        ], "Final value is hashed, because that was the last strategy"

        switch_order = {
            "values": [value],
            "masking_strategy": [
                {
                    "strategy": HashMaskingStrategy.name,
                    "configuration": {},
                },
                {
                    "strategy": StringRewriteMaskingStrategy.name,
                    "configuration": {"rewrite_value": rewrite_val},
                },
            ],
        }
        response = api_client.put(
            f"{V1_URL_PREFIX}{MASKING}", json=switch_order, headers=auth_header
        )
        assert 200 == response.status_code
        assert response.json()["plain"] == ["check"]
        assert response.json()["masked_values"] == [
            rewrite_val
        ], "Final value is rewrite value, because that was the last strategy specified"

    def test_flexible_config(self, api_client: TestClient, generate_auth_header):
        auth_header = generate_auth_header(scopes=[MASKING_EXEC])
        """Test that this request is allowed.  Allow the configuration to be
        very flexible so different configuration requirements by many masking strategies are supported
        """
        value = "my_email"
        request = {
            "values": [value],
            "masking_strategy": {
                "strategy": NullMaskingStrategy.name,
                "configuration": {"test_val": {"test": [["test"]]}},
            },
        }

        response = api_client.put(
            f"{V1_URL_PREFIX}{MASKING}", json=request, headers=auth_header
        )
        assert 200 == response.status_code
