"""Tests for data category tagging_instructions field and endpoints."""

import json

import pytest
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from fides.api.models.client import ClientDetail
from fides.api.models.sql_models import DataCategory
from fides.common.api.scope_registry import (
    DATA_CATEGORY,
    DATA_CATEGORY_CREATE,
    DATA_CATEGORY_READ,
    DATA_CATEGORY_UPDATE,
    STORAGE_READ,
)
from fides.common.api.v1.urn_registry import V1_URL_PREFIX


class TestDataCategoryTaggingInstructionsSchema:
    """Test that tagging_instructions is included in schemas."""

    @pytest.fixture(scope="function", autouse=True)
    def cleanup_test_categories(self, db: Session):
        """Clean up any test categories before and after each test."""
        # Cleanup before test
        for key in [
            "test_create_with_instructions",
            "test_create_no_instructions",
            "test_update_category",
        ]:
            cat = DataCategory.get_by(db=db, field="fides_key", value=key)
            if cat:
                cat.delete(db)
        yield
        # Cleanup after test
        for key in [
            "test_create_with_instructions",
            "test_create_no_instructions",
            "test_update_category",
        ]:
            cat = DataCategory.get_by(db=db, field="fides_key", value=key)
            if cat:
                cat.delete(db)

    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + "/" + DATA_CATEGORY

    @pytest.fixture(scope="function")
    def data_category_with_tagging_instructions(self, db: Session):
        """Create a data category with tagging_instructions for testing."""
        payload = {
            "name": "Test Category",
            "fides_key": "test_category_with_instructions",
            "organization_fides_key": "default_organization",
            "active": True,
            "is_default": False,
            "description": "Test category for tagging instructions",
            "tagging_instructions": "* DO TAG: email addresses\n* DO NOT TAG: encrypted data",
        }
        category = DataCategory.create(db=db, data=payload, check_name=False)
        yield category
        category.delete(db)

    def test_create_data_category_with_tagging_instructions(
        self,
        db: Session,
        api_client: TestClient,
        url,
        generate_auth_header,
    ):
        """Test creating a data category with tagging_instructions."""
        auth_header = generate_auth_header([DATA_CATEGORY_CREATE])
        payload = {
            "name": "Test Category",
            "fides_key": "test_create_with_instructions",
            "organization_fides_key": "default_organization",
            "active": True,
            "is_default": False,
            "description": "Test category",
            "tagging_instructions": "* DO TAG: names\n* DO NOT TAG: ids",
        }

        response = api_client.post(url, headers=auth_header, json=payload)
        assert response.status_code == 201

        response_body = json.loads(response.text)
        assert (
            response_body["tagging_instructions"]
            == "* DO TAG: names\n* DO NOT TAG: ids"
        )

        # Cleanup
        category = DataCategory.get_by(
            db=db, field="fides_key", value="test_create_with_instructions"
        )
        if category:
            category.delete(db)

    def test_create_data_category_without_tagging_instructions(
        self,
        db: Session,
        api_client: TestClient,
        url,
        generate_auth_header,
    ):
        """Test creating a data category without tagging_instructions (should be None)."""
        auth_header = generate_auth_header([DATA_CATEGORY_CREATE])
        payload = {
            "name": "Test Category No Instructions",
            "fides_key": "test_create_no_instructions",
            "organization_fides_key": "default_organization",
            "active": True,
            "is_default": False,
            "description": "Test category without tagging instructions",
        }

        response = api_client.post(url, headers=auth_header, json=payload)
        assert response.status_code == 201

        response_body = json.loads(response.text)
        assert response_body.get("tagging_instructions") is None

        # Cleanup
        category = DataCategory.get_by(
            db=db, field="fides_key", value="test_create_no_instructions"
        )
        if category:
            category.delete(db)

    def test_update_data_category_with_tagging_instructions(
        self,
        db: Session,
        api_client: TestClient,
        url,
        generate_auth_header,
    ):
        """Test updating a data category to add tagging_instructions via PUT."""
        # First create a category without tagging_instructions
        category = DataCategory.create(
            db=db,
            check_name=False,
            data={
                "name": "Test Update Category",
                "fides_key": "test_update_category",
                "organization_fides_key": "default_organization",
                "active": True,
                "is_default": False,
                "description": "Category to update",
            },
        )

        auth_header = generate_auth_header([DATA_CATEGORY_UPDATE])
        payload = {
            "fides_key": "test_update_category",
            "name": "Updated Category",
            "description": "Updated description",
            "tagging_instructions": "* DO TAG: updated instructions",
        }

        response = api_client.put(url, headers=auth_header, json=payload)
        assert response.status_code == 200

        response_body = json.loads(response.text)
        assert response_body["tagging_instructions"] == "* DO TAG: updated instructions"
        assert response_body["name"] == "Updated Category"

        # Cleanup
        category.delete(db)

    def test_get_data_category_includes_tagging_instructions(
        self,
        api_client: TestClient,
        data_category_with_tagging_instructions,
        generate_auth_header,
    ):
        """Test that GET includes tagging_instructions in response."""
        auth_header = generate_auth_header([DATA_CATEGORY_READ])
        url = f"{V1_URL_PREFIX}/{DATA_CATEGORY}?fides_key={data_category_with_tagging_instructions.fides_key}"

        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200

        response_body = json.loads(response.text)
        # Handle both list and paginated responses
        if isinstance(response_body, list):
            items = response_body
        else:
            items = response_body.get("items", [])
        assert len(items) > 0

        category = next(
            (
                item
                for item in items
                if item["fides_key"]
                == data_category_with_tagging_instructions.fides_key
            ),
            None,
        )
        assert category is not None
        assert "tagging_instructions" in category
        assert "DO TAG: email addresses" in category["tagging_instructions"]


