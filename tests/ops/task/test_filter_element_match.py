import copy

import pytest
from fidesops.ops.graph.config import FieldPath
from fidesops.ops.task.filter_element_match import (
    _expand_array_paths_to_preserve,
    _remove_paths_from_row,
    filter_element_match,
)
from fidesops.ops.util.collection_util import FIDESOPS_DO_NOT_MASK_INDEX


class TestFilterElementMatch:
    def test_filter_element_match_no_paths(self):
        row = {"A": "B", "C": "D"}
        query_paths = {}
        assert filter_element_match(copy.deepcopy(row), query_paths) == row

    def test_filter_element_match_no_record(self):
        row = {}
        query_paths = {FieldPath("A", "B", "C"): [1, 2]}
        assert filter_element_match(row, query_paths) == {}

    def test_object_match_no_change(self):
        row = {"A": "B", "C": {"D": {"E": "F", "G": "H"}}}
        query_paths = {FieldPath("A"): ["B"], FieldPath("C", "D", "E"): ["F"]}
        assert filter_element_match(row, query_paths) == row

    def test_array_match(self):
        row = {
            "A": ["b", "c", "d", "e"],
            "C": {"D": {"E": ["g", "h", "i", "j"], "G": "H"}},
            "J": ["K", "L", "M"],
        }

        query_paths = {FieldPath("A"): ["c", "d"], FieldPath("C", "D", "E"): ["h", "i"]}
        assert filter_element_match(row, query_paths) == {
            "A": ["c", "d"],
            "C": {"D": {"E": ["h", "i"], "G": "H"}},
            "J": ["K", "L", "M"],
        }

    def test_multiple_embedded_objects_match(self):
        row = {
            "A": ["b", "c", "d", "e"],
            "C": {"D": {"E": ["g", "h", "i", "j"], "G": "H"}},
            "J": [
                {"K": 1, "J": 2},
                {"K": 3, "J": 4},
                {"K": 1, "J": 6},
                {"K": 2, "J": 4},
            ],
        }
        query_paths = {FieldPath("J", "K"): [2], FieldPath("J", "J"): [4]}
        assert filter_element_match(row, query_paths) == {
            "A": ["b", "c", "d", "e"],
            "C": {"D": {"E": ["g", "h", "i", "j"], "G": "H"}},
            "J": [{"K": 3, "J": 4}, {"K": 2, "J": 4}],
        }

    def test_filter_element_large_data(self, sample_data):
        incoming_paths = {
            FieldPath(
                "F",
            ): ["a"],
            FieldPath("snacks"): ["pizza"],
            FieldPath("thread", "comment"): ["com_0002"],
        }

        filtered_record = filter_element_match(sample_data, incoming_paths)
        assert filtered_record == {
            "_id": 12345,
            "thread": [
                {
                    "comment": "com_0002",
                    "message": "yep, got your message, looks like it works",
                    "chat_name": "Jane",
                },
                {"comment": "com_0002", "message": "hello!", "chat_name": "Jeanne"},
            ],
            "snacks": ["pizza"],
            "seats": {"first_choice": "A2", "second_choice": "B3"},
            "upgrades": {
                "magazines": ["Time", "People"],
                "books": ["Once upon a Time", "SICP"],
                "earplugs": True,
            },
            "other_flights": [
                {"DFW": ["11 AM", "12 PM"], "CHO": ["12 PM", "1 PM"]},
                {"DFW": ["2 AM", "12 PM"], "CHO": ["2 PM", "1 PM"]},
                {"DFW": ["3 AM", "2 AM"], "CHO": ["2 PM", "1:30 PM"]},
            ],
            "months": {
                "july": [
                    {
                        "activities": ["swimming", "hiking"],
                        "crops": ["watermelon", "cheese", "grapes"],
                    },
                    {"activities": ["tubing"], "crops": ["corn"]},
                ],
                "march": [
                    {
                        "activities": ["skiing", "bobsledding"],
                        "crops": ["swiss chard", "swiss chard"],
                    },
                    {"activities": ["hiking"], "crops": ["spinach"]},
                ],
            },
            "hello": [1, 2, 3, 4, 2],
            "weights": [[1, 2], [3, 4]],
            "toppings": [[["pepperoni", "salami"], ["pepperoni", "cheese", "cheese"]]],
            "A": {"C": [{"M": ["p", "n", "n"]}]},
            "C": [["A", "B", "C", "B"], ["G", "H", "B", "B"]],
            "D": [
                [["A", "B", "C", "B"], ["G", "H", "B", "B"]],
                [["A", "B", "C", "B"], ["G", "H", "B", "B"]],
            ],
            "E": [[["B"], [["A", "B", "C", "B"], ["G", "H", "B", "B"]]]],
            "F": ["a", ["a", [["a", "a"]]]],
        }


