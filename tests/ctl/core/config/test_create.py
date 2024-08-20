import os

import pytest
import toml
from py._path.local import LocalPath

from fides.config import FidesConfig
from fides.config.create import (
    build_field_documentation,
    create_and_update_config_file,
    create_config_file,
    validate_generated_config,
)


@pytest.mark.unit
def test_create_and_update_config_file_opt_in(
    tmpdir: LocalPath, test_config: FidesConfig
) -> None:
    """Test that config creation works when opting-in to analytics."""

    create_and_update_config_file(
        config=test_config, fides_directory_location=str(tmpdir), opt_in=True
    )
    assert True


@pytest.mark.unit
class TestValidateGeneratedConfig:
    def test_valid_config(self) -> None:
        """Test that a minimal, but still valid config, can be built."""
        config_docs = toml.dumps({"database": {"server_port": "1234"}})
        validate_generated_config(config_docs)
        assert True

    def test_invalid_toml(self) -> None:
        """Test that a config with invalid toml throws an error."""
        with pytest.raises(ValueError):
            config_docs = "[database]\nsom_key = # Empty value, will cause error"
            validate_generated_config(config_docs)

    def test_includes_todo(self) -> None:
        """Test that a valid config that contains '# TODO' is invalid."""
        with pytest.raises(ValueError):
            config_docs = toml.dumps({"database": {"server_port": "# TODO"}})
            validate_generated_config(config_docs)
        assert True


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
        config_path = create_config_file(config, tmp_path)

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

        config_path = create_config_file(config, tmp_path)

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
            toml.dump(config.model_dump(mode="json"), f)

        config_path = create_config_file(config, tmp_path)

        out, _ = capfd.readouterr()

        assert f"Directory '{fides_directory}' already exists" in out
        assert f"Configuration file already exists: {fides_file_path}" in out
        assert config_path == str(fides_file_path)
