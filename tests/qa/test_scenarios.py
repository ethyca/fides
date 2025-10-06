#!/usr/bin/env python3
"""
Pytest test suite for QA scenarios.

This module dynamically discovers all QA scenarios and tests their setup/teardown methods.
"""

import sys
from pathlib import Path
from typing import Type

# Add project root and qa directory to path for imports
project_root = Path(__file__).parent.parent.parent
qa_dir = project_root / "qa"

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(qa_dir) not in sys.path:
    sys.path.insert(0, str(qa_dir))

import pytest

from qa.__main__ import discover_scenarios
from qa.utils import QATestScenario


def create_scenario_instance(scenario_class: Type[QATestScenario]) -> QATestScenario:
    """Create a scenario instance with test parameters."""
    # Use minimal dataset count for faster testing
    return scenario_class(base_url="http://localhost:8080", datasets=3)


# Get scenarios for parametrization
SCENARIOS = discover_scenarios()


@pytest.mark.xfail(
    reason="These tests require too many external services to run. Skipping for now."
)
@pytest.mark.external
@pytest.mark.parametrize("scenario_name,scenario_class", list(SCENARIOS.items()))
def test_scenario_setup_and_teardown(scenario_name, scenario_class):
    """Test each scenario's setup and teardown methods."""
    # Create scenario instance
    scenario = create_scenario_instance(scenario_class)

    # Verify basic properties
    assert hasattr(
        scenario, "description"
    ), f"Scenario {scenario_name} should have description property"
    assert (
        scenario.description
    ), f"Scenario {scenario_name} should have non-empty description"

    # Test setup
    setup_result = scenario.setup()
    assert (
        setup_result is True
    ), f"Scenario {scenario_name} setup should succeed and return True"

    # Test teardown after setup
    final_teardown_result = scenario.teardown()
    assert isinstance(
        final_teardown_result, bool
    ), f"Scenario {scenario_name} teardown should return boolean"
