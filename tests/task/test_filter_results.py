import copy
from datetime import datetime

from bson import ObjectId

from fidesops.graph.config import FieldPath, CollectionAddress
from fidesops.task.filter_results import (
    select_and_save_field,
    remove_empty_containers,
    filter_data_categories,
)


def test_select_and_save_field():
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
            "Y": [{"J": "l", "K": ["n"]}, {"J": "m", "K": ["customer@example.com"]}],
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
                "L": {"M": {"N": {"O": ["customer@example.com", "customer@gmail.com"]}}}
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
                "L": {"M": {"N": {"O": ["customer@example.com", "customer@gmail.com"]}}}
            }
        },
        "B": "b",
    }

    assert select_and_save_field(final_results, flat, FieldPath("K", "L"),) == {
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
                "L": {"M": {"N": {"O": ["customer@example.com", "customer@gmail.com"]}}}
            }
        },
        "B": "b",
        "K": [{"L": "l"}, {"L": "n"}],
    }


def test_remove_empty_containers():
    # No empty dicts or arrays
    orig = {"A": {"B": {"C": 0}, "G": {"H": None}}, "I": 0, "J": False}
    results = copy.deepcopy(orig)
    remove_empty_containers(results)
    assert results == orig

    # Empty arrays
    results = {"A": [], "B": [], "C": False}
    remove_empty_containers(results)
    assert results == {"C": False}

    # Empty dicts
    results = {"A": {}, "B": {}, "C": {}}
    remove_empty_containers(results)
    assert results == {}

    # Empty array removed, which causes "C" key to be popped, which causes "B" to be popped
    orig = {"A": {"B": {"C": []}, "G": {"H": None}}, "I": 0, "J": False}
    results = copy.deepcopy(orig)
    remove_empty_containers(results)
    assert results == {"A": {"G": {"H": None}}, "I": 0, "J": False}

    # Deeply nested empty array and deeply nested empty dict removed - G - H - I levels gone and A - B - C levels gone
    orig = {"A": {"B": {"C": []}, "G": {"H": {"I": {}}}}, "J": 0}
    results = copy.deepcopy(orig)
    remove_empty_containers(results)
    assert results == {"J": 0}

    orig = {
        "A": [{"B": "C", "D": {}}, {"B": "G", "D": {}}, {"B": "J", "D": {"J": "K"}}]
    }
    results = copy.deepcopy(orig)
    remove_empty_containers(results)
    assert results == {"A": [{"B": "C"}, {"B": "G"}, {"B": "J", "D": {"J": "K"}}]}

    # Empty dict returns original empty dict
    orig = {}
    results = copy.deepcopy(orig)
    remove_empty_containers(results)
    assert results == {}

    # Empty dict returned
    orig = {"A": {}}
    results = copy.deepcopy(orig)
    remove_empty_containers(results)
    assert results == {}

    # Removing multiple levels of empty arrays and empty dicts
    orig = {"A": [[{"B": "C", "D": [{"F": {}}, {"G": []}]}, {"B": "D"}, {"B": "G"}]]}
    results = copy.deepcopy(orig)
    remove_empty_containers(results)
    assert results == {"A": [[{"B": "C"}, {"B": "D"}, {"B": "G"}]]}


