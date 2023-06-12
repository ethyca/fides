import pytest

from docker_nox import (
    generate_multiplatform_buildx_command,
    get_buildx_commands,
)
from constants_nox import (
    DEV_TAG_SUFFIX,
    PRERELEASE_TAG_SUFFIX,
    RC_TAG_SUFFIX,
)


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
        "tags,expected_commands",
        [
            (
                [DEV_TAG_SUFFIX],
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
                [PRERELEASE_TAG_SUFFIX],
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
                [RC_TAG_SUFFIX],
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
            (
                ["2.9.0a4"],
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
                ],
            ),
            (
                ["2.9.0", "latest"],
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
            ),
        ],
    )
    def test_tags(
        self,
        tags,
        expected_commands,
    ) -> None:
        buildx_commands = get_buildx_commands(tags)

        assert buildx_commands == expected_commands
