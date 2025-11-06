import pytest

from fides.api.models.saas_official_dataset import SaasOfficialDataset


class TestSaasOfficialDataset:
    def test_repr(self, db):
        """Test the __repr__ method returns the expected string representation."""
        # Create a SaasOfficialDataset instance
        dataset = SaasOfficialDataset.create(
            db=db,
            data={
                "connection_type": "mailchimp",
                "dataset_json": {"name": "test_dataset", "collections": []},
            },
        )

        repr_string = repr(dataset)
        expected = "<SaasOfficialDataset(connection_type='mailchimp')>"

        assert repr_string == expected
