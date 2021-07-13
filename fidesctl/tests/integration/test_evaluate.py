import pytest
from unittest import mock

from fidesctl.core import apply, evaluate, manifests, models


def test_evaluate():
    assert True


def test_dry_evaluate_system_pass(server_url, objects_dict):
    test_system = objects_dict["system"]
    test_manifest = {"system": [test_system.dict()]}

    # Need to store the original function and restore it after the call
    original_ingest_manifests = manifests.ingest_manifests
    manifests.ingest_manifests = mock.Mock(return_value=test_manifest)
    response = evaluate.dry_evaluate(
        url=server_url, manifests_dir="test", fides_key="test_system"
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
        url=server_url, manifests_dir="test", fides_key="test_registry"
    )
    manifests.ingest_manifests = original_ingest_manifests

    print(response.json())
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "PASS"


def test_dry_evaluate_system_error(server_url, objects_dict):
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
        url=server_url, manifests_dir="test", fides_key="test_system"
    )
    manifests.ingest_manifests = original_ingest_manifests

    print(response.json())
    assert response.status_code == 500
    assert response.json()["errors"]


def test_dry_evaluate_system_fail(server_url, objects_dict):
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
        url=server_url, manifests_dir="test", fides_key="test_system"
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
    )

    print(response.json())
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "PASS"


def test_apply_evaluate_example_manifests(server_url):
    """
    This test is designed to verify that the example manifests
    included in the repo are valid and can be used within the docs tutorial.
    """

    apply.apply(server_url, "data/sample/")
    evaluation = evaluate.evaluate(
        url=server_url,
        object_type="system",
        fides_key="demoSystem",
        tag="test",
        message="test",
    ).json()

    print(evaluation)
    assert evaluation["data"]["status"] == "PASS"