class TestFilterElementMatchReplaceIndices:
    """Test filter_element_match with delete_elements=False

    Instead of removing unmatched elements, unmatched elements are replaced with dummy text
    """

    def test_filter_element_match_no_paths(self):
        row = {"A": "B", "C": "D"}
        query_paths = {}
        assert (
            filter_element_match(copy.deepcopy(row), query_paths, delete_elements=False)
            == row
        )

    def test_filter_element_match_no_record(self):
        row = {}
        query_paths = {FieldPath("A", "B", "C"): [1, 2]}
        assert filter_element_match(row, query_paths, delete_elements=False) == {}

    def test_object_match_no_change(self):
        row = {"A": "B", "C": {"D": {"E": "F", "G": "H"}}}
        query_paths = {FieldPath("A"): ["B"], FieldPath("C", "D", "E"): ["F"]}
        assert filter_element_match(row, query_paths, delete_elements=False) == row

    def test_array_match(self):
        row = {
            "A": ["b", "c", "d", "e"],
            "C": {"D": {"E": ["g", "h", "i", "j"], "G": "H"}},
            "J": ["K", "L", "M"],
        }

        query_paths = {FieldPath("A"): ["c", "d"], FieldPath("C", "D", "E"): ["h", "i"]}
        assert filter_element_match(row, query_paths, delete_elements=False) == {
            "A": [FIDESOPS_DO_NOT_MASK_INDEX, "c", "d", FIDESOPS_DO_NOT_MASK_INDEX],
            "C": {
                "D": {
                    "E": [
                        FIDESOPS_DO_NOT_MASK_INDEX,
                        "h",
                        "i",
                        FIDESOPS_DO_NOT_MASK_INDEX,
                    ],
                    "G": "H",
                }
            },
            "J": ["K", "L", "M"],
        }

    def test_multiple_embedded_objects_match(self):
        row = {
            "A": ["b", "c", "d", "e"],
            "C": {"D": {"E": ["g", "h", "i", "j"], "G": "H"}},
            "J": [
                {"K": 1, "J": 2},
                {"K": 3, "J": 4},
                {"K": 1, "J": 6},
                {"K": 2, "J": 4},
            ],
        }
        query_paths = {FieldPath("J", "K"): [2], FieldPath("J", "J"): [4]}
        assert filter_element_match(row, query_paths, delete_elements=False) == {
            "A": ["b", "c", "d", "e"],
            "C": {"D": {"E": ["g", "h", "i", "j"], "G": "H"}},
            "J": [
                FIDESOPS_DO_NOT_MASK_INDEX,
                {"K": 3, "J": 4},
                FIDESOPS_DO_NOT_MASK_INDEX,
                {"K": 2, "J": 4},
            ],
        }

    def test_filter_element_large_data(self, sample_data):
        incoming_paths = {
            FieldPath(
                "F",
            ): ["a"],
            FieldPath("snacks"): ["pizza"],
            FieldPath("thread", "comment"): ["com_0002"],
        }
        filtered_record = filter_element_match(
            sample_data, incoming_paths, delete_elements=False
        )
        assert filtered_record == {
            "_id": 12345,
            "thread": [
                FIDESOPS_DO_NOT_MASK_INDEX,
                {
                    "comment": "com_0002",
                    "message": "yep, got your message, looks like it works",
                    "chat_name": "Jane",
                },
                {"comment": "com_0002", "message": "hello!", "chat_name": "Jeanne"},
            ],
            "snacks": ["pizza", FIDESOPS_DO_NOT_MASK_INDEX],
            "seats": {"first_choice": "A2", "second_choice": "B3"},
            "upgrades": {
                "magazines": ["Time", "People"],
                "books": ["Once upon a Time", "SICP"],
                "earplugs": True,
            },
            "other_flights": [
                {"DFW": ["11 AM", "12 PM"], "CHO": ["12 PM", "1 PM"]},
                {"DFW": ["2 AM", "12 PM"], "CHO": ["2 PM", "1 PM"]},
                {"DFW": ["3 AM", "2 AM"], "CHO": ["2 PM", "1:30 PM"]},
            ],
            "months": {
                "july": [
                    {
                        "activities": ["swimming", "hiking"],
                        "crops": ["watermelon", "cheese", "grapes"],
                    },
                    {"activities": ["tubing"], "crops": ["corn"]},
                ],
                "march": [
                    {
                        "activities": ["skiing", "bobsledding"],
                        "crops": ["swiss chard", "swiss chard"],
                    },
                    {"activities": ["hiking"], "crops": ["spinach"]},
                ],
            },
            "hello": [1, 2, 3, 4, 2],
            "weights": [[1, 2], [3, 4]],
            "toppings": [[["pepperoni", "salami"], ["pepperoni", "cheese", "cheese"]]],
            "A": {"C": [{"M": ["p", "n", "n"]}]},
            "C": [["A", "B", "C", "B"], ["G", "H", "B", "B"]],
            "D": [
                [["A", "B", "C", "B"], ["G", "H", "B", "B"]],
                [["A", "B", "C", "B"], ["G", "H", "B", "B"]],
            ],
            "E": [[["B"], [["A", "B", "C", "B"], ["G", "H", "B", "B"]]]],
            "F": [
                "a",
                [
                    FIDESOPS_DO_NOT_MASK_INDEX,
                    "a",
                    [[FIDESOPS_DO_NOT_MASK_INDEX, "a", "a"]],
                ],
            ],
        }