class TestUpdateTaggingInstructionsPatchEndpoint:
    """Test the PATCH endpoint for updating tagging_instructions."""

    @pytest.fixture(scope="function", autouse=True)
    def cleanup_patch_test_categories(self, db: Session):
        """Clean up any test categories before and after each test."""
        # Cleanup before test
        for key in ["test_patch_category", "test_overwrite_category"]:
            cat = DataCategory.get_by(db=db, field="fides_key", value=key)
            if cat:
                cat.delete(db)
        yield
        # Cleanup after test
        for key in ["test_patch_category", "test_overwrite_category"]:
            cat = DataCategory.get_by(db=db, field="fides_key", value=key)
            if cat:
                cat.delete(db)

    @pytest.fixture(scope="function")
    def data_category_for_patch(self, db: Session):
        """Create a data category for PATCH testing."""
        payload = {
            "name": "Patch Test Category",
            "fides_key": "test_patch_category",
            "organization_fides_key": "default_organization",
            "active": True,
            "is_default": False,
            "description": "Category for patch testing",
        }
        category = DataCategory.create(db=db, data=payload, check_name=False)
        yield category
        category.delete(db)

    @pytest.fixture(scope="function")
    def patch_url(self, data_category_for_patch):
        return f"{V1_URL_PREFIX}/{DATA_CATEGORY}/{data_category_for_patch.fides_key}/tagging_instructions"

    def test_patch_tagging_instructions_not_authenticated(
        self,
        api_client: TestClient,
        patch_url,
    ):
        """Test PATCH without authentication."""
        response = api_client.patch(
            patch_url,
            headers={},
            json={"tagging_instructions": "* DO TAG: test"},
        )
        assert response.status_code == 401

    def test_patch_tagging_instructions_incorrect_scope(
        self,
        api_client: TestClient,
        patch_url,
        generate_auth_header,
    ):
        """Test PATCH with incorrect scope."""
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.patch(
            patch_url,
            headers=auth_header,
            json={"tagging_instructions": "* DO TAG: test"},
        )
        assert response.status_code == 403

    def test_patch_tagging_instructions_success(
        self,
        db: Session,
        api_client: TestClient,
        patch_url,
        data_category_for_patch,
        generate_auth_header,
    ):
        """Test successfully updating tagging_instructions via PATCH."""
        auth_header = generate_auth_header([DATA_CATEGORY_UPDATE])
        new_instructions = "* DO TAG: phone numbers\n* DO NOT TAG: hashed values"

        response = api_client.patch(
            patch_url,
            headers=auth_header,
            json={"tagging_instructions": new_instructions},
        )
        assert response.status_code == 200

        response_body = json.loads(response.text)
        assert response_body["tagging_instructions"] == new_instructions
        assert response_body["fides_key"] == data_category_for_patch.fides_key

        # Verify in database
        db.refresh(data_category_for_patch)
        assert data_category_for_patch.tagging_instructions == new_instructions

    def test_patch_tagging_instructions_nonexistent_category(
        self,
        api_client: TestClient,
        generate_auth_header,
    ):
        """Test PATCH on a non-existent data category."""
        auth_header = generate_auth_header([DATA_CATEGORY_UPDATE])
        url = f"{V1_URL_PREFIX}/{DATA_CATEGORY}/nonexistent.key/tagging_instructions"

        response = api_client.patch(
            url,
            headers=auth_header,
            json={"tagging_instructions": "* DO TAG: test"},
        )
        assert response.status_code == 404

    def test_patch_tagging_instructions_overwrites_existing(
        self,
        db: Session,
        api_client: TestClient,
        generate_auth_header,
    ):
        """Test that PATCH overwrites existing tagging_instructions."""
        # Create category with existing instructions
        category = DataCategory.create(
            db=db,
            check_name=False,
            data={
                "name": "Overwrite Test",
                "fides_key": "test_overwrite_category",
                "organization_fides_key": "default_organization",
                "active": True,
                "is_default": False,
                "description": "Test overwriting instructions",
                "tagging_instructions": "* DO TAG: old instructions",
            },
        )

        auth_header = generate_auth_header([DATA_CATEGORY_UPDATE])
        url = (
            f"{V1_URL_PREFIX}/{DATA_CATEGORY}/{category.fides_key}/tagging_instructions"
        )
        new_instructions = "* DO TAG: new instructions"

        response = api_client.patch(
            url,
            headers=auth_header,
            json={"tagging_instructions": new_instructions},
        )
        assert response.status_code == 200

        response_body = json.loads(response.text)
        assert response_body["tagging_instructions"] == new_instructions
        assert "old instructions" not in response_body["tagging_instructions"]

        # Cleanup
        category.delete(db)


