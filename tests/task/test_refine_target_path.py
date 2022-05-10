from fidesops.graph.config import FieldPath
from fidesops.task.refine_target_path import (
    refine_target_path,
    build_refined_target_paths,
    join_detailed_path,
    _match_found,
)
from fidesops.util.collection_util import FIDESOPS_DO_NOT_MASK_INDEX


class TestRefineTargetPathToValue:
    """Test target paths built to specific matched values"""

    def test_refine_target_path_value_does_not_match(self):
        data = {"A": "a", "B": "b"}

        assert refine_target_path(data, ["A"], only=["b"]) == []

    def test_refine_target_path_to_scalar_value(self):
        data = {"A": "a", "B": "b"}
        assert refine_target_path(data, ["A"], only=["a"]) == [
            "A"
        ]  # Target path is unchanged

    def test_refine_target_path_to_scalar_from_multiple_options(self):
        data = {"A": "a", "B": "b"}
        assert refine_target_path(data, ["A"], only=["a", "b", "c"]) == [
            "A"
        ]  # Target path is unchanged

    def test_refine_target_path_to_nested_value(self):
        data = {"A": {"B": {"C": "D", "E": "F", "G": "G"}}}
        assert refine_target_path(data, ["A", "B", "C"], only=["D"]) == [
            "A",
            "B",
            "C",
        ]  # Target path is unchanged

    def test_refine_target_path_to_top_level_array(self):
        data = {"A": ["a", "b", "c"], "D": ["e", "f", "g"]}
        assert refine_target_path(data, ["A"], only=["c"]) == ["A", 2]

    def test_refine_target_path_to_nested_array(self):
        data = {"A": {"B": {"C": ["d", "e", "f"], "D": ["g", "h", "i"]}}}
        assert refine_target_path(data, ["A", "B", "C"], ["e"]) == ["A", "B", "C", 1]

    def test_refine_target_paths_to_multiple_indices_in_nested_arrays(self):
        data = {"A": {"B": {"C": ["d", "e", "f", "e", "e"], "D": ["g", "h", "i"]}}}
        assert refine_target_path(data, ["A", "B", "C"], only=["e"]) == [
            ["A", "B", "C", 1],
            ["A", "B", "C", 3],
            ["A", "B", "C", 4],
        ]

    def test_refine_target_path_to_embedded_object_in_arrays(self):
        data = {
            "A": [
                {"B": "C", "D": "E", "F": "G"},
                {"D": "J"},
                {"B": "I", "D": "K", "F": "J"},
            ]
        }
        assert refine_target_path(data, ["A", "F"], only=["G"]) == ["A", 0, "F"]

    def test_refine_target_path_to_multiple_embedded_objects_in_arrays(self):
        data = {
            "A": [
                {"B": "C", "D": "E", "F": "G"},
                {"D": "J"},
                {"B": "I", "D": "K", "F": "J"},
                {"B": "J", "D": "M", "F": "G"},
            ],
            "B": "C",
        }
        assert refine_target_path(data, ["A", "F"], only=["G"]) == [
            ["A", 0, "F"],
            ["A", 3, "F"],
        ]

    def test_refine_target_path_to_multiple_objects_from_multiple_possibilities(self):
        data = {
            "A": [
                {"B": "C", "D": "E", "F": "G"},
                {"D": "J"},
                {"B": "I", "D": "K", "F": "J"},
                {"B": "J", "D": "M", "F": "G"},
                {"B": "J", "D": "M", "F": "H"},
                {"B": "J", "D": "M", "F": "I"},
            ],
            "B": "C",
        }
        assert refine_target_path(data, ["A", "F"], only=["G", "I"]) == [
            ["A", 0, "F"],
            ["A", 3, "F"],
            ["A", 5, "F"],
        ]

    def test_refined_target_path_array_of_arrays(self):
        data = {"A": [["B", "C", "D", "C", "E"]], "C": ["E", "F"]}
        assert refine_target_path(data, ["A"], only=["C", "E"]) == [
            ["A", 0, 1],
            ["A", 0, 3],
            ["A", 0, 4],
        ]

    def test_refine_target_path_large_data(self, sample_data):
        result = refine_target_path(
            sample_data, ["months", "march", "crops"], ["swiss chard"]
        )
        assert result == [
            ["months", "march", 0, "crops", 0],
            ["months", "march", 0, "crops", 1],
        ]

        result = refine_target_path(sample_data, ["_id"], [12345])
        assert result == ["_id"]

        result = refine_target_path(sample_data, ["snacks"], ["pizza"])
        assert result == ["snacks", 0]

        result = refine_target_path(sample_data, ["thread", "comment"], ["com_0002"])
        assert result == [["thread", 1, "comment"], ["thread", 2, "comment"]]

        result = refine_target_path(sample_data, ["seats", "first_choice"], ["A2"])
        assert result == ["seats", "first_choice"]

        result = refine_target_path(sample_data, ["upgrades", "books"], ["SICP"])
        assert result == ["upgrades", "books", 1]

        result = refine_target_path(sample_data, ["other_flights", "CHO"], ["1 PM"])
        assert result == [
            ["other_flights", 0, "CHO", 1],
            ["other_flights", 1, "CHO", 1],
        ]

        result = refine_target_path(sample_data, ["bad_path"], ["bad match"])
        assert result == []

        result = refine_target_path(sample_data, ["hello"], only=[2])
        assert result == [["hello", 1], ["hello", 4]]

        result = refine_target_path(
            sample_data, ["months", "july", "crops"], ["watermelon", "grapes"]
        )
        assert result == [
            ["months", "july", 0, "crops", 0],
            ["months", "july", 0, "crops", 2],
        ]

        result = refine_target_path(sample_data, ["weights"], [4])
        assert result == ["weights", 1, 1]

        result = refine_target_path(sample_data, ["toppings"], ["cheese"])
        assert result == [["toppings", 0, 1, 1], ["toppings", 0, 1, 2]]

        result = refine_target_path(sample_data, ["A", "C", "M"], ["n"])
        assert result == [["A", "C", 0, "M", 1], ["A", "C", 0, "M", 2]]

        result = refine_target_path(sample_data, [], ["pizza"])
        assert result == []

        result = refine_target_path(sample_data, ["C"], ["B"])
        assert result == [["C", 0, 1], ["C", 0, 3], ["C", 1, 2], ["C", 1, 3]]

        result = refine_target_path(sample_data, ["D"], ["B"])
        assert result == [
            ["D", 0, 0, 1],
            ["D", 0, 0, 3],
            ["D", 0, 1, 2],
            ["D", 0, 1, 3],
            ["D", 1, 0, 1],
            ["D", 1, 0, 3],
            ["D", 1, 1, 2],
            ["D", 1, 1, 3],
        ]

        result = refine_target_path(sample_data, ["E"], ["B"])
        assert result == [
            ["E", 0, 0, 0],
            ["E", 0, 1, 0, 1],
            ["E", 0, 1, 0, 3],
            ["E", 0, 1, 1, 2],
            ["E", 0, 1, 1, 3],
        ]

        result = refine_target_path(sample_data, ["F"], ["a"])
        assert result == [["F", 0], ["F", 1, 1], ["F", 1, 2, 0, 1], ["F", 1, 2, 0, 2]]


