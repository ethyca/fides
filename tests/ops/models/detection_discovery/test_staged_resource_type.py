import pytest

from fides.api.models.detection_discovery.core import StagedResourceType


class TestStagedResourceType:
    """
    Tests for the StagedResourceType enum
    """

    def test_get_datastore_resource_types(self):
        assert StagedResourceType.get_datastore_resource_types() == [
            StagedResourceType.DATABASE,
            StagedResourceType.SCHEMA,
            StagedResourceType.TABLE,
            StagedResourceType.FIELD,
            StagedResourceType.ENDPOINT,
        ]

    def test_get_website_monitor_resource_types(self):
        assert StagedResourceType.get_website_monitor_resource_types() == [
            StagedResourceType.COOKIE,
            StagedResourceType.BROWSER_REQUEST,
            StagedResourceType.IMAGE_BROWSER_REQUEST,
            StagedResourceType.IFRAME_BROWSER_REQUEST,
            StagedResourceType.JAVASCRIPT_BROWSER_REQUEST,
        ]

    @pytest.mark.parametrize(
        "resource_type_string,expected_resource_type",
        [
            ("Database", StagedResourceType.DATABASE),
            ("Schema", StagedResourceType.SCHEMA),
            ("Table", StagedResourceType.TABLE),
            ("Field", StagedResourceType.FIELD),
            ("Endpoint", StagedResourceType.ENDPOINT),
            ("Cookie", StagedResourceType.COOKIE),
            ("Browser request", StagedResourceType.BROWSER_REQUEST),
            ("Image", StagedResourceType.IMAGE_BROWSER_REQUEST),
            ("iFrame", StagedResourceType.IFRAME_BROWSER_REQUEST),
            ("Javascript tag", StagedResourceType.JAVASCRIPT_BROWSER_REQUEST),
        ],
    )
    def test_can_instantiate_from_string(
        self, resource_type_string: str, expected_resource_type: StagedResourceType
    ):
        assert StagedResourceType(resource_type_string) == expected_resource_type
