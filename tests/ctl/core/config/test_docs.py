import os

import pytest
import toml

from fides.core.config import create


@pytest.fixture()
def remove_fides_dir(tmp_path) -> None:
    try:
        os.remove(tmp_path / ".fides/fides.toml")
        os.rmdir(tmp_path / ".fides")
    except FileNotFoundError:
        pass
    except NotADirectoryError:
        pass


@pytest.mark.unit
class TestCreateConfigFile:
    def test_create_config_file(
        self, config, tmp_path, capfd, remove_fides_dir
    ) -> None:
        config_path = create.create_config_file(config, tmp_path)

        fides_directory = tmp_path / ".fides"
        fides_file_path = fides_directory / "fides.toml"
        out, _ = capfd.readouterr()

        assert f"Created a '{fides_directory}' directory" in out
        assert f"Exported configuration file to: {fides_file_path}" in out
        assert config_path == str(fides_file_path)

    def test_create_config_file_dir_exists(
        self, config, tmp_path, capfd, remove_fides_dir
    ) -> None:
        fides_directory = tmp_path / ".fides"
        fides_directory.mkdir()
        fides_file_path = fides_directory / "fides.toml"

        config_path = create.create_config_file(config, tmp_path)

        out, _ = capfd.readouterr()

        assert f"Directory '{fides_directory}' already exists" in out
        assert f"Exported configuration file to: {fides_file_path}" in out
        assert config_path == str(fides_file_path)

    def test_create_config_file_exists(
        self, config, tmp_path, capfd, remove_fides_dir
    ) -> None:
        fides_directory = tmp_path / ".fides"
        fides_directory.mkdir()
        fides_file_path = fides_directory / "fides.toml"

        with open(fides_file_path, "w", encoding="utf-8") as f:
            toml.dump(config.dict(), f)

        config_path = create.create_config_file(config, tmp_path)

        out, _ = capfd.readouterr()

        assert f"Directory '{fides_directory}' already exists" in out
        assert f"Configuration file already exists: {fides_file_path}" in out
        assert config_path == str(fides_file_path)