class TestRefineTargetPathToAll:
    """Test expanding target path to all possible paths"""

    def test_refine_target_path_to_scalar_value(self):
        data = {"A": "a", "B": "b"}
        assert refine_target_path(data, ["A"]) == ["A"]

    def test_refine_target_path_to_nested_value(self):
        data = {"A": {"B": {"C": "D", "E": "F", "G": "G"}}}
        assert refine_target_path(data, ["A", "B", "C"]) == [
            "A",
            "B",
            "C",
        ]  # Target path is unchanged

    def test_refine_target_path_to_top_level_array(self):
        data = {"A": ["a", "b", "c"], "D": ["e", "f", "g"]}
        assert refine_target_path(data, ["A"]) == [["A", 0], ["A", 1], ["A", 2]]

    def test_refine_target_path_to_nested_array(self):
        data = {"A": {"B": {"C": ["d", "e", "f"], "D": ["g", "h", "i"]}}}
        assert refine_target_path(data, ["A", "B", "C"]) == [
            ["A", "B", "C", 0],
            ["A", "B", "C", 1],
            ["A", "B", "C", 2],
        ]

    def test_refine_target_path_to_embedded_object_in_arrays(self):
        data = {
            "A": [
                {"B": "C", "D": "E", "F": "G"},
                {"D": "J"},
                {"B": "I", "D": "K", "F": "J"},
            ]
        }
        assert refine_target_path(data, ["A", "F"]) == [["A", 0, "F"], ["A", 2, "F"]]

    def test_refined_target_path_array_of_arrays(self):
        data = {"A": [["B", "C", "D", "C", "E"]], "C": ["E", "F"]}
        assert refine_target_path(data, ["A"]) == [
            ["A", 0, 0],
            ["A", 0, 1],
            ["A", 0, 2],
            ["A", 0, 3],
            ["A", 0, 4],
        ]


