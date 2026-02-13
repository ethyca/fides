from subprocess import CalledProcessError
from unittest import mock

import pytest

import fides
from fides.core import deploy


@pytest.mark.unit
class TestDeploy:
    def test_convert_semver_to_list(self):
        assert deploy.convert_semver_to_list("0.1.0") == [0, 1, 0]

    @pytest.mark.parametrize(
        "semver_1, semver_2, expected",
        [
            ([2, 10, 3], [2, 10, 2], True),
            ([3, 1, 3], [2, 10, 2], True),
            ([2, 10, 2], [2, 10, 2], True),
            ([1, 1, 3], [2, 10, 2], False),
            ([1, 10, 1], [1, 1, 0], True),
            ([1, 1, 0], [1, 10, 1], False),
            ([1, 1, 1], [1, 1, 0], True),
            ([1, 1, 0], [1, 1, 1], False),
        ],
    )
    def test_compare_semvers(self, semver_1, semver_2, expected):
        assert deploy.compare_semvers(semver_1, semver_2) is expected

    @mock.patch("fides.core.deploy.sys")
    def test_check_virtualenv(self, mock_sys):
        # Emulate non-virtual environment
        mock_sys.prefix = (
            "/usr/local/opt/python@3.9/Frameworks/Python.framework/Versions/3.9"
        )
        mock_sys.base_prefix = (
            "/usr/local/opt/python@3.9/Frameworks/Python.framework/Versions/3.9"
        )
        assert deploy.check_virtualenv() is False

        # Emulate virtual environment
        mock_sys.prefix = "/Users/fidesuser/fides/venv"
        mock_sys.base_prefix = (
            "/usr/local/opt/python@3.9/Frameworks/Python.framework/Versions/3.9"
        )
        assert deploy.check_virtualenv() is True


@pytest.mark.unit
class TestCheckDockerVersion:
    def test_docker_version_exception(self):
        with pytest.raises(SystemExit):
            result = deploy.check_docker_version("30.1.24")
            assert result


@pytest.mark.unit
@mock.patch("fides.core.deploy.run_shell")
def test_pull_specific_docker_image_with_custom_image(mock_run_shell):
    custom_image = "registry.example.com/fides:2.54.0"
    version = "2.54.0"

    with mock.patch.object(fides, "__version__", version):
        deploy.pull_specific_docker_image(custom_image)

    expected_calls = [
        mock.call(f"docker pull {custom_image}"),
        mock.call("docker tag registry.example.com/fides:2.54.0 ethyca/fides:local"),
        mock.call("docker pull ethyca/fides-privacy-center:2.54.0"),
        mock.call(
            "docker tag ethyca/fides-privacy-center:2.54.0 ethyca/fides-privacy-center:local"
        ),
        mock.call("docker pull ethyca/fides-sample-app:2.54.0"),
        mock.call(
            "docker tag ethyca/fides-sample-app:2.54.0 ethyca/fides-sample-app:local"
        ),
    ]
    assert mock_run_shell.call_args_list == expected_calls


@pytest.mark.unit
@mock.patch("fides.core.deploy.run_shell")
def test_pull_specific_docker_image_custom_image_fallback(mock_run_shell):
    custom_image = "registry.example.com/fides:2.54.0"
    version = "2.54.0"

    def side_effect(command):  # pylint: disable=unused-argument
        if command in {
            "docker pull ethyca/fides-privacy-center:2.54.0",
            "docker pull ethyca/fides-sample-app:2.54.0",
        }:
            raise CalledProcessError(1, command)

    mock_run_shell.side_effect = side_effect

    with mock.patch.object(fides, "__version__", version):
        deploy.pull_specific_docker_image(custom_image)

    called_commands = {call.args[0] for call in mock_run_shell.call_args_list}
    assert "docker pull ethyca/fides-privacy-center:dev" in called_commands
    assert "docker pull ethyca/fides-sample-app:dev" in called_commands
    assert "docker pull ethyca/fides:dev" not in called_commands
