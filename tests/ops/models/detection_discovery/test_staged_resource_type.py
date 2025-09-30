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

    @pytest.mark.parametrize(
        "resource_type,is_datastore,is_website_monitor",
        [
            (StagedResourceType.DATABASE, True, False),
            (StagedResourceType.SCHEMA, True, False),
            (StagedResourceType.TABLE, True, False),
            (StagedResourceType.FIELD, True, False),
            (StagedResourceType.ENDPOINT, True, False),
            (StagedResourceType.COOKIE, False, True),
            (StagedResourceType.BROWSER_REQUEST, False, True),
            (StagedResourceType.IMAGE_BROWSER_REQUEST, False, True),
            (StagedResourceType.IFRAME_BROWSER_REQUEST, False, True),
            (StagedResourceType.JAVASCRIPT_BROWSER_REQUEST, False, True),
        ],
    )
    def test_is_datastore_or_is_website_monitor(
        self,
        resource_type: StagedResourceType,
        is_datastore: bool,
        is_website_monitor: bool,
    ):
        assert resource_type.is_datastore_resource() == is_datastore
        assert resource_type.is_website_monitor_resource() == is_website_monitor

    def test_all_resource_types_are_either_datastore_or_website_monitor(self):
        """
        Tests that all resource types are either datastore or website monitor.
        If a new resource type is added to the enum but not to either of the
        datastore or website monitor lists, the test will fail.
        """
        for resource_type in StagedResourceType:
            assert (
                resource_type.is_datastore_resource()
                or resource_type.is_website_monitor_resource()
            )
