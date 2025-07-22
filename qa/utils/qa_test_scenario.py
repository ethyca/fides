#!/usr/bin/env python3
"""
Abstract base class for QA test scenarios.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type
from dataclasses import dataclass
from utils.fides_api import FidesAPI
from utils.rich_helpers import RichFormatter


@dataclass
class Argument:
    """Represents a scenario argument specification."""
    type: Type = str
    default: Any = None
    description: str = ""


class QATestScenario(ABC):
    """Base class for QA test scenarios with built-in Rich formatting support."""

    # Class attribute for argument specifications
    arguments: Dict[str, Argument] = {}

    def __init__(self, base_url: str = "http://localhost:8080", **kwargs):
        self.base_url = base_url
        self.api = FidesAPI(base_url)
        self.formatter = RichFormatter()

        # Store any additional arguments passed to the scenario
        for key, value in kwargs.items():
            setattr(self, key, value)

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

    # Convenience methods for consistent formatting
    def setup_phase(self) -> None:
        """Print a setup phase header."""
        self.formatter.phase_header("Setup Phase", style="green")

    def cleanup_phase(self) -> None:
        """Print a cleanup phase header."""
        self.formatter.phase_header("Cleanup Phase", style="yellow")

    def step(self, step_num: int, title: str) -> None:
        """Print a numbered step header."""
        self.formatter.step_header(step_num, title)

    def success(self, message: str, indent: int = 2) -> None:
        """Print a success message."""
        self.formatter.success(message, indent)

    def error(self, message: str, indent: int = 2) -> None:
        """Print an error message."""
        self.formatter.error(message, indent)

    def warning(self, message: str, indent: int = 2) -> None:
        """Print a warning message."""
        self.formatter.warning(message, indent)

    def info(self, message: str, indent: int = 2) -> None:
        """Print an info message."""
        self.formatter.info(message, indent)

    def already_cleaned(
        self, resource_type: str, resource_id: str, indent: int = 2
    ) -> None:
        """Print a message for resources that are already cleaned."""
        self.formatter.already_cleaned(resource_type, resource_id, indent)

    def summary(self, title: str, data: Dict[str, int]) -> None:
        """Print a summary table."""
        self.formatter.summary_table(title, data)

    def final_success(self, message: str) -> None:
        """Print a final success message."""
        self.formatter.final_success(message)

    def final_error(self, message: str) -> None:
        """Print a final error message."""
        self.formatter.final_error(message)
