from unittest import mock

import pytest

from docker_nox import generate_multiplatform_buildx_command, get_buildx_commands


class TestGenerateMultiplatformBuilxCommand:
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


class TestGetBuildxCommands:
    @pytest.mark.parametrize(
        "tag,expected_commands",
        [
            (
                "dev",
                [
                    (
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
                    ),
                    (
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
                    ),
                    (
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
                    ),
                ],
            ),
            (
                "prerelease",
                [
                    (
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
                    ),
                    (
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
                    ),
                    (
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
                    ),
                ],
            ),
            (
                "rc",
                [
                    (
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
                    ),
                    (
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
                    ),
                    (
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
                    ),
                ],
            ),
        ],
    )
    def test_standard_tags(
        self,
        tag,
        expected_commands,
    ):
        buildx_commands = get_buildx_commands(tag)

        assert buildx_commands == expected_commands

    @mock.patch("docker_nox.verify_git_tag")
    def test_git_tag_valid(
        self,
        mock_verify_git_tag,
    ):
        expected_result = [
            (
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
            ),
            (
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
            ),
            (
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
            ),
        ]
        mock_verify_git_tag.return_value = "2.9.0a4"
        buildx_commands = get_buildx_commands(mock_verify_git_tag)
        assert buildx_commands == expected_result

    @mock.patch("docker_nox.get_current_tag")
    def test_standard_tags(
        self,
        mock_get_current_tag,
    ):
        expected_result = (
            [
                (
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
                ),
                (
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
                ),
                (
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
                ),
            ],
        )
        mock_get_current_tag.return_value = "2.9.0"
        buildx_commands = get_buildx_commands(tag)

        assert buildx_commands == expected_result
