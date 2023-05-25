from docker_nox import publish_multiplatform_privacy_center


class TestBuildxPrivacyCenter:
    def test_single_tag(self) -> None:
        actual_result = publish_multiplatform_privacy_center(["foo"])
        expected_result = (
            "docker",
            "build",
            "--target=prod_pc",
            "--platform",
            "linux/amd64,linux/arm64",
            "--tag",
            "foo" ".",
        )
        assert actual_result == expected_result
