from typing import Dict

import pytest
from fidesctl.core import evaluate, manifests, models


@pytest.mark.unit
def test_dry_evaluate_system_error():
    assert True