class TestRemovePathsFromRowDeleteElements:
    """Test sub-method remove_paths_from_row. Non-matching targeted array elements are removed."""

    @pytest.fixture(scope="function")
    def row(self):
        return {
            "A": "a",
            "B": [1, 2, 3, 4],
            "C": {"D": [4, 5, 6], "E": [7, 8, 9]},
            "D": [{"F": "g", "J": "j"}, {"F": "h", "J": "k"}, {"F": "i"}],
            "E": [[[1, 3, 2], [4, 5, 6]]],
            "G": [{"H": [{"I": {"J": ["a", "b", "c", "D"]}}]}],
        }

    def test_path_does_not_exist(self, row):
        modified_row = _remove_paths_from_row(row, {"E.F.G.H.1": [2]})
        assert row == modified_row

    def test_edge_case_index_not_in_row(self, row):
        """This shouldn't be hit, this is for completeness."""
        row = _remove_paths_from_row(row, {"B": [10]})
        assert row == row  # No change

    def test_remove_top_level_array_indices(self, row):
        row = _remove_paths_from_row(row, {"B": [1, 3]})
        assert row["B"] == [2, 4]

    def test_remove_index_from_nested_array(self, row):
        row = _remove_paths_from_row(row, {"C.D": [1]})
        assert row["C"]["D"] == [5]

    def test_remove_nested_document(self, row):
        row = _remove_paths_from_row(row, {"D": [2]})
        assert row["D"] == [{"F": "i"}]

    def test_remove_element_in_array_of_arrays(self, row):
        row = _remove_paths_from_row(row, {"E.0.1": [2]})
        assert row["E"] == [[[1, 3, 2], [6]]]

    def test_deeply_nested_path(self, row):
        row = _remove_paths_from_row(row, {"G.0.H.0.I.J": [0, 2]})
        assert row["G"] == [{"H": [{"I": {"J": ["a", "c"]}}]}]