def test_filter_data_categories():
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

    data_category_fields = {
        CollectionAddress("postgres_example", "supplies"): {
            "A": [FieldPath("foods", "fruits", "apples"), FieldPath("clothing")],
            "B": [FieldPath("foods", "vegetables")],
            "C": [
                FieldPath("foods", "grains", "rice"),
                FieldPath("foods", "grains", "wheat"),
            ],
            "D": [],
            "E": [
                FieldPath("foods", "fruits", "berries", "strawberries"),
                FieldPath("foods", "fruits", "oranges"),
            ],
        }
    }

    only_a_categories = filter_data_categories(
        copy.deepcopy(access_request_results), {"A"}, data_category_fields
    )

    assert only_a_categories == {
        "postgres_example:supplies": [
            {"foods": {"fruits": {"apples": True}}, "clothing": True}
        ]
    }

    only_b_categories = filter_data_categories(
        copy.deepcopy(access_request_results), {"B"}, data_category_fields
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
        copy.deepcopy(access_request_results), {"C"}, data_category_fields
    )
    assert only_c_categories == {
        "postgres_example:supplies": [
            {"foods": {"grains": {"rice": False, "wheat": True}}}
        ]
    }

    only_d_categories = filter_data_categories(
        copy.deepcopy(access_request_results), {"D"}, data_category_fields
    )
    assert only_d_categories == {}

    only_e_categories = filter_data_categories(
        copy.deepcopy(access_request_results), {"E"}, data_category_fields
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


def test_filter_data_categories_arrays():
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

    data_category_fields = {
        CollectionAddress("postgres_example", "flights"): {
            "A": [FieldPath("people", "passenger_ids")],
            "B": [FieldPath("people", "pilot_ids")],
        }
    }

    only_a_category = filter_data_categories(
        copy.deepcopy(access_request_results), {"A"}, data_category_fields
    )

    # Nested array field retrieved
    assert only_a_category == {
        "postgres_example:flights": [
            {"people": {"passenger_ids": [222, 445, 311, 4444]}}
        ]
    }

    only_b_category = filter_data_categories(
        copy.deepcopy(access_request_results), {"B"}, data_category_fields
    )
    assert only_b_category == {
        "postgres_example:flights": [{"people": {"pilot_ids": [123, 12, 112]}}]
    }


def test_filter_data_categories_limited_results():
    """
    Test scenario where the related data for a given identity is only a small subset of all the annotated fields.
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

    target_categories = {"user.provided.identifiable"}

    data_category_fields = {
        CollectionAddress.from_string("postgres_example:address"): {
            "user.provided.identifiable.contact.city": [
                FieldPath(
                    "city",
                )
            ],
            "user.provided.identifiable.contact.street": [
                FieldPath(
                    "house",
                ),
                FieldPath(
                    "street",
                ),
            ],
            "system.operations": [
                FieldPath(
                    "id",
                )
            ],
            "user.provided.identifiable.contact.state": [
                FieldPath(
                    "state",
                )
            ],
            "user.provided.identifiable.contact.postal_code": [
                FieldPath(
                    "zip",
                )
            ],
        },
        CollectionAddress.from_string("postgres_example:customer"): {
            "system.operations": [
                FieldPath(
                    "address_id",
                ),
                FieldPath(
                    "created",
                ),
            ],
            "user.provided.identifiable.contact.email": [
                FieldPath(
                    "email",
                )
            ],
            "user.derived.identifiable.unique_id": [
                FieldPath(
                    "id",
                )
            ],
            "user.provided.identifiable.name": [
                FieldPath(
                    "name",
                )
            ],
        },
        CollectionAddress.from_string("postgres_example:employee"): {
            "system.operations": [
                FieldPath(
                    "address_id",
                )
            ],
            "user.provided.identifiable.contact.email": [
                FieldPath(
                    "email",
                )
            ],
            "user.derived.identifiable.unique_id": [
                FieldPath(
                    "id",
                )
            ],
            "user.provided.identifiable.name": [
                FieldPath(
                    "name",
                )
            ],
        },
        CollectionAddress.from_string("postgres_example:login"): {
            "user.derived.identifiable.unique_id": [
                FieldPath(
                    "customer_id",
                )
            ],
            "system.operations": [
                FieldPath(
                    "id",
                )
            ],
            "user.derived.nonidentifiable.sensor": [
                FieldPath(
                    "time",
                )
            ],
        },
        CollectionAddress.from_string("postgres_example:order_item"): {
            "system.operations": [
                FieldPath(
                    "order_id",
                ),
                FieldPath(
                    "product_id",
                ),
                FieldPath(
                    "quantity",
                ),
            ]
        },
        CollectionAddress.from_string("postgres_example:orders"): {
            "user.derived.identifiable.unique_id": [
                FieldPath(
                    "customer_id",
                )
            ],
            "system.operations": [
                FieldPath(
                    "id",
                ),
                FieldPath(
                    "shipping_address_id",
                ),
            ],
        },
        CollectionAddress.from_string("postgres_example:payment_card"): {
            "system.operations": [
                FieldPath(
                    "billing_address_id",
                ),
                FieldPath(
                    "id",
                ),
            ],
            "user.provided.identifiable.financial.account_number": [
                FieldPath(
                    "ccn",
                )
            ],
            "user.provided.identifiable.financial": [
                FieldPath(
                    "code",
                ),
                FieldPath(
                    "name",
                ),
            ],
            "user.derived.identifiable.unique_id": [
                FieldPath(
                    "customer_id",
                )
            ],
            "user.provided.nonidentifiable": [
                FieldPath(
                    "preferred",
                )
            ],
        },
        CollectionAddress.from_string("postgres_example:product"): {
            "system.operations": [
                FieldPath(
                    "id",
                ),
                FieldPath(
                    "name",
                ),
                FieldPath(
                    "price",
                ),
            ]
        },
        CollectionAddress.from_string("postgres_example:report"): {
            "user.provided.identifiable.contact.email": [
                FieldPath(
                    "email",
                )
            ],
            "system.operations": [
                FieldPath(
                    "id",
                ),
                FieldPath(
                    "month",
                ),
                FieldPath(
                    "name",
                ),
                FieldPath(
                    "total_visits",
                ),
                FieldPath(
                    "year",
                ),
            ],
        },
        CollectionAddress.from_string("postgres_example:service_request"): {
            "user.provided.identifiable.contact.email": [
                FieldPath(
                    "alt_email",
                )
            ],
            "system.operations": [
                FieldPath(
                    "closed",
                ),
                FieldPath(
                    "email",
                ),
                FieldPath(
                    "id",
                ),
                FieldPath(
                    "opened",
                ),
            ],
            "user.derived.identifiable.unique_id": [
                FieldPath(
                    "employee_id",
                )
            ],
        },
        CollectionAddress.from_string("postgres_example:visit"): {
            "user.provided.identifiable.contact.email": [
                FieldPath(
                    "email",
                )
            ],
            "system.operations": [
                FieldPath(
                    "last_visit",
                )
            ],
        },
        CollectionAddress.from_string("mongo_test:customer_details"): {
            "system.operations": [
                FieldPath(
                    "_id",
                )
            ],
            "user.provided.identifiable.date_of_birth": [
                FieldPath(
                    "birthday",
                )
            ],
            "user.derived.identifiable.unique_id": [
                FieldPath(
                    "customer_id",
                )
            ],
            "user.provided.identifiable.gender": [
                FieldPath(
                    "gender",
                )
            ],
            "user.provided.identifiable.job_title": [
                FieldPath("workplace_info", "position")
            ],
        },
        CollectionAddress.from_string("mongo_test:customer_feedback"): {
            "system.operations": [
                FieldPath(
                    "_id",
                )
            ],
            "user.provided.identifiable.contact.phone_number": [
                FieldPath("customer_information", "phone")
            ],
            "user.provided.nonidentifiable": [
                FieldPath(
                    "message",
                ),
                FieldPath(
                    "rating",
                ),
            ],
        },
        CollectionAddress.from_string("mongo_test:internal_customer_profile"): {
            "user.derived": [
                FieldPath(
                    "derived_interests",
                )
            ]
        },
    }

    filtered_results = filter_data_categories(
        copy.deepcopy(jane_results), target_categories, data_category_fields
    )

    assert filtered_results == {
        "mongo_test:customer_details": [
            {"gender": "female", "birthday": datetime(1990, 2, 28)}
        ],
        "postgres_example:address": [
            {
                "city": "Example Mountain",
                "house": 1111,
                "state": "TX",
                "street": "Example Place",
                "zip": "54321",
            }
        ],
        "postgres_example:customer": [
            {"email": "jane@example.com", "name": "Jane Customer"}
        ],
        "postgres_example:payment_card": [
            {"ccn": 373719391, "code": 222, "name": "Example Card 3"}
        ],
    }
