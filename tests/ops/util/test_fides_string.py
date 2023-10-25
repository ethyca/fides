import pytest

from fides.api.common_exceptions import DecodeFidesStringError
from fides.api.util.tcf.fides_string import build_fides_string, split_fides_string


def test_build_fides_string():
    tc_string = "CPz1hddPz1hddDxAAAENCZCgADgAAAAAAAAAAEBcABioAAA.YAAAAAAAAAA"
    ac_string = "1~1.35.41.101"

    # TC string but no AC string
    assert (
        build_fides_string(tc_string, "")
        == "CPz1hddPz1hddDxAAAENCZCgADgAAAAAAAAAAEBcABioAAA.YAAAAAAAAAA"
    )

    # Cannot build TC string with AC string alone
    with pytest.raises(DecodeFidesStringError):
        assert build_fides_string("", ac_string) == ",1~1.35.41.101"

    # Both TC String and AC String
    assert (
        build_fides_string(tc_string, ac_string)
        == "CPz1hddPz1hddDxAAAENCZCgADgAAAAAAAAAAEBcABioAAA.YAAAAAAAAAA,1~1.35.41.101"
    )

    # Neither TC String or AC String
    with pytest.raises(DecodeFidesStringError):
        build_fides_string("", "")

    with pytest.raises(DecodeFidesStringError):
        assert build_fides_string(None, None)


def test_split_fides_string():
    # No fides_string, so tc str and ac str are both None
    tc_str, ac_str = split_fides_string(None)
    assert tc_str is None
    assert ac_str is None

    # Only a TC string was supplied
    tc_str, ac_str = split_fides_string(
        "CPz1hddPz1hddDxAAAENCZCgADgAAAAAAAAAAEBcABioAAA.YAAAAAAAAAA"
    )
    assert tc_str == "CPz1hddPz1hddDxAAAENCZCgADgAAAAAAAAAAEBcABioAAA.YAAAAAAAAAA"
    assert ac_str is None

    # Both TC and AC string were supplied
    tc_str, ac_str = split_fides_string(
        "CPz1hddPz1hddDxAAAENCZCgADgAAAAAAAAAAEBcABioAAA.YAAAAAAAAAA,1~100.1000"
    )
    assert tc_str == "CPz1hddPz1hddDxAAAENCZCgADgAAAAAAAAAAEBcABioAAA.YAAAAAAAAAA"
    assert ac_str == "1~100.1000"

    # Only an AC string was supplied - invalid, because core TC string needed for complete signal
    with pytest.raises(DecodeFidesStringError):
        split_fides_string(",1~100.1000")

    # Three sections supplied, so we just take the first two.
    tc_str, ac_str = split_fides_string(
        "CPz1hddPz1hddDxAAAENCZCgADgAAAAAAAAAAEBcABioAAA.YAAAAAAAAAA,1~100.1000,another_section"
    )
    assert tc_str == "CPz1hddPz1hddDxAAAENCZCgADgAAAAAAAAAAEBcABioAAA.YAAAAAAAAAA"
    assert ac_str == "1~100.1000"

    # AC string with everything opted-out is supplied
    tc_str, ac_str = split_fides_string(
        "CPz1hddPz1hddDxAAAENCZCgADgAAAAAAAAAAEBcABioAAA.YAAAAAAAAAA,1~"
    )
    assert tc_str == "CPz1hddPz1hddDxAAAENCZCgADgAAAAAAAAAAEBcABioAAA.YAAAAAAAAAA"
    assert ac_str == "1~"

    # Empty AC String supplied
    tc_str, ac_str = split_fides_string(
        "CPz1hddPz1hddDxAAAENCZCgADgAAAAAAAAAAEBcABioAAA.YAAAAAAAAAA,"
    )
    assert tc_str == "CPz1hddPz1hddDxAAAENCZCgADgAAAAAAAAAAEBcABioAAA.YAAAAAAAAAA"
    assert ac_str == ""

    # Bad AC format
    with pytest.raises(DecodeFidesStringError):
        split_fides_string(
            "CPz1hddPz1hddDxAAAENCZCgADgAAAAAAAAAAEBcABioAAA.YAAAAAAAAAA,100.1000"
        )
