import pytest

from fides.api.schemas.property import Property, PropertyType


class TestPropertySchema:
    @pytest.mark.parametrize(
        "paths",
        [
            ["path1", "path2"],
            ("path1", "path2"),
            {"path1", "path2"},
        ],
    )
    def test_valid_paths(self, paths):
        data = {
            "name": "Test Property",
            "type": PropertyType.website,
            "experiences": [],
            "messaging_templates": [],
            "paths": paths,
        }
        prop = Property(**data)
        assert sorted(prop.paths) == ["path1", "path2"]

    @pytest.mark.parametrize(
        "paths",
        [
            "path1",
            123,
        ],
    )
    def test_invalid_paths(self, paths):
        data = {
            "name": "Test Property",
            "type": PropertyType.website,
            "experiences": [],
            "messaging_templates": [],
            "paths": paths,
        }
        with pytest.raises(ValueError):
            Property(**data)
