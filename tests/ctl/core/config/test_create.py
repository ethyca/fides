import os

import pytest
import toml
from py._path.local import LocalPath

from fides.cli.utils import request_analytics_consent
from fides.config import FidesConfig
from fides.config.create import (
    build_field_documentation,
    create_and_update_config_file,
    create_config_file,
    validate_generated_config,
)


@pytest.mark.unit
def test_create_and_update_config_file_opt_in(
    tmpdir: LocalPath, test_config: FidesConfig, monkeypatch
) -> None:
    """Opting in should skip the prompt and update the config file."""

    config_copy = test_config.model_copy(deep=True)

    def no_prompt(*args, **kwargs) -> bool:  # pragma: no cover - should not run
        raise AssertionError("Should not prompt for analytics when opting in")

    monkeypatch.setattr("fides.cli.utils.click.confirm", no_prompt)
    monkeypatch.setattr("fides.cli.utils.check_server_health", lambda *_, **__: None)
    monkeypatch.setattr("fides.cli.utils.is_user_registered", lambda *_: True)

    updated_config, config_path = create_and_update_config_file(
        config=config_copy, fides_directory_location=str(tmpdir), opt_in=True
    )

    assert updated_config.user.analytics_opt_out is False
    rendered_config = toml.load(config_path)
    assert rendered_config["user"]["analytics_opt_out"] is False


@pytest.mark.unit
def test_create_and_update_config_file_opt_out(
    tmpdir: LocalPath, test_config: FidesConfig, monkeypatch
) -> None:
    """Opting out should skip the prompt and persist the opt-out."""

    config_copy = test_config.model_copy(deep=True)
    config_copy.user.analytics_opt_out = False

    def no_prompt(*args, **kwargs) -> bool:  # pragma: no cover - should not run
        raise AssertionError("Should not prompt for analytics when opting out")

    monkeypatch.setattr("fides.cli.utils.click.confirm", no_prompt)

    updated_config, config_path = create_and_update_config_file(
        config=config_copy, fides_directory_location=str(tmpdir), opt_out=True
    )

    assert updated_config.user.analytics_opt_out is True
    rendered_config = toml.load(config_path)
    assert rendered_config["user"]["analytics_opt_out"] is True


@pytest.mark.unit
def test_request_analytics_consent_conflicting_flags(test_config: FidesConfig) -> None:
    config_copy = test_config.model_copy(deep=True)

    with pytest.raises(ValueError):
        request_analytics_consent(config_copy, opt_in=True, opt_out=True)


@pytest.mark.unit
def test_request_analytics_consent_opt_out_skips_prompt(
    test_config: FidesConfig, monkeypatch
) -> None:
    config_copy = test_config.model_copy(deep=True)
    config_copy.user.analytics_opt_out = False

    def no_prompt(*args, **kwargs) -> bool:  # pragma: no cover - should not run
        raise AssertionError("Should not prompt when opt-out provided")

    monkeypatch.setattr("fides.cli.utils.click.confirm", no_prompt)

    updated = request_analytics_consent(config_copy, opt_out=True)

    assert updated.user.analytics_opt_out is True


@pytest.mark.unit
def test_request_analytics_consent_env_false_opt_in(
    test_config: FidesConfig, monkeypatch
) -> None:
    config_copy = test_config.model_copy(deep=True)
    config_copy.user.analytics_opt_out = True

    monkeypatch.setenv("FIDES__USER__ANALYTICS_OPT_OUT", "false")
    monkeypatch.setattr("fides.cli.utils.click.confirm", lambda *_, **__: True)
    monkeypatch.setattr("fides.cli.utils.check_server_health", lambda *_, **__: None)
    monkeypatch.setattr("fides.cli.utils.is_user_registered", lambda *_: True)

    updated = request_analytics_consent(config_copy)

    assert updated.user.analytics_opt_out is False
    monkeypatch.delenv("FIDES__USER__ANALYTICS_OPT_OUT", raising=False)


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
