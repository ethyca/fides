
import uuid
from typing import Any, Dict

import pydash
import pytest

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,

)

from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("segment")


@pytest.fixture(scope="session")
def segment_rtf_only_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "segment.domain") or secrets["domain"],
        "workspace": pydash.get(saas_config, "segment.workspace")
        or secrets["workspace"],
        "access_token": pydash.get(saas_config, "segment.access_token")
        or secrets["access_token"],
    }

@pytest.fixture
def segment_rtf_only_erasure_identity_email() -> str:
    return generate_random_email()



@pytest.fixture
def segment_rtf_only_external_references() -> Dict[str, Any]:
    return {"segment_user_id": uuid.uuid4()}

@pytest.fixture
def segment_rtf_only_erasure_external_references() -> Dict[str, Any]:
    return {"segment_user_id": uuid.uuid4()}


@pytest.fixture
def segment_rtf_only_runner(
    db,
    cache,
    segment_rtf_only_secrets,
    segment_rtf_only_external_references,
    segment_rtf_only_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "segment_rtf_only",
        segment_rtf_only_secrets,
        external_references=segment_rtf_only_external_references,
        erasure_external_references=segment_rtf_only_erasure_external_references,
    )