class TestDeleteTaggingInstructionsEndpoint:
    """Test the DELETE endpoint for removing tagging_instructions."""

    @pytest.fixture(scope="function", autouse=True)
    def cleanup_delete_test_categories(self, db: Session):
        """Clean up any test categories before and after each test."""
        # Cleanup before test
        for key in ["test_delete_instructions", "test_no_instructions_delete"]:
            cat = DataCategory.get_by(db=db, field="fides_key", value=key)
            if cat:
                cat.delete(db)
        yield
        # Cleanup after test
        for key in ["test_delete_instructions", "test_no_instructions_delete"]:
            cat = DataCategory.get_by(db=db, field="fides_key", value=key)
            if cat:
                cat.delete(db)

    @pytest.fixture(scope="function")
    def data_category_with_instructions(self, db: Session):
        """Create a data category with tagging_instructions for deletion testing."""
        payload = {
            "name": "Delete Test Category",
            "fides_key": "test_delete_category",
            "organization_fides_key": "default_organization",
            "active": True,
            "is_default": False,
            "description": "Category for delete testing",
            "tagging_instructions": "* DO TAG: to be deleted",
        }
        category = DataCategory.create(db=db, data=payload, check_name=False)
        yield category
        category.delete(db)

    @pytest.fixture(scope="function")
    def delete_url(self, data_category_with_instructions):
        return f"{V1_URL_PREFIX}/{DATA_CATEGORY}/{data_category_with_instructions.fides_key}/tagging_instructions"

    def test_delete_tagging_instructions_not_authenticated(
        self,
        api_client: TestClient,
        delete_url,
    ):
        """Test DELETE without authentication."""
        response = api_client.delete(delete_url, headers={})
        assert response.status_code == 401

    def test_delete_tagging_instructions_incorrect_scope(
        self,
        api_client: TestClient,
        delete_url,
        generate_auth_header,
    ):
        """Test DELETE with incorrect scope."""
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.delete(delete_url, headers=auth_header)
        assert response.status_code == 403

    def test_delete_tagging_instructions_success(
        self,
        db: Session,
        api_client: TestClient,
        delete_url,
        data_category_with_instructions,
        generate_auth_header,
    ):
        """Test successfully deleting tagging_instructions."""
        auth_header = generate_auth_header([DATA_CATEGORY_UPDATE])

        # Verify instructions exist before delete
        assert data_category_with_instructions.tagging_instructions is not None

        response = api_client.delete(delete_url, headers=auth_header)
        assert response.status_code == 200

        response_body = json.loads(response.text)
        assert response_body["tagging_instructions"] is None
        assert response_body["fides_key"] == data_category_with_instructions.fides_key

        # Verify in database
        db.refresh(data_category_with_instructions)
        assert data_category_with_instructions.tagging_instructions is None

    def test_delete_tagging_instructions_nonexistent_category(
        self,
        api_client: TestClient,
        generate_auth_header,
    ):
        """Test DELETE on a non-existent data category."""
        auth_header = generate_auth_header([DATA_CATEGORY_UPDATE])
        url = f"{V1_URL_PREFIX}/{DATA_CATEGORY}/nonexistent.key/tagging_instructions"

        response = api_client.delete(url, headers=auth_header)
        assert response.status_code == 404

    def test_delete_tagging_instructions_already_none(
        self,
        db: Session,
        api_client: TestClient,
        generate_auth_header,
    ):
        """Test DELETE when tagging_instructions is already None."""
        # Create category without instructions
        category = DataCategory.create(
            db=db,
            check_name=False,
            data={
                "name": "No Instructions Delete Test",
                "fides_key": "test_no_instructions_delete",
                "organization_fides_key": "default_organization",
                "active": True,
                "is_default": False,
                "description": "Category without instructions for delete test",
            },
        )

        auth_header = generate_auth_header([DATA_CATEGORY_UPDATE])
        url = (
            f"{V1_URL_PREFIX}/{DATA_CATEGORY}/{category.fides_key}/tagging_instructions"
        )

        response = api_client.delete(url, headers=auth_header)
        assert response.status_code == 200

        response_body = json.loads(response.text)
        assert response_body["tagging_instructions"] is None

        # Cleanup
        category.delete(db)
