import pytest

from fides.api.models.saas_template_dataset import SaasTemplateDataset


class TestSaasTemplateDataset:
    def test_repr(self, db):
        """Test the __repr__ method returns the expected string representation."""
        # Get or create a SaasTemplateDataset instance
        _, dataset = SaasTemplateDataset.get_or_create(
            db=db,
            connector_type="mailchimp",
            dataset_json={"name": "test_dataset", "collections": []},
        )

        repr_string = repr(dataset)
        expected = "<SaasTemplateDataset(connection_type='mailchimp')>"

        assert repr_string == expected
