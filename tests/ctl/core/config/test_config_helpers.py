from unittest.mock import patch

import pytest
import toml

from fides.core.config import helpers


@pytest.mark.unit
class TestConfigHelpers:
    def test_load_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            helpers.load_file(["bad.toml"])

    def test_get_config_from_file(self, tmp_path):
        file = tmp_path / "fides.toml"
        with open(file, "w") as f:
            toml.dump(
                {
                    "section 1": {"sub 1": "value 1"},
                    "section 2": {"sub 2": "value 2", "sub 3": "value 3"},
                },
                f,
            )

        assert helpers.get_config_from_file(file, "section 2", "sub 2")

    @pytest.mark.parametrize(
        "section, option", [("good", "something"), ("bad", "something")]
    )
    def test_get_config_from_file_none(self, section, option, tmp_path):
        file = tmp_path / "fides.toml"
        with open(file, "w") as f:
            toml.dump({section: {option: "value"}}, f)

        assert helpers.get_config_from_file(file, "bad", "missing") is None

