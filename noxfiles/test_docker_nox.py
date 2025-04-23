from docker_nox import generate_buildx_command


class TestGenerateBuildxCommand:
    def test_single_tag(self) -> None:
        actual_result = generate_buildx_command(
            image_tags=["foo"],
            docker_build_target="prod",
            dockerfile_path=".",
        )
        expected_result = (
            "docker",
            "buildx",
            "build",
            "--push",
            "--provenance=false",
            "--target=prod",
            "--platform",
            "linux/amd64,linux/arm64",
            ".",
            "--tag",
            "foo",
        )
        assert actual_result == expected_result

    def test_multiplte_tags(self) -> None:
        actual_result = generate_buildx_command(
            image_tags=["foo", "bar"],
            docker_build_target="prod",
            dockerfile_path=".",
        )
        expected_result = (
            "docker",
            "buildx",
            "build",
            "--push",
            "--provenance=false",
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
        actual_result = generate_buildx_command(
            image_tags=["foo", "bar"],
            docker_build_target="prod",
            dockerfile_path="other_path",
        )
        expected_result = (
            "docker",
            "buildx",
            "build",
            "--push",
            "--provenance=false",
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
