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
            == ["user.contact.email"]
        )