class TestBuildRefinedTargetPaths:
    def test_build_refined_paths_bad_path(self):
        row = {"A": [1, 2, 3], "B": "C"}
        result = build_refined_target_paths(row, {FieldPath("A", "B", "C"): ["F"]})
        assert result == []

    def test_one_match_makes_list_of_lists(self):
        row = {"A": [1, 2, 3], "B": "C"}
        result = build_refined_target_paths(row, {FieldPath("A"): [1]})
        assert result == [["A", 0]]

    def test_two_matches_makes_list_of_lists(self):
        row = {"A": [1, 2, 3], "B": "C"}
        result = build_refined_target_paths(row, {FieldPath("A"): [1, 3]})
        assert result == [["A", 0], ["A", 2]]

    def test_list_of_list_of_lists(self):
        row = {"A": [[[1, 2, 3]], [[4, 5, 6]]], "B": "C"}
        result = build_refined_target_paths(row, {FieldPath("A"): [1, 3]})
        assert result == [["A", 0, 0, 0], ["A", 0, 0, 2]]

    def test_build_refined_path_multiple_matches_in_array(self):
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

        result = build_refined_target_paths(
            row, {FieldPath("J", "K"): [2], FieldPath("J", "J"): [4]}
        )
        assert result == [["J", 3, "K"], ["J", 1, "J"], ["J", 3, "J"]]

    def test_build_refined_target_paths_large_data(self, sample_data):
        incoming_paths = {
            FieldPath(
                "F",
            ): ["a"],
            FieldPath("snacks"): ["pizza"],
            FieldPath("thread", "comment"): ["com_0002"],
        }
        result = build_refined_target_paths(sample_data, incoming_paths)
        assert result == [
            ["F", 0],
            ["snacks", 0],
            ["F", 1, 1],
            ["thread", 1, "comment"],
            ["thread", 2, "comment"],
            ["F", 1, 2, 0, 1],
            ["F", 1, 2, 0, 2],
        ]


def test_join_detailed_path():
    assert join_detailed_path(["A", 0, 1, 2]) == "A.0.1.2"

    assert join_detailed_path([0]) == "0"

    assert join_detailed_path(["A"]) == "A"

    assert join_detailed_path([]) == ""


def test_match_found():
    assert _match_found(FIDESOPS_DO_NOT_MASK_INDEX) is False

    assert _match_found("A") is True

    assert _match_found(1) is True

    assert _match_found("A", ["B"]) is False

    assert _match_found("A", ["A", "B"]) is True