class TestRemovePathsFromRowReplaceElements:
    """Test sub-method remove_paths_from_row with delete_elements=False.  Elements are replaced instead of removed"""

    @pytest.fixture(scope="function")
    def row(self):
        return {
            "A": "a",
            "B": [1, 2, 3, 4],
            "C": {"D": [4, 5, 6], "E": [7, 8, 9]},
            "D": [{"F": "g", "J": "j"}, {"F": "h", "J": "k"}, {"F": "i"}],
            "E": [[[1, 3, 2], [4, 5, 6]]],
            "G": [{"H": [{"I": {"J": ["a", "b", "c", "D"]}}]}],
        }

    def test_path_does_not_exist(self, row):
        modified_row = _remove_paths_from_row(
            row, {"E.F.G.H.1": [2]}, delete_elements=False
        )
        assert row == modified_row

    def test_edge_case_index_not_in_row(self, row):
        """This shouldn't be hit, this is for completeness."""
        row = _remove_paths_from_row(row, {"B": [10]}, delete_elements=False)
        assert row == row  # No change

    def test_remove_top_level_array_indices(self, row):
        row = _remove_paths_from_row(row, {"B": [1, 3]}, delete_elements=False)
        assert row["B"] == [
            FIDESOPS_DO_NOT_MASK_INDEX,
            2,
            FIDESOPS_DO_NOT_MASK_INDEX,
            4,
        ]

    def test_remove_index_from_nested_array(self, row):
        row = _remove_paths_from_row(row, {"C.D": [1]}, delete_elements=False)
        assert row["C"]["D"] == [
            FIDESOPS_DO_NOT_MASK_INDEX,
            5,
            FIDESOPS_DO_NOT_MASK_INDEX,
        ]

    def test_remove_nested_document(self, row):
        row = _remove_paths_from_row(row, {"D": [2]}, delete_elements=False)
        assert row["D"] == [
            FIDESOPS_DO_NOT_MASK_INDEX,
            FIDESOPS_DO_NOT_MASK_INDEX,
            {"F": "i"},
        ]

    def test_remove_element_in_array_of_arrays(self, row):
        row = _remove_paths_from_row(row, {"E.0.1": [2]}, delete_elements=False)
        assert row["E"] == [
            [[1, 3, 2], [FIDESOPS_DO_NOT_MASK_INDEX, FIDESOPS_DO_NOT_MASK_INDEX, 6]]
        ]

    def test_deeply_nested_path(self, row):
        row = _remove_paths_from_row(
            row, {"G.0.H.0.I.J": [0, 2]}, delete_elements=False
        )
        assert row["G"] == [
            {
                "H": [
                    {
                        "I": {
                            "J": [
                                "a",
                                FIDESOPS_DO_NOT_MASK_INDEX,
                                "c",
                                FIDESOPS_DO_NOT_MASK_INDEX,
                            ]
                        }
                    }
                ]
            }
        ]


class TestExpandArrayPathsToPreserve:
    """Test sub-method of filter_element_match"""

    def test_no_array_paths(self):
        """All of these paths are to nested fields in objects, no arrays are included here."""
        expanded_field_paths = [
            ["A", "B"],
            ["A", "C"],
            ["A", "D", "E", "F"],
            ["A", "G", "E", "I"],
        ]

        assert _expand_array_paths_to_preserve(expanded_field_paths) == {}

    def test_array_at_deepest_level(self):
        expanded_field_paths = [["A", "B", 1], ["A", "B", 19]]
        assert _expand_array_paths_to_preserve(expanded_field_paths) == {"A.B": [1, 19]}

    def test_array_of_objects(self):
        """Removing all indices from resource["A"]["B"] except for 0 and 1"""
        expanded_field_paths = [
            ["A", "B", 0, "C"],
            ["A", "B", 0, "D"],
            ["A", "B", 1, "C"],
        ]

        assert _expand_array_paths_to_preserve(expanded_field_paths) == {"A.B": [0, 1]}

    def test_no_paths(self):
        """Removing all indices from resource["A"]["B"] except for 0 and 1"""
        expanded_field_paths = []

        assert _expand_array_paths_to_preserve(expanded_field_paths) == {}

    def test_multiple_levels_of_paths(self):
        expanded_field_paths = [
            ["A", 1],
            ["B", "C", 2],
            ["B", "D", 3],
            ["C", "D", "E", 5],
            ["D", 1, "E", "F", "G"],
            ["D", 2, "E", "F"],
            ["E"],
        ]

        assert _expand_array_paths_to_preserve(expanded_field_paths) == {
            "A": [1],
            "B.C": [2],
            "B.D": [3],
            "C.D.E": [5],
            "D": [1, 2],
        }

    def test_multiple_matching_embedded_objects(self):
        expanded_field_paths = [["J", 3, "K"], ["J", 1, "J"], ["J", 3, "J"]]
        assert _expand_array_paths_to_preserve(expanded_field_paths) == {"J": [3, 1]}

    def test_nested_arrays_of_arrays(self):
        expanded_field_paths = [
            ["F", 0],
            ["snacks", 0],
            ["F", 1, 1],
            ["thread", 1, "comment"],
            ["thread", 2, "comment"],
            ["F", 1, 2, 0, 1],
            ["F", 1, 2, 0, 2],
            ["Non", "integer"],
        ]

        assert _expand_array_paths_to_preserve(expanded_field_paths) == {
            "F": [0, 1],
            "snacks": [0],
            "F.1": [1, 2],
            "thread": [1, 2],
            "F.1.2": [0],
            "F.1.2.0": [1, 2],
        }
