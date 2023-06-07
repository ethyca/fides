from unittest import mock

import pytest

from docker_nox import generate_multiplatform_buildx_command, push


class TestBuildxPrivacyCenter:
    def test_single_tag(self) -> None:
        actual_result = generate_multiplatform_buildx_command(["foo"], "prod")
        expected_result = (
            "docker",
            "buildx",
            "build",
            "--push",
            "--target=prod",
            "--platform",
            "linux/amd64,linux/arm64",
            ".",
            "--tag",
            "foo",
        )
        assert actual_result == expected_result

    def test_multiplte_tags(self) -> None:
        actual_result = generate_multiplatform_buildx_command(["foo", "bar"], "prod")
        expected_result = (
            "docker",
            "buildx",
            "build",
            "--push",
            "--target=prod",
            "--platform",
            "linux/amd64,linux/arm64",
            ".",
            "--tag",
            "foo",
            "--tag",
            "bar",
        )
        assert actual_result == expected_result

    def test_different_path(self) -> None:
        actual_result = generate_multiplatform_buildx_command(
            ["foo", "bar"], "prod", "other_path"
        )
        expected_result = (
            "docker",
            "buildx",
            "build",
            "--push",
            "--target=prod",
            "--platform",
            "linux/amd64,linux/arm64",
            "other_path",
            "--tag",
            "foo",
            "--tag",
            "bar",
        )
        assert actual_result == expected_result

    @pytest.mark.parametrize(
        "tag,expected_commands",
        [
            (
                "dev",
                [
                    mock.call.run(
                        "docker",
                        "buildx",
                        "build",
                        "--push",
                        "--target=prod",
                        "--platform",
                        "linux/amd64,linux/arm64",
                        ".",
                        "--tag",
                        "ethyca/fides:dev",
                        external=True,
                    ),
                    mock.call.run(
                        "docker",
                        "buildx",
                        "build",
                        "--push",
                        "--target=prod_pc",
                        "--platform",
                        "linux/amd64,linux/arm64",
                        ".",
                        "--tag",
                        "ethyca/fides-privacy-center:dev",
                        external=True,
                    ),
                    mock.call.run(
                        "docker",
                        "buildx",
                        "build",
                        "--push",
                        "--target=prod",
                        "--platform",
                        "linux/amd64,linux/arm64",
                        "clients/sample-app",
                        "--tag",
                        "ethyca/fides-sample-app:dev",
                        external=True,
                    ),
                ],
            ),
            (
                "prerelease",
                [
                    mock.call.run(
                        "docker",
                        "buildx",
                        "build",
                        "--push",
                        "--target=prod",
                        "--platform",
                        "linux/amd64,linux/arm64",
                        ".",
                        "--tag",
                        "ethyca/fides:prerelease",
                        external=True,
                    ),
                    mock.call.run(
                        "docker",
                        "buildx",
                        "build",
                        "--push",
                        "--target=prod_pc",
                        "--platform",
                        "linux/amd64,linux/arm64",
                        ".",
                        "--tag",
                        "ethyca/fides-privacy-center:prerelease",
                        external=True,
                    ),
                    mock.call.run(
                        "docker",
                        "buildx",
                        "build",
                        "--push",
                        "--target=prod",
                        "--platform",
                        "linux/amd64,linux/arm64",
                        "clients/sample-app",
                        "--tag",
                        "ethyca/fides-sample-app:prerelease",
                        external=True,
                    ),
                ],
            ),
            (
                "rc",
                [
                    mock.call.run(
                        "docker",
                        "buildx",
                        "build",
                        "--push",
                        "--target=prod",
                        "--platform",
                        "linux/amd64,linux/arm64",
                        ".",
                        "--tag",
                        "ethyca/fides:rc",
                        external=True,
                    ),
                    mock.call.run(
                        "docker",
                        "buildx",
                        "build",
                        "--push",
                        "--target=prod_pc",
                        "--platform",
                        "linux/amd64,linux/arm64",
                        ".",
                        "--tag",
                        "ethyca/fides-privacy-center:rc",
                        external=True,
                    ),
                    mock.call.run(
                        "docker",
                        "buildx",
                        "build",
                        "--push",
                        "--target=prod",
                        "--platform",
                        "linux/amd64,linux/arm64",
                        "clients/sample-app",
                        "--tag",
                        "ethyca/fides-sample-app:rc",
                        external=True,
                    ),
                ],
            ),
            (
                "git-tag",
                [
                    mock.call.run(
                        "docker",
                        "buildx",
                        "build",
                        "--push",
                        "--target=prod",
                        "--platform",
                        "linux/amd64,linux/arm64",
                        ".",
                        "--tag",
                        "ethyca/fides:2.9.0a4",
                        external=True,
                    ),
                    mock.call.run(
                        "docker",
                        "buildx",
                        "build",
                        "--push",
                        "--target=prod_pc",
                        "--platform",
                        "linux/amd64,linux/arm64",
                        ".",
                        "--tag",
                        "ethyca/fides-privacy-center:2.9.0a4",
                        external=True,
                    ),
                    mock.call.run(
                        "docker",
                        "buildx",
                        "build",
                        "--push",
                        "--target=prod",
                        "--platform",
                        "linux/amd64,linux/arm64",
                        "clients/sample-app",
                        "--tag",
                        "ethyca/fides-sample-app:2.9.0a4",
                        external=True,
                    ),
                ],
            ),
            (
                "prod",
                [
                    mock.call.run(
                        "docker",
                        "buildx",
                        "build",
                        "--push",
                        "--target=prod",
                        "--platform",
                        "linux/amd64,linux/arm64",
                        ".",
                        "--tag",
                        "ethyca/fides:2.9.0",
                        "--tag",
                        "ethyca/fides:latest",
                        external=True,
                    ),
                    mock.call.run(
                        "docker",
                        "buildx",
                        "build",
                        "--push",
                        "--target=prod_pc",
                        "--platform",
                        "linux/amd64,linux/arm64",
                        ".",
                        "--tag",
                        "ethyca/fides-privacy-center:2.9.0",
                        "--tag",
                        "ethyca/fides-privacy-center:latest",
                        external=True,
                    ),
                    mock.call.run(
                        "docker",
                        "buildx",
                        "build",
                        "--push",
                        "--target=prod",
                        "--platform",
                        "linux/amd64,linux/arm64",
                        "clients/sample-app",
                        "--tag",
                        "ethyca/fides-sample-app:2.9.0",
                        "--tag",
                        "ethyca/fides-sample-app:latest",
                        external=True,
                    ),
                ],
            ),
        ],
    )
    @mock.patch("docker_nox.get_current_tag")
    @mock.patch("docker_nox.verify_git_tag")
    @mock.patch("nox.Session.run")
    def test_nox_push(
        self,
        mock_session_run: mock.MagicMock,
        mock_verify_git_tag: mock.MagicMock,
        mock_get_current_tag: mock.MagicMock,
        tag,
        expected_commands,
    ):
        mock_verify_git_tag.return_value = "2.9.0a4"
        mock_get_current_tag.return_value = "2.9.0"
        push(mock_session_run, tag)
        # first call to session.run is a separate call we're not evaluating here
        assert mock_session_run.mock_calls[1:] == expected_commands
