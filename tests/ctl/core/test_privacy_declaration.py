from typing import Dict, Set

import pytest

from fides.api.models.sql_models import PrivacyDeclaration
from fides.api.util.data_category import get_data_categories_map


class TestPrivacyDeclaration:

    @pytest.fixture(scope="function")
    def data_categories_map(self, db) -> Dict[str, Set[str]]:
        return get_data_categories_map(db)

    def test_privacy_declaration_dataset_data_categories(
        self,
        privacy_declaration_with_multiple_dataset_references: PrivacyDeclaration,
        data_categories_map,
    ):
        assert set(
            privacy_declaration_with_multiple_dataset_references.dataset_data_categories(
                data_categories_map
            )
        ) == {
            "user.behavior",
            "user.name.first",
            "user.unique_id",
            "user.contact.address.street",
        }

    def test_privacy_declaration_undeclared_data_categories(
        self,
        privacy_declaration_with_single_dataset_reference: PrivacyDeclaration,
        data_categories_map,
    ):
        assert privacy_declaration_with_single_dataset_reference.undeclared_data_categories(
            data_categories_map
        ) == {
            "user.contact.email"
        }

    def test_privacy_declaration_data_category_defined_on_sibling(
        self,
        db,
        privacy_declaration_with_single_dataset_reference: PrivacyDeclaration,
        data_categories_map,
    ):
        system = privacy_declaration_with_single_dataset_reference.system

        # Create a new privacy declaration with the data category we're searching for
        PrivacyDeclaration.create(
            db=db,
            data={
                "name": "Collect data for third party sharing",
                "system_id": system.id,
                "data_categories": ["user.contact.email"],
                "data_use": "third_party_sharing",
                "data_subjects": ["customer"],
                "dataset_references": None,
                "egress": None,
                "ingress": None,
            },
        )

        db.refresh(system)

        # Check that the original privacy declaration doesn't have any undeclared data categories
        # because we also search sibling privacy declarations for the data category
        assert (
            privacy_declaration_with_single_dataset_reference.undeclared_data_categories(
                data_categories_map
            )
            == set()
        )
