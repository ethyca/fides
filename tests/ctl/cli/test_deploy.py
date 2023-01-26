import pytest

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
