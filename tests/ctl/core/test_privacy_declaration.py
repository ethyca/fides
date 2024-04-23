from fides.api.models.sql_models import PrivacyDeclaration


class TestPrivacyDeclaration:
    def test_privacy_declaration_datasets(
        self,
        privacy_declaration_with_dataset_references: PrivacyDeclaration,
    ) -> None:
        assert len(privacy_declaration_with_dataset_references.datasets) == 1

    def test_privacy_declaration_undeclared_data_categories(
        self, privacy_declaration_with_dataset_references
    ):
        assert (
            privacy_declaration_with_dataset_references.undeclared_data_categories
            == {"user.contact.email"}
        )

    def test_privacy_declaration_data_category_defined_on_sibling(
        self, db, privacy_declaration_with_dataset_references
    ):
        system = privacy_declaration_with_dataset_references.system

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
            privacy_declaration_with_dataset_references.undeclared_data_categories
            == set()
        )
