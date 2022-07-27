from fidesops.graph.config import FieldPath
from fidesops.task.consolidate_query_matches import consolidate_query_matches


def test_consolidate_query_matches():
    # Matching scalar returned
    input_data = {"B": 55}
    target_path = FieldPath("B")
    assert consolidate_query_matches(input_data, target_path) == [55]

    # Matching array returned as-is
    input_data = {"A": [1, 2, 3]}
    target_path = FieldPath("A")
    assert consolidate_query_matches(input_data, target_path) == [1, 2, 3]

    # Array of embedded objects have multiple matching sub-paths merged
    field_path = FieldPath("A", "B")
    input_data = {"A": [{"B": 1, "C": 2}, {"B": 3, "C": 4}, {"B": 5, "C": 6}]}
    assert consolidate_query_matches(input_data, field_path) == [1, 3, 5]

    # Nested array returned
    input_data = {"A": {"B": {"C": [9, 8, 7]}}, "D": {"E": {"F": "G"}}}
    field_path = FieldPath("A", "B", "C")
    assert consolidate_query_matches(input_data, field_path) == [9, 8, 7]

    # Array of arrays are merged
    input_data = {"A": [[5, 6], [7, 8], [9, 10]], "B": [[5, 6], [7, 8], [9, 10]]}
    field_path = FieldPath("A")
    assert consolidate_query_matches(input_data, field_path) == [5, 6, 7, 8, 9, 10]

    # Array of arrays of embedded objects are merged
    input_data = {
        "A": [
            [{"B": 1, "C": 2, "D": [3]}, {}],
            [{"B": 3, "C": 4, "D": [5]}, {"B": 77, "C": 88, "D": [99]}],
        ],
        "B": [[5, 6], [7, 8], [9, 10]],
    }
    field_path = FieldPath("A", "D")
    assert consolidate_query_matches(input_data, field_path) == [3, 5, 99]

    # Target path doesn't exist in data
    field_path = FieldPath("A", "E", "X")
    input_data = {"A": [{"B": 1, "C": 2}, {"B": 3, "C": 4}, {"B": 5, "C": 6}]}
    assert consolidate_query_matches(input_data, field_path) == []

    # No field path
    field_path = FieldPath()
    input_data = {"A": [{"B": 1, "C": 2}, {"B": 3, "C": 4}, {"B": 5, "C": 6}]}
    assert consolidate_query_matches(input_data, field_path) == []
