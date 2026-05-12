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

    def test_get_cloud_infra_resource_types(self):
        assert StagedResourceType.get_cloud_infra_resource_types() == [
            StagedResourceType.CLOUD_INFRA,
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
            ("Cloud Infrastructure", StagedResourceType.CLOUD_INFRA),
        ],
    )
    def test_can_instantiate_from_string(
        self, resource_type_string: str, expected_resource_type: StagedResourceType
    ):
        assert StagedResourceType(resource_type_string) == expected_resource_type

    @pytest.mark.parametrize(
        "resource_type,is_datastore,is_website_monitor,is_cloud_infra",
        [
            (StagedResourceType.DATABASE, True, False, False),
            (StagedResourceType.SCHEMA, True, False, False),
            (StagedResourceType.TABLE, True, False, False),
            (StagedResourceType.FIELD, True, False, False),
            (StagedResourceType.ENDPOINT, True, False, False),
            (StagedResourceType.COOKIE, False, True, False),
            (StagedResourceType.BROWSER_REQUEST, False, True, False),
            (StagedResourceType.IMAGE_BROWSER_REQUEST, False, True, False),
            (StagedResourceType.IFRAME_BROWSER_REQUEST, False, True, False),
            (StagedResourceType.JAVASCRIPT_BROWSER_REQUEST, False, True, False),
            (StagedResourceType.CLOUD_INFRA, False, False, True),
        ],
    )
    def test_is_datastore_or_is_website_monitor_or_is_cloud_infra(
        self,
        resource_type: StagedResourceType,
        is_datastore: bool,
        is_website_monitor: bool,
        is_cloud_infra: bool,
    ):
        assert resource_type.is_datastore_resource() == is_datastore
        assert resource_type.is_website_monitor_resource() == is_website_monitor
        assert resource_type.is_cloud_infra_resource() == is_cloud_infra

    def test_all_resource_types_belong_to_exactly_one_category(self):
        """
        Every resource type must belong to exactly one monitor category.
        If a new type is added to the enum but not to any category list, this test fails.
        """
        for resource_type in StagedResourceType:
            categories = [
                resource_type.is_datastore_resource(),
                resource_type.is_website_monitor_resource(),
                resource_type.is_cloud_infra_resource(),
            ]
            assert sum(categories) == 1, (
                f"{resource_type} belongs to {sum(categories)} categories, expected exactly 1"
            )
