import pytest

from fides.api.schemas.partitioning.time_based_partitioning import TimeUnit


class TestTimeUnitParse:
    """Unit tests for the TimeUnit.parse helper."""

    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("day", TimeUnit.DAY),
            ("DAYS", TimeUnit.DAY),
            (" Week", TimeUnit.WEEK),
            ("weeks ", TimeUnit.WEEK),
            ("month", TimeUnit.MONTH),
            ("MONTHS", TimeUnit.MONTH),
            ("Year", TimeUnit.YEAR),
            ("YEARS", TimeUnit.YEAR),
        ],
    )
    def test_parse_valid(self, raw, expected):
        assert TimeUnit.parse(raw) is expected

    def test_parse_invalid(self):
        with pytest.raises(ValueError):
            TimeUnit.parse("fortnight")
