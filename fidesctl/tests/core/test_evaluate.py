from typing import Dict

import pytest
from unittest import mock
from fidesctl.core.config import generate_request_headers
from fidesctl.core import apply, evaluate, manifests, models

# Helpers
test_headers: Dict[str, str] = generate_request_headers(1, "test_api_key")


@pytest.mark.integration
def test_dry_evaluate_system_pass(test_config, objects_dict):
    test_system = objects_dict["system"]
    test_manifest = {"system": [test_system.dict()]}

    # Need to store the original function and restore it after the call
    original_ingest_manifests = manifests.ingest_manifests
    manifests.ingest_manifests = mock.Mock(return_value=test_manifest)
    response = evaluate.dry_evaluate(
        url=test_config.cli.server_url,
        headers=test_config.user.request_headers,
        manifests_dir="test",
        fides_key="test_system",
    )
    manifests.ingest_manifests = original_ingest_manifests

    print(response.json())
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "PASS"


@pytest.mark.integration
def test_dry_evaluate_registry_pass(test_config, objects_dict):
    test_system = objects_dict["registry"]
    test_manifest = {"registry": [test_system.dict()]}

    # Need to store the original function and restore it after the call
    original_ingest_manifests = manifests.ingest_manifests
    manifests.ingest_manifests = mock.Mock(return_value=test_manifest)
    response = evaluate.dry_evaluate(
        url=test_config.cli.server_url,
        headers=test_config.user.request_headers,
        manifests_dir="test",
        fides_key="test_registry",
    )
    manifests.ingest_manifests = original_ingest_manifests

    print(response.json())
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "PASS"


@pytest.mark.integration
def test_dry_evaluate_system_error(test_config, objects_dict):
    # Set up the test system
    test_system = objects_dict["system"]
    failing_declaration = [
        models.PrivacyDeclaration(
            name="declaration-name",
            dataCategories=["customer_content_data"],
            dataUse="provi",
            dataSubjects=["customer"],
            dataQualifier="identified_data",
        )
    ]
    test_system.privacyDeclarations = failing_declaration
    test_manifest = {"system": [test_system.dict()]}

    # Need to store the original function and restore it after the call
    original_ingest_manifests = manifests.ingest_manifests
    manifests.ingest_manifests = mock.Mock(return_value=test_manifest)
    response = evaluate.dry_evaluate(
        url=test_config.cli.server_url,
        headers=test_config.user.request_headers,
        manifests_dir="test",
        fides_key="test_system",
    )
    manifests.ingest_manifests = original_ingest_manifests

    print(response.json())

    assert response.status_code == 500
    assert response.json()["errors"]


@pytest.mark.integration
def test_dry_evaluate_system_fail(test_config, objects_dict):
    # Set up the test system
    test_system = objects_dict["system"]
    failing_declaration = [
        models.PrivacyDeclaration(
            name="declaration-name",
            dataCategories=["customer_content_data"],
            dataUse="provide",
            dataSubjects=["customer"],
            dataQualifier="identified_data",
        )
    ]
    test_system.privacyDeclarations = failing_declaration
    test_manifest = {"system": [test_system.dict()]}

    # Need to store the original function and restore it after the call
    original_ingest_manifests = manifests.ingest_manifests
    manifests.ingest_manifests = mock.Mock(return_value=test_manifest)
    response = evaluate.dry_evaluate(
        url=test_config.cli.server_url,
        headers=test_config.user.request_headers,
        manifests_dir="test",
        fides_key="test_system",
    )
    manifests.ingest_manifests = original_ingest_manifests

    print(response.json())
    assert response.status_code == 500
    assert response.json()["data"]["status"] == "FAIL"


@pytest.mark.integration
def test_evaluate_system_pass(test_config, objects_dict):
    response = evaluate.evaluate(
        url=test_config.cli.server_url,
        headers=test_config.user.request_headers,
        object_type="system",
        fides_key="test_system_1",
        tag="tag",
        message="message",
    )

    print(response.json())
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "PASS"


@pytest.mark.integration
def test_evaluate_registry_pass(test_config, objects_dict):
    response = evaluate.evaluate(
        url=test_config.cli.server_url,
        headers=test_config.user.request_headers,
        object_type="registry",
        fides_key="default_registry",
        tag="tag",
        message="message",
    )

    print(response.json())
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "PASS"


@pytest.mark.integration
def test_apply_evaluate_example_manifests(test_config):
    """
    This test is designed to verify that the example manifests
    included in the repo are valid and can be used within the docs tutorial.
    """

    apply.apply(
        test_config.cli.server_url,
        "data/sample/",
        headers=test_config.user.request_headers,
    )
    evaluate_response = evaluate.evaluate(
        url=test_config.cli.server_url,
        headers=test_config.user.request_headers,
        object_type="system",
        fides_key="demoPassingSystem",
        tag="test",
        message="test",
    ).json()

    print(evaluate_response)
    assert evaluate_response["data"]["status"] == "PASS"
