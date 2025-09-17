"""Tests for system endpoint sorting functionality."""

import pytest
from fastapi_pagination import Params
from sqlalchemy.orm import Session
from starlette.status import HTTP_200_OK
from starlette.testclient import TestClient

from fides.api.models.sql_models import System
from fides.common.api.scope_registry import SYSTEM_READ
from fides.common.api.v1.urn_registry import V1_URL_PREFIX


class TestSystemEndpointSorting:
    """Test system sorting functionality for API endpoint."""

    @pytest.fixture
    def url(self):
        """URL for the system endpoint."""
        return f"{V1_URL_PREFIX}/system"

    @pytest.fixture
    def sorting_test_systems(self, db: Session) -> list[System]:
        """Create multiple systems with different names for sorting endpoint tests."""
        systems = []

        # Create systems with specific names to test sorting
        system_names = [
            ("delta_system", "Delta System"),
            ("alpha_system", "Alpha System"),
            ("bravo_system", "Bravo System"),
            ("charlie_system", "Charlie System"),
        ]

        for fides_key, name in system_names:
            system = System.create(
                db=db,
                data={
                    "fides_key": fides_key,
                    "name": name,
                    "description": f"Description for {name}",
                    "organization_fides_key": "test_organization",
                    "system_type": "Service",
                },
            )
            systems.append(system)

        yield systems

        # Cleanup
        for system in systems:
            system.delete(db)

    def test_get_systems_sort_by_name_ascending(
        self,
        url: str,
        generate_auth_header,
        api_client: TestClient,
        sorting_test_systems: list[System],
    ):
        """Test API endpoint sorts systems by name in ascending order."""
        auth_header = generate_auth_header(scopes=[SYSTEM_READ])

        response = api_client.get(
            url,
            params={
                "size": 20,
                "page": 1,
                "sort_by": ["name"],
                "sort_asc": True,
            },
            headers=auth_header,
        )

        assert response.status_code == HTTP_200_OK
        data = response.json()

        # Find our test systems in the response
        test_system_names = [
            "Alpha System",
            "Bravo System",
            "Charlie System",
            "Delta System",
        ]
        found_systems = []

        for item in data["items"]:
            if item["name"] in test_system_names:
                found_systems.append(item["name"])

        # Should be in ascending order
        sorted_found = sorted(found_systems)
        assert (
            found_systems == sorted_found
        ), f"Expected sorted order, got {found_systems}"
        assert len(found_systems) == 4, "Should find all 4 test systems"

    def test_get_systems_sort_by_name_descending(
        self,
        url: str,
        generate_auth_header,
        api_client: TestClient,
        sorting_test_systems: list[System],
    ):
        """Test API endpoint sorts systems by name in descending order."""
        auth_header = generate_auth_header(scopes=[SYSTEM_READ])

        response = api_client.get(
            url,
            params={
                "size": 20,
                "page": 1,
                "sort_by": ["name"],
                "sort_asc": False,
            },
            headers=auth_header,
        )

        assert response.status_code == HTTP_200_OK
        data = response.json()

        # Find our test systems in the response
        test_system_names = [
            "Alpha System",
            "Bravo System",
            "Charlie System",
            "Delta System",
        ]
        found_systems = []

        for item in data["items"]:
            if item["name"] in test_system_names:
                found_systems.append(item["name"])

        # Should be in descending order
        reverse_sorted_found = sorted(found_systems, reverse=True)
        assert (
            found_systems == reverse_sorted_found
        ), f"Expected reverse sorted order, got {found_systems}"
        assert len(found_systems) == 4, "Should find all 4 test systems"

    def test_get_systems_sort_with_search(
        self,
        url: str,
        generate_auth_header,
        api_client: TestClient,
        sorting_test_systems: list[System],
    ):
        """Test API endpoint sorting works with search filtering."""
        auth_header = generate_auth_header(scopes=[SYSTEM_READ])

        response = api_client.get(
            url,
            params={
                "size": 20,
                "page": 1,
                "search": "System",
                "sort_by": ["name"],
                "sort_asc": True,
            },
            headers=auth_header,
        )

        assert response.status_code == HTTP_200_OK
        data = response.json()

        # Should find systems containing "System" and be sorted
        found_systems = [
            item["name"] for item in data["items"] if "System" in item["name"]
        ]
        sorted_found = sorted(found_systems)

        assert found_systems == sorted_found, "Found systems should be sorted by name"
        assert len(found_systems) >= 4, "Should find at least our 4 test systems"

    def test_get_systems_no_sorting_params_still_works(
        self,
        url: str,
        generate_auth_header,
        api_client: TestClient,
        sorting_test_systems: list[System],
    ):
        """Test that API endpoint still works without sorting parameters."""
        auth_header = generate_auth_header(scopes=[SYSTEM_READ])

        response = api_client.get(
            url,
            params={
                "size": 20,
                "page": 1,
            },
            headers=auth_header,
        )

        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) > 0

        # Find our test systems in the response
        test_system_names = [
            "Alpha System",
            "Bravo System",
            "Charlie System",
            "Delta System",
        ]
        found_systems = []

        for item in data["items"]:
            if item["name"] in test_system_names:
                found_systems.append(item["name"])

        # Should default to ascending name sort even without explicit sorting parameters
        sorted_found = sorted(found_systems)
        assert (
            found_systems == sorted_found
        ), f"Expected default sorted order by name, got {found_systems}"
        assert len(found_systems) == 4, "Should find all 4 test systems"

    def test_get_systems_with_pagination_and_sorting(
        self,
        url: str,
        generate_auth_header,
        api_client: TestClient,
        sorting_test_systems: list[System],
    ):
        """Test sorting works correctly with pagination."""
        auth_header = generate_auth_header(scopes=[SYSTEM_READ])

        # Get first page
        response = api_client.get(
            url,
            params={
                "size": 2,  # Small page size to test pagination
                "page": 1,
                "sort_by": ["name"],
                "sort_asc": True,
            },
            headers=auth_header,
        )

        assert response.status_code == HTTP_200_OK
        data = response.json()

        # Verify pagination structure
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data

        # Get system names from first page
        first_page_names = [item["name"] for item in data["items"]]

        # Get second page
        response = api_client.get(
            url,
            params={
                "size": 2,
                "page": 2,
                "sort_by": ["name"],
                "sort_asc": True,
            },
            headers=auth_header,
        )

        assert response.status_code == HTTP_200_OK
        data = response.json()

        second_page_names = [item["name"] for item in data["items"]]

        # Combined list should be sorted
        all_names = first_page_names + second_page_names
        if len(all_names) > 1:
            # Check that the combined list maintains sort order
            # (first page should have names that come before second page)
            for i in range(len(first_page_names)):
                for j in range(len(second_page_names)):
                    assert (
                        first_page_names[i] <= second_page_names[j]
                    ), f"Pagination broke sort order: {first_page_names[i]} should come before {second_page_names[j]}"
