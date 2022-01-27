import pytest

from fidesops.common_exceptions import FidesopsException
from fidesops.util.nested_utils import unflatten_dict


def test_unflatten_dict():
    input_data = {"A.B": 1, "A.C": 2, "A.D.E": 3}
    assert unflatten_dict(input_data) == {"A": {"B": 1, "C": 2, "D": {"E": 3}}}

    input_data = {"A": 2, "B": 3, "C": 4}
    assert unflatten_dict(input_data) == input_data

    assert unflatten_dict({}) == {}

    assert unflatten_dict({'A.B': 1, 'A.B': 2}) == {"A": {"B": 2}}  # Conflicting values, second value is retained

    input_data = {"A.B": 1, "A": 2, "A.C": 3}
    # You don't want to pass in input data like this, you have conflicts here -
    with pytest.raises(FidesopsException):
        unflatten_dict(input_data)

    with pytest.raises(FidesopsException):
        # Data passed in is not completely flattened
        unflatten_dict({'A.B.C': 1, 'A': {'B.D': 2}})

    with pytest.raises(IndexError):
        # unflatten_dict shouldn't be called with a None separator
        unflatten_dict({"": "hello"}, separator=None)
