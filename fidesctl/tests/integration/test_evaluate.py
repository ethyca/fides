from typing import Dict

from unittest import mock

from fidesctl.cli.config import FidesConfig
from fidesctl.core import evaluate, manifests, models

test_headers: Dict[str, str] = FidesConfig(1, "test_api_key").generate_request_headers()


def test_evaluate():
    assert True


def test_dry_evaluate_system_pass(server_url, objects_dict):
    test_system = objects_dict["system"]
    test_system.datasets = (
        []
    )  # The server checks will fail if the dataset doesn't exist
    test_manifest = {"system": [test_system.dict()]}

    # Need to store the original function and restore it after the call
    original_ingest_manifests = manifests.ingest_manifests
    manifests.ingest_manifests = mock.Mock(return_value=test_manifest)
    response = evaluate.dry_evaluate(
        url=server_url,
        manifests_dir="test",
        fides_key="test_system",
        headers=test_headers,
    )
    manifests.ingest_manifests = original_ingest_manifests

    print(response.json())
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "PASS"


def test_dry_evaluate_registry_pass(server_url, objects_dict):
    test_system = objects_dict["registry"]
    test_manifest = {"registry": [test_system.dict()]}

    # Need to store the original function and restore it after the call
    original_ingest_manifests = manifests.ingest_manifests
    manifests.ingest_manifests = mock.Mock(return_value=test_manifest)
    response = evaluate.dry_evaluate(
        url=server_url,
        manifests_dir="test",
        fides_key="test_registry",
        headers=test_headers,
    )
    manifests.ingest_manifests = original_ingest_manifests

    print(response.json())
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "PASS"


def test_dry_evaluate_system_error(server_url, objects_dict):
    test_system = objects_dict["system"]
    test_manifest = {"system": [test_system.dict()]}

    # Need to store the original function and restore it after the call
    original_ingest_manifests = manifests.ingest_manifests
    manifests.ingest_manifests = mock.Mock(return_value=test_manifest)
    response = evaluate.dry_evaluate(
        url=server_url,
        manifests_dir="test",
        fides_key="test_system",
        headers=test_headers,
    )
    manifests.ingest_manifests = original_ingest_manifests

    print(response.json())
    assert response.status_code == 500
    assert response.json()["data"]["status"] == "ERROR"


def test_dry_evaluate_system_fail(server_url, objects_dict):
    # Set up the test system
    test_system = objects_dict["system"]
    failing_declaration = [
        models.DataDeclaration(
            name="declaration-name",
            dataCategories=["customer_content_data"],
            dataUse="provide",
            dataSubjectCategories=["customer"],
            dataQualifier="identified_data",
        )
    ]
    test_system.declarations = failing_declaration
    test_system.datasets = (
        []
    )  # The server checks will fail if the dataset doesn't exist
    test_manifest = {"system": [test_system.dict()]}

    # Need to store the original function and restore it after the call
    original_ingest_manifests = manifests.ingest_manifests
    manifests.ingest_manifests = mock.Mock(return_value=test_manifest)
    response = evaluate.dry_evaluate(
        url=server_url,
        manifests_dir="test",
        fides_key="test_system",
        headers=test_headers,
    )
    manifests.ingest_manifests = original_ingest_manifests

    print(response.json())
    assert response.status_code == 500
    assert response.json()["data"]["status"] == "FAIL"


def test_evaluate_system_pass(server_url, objects_dict):
    response = evaluate.evaluate(
        url=server_url,
        object_type="system",
        fides_key="test_system_1",
        tag="tag",
        message="message",
        headers=test_headers,
    )

    print(response.json())
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "PASS"


def test_evaluate_registry_pass(server_url, objects_dict):
    response = evaluate.evaluate(
        url=server_url,
        object_type="registry",
        fides_key="test",
        tag="tag",
        message="message",
        headers=test_headers,
    )

    print(response.json())
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "PASS"
