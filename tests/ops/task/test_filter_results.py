import copy
from datetime import datetime

import pytest
from bson import ObjectId
from fideslang.models import Dataset

from fides.api.graph.config import FieldPath
from fides.api.graph.graph import DatasetGraph
from fides.api.models.datasetconfig import convert_dataset_to_graph
from fides.api.task.filter_results import (
    filter_data_categories,
    remove_empty_containers,
    select_and_save_field,
    unpack_fides_connector_results,
)


@pytest.mark.unit
class TestFilterResults:
    def test_select_and_save_field(self):
        final_results = {}
        flat = {
            "A": "a",
            "B": "b",
            "C": ["d", "e", "f"],
            "D": ["g", "h", "i", "j"],
            "E": {
                "F": "g",
                "H": "i",
                "J": {"K": {"L": {"M": ["m", "n", "o"], "P": "p"}}, "N": {"O": "o"}},
            },
            "F": [{"G": "g", "H": "h"}, {"G": "h", "H": "i"}, {"G": "i", "H": "j"}],
            "H": [
                [
                    {"M": [1, 2, 3], "N": "n"},
                    {"M": [3, 2, 1], "N": "o"},
                    {"M": [1, 1, 1], "N": "p"},
                ],
                [
                    {"M": [4, 5, 6], "N": "q"},
                    {"M": [2, 2, 2], "N": "s"},
                    {"M": [], "N": "u"},
                ],
                [
                    {"M": [7, 8, 9], "N": "w"},
                    {"M": [6, 6, 6], "N": "y"},
                    {"M": [2], "N": "z"},
                ],
            ],
            "I": {
                "X": [
                    {"J": "j", "K": ["k"]},
                    {"J": "m", "K": ["customer@example.com", "customer-1@example.com"]},
                ],
                "Y": [
                    {"J": "l", "K": ["n"]},
                    {"J": "m", "K": ["customer@example.com"]},
                ],
                "Z": [{"J": "m", "K": ["n"]}],
            },
            "J": {
                "K": {
                    "L": {
                        "M": {
                            "N": {
                                "O": ["customer@example.com", "customer@gmail.com"],
                                "P": ["customer@yahoo.com", "customer@customer.com"],
                            }
                        }
                    }
                }
            },
            "K": [{"L": "l", "M": "m"}, {"L": "n", "M": "o"}],
        }

        # Test simple scalar field selected
        assert select_and_save_field(final_results, flat, FieldPath("A")) == {"A": "a"}
        # Test array field selected, and added to final results
        assert select_and_save_field(final_results, flat, FieldPath("C")) == {
            "A": "a",
            "C": ["d", "e", "f"],
        }

        # Test array field selected and added to results
        assert select_and_save_field(final_results, flat, FieldPath("D")) == {
            "A": "a",
            "C": ["d", "e", "f"],
            "D": ["g", "h", "i", "j"],
        }
        # Test nested field selected and added to final results
        assert select_and_save_field(final_results, flat, FieldPath("E", "F")) == {
            "A": "a",
            "C": ["d", "e", "f"],
            "D": ["g", "h", "i", "j"],
            "E": {"F": "g"},
        }
        # Test select field not in results - no error
        assert select_and_save_field(
            final_results, flat, FieldPath("E", "F", "Z", "X")
        ) == {
            "A": "a",
            "C": ["d", "e", "f"],
            "D": ["g", "h", "i", "j"],
            "E": {"F": "g"},
        }

        # Test more deeply nested scalar from previous dict
        assert select_and_save_field(
            final_results,
            flat,
            FieldPath("E", "J", "K", "L", "M"),
        ) == {
            "A": "a",
            "C": ["d", "e", "f"],
            "D": ["g", "h", "i", "j"],
            "E": {"F": "g", "J": {"K": {"L": {"M": ["m", "n", "o"]}}}},
        }

        # Test get matching dict key for each element in array
        assert select_and_save_field(final_results, flat, FieldPath("F", "G")) == {
            "A": "a",
            "C": ["d", "e", "f"],
            "D": ["g", "h", "i", "j"],
            "E": {"F": "g", "J": {"K": {"L": {"M": ["m", "n", "o"]}}}},
            "F": [{"G": "g"}, {"G": "h"}, {"G": "i"}],
        }

        # Test get nested fields inside nested arrays
        assert select_and_save_field(final_results, flat, FieldPath("H", "N")) == {
            "A": "a",
            "C": ["d", "e", "f"],
            "D": ["g", "h", "i", "j"],
            "E": {"F": "g", "J": {"K": {"L": {"M": ["m", "n", "o"]}}}},
            "F": [{"G": "g"}, {"G": "h"}, {"G": "i"}],
            "H": [
                [{"N": "n"}, {"N": "o"}, {"N": "p"}],
                [{"N": "q"}, {"N": "s"}, {"N": "u"}],
                [{"N": "w"}, {"N": "y"}, {"N": "z"}],
            ],
        }

        # Test get nested fields inside nested arrays
        assert select_and_save_field(final_results, flat, FieldPath("H", "M")) == {
            "A": "a",
            "C": ["d", "e", "f"],
            "D": ["g", "h", "i", "j"],
            "E": {"F": "g", "J": {"K": {"L": {"M": ["m", "n", "o"]}}}},
            "F": [{"G": "g"}, {"G": "h"}, {"G": "i"}],
            "H": [
                [
                    {"N": "n", "M": [1, 2, 3]},
                    {"N": "o", "M": [3, 2, 1]},
                    {"N": "p", "M": [1, 1, 1]},
                ],
                [
                    {"N": "q", "M": [4, 5, 6]},
                    {"N": "s", "M": [2, 2, 2]},
                    {"N": "u", "M": []},
                ],
                [
                    {"N": "w", "M": [7, 8, 9]},
                    {"N": "y", "M": [6, 6, 6]},
                    {"N": "z", "M": [2]},
                ],
            ],
        }

        # Test get dict of array of dict fields
        assert select_and_save_field(final_results, flat, FieldPath("I", "X", "J")) == {
            "A": "a",
            "C": ["d", "e", "f"],
            "D": ["g", "h", "i", "j"],
            "E": {"F": "g", "J": {"K": {"L": {"M": ["m", "n", "o"]}}}},
            "F": [{"G": "g"}, {"G": "h"}, {"G": "i"}],
            "H": [
                [
                    {"N": "n", "M": [1, 2, 3]},
                    {"N": "o", "M": [3, 2, 1]},
                    {"N": "p", "M": [1, 1, 1]},
                ],
                [
                    {"N": "q", "M": [4, 5, 6]},
                    {"N": "s", "M": [2, 2, 2]},
                    {"N": "u", "M": []},
                ],
                [
                    {"N": "w", "M": [7, 8, 9]},
                    {"N": "y", "M": [6, 6, 6]},
                    {"N": "z", "M": [2]},
                ],
            ],
            "I": {"X": [{"J": "j"}, {"J": "m"}]},
        }

        # Test get deeply nested array field with only matching data, array in arrays
        assert select_and_save_field(final_results, flat, FieldPath("I", "X", "K")) == {
            "A": "a",
            "C": ["d", "e", "f"],
            "D": ["g", "h", "i", "j"],
            "E": {"F": "g", "J": {"K": {"L": {"M": ["m", "n", "o"]}}}},
            "F": [{"G": "g"}, {"G": "h"}, {"G": "i"}],
            "H": [
                [
                    {"N": "n", "M": [1, 2, 3]},
                    {"N": "o", "M": [3, 2, 1]},
                    {"N": "p", "M": [1, 1, 1]},
                ],
                [
                    {"N": "q", "M": [4, 5, 6]},
                    {"N": "s", "M": [2, 2, 2]},
                    {"N": "u", "M": []},
                ],
                [
                    {"N": "w", "M": [7, 8, 9]},
                    {"N": "y", "M": [6, 6, 6]},
                    {"N": "z", "M": [2]},
                ],
            ],
            "I": {
                "X": [
                    {"J": "j", "K": ["k"]},
                    {"J": "m", "K": ["customer@example.com", "customer-1@example.com"]},
                ]
            },
        }

        # Get deeply nested array inside of dicts, with only matching data
        assert select_and_save_field(final_results, flat, FieldPath("I", "Y", "K")) == {
            "A": "a",
            "C": ["d", "e", "f"],
            "D": ["g", "h", "i", "j"],
            "E": {"F": "g", "J": {"K": {"L": {"M": ["m", "n", "o"]}}}},
            "F": [{"G": "g"}, {"G": "h"}, {"G": "i"}],
            "H": [
                [
                    {"N": "n", "M": [1, 2, 3]},
                    {"N": "o", "M": [3, 2, 1]},
                    {"N": "p", "M": [1, 1, 1]},
                ],
                [
                    {"N": "q", "M": [4, 5, 6]},
                    {"N": "s", "M": [2, 2, 2]},
                    {"N": "u", "M": []},
                ],
                [
                    {"N": "w", "M": [7, 8, 9]},
                    {"N": "y", "M": [6, 6, 6]},
                    {"N": "z", "M": [2]},
                ],
            ],
            "I": {
                "X": [
                    {"J": "j", "K": ["k"]},
                    {"J": "m", "K": ["customer@example.com", "customer-1@example.com"]},
                ],
                "Y": [{"K": ["n"]}, {"K": ["customer@example.com"]}],
            },
        }

        assert select_and_save_field(
            final_results,
            flat,
            FieldPath("J", "K", "L", "M", "N", "O"),
        ) == {
            "A": "a",
            "C": ["d", "e", "f"],
            "D": ["g", "h", "i", "j"],
            "E": {"F": "g", "J": {"K": {"L": {"M": ["m", "n", "o"]}}}},
            "F": [{"G": "g"}, {"G": "h"}, {"G": "i"}],
            "H": [
                [
                    {"N": "n", "M": [1, 2, 3]},
                    {"N": "o", "M": [3, 2, 1]},
                    {"N": "p", "M": [1, 1, 1]},
                ],
                [
                    {"N": "q", "M": [4, 5, 6]},
                    {"N": "s", "M": [2, 2, 2]},
                    {"N": "u", "M": []},
                ],
                [
                    {"N": "w", "M": [7, 8, 9]},
                    {"N": "y", "M": [6, 6, 6]},
                    {"N": "z", "M": [2]},
                ],
            ],
            "I": {
                "X": [
                    {"J": "j", "K": ["k"]},
                    {"J": "m", "K": ["customer@example.com", "customer-1@example.com"]},
                ],
                "Y": [{"K": ["n"]}, {"K": ["customer@example.com"]}],
            },
            "J": {
                "K": {
                    "L": {
                        "M": {
                            "N": {"O": ["customer@example.com", "customer@gmail.com"]}
                        }
                    }
                }
            },
        }

        # Test "only" param does not apply to regular scalar fields
        assert select_and_save_field(final_results, flat, FieldPath("B")) == {
            "A": "a",
            "C": ["d", "e", "f"],
            "D": ["g", "h", "i", "j"],
            "E": {"F": "g", "J": {"K": {"L": {"M": ["m", "n", "o"]}}}},
            "F": [{"G": "g"}, {"G": "h"}, {"G": "i"}],
            "H": [
                [
                    {"N": "n", "M": [1, 2, 3]},
                    {"N": "o", "M": [3, 2, 1]},
                    {"N": "p", "M": [1, 1, 1]},
                ],
                [
                    {"N": "q", "M": [4, 5, 6]},
                    {"N": "s", "M": [2, 2, 2]},
                    {"N": "u", "M": []},
                ],
                [
                    {"N": "w", "M": [7, 8, 9]},
                    {"N": "y", "M": [6, 6, 6]},
                    {"N": "z", "M": [2]},
                ],
            ],
            "I": {
                "X": [
                    {"J": "j", "K": ["k"]},
                    {"J": "m", "K": ["customer@example.com", "customer-1@example.com"]},
                ],
                "Y": [{"K": ["n"]}, {"K": ["customer@example.com"]}],
            },
            "J": {
                "K": {
                    "L": {
                        "M": {
                            "N": {"O": ["customer@example.com", "customer@gmail.com"]}
                        }
                    }
                }
            },
            "B": "b",
        }

        assert select_and_save_field(
            final_results,
            flat,
            FieldPath("K", "L"),
        ) == {
            "A": "a",
            "C": ["d", "e", "f"],
            "D": ["g", "h", "i", "j"],
            "E": {"F": "g", "J": {"K": {"L": {"M": ["m", "n", "o"]}}}},
            "F": [{"G": "g"}, {"G": "h"}, {"G": "i"}],
            "H": [
                [
                    {"N": "n", "M": [1, 2, 3]},
                    {"N": "o", "M": [3, 2, 1]},
                    {"N": "p", "M": [1, 1, 1]},
                ],
                [
                    {"N": "q", "M": [4, 5, 6]},
                    {"N": "s", "M": [2, 2, 2]},
                    {"N": "u", "M": []},
                ],
                [
                    {"N": "w", "M": [7, 8, 9]},
                    {"N": "y", "M": [6, 6, 6]},
                    {"N": "z", "M": [2]},
                ],
            ],
            "I": {
                "X": [
                    {"J": "j", "K": ["k"]},
                    {"J": "m", "K": ["customer@example.com", "customer-1@example.com"]},
                ],
                "Y": [{"K": ["n"]}, {"K": ["customer@example.com"]}],
            },
            "J": {
                "K": {
                    "L": {
                        "M": {
                            "N": {"O": ["customer@example.com", "customer@gmail.com"]}
                        }
                    }
                }
            },
            "B": "b",
            "K": [{"L": "l"}, {"L": "n"}],
        }

    @pytest.mark.parametrize(
        "orig, expected",
        [
            (
                {"A": {"B": {"C": 0}, "G": {"H": None}}, "I": 0, "J": False},
                {"A": {"B": {"C": 0}, "G": {"H": None}}, "I": 0, "J": False},
            ),
            (
                {"A": [], "B": [], "C": False},
                {"C": False},
            ),
            (
                {"A": {}, "B": {}, "C": {}},
                {},
            ),
            (
                {"A": {"B": {"C": []}, "G": {"H": None}}, "I": 0, "J": False},
                {"A": {"G": {"H": None}}, "I": 0, "J": False},
            ),
            (
                {"A": {"B": {"C": []}, "G": {"H": {"I": {}}}}, "J": 0},
                {"J": 0},
            ),
            (
                {
                    "A": [
                        {"B": "C", "D": {}},
                        {"B": "G", "D": {}},
                        {"B": "J", "D": {"J": "K"}},
                    ]
                },
                {"A": [{"B": "C"}, {"B": "G"}, {"B": "J", "D": {"J": "K"}}]},
            ),
            (
                {},
                {},
            ),
            (
                {"A": {}},
                {},
            ),
            (
                {
                    "A": [
                        [
                            {"B": "C", "D": [{"F": {}}, {"G": []}]},
                            {"B": "D"},
                            {"B": "G"},
                        ]
                    ]
                },
                {"A": [[{"B": "C"}, {"B": "D"}, {"B": "G"}]]},
            ),
            (
                [
                    {"A": {"B": {"C": 0}, "G": {"H": None}}, "I": 0, "J": False},
                    {"K": "L"},
                ],
                [
                    {"A": {"B": {"C": 0}, "G": {"H": None}}, "I": 0, "J": False},
                    {"K": "L"},
                ],
            ),
            (
                [{"A": [], "B": [], "C": False}],
                [{"C": False}],
            ),
            (
                [{"A": {}, "B": {}, "C": {}}, {"D": "E"}],
                [{"D": "E"}],
            ),
            (
                [{"A": {"B": {"C": []}, "G": {"H": None}}, "I": 0, "J": False}],
                [{"A": {"G": {"H": None}}, "I": 0, "J": False}],
            ),
            (
                [{"A": {"B": {"C": []}, "G": {"H": {"I": {}}}}, "J": 0}],
                [{"J": 0}],
            ),
            (
                [
                    {
                        "A": [
                            {"B": "C", "D": {}},
                            {"B": "G", "D": {}},
                            {"B": "J", "D": {"J": "K"}},
                        ]
                    }
                ],
                [{"A": [{"B": "C"}, {"B": "G"}, {"B": "J", "D": {"J": "K"}}]}],
            ),
            (
                [{}],
                [],
            ),
            (
                [{"A": {}}],
                [],
            ),
            (
                [
                    {
                        "A": [
                            [
                                {"B": "C", "D": [{"F": {}}, {"G": []}]},
                                {"B": "D"},
                                {"B": "G"},
                            ]
                        ]
                    }
                ],
                [{"A": [[{"B": "C"}, {"B": "D"}, {"B": "G"}]]}],
            ),
        ],
    )
    def test_remove_empty_containers(self, orig, expected):
        results = copy.deepcopy(orig)
        remove_empty_containers(results)
        assert results == expected

    def test_filter_data_categories(self):
        """Test different combinations of data categories to ensure the access_request_results are filtered properly"""
        access_request_results = {
            "postgres_example:supplies": [
                {
                    "foods": {
                        "vegetables": True,
                        "fruits": {
                            "apples": True,
                            "oranges": False,
                            "berries": {"strawberries": True, "blueberries": False},
                        },
                        "grains": {"rice": False, "wheat": True},
                    },
                    "clothing": True,
                }
            ]
        }

        dataset = {
            "fides_key": "postgres_example",
            "name": "postgres_example",
            "collections": [
                {
                    "name": "supplies",
                    "fields": [
                        {
                            "name": "foods",
                            "fields": [
                                {
                                    "name": "fruits",
                                    "fields": [
                                        {"name": "apples", "data_categories": ["A"]},
                                        {
                                            "name": "berries",
                                            "fields": [
                                                {
                                                    "name": "strawberries",
                                                    "data_categories": ["E"],
                                                }
                                            ],
                                        },
                                        {"name": "oranges", "data_categories": ["E"]},
                                    ],
                                },
                                {"name": "vegetables", "data_categories": ["B"]},
                                {
                                    "name": "grains",
                                    "fields": [
                                        {"name": "rice", "data_categories": ["C"]},
                                        {"name": "wheat", "data_categories": ["C"]},
                                    ],
                                },
                            ],
                        },
                        {"name": "clothing", "data_categories": ["A"]},
                    ],
                }
            ],
        }

        dataset_graph = DatasetGraph(
            *[
                convert_dataset_to_graph(
                    Dataset.model_validate(dataset), "postgres_example"
                )
            ]
        )

        only_a_categories = filter_data_categories(
            copy.deepcopy(access_request_results), {"A"}, dataset_graph
        )

        assert only_a_categories == {
            "postgres_example:supplies": [
                {"foods": {"fruits": {"apples": True}}, "clothing": True}
            ]
        }

        only_b_categories = filter_data_categories(
            copy.deepcopy(access_request_results), {"B"}, dataset_graph
        )
        assert only_b_categories == {
            "postgres_example:supplies": [
                {
                    "foods": {
                        "vegetables": True,
                    }
                }
            ]
        }

        only_c_categories = filter_data_categories(
            copy.deepcopy(access_request_results), {"C"}, dataset_graph
        )
        assert only_c_categories == {
            "postgres_example:supplies": [
                {"foods": {"grains": {"rice": False, "wheat": True}}}
            ]
        }

        only_d_categories = filter_data_categories(
            copy.deepcopy(access_request_results), {"D"}, dataset_graph
        )
        assert only_d_categories == {}

        only_e_categories = filter_data_categories(
            copy.deepcopy(access_request_results), {"E"}, dataset_graph
        )
        assert only_e_categories == {
            "postgres_example:supplies": [
                {
                    "foods": {
                        "fruits": {
                            "oranges": False,
                            "berries": {"strawberries": True},
                        }
                    }
                }
            ]
        }

    def test_filter_data_categories_arrays(self):
        access_request_results = {
            "postgres_example:flights": [
                {
                    "people": {
                        "passenger_ids": [222, 445, 311, 4444],
                        "pilot_ids": [123, 12, 112],
                    },
                    "flight_number": 101,
                }
            ]
        }

        dataset = {
            "fides_key": "postgres_example",
            "name": "postgres_example",
            "collections": [
                {
                    "name": "flights",
                    "fields": [
                        {
                            "name": "people",
                            "fields": [
                                {
                                    "name": "passenger_ids",
                                    "data_categories": ["A"],
                                },
                                {
                                    "name": "pilot_ids",
                                    "data_categories": ["B"],
                                },
                            ],
                        },
                    ],
                }
            ],
        }

        dataset_graph = DatasetGraph(
            *[
                convert_dataset_to_graph(
                    Dataset.model_validate(dataset), "postgres_example"
                )
            ]
        )

        only_a_category = filter_data_categories(
            copy.deepcopy(access_request_results), {"A"}, dataset_graph
        )

        # Nested array field retrieved
        assert only_a_category == {
            "postgres_example:flights": [
                {"people": {"passenger_ids": [222, 445, 311, 4444]}}
            ]
        }

        only_b_category = filter_data_categories(
            copy.deepcopy(access_request_results), {"B"}, dataset_graph
        )
        assert only_b_category == {
            "postgres_example:flights": [{"people": {"pilot_ids": [123, 12, 112]}}]
        }

    def test_filter_data_categories_limited_results(self):
        """
        Test scenario where the related data for a given identity is only a
        small subset of all the annotated fields.
        """
        jane_results = {
            "mongo_test:customer_details": [
                {
                    "_id": ObjectId("61f2bc8d6362fd78d72d8791"),
                    "customer_id": 3.0,
                    "gender": "female",
                    "birthday": datetime(1990, 2, 28, 0, 0),
                }
            ],
            "postgres_example:order_item": [],
            "postgres_example:report": [],
            "postgres_example:orders": [
                {"customer_id": 3, "id": "ord_ddd-eee", "shipping_address_id": 4}
            ],
            "postgres_example:employee": [],
            "postgres_example:address": [
                {
                    "city": "Example Mountain",
                    "house": 1111,
                    "id": 4,
                    "state": "TX",
                    "street": "Example Place",
                    "zip": "54321",
                }
            ],
            "postgres_example:visit": [],
            "postgres_example:product": [],
            "postgres_example:customer": [
                {
                    "address_id": 4,
                    "created": datetime(2020, 4, 1, 11, 47, 42),
                    "email": "jane@example.com",
                    "id": 3,
                    "name": "Jane Customer",
                }
            ],
            "postgres_example:service_request": [],
            "postgres_example:payment_card": [
                {
                    "billing_address_id": 4,
                    "ccn": 373719391,
                    "code": 222,
                    "customer_id": 3,
                    "id": "pay_ccc-ccc",
                    "name": "Example Card 3",
                    "preferred": False,
                }
            ],
            "mongo_test:customer_feedback": [],
            "postgres_example:login": [
                {"customer_id": 3, "id": 8, "time": datetime(2021, 1, 6, 1, 0)}
            ],
            "mongo_test:internal_customer_profile": [],
        }

        target_categories = {"user"}

        postgres_dataset = {
            "fides_key": "postgres_example",
            "name": "postgres_example",
            "collections": [
                {
                    "name": "address",
                    "fields": [
                        {
                            "name": "city",
                            "data_categories": ["user.contact.address.city"],
                        },
                        {
                            "name": "house",
                            "data_categories": ["user.contact.address.street"],
                        },
                        {
                            "name": "street",
                            "data_categories": ["user.contact.address.street"],
                        },
                        {
                            "name": "id",
                            "data_categories": ["system.operations"],
                        },
                        {
                            "name": "state",
                            "data_categories": ["user.contact.address.state"],
                        },
                        {
                            "name": "zip",
                            "data_categories": ["user.contact.address.postal_code"],
                        },
                    ],
                },
                {
                    "name": "customer",
                    "fields": [
                        {
                            "name": "address_id",
                            "data_categories": ["system.operations"],
                        },
                        {
                            "name": "created",
                            "data_categories": ["system.operations"],
                        },
                        {
                            "name": "email",
                            "data_categories": ["user.contact.email"],
                        },
                        {
                            "name": "id",
                            "data_categories": ["user.unique_id"],
                        },
                        {
                            "name": "name",
                            "data_categories": ["user.name"],
                        },
                    ],
                },
                {
                    "name": "employee",
                    "fields": [
                        {
                            "name": "address_id",
                            "data_categories": ["system.operations"],
                        },
                        {
                            "name": "email",
                            "data_categories": ["user.contact.email"],
                        },
                        {
                            "name": "id",
                            "data_categories": ["user.unique_id"],
                        },
                        {
                            "name": "name",
                            "data_categories": ["user.name"],
                        },
                    ],
                },
                {
                    "name": "login",
                    "fields": [
                        {
                            "name": "customer_id",
                            "data_categories": ["user.unique_id"],
                        },
                        {
                            "name": "id",
                            "data_categories": ["system.operations"],
                        },
                        {
                            "name": "time",
                            "data_categories": ["user.sensor"],
                        },
                    ],
                },
                {
                    "name": "order_item",
                    "fields": [
                        {
                            "name": "order_id",
                            "data_categories": ["system.operations"],
                        },
                        {
                            "name": "product_id",
                            "data_categories": ["system.operations"],
                        },
                        {
                            "name": "quantity",
                            "data_categories": ["system.operations"],
                        },
                    ],
                },
                {
                    "name": "orders",
                    "fields": [
                        {
                            "name": "customer_id",
                            "data_categories": ["user.unique_id"],
                        },
                        {
                            "name": "id",
                            "data_categories": ["system.operations"],
                        },
                        {
                            "name": "shipping_address_id",
                            "data_categories": ["system.operations"],
                        },
                    ],
                },
                {
                    "name": "payment_card",
                    "fields": [
                        {
                            "name": "billing_address_id",
                            "data_categories": ["system.operations"],
                        },
                        {
                            "name": "id",
                            "data_categories": ["system.operations"],
                        },
                        {
                            "name": "ccn",
                            "data_categories": ["user.financial.bank_account"],
                        },
                        {
                            "name": "code",
                            "data_categories": ["user.financial"],
                        },
                        {
                            "name": "name",
                            "data_categories": ["user.financial"],
                        },
                        {
                            "name": "customer_id",
                            "data_categories": ["user.unique_id"],
                        },
                        {
                            "name": "preferred",
                            "data_categories": ["user"],
                        },
                    ],
                },
                {
                    "name": "product",
                    "fields": [
                        {
                            "name": "id",
                            "data_categories": ["system.operations"],
                        },
                        {
                            "name": "name",
                            "data_categories": ["system.operations"],
                        },
                        {
                            "name": "price",
                            "data_categories": ["system.operations"],
                        },
                    ],
                },
                {
                    "name": "report",
                    "fields": [
                        {
                            "name": "email",
                            "data_categories": ["user.contact.email"],
                        },
                        {
                            "name": "id",
                            "data_categories": ["system.operations"],
                        },
                        {
                            "name": "month",
                            "data_categories": ["system.operations"],
                        },
                        {
                            "name": "name",
                            "data_categories": ["system.operations"],
                        },
                        {
                            "name": "total_visits",
                            "data_categories": ["system.operations"],
                        },
                        {
                            "name": "year",
                            "data_categories": ["system.operations"],
                        },
                    ],
                },
                {
                    "name": "service_request",
                    "fields": [
                        {
                            "name": "alt_email",
                            "data_categories": ["user.contact.email"],
                        },
                        {
                            "name": "closed",
                            "data_categories": ["system.operations"],
                        },
                        {
                            "name": "email",
                            "data_categories": ["system.operations"],
                        },
                        {
                            "name": "id",
                            "data_categories": ["system.operations"],
                        },
                        {
                            "name": "opened",
                            "data_categories": ["system.operations"],
                        },
                        {
                            "name": "employee_id",
                            "data_categories": ["user.unique_id"],
                        },
                    ],
                },
                {
                    "name": "visit",
                    "fields": [
                        {
                            "name": "email",
                            "data_categories": ["user.contact.email"],
                        },
                        {
                            "name": "last_visit",
                            "data_categories": ["system.operations"],
                        },
                    ],
                },
            ],
        }

        mongo_dataset = {
            "fides_key": "mongo_test",
            "name": "mongo_test",
            "collections": [
                {
                    "name": "customer_details",
                    "fields": [
                        {
                            "name": "_id",
                            "data_categories": ["system.operations"],
                        },
                        {
                            "name": "birthday",
                            "data_categories": ["user.demographic.date_of_birth"],
                        },
                        {
                            "name": "customer_id",
                            "data_categories": ["user.unique_id"],
                        },
                        {
                            "name": "gender",
                            "data_categories": ["user.demographic.gender"],
                        },
                        {
                            "name": "workplace_info",
                            "fields": [
                                {
                                    "name": "position",
                                    "data_categories": ["user.job_title"],
                                }
                            ],
                        },
                    ],
                },
                {
                    "name": "customer_feedback",
                    "fields": [
                        {
                            "name": "_id",
                            "data_categories": ["system.operations"],
                        },
                        {
                            "name": "customer_information",
                            "fields": [
                                {
                                    "name": "phone",
                                    "data_categories": ["user.contact.phone_number"],
                                }
                            ],
                        },
                        {
                            "name": "message",
                            "data_categories": ["user"],
                        },
                        {
                            "name": "rating",
                            "data_categories": ["user"],
                        },
                    ],
                },
                {
                    "name": "internal_customer_profile",
                    "fields": [
                        {
                            "name": "derived_interests",
                            "data_categories": ["user"],
                        }
                    ],
                },
            ],
        }

        dataset_graph = DatasetGraph(
            *[
                convert_dataset_to_graph(
                    Dataset.model_validate(postgres_dataset), "postgres_example"
                ),
                convert_dataset_to_graph(
                    Dataset.model_validate(mongo_dataset), "mongo_test"
                ),
            ]
        )

        filtered_results = filter_data_categories(
            copy.deepcopy(jane_results), target_categories, dataset_graph
        )
        expected_results = {
            "mongo_test:customer_details": [
                {
                    "birthday": datetime(1990, 2, 28, 0, 0),
                    "gender": "female",
                    "customer_id": 3.0,
                }
            ],
            "postgres_example:orders": [{"customer_id": 3}],
            "postgres_example:address": [
                {
                    "state": "TX",
                    "street": "Example Place",
                    "zip": "54321",
                    "house": 1111,
                    "city": "Example Mountain",
                }
            ],
            "postgres_example:customer": [
                {"id": 3, "name": "Jane Customer", "email": "jane@example.com"}
            ],
            "postgres_example:payment_card": [
                {
                    "code": 222,
                    "name": "Example Card 3",
                    "customer_id": 3,
                    "preferred": False,
                    "ccn": 373719391,
                }
            ],
            "postgres_example:login": [
                {"time": datetime(2021, 1, 6, 1, 0), "customer_id": 3}
            ],
        }

        print(filtered_results)
        print("-" * 10)
        print(expected_results)
        assert filtered_results == expected_results

    def test_unpack_fides_connector_results_key_error(self, loguru_caplog):
        unpack_fides_connector_results(
            connector_results=[{"test": "bad"}],
            filtered_access_results={"test": [{"test": "t"}]},
            rule_key="bad",
            node_address="nothing",
        )

        assert "Did not find a result entry" in loguru_caplog.text

    def test_filter_by_collection_level_parent_data_category(self):
        """
        Verify that collection-level data categories apply to all child fields, even if the fields aren't explicitly defined in the dataset
        """

        access_request_results = {
            "postgres_example:supplies": [
                {
                    "foods": {
                        "vegetables": True,
                        "fruits": {
                            "apples": True,
                            "oranges": False,
                            "berries": {"strawberries": True, "blueberries": False},
                        },
                        "grains": {"rice": False, "wheat": True},
                    },
                    "clothing": True,
                }
            ]
        }

        dataset = {
            "fides_key": "postgres_example",
            "name": "postgres_example",
            "collections": [
                {
                    "name": "supplies",
                    "data_categories": ["user.content"],
                    "fields": [],
                }
            ],
        }

        dataset_graph = DatasetGraph(
            *[
                convert_dataset_to_graph(
                    Dataset.model_validate(dataset), "postgres_example"
                )
            ]
        )

        # here we filter by the `user` data category and since the collection-level
        # data category of `user.content` is a subset of `user`, we'll return all the fields,
        # even if they're not specified in the dataset
        assert (
            filter_data_categories(
                copy.deepcopy(access_request_results), {"user"}, dataset_graph
            )
            == access_request_results
        )

    def test_filter_by_collection_level_child_data_category(self):
        access_request_results = {
            "postgres_example:supplies": [
                {
                    "foods": {
                        "vegetables": True,
                        "fruits": {
                            "apples": True,
                            "oranges": False,
                            "berries": {"strawberries": True, "blueberries": False},
                        },
                        "grains": {"rice": False, "wheat": True},
                    },
                    "clothing": True,
                }
            ]
        }

        dataset = {
            "fides_key": "postgres_example",
            "name": "postgres_example",
            "collections": [
                {
                    "name": "supplies",
                    "data_categories": ["user"],
                    "fields": [
                        {"name": "clothing", "data_categories": ["user.content"]}
                    ],
                }
            ],
        }

        dataset_graph = DatasetGraph(
            *[
                convert_dataset_to_graph(
                    Dataset.model_validate(dataset), "postgres_example"
                )
            ]
        )

        # Here we filter by the `user.content` which is more specific than the collection-level
        # data category of `user` so we won't use collection-level filtering.
        # Verify the field level data category filtering is still used.
        assert filter_data_categories(
            copy.deepcopy(access_request_results), {"user.content"}, dataset_graph
        ) == {"postgres_example:supplies": [{"clothing": True}]}

    def test_filter_by_collection_level_exact_data_category(self):
        access_request_results = {
            "postgres_example:supplies": [
                {
                    "foods": {
                        "vegetables": True,
                        "fruits": {
                            "apples": True,
                            "oranges": False,
                            "berries": {"strawberries": True, "blueberries": False},
                        },
                        "grains": {"rice": False, "wheat": True},
                    },
                    "clothing": True,
                }
            ]
        }

        dataset = {
            "fides_key": "postgres_example",
            "name": "postgres_example",
            "collections": [
                {
                    "name": "supplies",
                    "data_categories": ["user.content"],
                    "fields": [],
                }
            ],
        }

        dataset_graph = DatasetGraph(
            *[
                convert_dataset_to_graph(
                    Dataset.model_validate(dataset), "postgres_example"
                )
            ]
        )

        assert (
            filter_data_categories(
                copy.deepcopy(access_request_results), {"user.content"}, dataset_graph
            )
            == access_request_results
        )
