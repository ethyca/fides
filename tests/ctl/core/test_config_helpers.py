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

    def test_create_config_file(self, config, tmp_path, capfd):
        config_path = helpers.create_config_file(config, tmp_path)

        fides_directory = tmp_path / ".fides"
        fides_file_path = fides_directory / "fides.toml"
        out, _ = capfd.readouterr()

        assert f"Created a '{fides_directory}' directory" in out
        assert f"Created a fides config file: {fides_file_path}" in out
        assert config_path == str(fides_file_path)

    def test_create_config_file_dir_exists(self, config, tmp_path, capfd):
        fides_directory = tmp_path / ".fides"
        fides_directory.mkdir()
        fides_file_path = fides_directory / "fides.toml"

        config_path = helpers.create_config_file(config, tmp_path)

        out, _ = capfd.readouterr()

        assert f"Directory '{fides_directory}' already exists" in out
        assert f"Created a fides config file: {fides_file_path}" in out
        assert config_path == str(fides_file_path)

    def test_create_config_file_exists(self, config, tmp_path, capfd):
        fides_directory = tmp_path / ".fides"
        fides_directory.mkdir()
        fides_file_path = fides_directory / "fides.toml"

        with open(fides_file_path, "w", encoding="utf-8") as f:
            toml.dump(config.dict(), f)

        config_path = helpers.create_config_file(config, tmp_path)

        out, _ = capfd.readouterr()

        assert f"Directory '{fides_directory}' already exists" in out
        assert f"Configuration file already exists: {fides_file_path}" in out
        assert config_path == str(fides_file_path)

    @patch("fides.core.config.helpers.get_config_from_file")
    def test_check_required_webserver_config_values(self, mock_get_config, capfd):
        mock_get_config.return_value = None

        with pytest.raises(SystemExit):
            helpers.check_required_webserver_config_values()
            out, _ = capfd.readouterr()

            assert "app_encryption_key" in out
            assert "oauth_root_client_id" in out
            assert "oauth_root_client_secret" in out

    @patch("fides.core.config.helpers.get_config_from_file")
    def test_check_required_webserver_config_values_file_not_found(
        self, mock_get_config, capfd
    ):
        mock_get_config.side_effect = FileNotFoundError

        with pytest.raises(SystemExit):
            helpers.check_required_webserver_config_values()
            out, _ = capfd.readouterr()

            assert "app_encryption_key" in out
            assert "oauth_root_client_id" in out
            assert "oauth_root_client_secret" in out
