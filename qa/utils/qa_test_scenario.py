#!/usr/bin/env python3
"""
Abstract base class for QA test scenarios.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type
from dataclasses import dataclass
from utils.fides_api import FidesAPI


@dataclass
class Argument:
    """Represents a scenario argument specification."""
    type: Type = str
    default: Any = None
    description: str = ""


class QATestScenario(ABC):
    """Base class for QA test scenarios."""

    # Class attribute for argument specifications
    arguments: Dict[str, Argument] = {}

    def __init__(self, base_url: str = "http://localhost:8080", **kwargs):
        self.base_url = base_url
        self.api = FidesAPI(base_url)

    @property
    @abstractmethod
    def description(self) -> str:
        """Return a description of this scenario for the list command."""
        pass

    @abstractmethod
    def setup(self) -> bool:
        """Set up the test scenario. Return True if successful, False otherwise."""
        pass

    @abstractmethod
    def teardown(self) -> bool:
        """Clean up the test scenario. Return True if successful, False otherwise."""
        pass
