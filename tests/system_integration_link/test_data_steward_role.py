"""Tests for the Data Steward role scope assignments."""

from fides.api.oauth.roles import (
    DATA_STEWARD,
    ROLES_TO_SCOPES_MAPPING,
    RoleRegistryEnum,
    viewer_scopes,
)
from fides.common.api.scope_registry import (
    SYSTEM_INTEGRATION_LINK_CREATE_OR_UPDATE,
    SYSTEM_INTEGRATION_LINK_DELETE,
    SYSTEM_INTEGRATION_LINK_READ,
)


class TestDataStewardRole:
    def test_role_exists_in_enum(self) -> None:
        assert RoleRegistryEnum.data_steward.value == DATA_STEWARD

    def test_role_in_scopes_mapping(self) -> None:
        assert DATA_STEWARD in ROLES_TO_SCOPES_MAPPING

    def test_has_all_viewer_scopes(self) -> None:
        steward_scopes = set(ROLES_TO_SCOPES_MAPPING[DATA_STEWARD])
        for scope in viewer_scopes:
            assert scope in steward_scopes, f"Missing viewer scope: {scope}"

    def test_has_link_read(self) -> None:
        assert SYSTEM_INTEGRATION_LINK_READ in ROLES_TO_SCOPES_MAPPING[DATA_STEWARD]

    def test_has_link_create_or_update(self) -> None:
        assert (
            SYSTEM_INTEGRATION_LINK_CREATE_OR_UPDATE
            in ROLES_TO_SCOPES_MAPPING[DATA_STEWARD]
        )

    def test_has_link_delete(self) -> None:
        assert SYSTEM_INTEGRATION_LINK_DELETE in ROLES_TO_SCOPES_MAPPING[DATA_STEWARD]

    def test_no_unexpected_write_scopes(self) -> None:
        """Data steward should only have link write scopes beyond viewer."""
        steward = set(ROLES_TO_SCOPES_MAPPING[DATA_STEWARD])
        viewer = set(viewer_scopes)
        extra = steward - viewer
        assert extra == {
            SYSTEM_INTEGRATION_LINK_CREATE_OR_UPDATE,
            SYSTEM_INTEGRATION_LINK_DELETE,
        }
