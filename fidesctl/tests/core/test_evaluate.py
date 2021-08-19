from typing import Dict

import pytest
from unittest import mock
from fidesctl.core import evaluate, manifests, models


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
