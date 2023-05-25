from docker_nox import generate_multiplatform_buildx_command


class TestBuildxPrivacyCenter:
    def test_single_tag(self) -> None:
        actual_result = generate_multiplatform_buildx_command(["foo"], "prod")
        expected_result = (
            "docker",
            "build",
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
            "build",
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
            "build",
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
