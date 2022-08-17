from tests.ops.test_helpers.dataset_utils import generate_collections, generate_dataset


class TestGenerateCollections:
    def test_empty_values(self):
        api_data = {"user": [{"a": None, "b": "", "c": [], "d": {}}]}
        assert generate_collections(api_data) == [
            {
                "name": "user",
                "fields": [
                    {"name": "a", "data_categories": ["system.operations"]},
                    {"name": "b", "data_categories": ["system.operations"]},
                    {"name": "c", "data_categories": ["system.operations"]},
                    {"name": "d", "data_categories": ["system.operations"]},
                ],
            }
        ]

    def test_boolean_true(self):
        api_data = {"user": [{"active": True}]}
        assert generate_collections(api_data) == [
            {
                "name": "user",
                "fields": [
                    {
                        "name": "active",
                        "data_categories": ["system.operations"],
                        "fidesops_meta": {"data_type": "boolean"},
                    }
                ],
            }
        ]

    def test_boolean_false(self):
        api_data = {"user": [{"active": False}]}
        assert generate_collections(api_data) == [
            {
                "name": "user",
                "fields": [
                    {
                        "name": "active",
                        "data_categories": ["system.operations"],
                        "fidesops_meta": {"data_type": "boolean"},
                    }
                ],
            }
        ]

    def test_integer(self):
        api_data = {"user": [{"id": 1}]}
        assert generate_collections(api_data) == [
            {
                "name": "user",
                "fields": [
                    {
                        "name": "id",
                        "data_categories": ["system.operations"],
                        "fidesops_meta": {"data_type": "integer"},
                    }
                ],
            }
        ]

    def test_zero(self):
        api_data = {"user": [{"id": 0}]}
        assert generate_collections(api_data) == [
            {
                "name": "user",
                "fields": [
                    {
                        "name": "id",
                        "data_categories": ["system.operations"],
                        "fidesops_meta": {"data_type": "integer"},
                    }
                ],
            }
        ]

    def test_float(self):
        api_data = {"user": [{"balance": 2.0}]}
        assert generate_collections(api_data) == [
            {
                "name": "user",
                "fields": [
                    {
                        "name": "balance",
                        "data_categories": ["system.operations"],
                        "fidesops_meta": {"data_type": "float"},
                    }
                ],
            }
        ]

    def test_float_zero(self):
        api_data = {"user": [{"balance": 0.0}]}
        assert generate_collections(api_data) == [
            {
                "name": "user",
                "fields": [
                    {
                        "name": "balance",
                        "data_categories": ["system.operations"],
                        "fidesops_meta": {"data_type": "float"},
                    }
                ],
            }
        ]

    def test_string(self):
        api_data = {"user": [{"first_name": "test"}]}
        assert generate_collections(api_data) == [
            {
                "name": "user",
                "fields": [
                    {
                        "name": "first_name",
                        "data_categories": ["system.operations"],
                        "fidesops_meta": {"data_type": "string"},
                    }
                ],
            }
        ]

    def test_object(self):
        api_data = {
            "user": [{"address": {"street1": "123 Fake St.", "city": "Springfield"}}]
        }
        assert generate_collections(api_data) == [
            {
                "name": "user",
                "fields": [
                    {
                        "name": "address",
                        "fidesops_meta": {"data_type": "object"},
                        "fields": [
                            {
                                "name": "street1",
                                "data_categories": ["system.operations"],
                                "fidesops_meta": {"data_type": "string"},
                            },
                            {
                                "name": "city",
                                "data_categories": ["system.operations"],
                                "fidesops_meta": {"data_type": "string"},
                            },
                        ],
                    }
                ],
            }
        ]

    def test_integer_list(self):
        api_data = {"user": [{"ids": [1]}]}
        assert generate_collections(api_data) == [
            {
                "name": "user",
                "fields": [
                    {
                        "name": "ids",
                        "data_categories": ["system.operations"],
                        "fidesops_meta": {"data_type": "integer[]"},
                    }
                ],
            }
        ]

    def test_float_list(self):
        api_data = {"user": [{"times": [2.0]}]}
        assert generate_collections(api_data) == [
            {
                "name": "user",
                "fields": [
                    {
                        "name": "times",
                        "data_categories": ["system.operations"],
                        "fidesops_meta": {"data_type": "float[]"},
                    }
                ],
            }
        ]

    def test_string_list(self):
        api_data = {"user": [{"names": ["first last"]}]}
        assert generate_collections(api_data) == [
            {
                "name": "user",
                "fields": [
                    {
                        "name": "names",
                        "data_categories": ["system.operations"],
                        "fidesops_meta": {"data_type": "string[]"},
                    }
                ],
            }
        ]

    def test_object_list(self):
        api_data = {
            "user": [
                {
                    "bank_accounts": [
                        {"bank_name": "Wells Fargo", "status": "active"},
                        {"bank_name": "Schools First", "status": "active"},
                    ]
                }
            ]
        }
        assert generate_collections(api_data) == [
            {
                "name": "user",
                "fields": [
                    {
                        "name": "bank_accounts",
                        "fidesops_meta": {"data_type": "object[]"},
                        "fields": [
                            {
                                "name": "bank_name",
                                "data_categories": ["system.operations"],
                                "fidesops_meta": {"data_type": "string"},
                            },
                            {
                                "name": "status",
                                "data_categories": ["system.operations"],
                                "fidesops_meta": {"data_type": "string"},
                            },
                        ],
                    }
                ],
            }
        ]


class TestGenerateDataset:
    def test_update_existing_name_only_field(self):
        """
        Ensures that an existing field with only a name is updated
        with a default data_category and data_type
        """

        existing_dataset = {
            "fides_key": "example",
            "name": "Example Dataset",
            "description": "An example dataset",
            "collections": [
                {
                    "name": "user",
                    "fields": [{"name": "a"}],
                }
            ],
        }
        api_data = {"user": [{"a": "property"}]}

        generated_dataset = generate_dataset(existing_dataset, api_data)

        assert generated_dataset == {
            "fides_key": "example",
            "name": "Example Dataset",
            "description": "An example dataset",
            "collections": [
                {
                    "name": "user",
                    "fields": [
                        {
                            "name": "a",
                            "data_categories": ["system.operations"],
                            "fidesops_meta": {"data_type": "string"},
                        }
                    ],
                }
            ],
        }

    def test_update_existing_field_with_category(self):
        """
        Ensures that an existing field with an already defined data_category isn't overwritten
        """

        existing_dataset = {
            "fides_key": "example",
            "name": "Example Dataset",
            "description": "An example dataset",
            "collections": [
                {
                    "name": "user",
                    "fields": [{"name": "a", "data_categories": ["user"]}],
                }
            ],
        }
        api_data = {"user": [{"a": "property"}]}

        assert generate_dataset(existing_dataset, api_data) == {
            "fides_key": "example",
            "name": "Example Dataset",
            "description": "An example dataset",
            "collections": [
                {
                    "name": "user",
                    "fields": [
                        {
                            "name": "a",
                            "data_categories": ["user"],
                            "fidesops_meta": {"data_type": "string"},
                        }
                    ],
                }
            ],
        }

    def test_update_existing_scalar_field_to_object_field(self):
        """
        Ensures that an existing scalar field's data type and data_category are updated
        if the generated field is an object type
        """

        existing_dataset = {
            "fides_key": "example",
            "name": "Example Dataset",
            "description": "An example dataset",
            "collections": [
                {
                    "name": "user",
                    "fields": [
                        {
                            "name": "a",
                            "data_categories": ["user"],
                            "fidesops_meta": {"data_type": "string"},
                        }
                    ],
                }
            ],
        }
        api_data = {"user": [{"a": {"first": "A", "last": "B"}}]}

        assert generate_dataset(existing_dataset, api_data) == {
            "fides_key": "example",
            "name": "Example Dataset",
            "description": "An example dataset",
            "collections": [
                {
                    "name": "user",
                    "fields": [
                        {
                            "name": "a",
                            "fidesops_meta": {"data_type": "object"},
                            "fields": [
                                {
                                    "name": "first",
                                    "data_categories": ["system.operations"],
                                    "fidesops_meta": {"data_type": "string"},
                                },
                                {
                                    "name": "last",
                                    "data_categories": ["system.operations"],
                                    "fidesops_meta": {"data_type": "string"},
                                },
                            ],
                        }
                    ],
                }
            ],
        }

    def test_keep_existing_object_field(self):
        """
        Ensures that an existing object field isn't overwritten if the field
        from the API response is empty
        """

        existing_dataset = {
            "fides_key": "example",
            "name": "Example Dataset",
            "description": "An example dataset",
            "collections": [
                {
                    "name": "user",
                    "fields": [
                        {
                            "name": "a",
                            "fidesops_meta": {"data_type": "object"},
                            "fields": [
                                {
                                    "name": "first",
                                    "data_categories": ["system.operations"],
                                    "fidesops_meta": {"data_type": "string"},
                                },
                                {
                                    "name": "last",
                                    "data_categories": ["system.operations"],
                                    "fidesops_meta": {"data_type": "string"},
                                },
                                {
                                    "name": "address",
                                    "fidesops_meta": {"data_type": "object"},
                                    "fields": [
                                        {
                                            "name": "city",
                                            "data_categories": ["system.operations"],
                                            "fidesops_meta": {"data_type": "string"},
                                        },
                                        {
                                            "name": "state",
                                            "data_categories": ["system.operations"],
                                            "fidesops_meta": {"data_type": "string"},
                                        },
                                    ],
                                },
                            ],
                        }
                    ],
                }
            ],
        }
        api_data = {"user": [{"a": None}]}

        assert generate_dataset(existing_dataset, api_data) == {
            "fides_key": "example",
            "name": "Example Dataset",
            "description": "An example dataset",
            "collections": [
                {
                    "name": "user",
                    "fields": [
                        {
                            "name": "a",
                            "fidesops_meta": {"data_type": "object"},
                            "fields": [
                                {
                                    "name": "first",
                                    "data_categories": ["system.operations"],
                                    "fidesops_meta": {"data_type": "string"},
                                },
                                {
                                    "name": "last",
                                    "data_categories": ["system.operations"],
                                    "fidesops_meta": {"data_type": "string"},
                                },
                                {
                                    "name": "address",
                                    "fidesops_meta": {"data_type": "object"},
                                    "fields": [
                                        {
                                            "name": "city",
                                            "data_categories": ["system.operations"],
                                            "fidesops_meta": {"data_type": "string"},
                                        },
                                        {
                                            "name": "state",
                                            "data_categories": ["system.operations"],
                                            "fidesops_meta": {"data_type": "string"},
                                        },
                                    ],
                                },
                            ],
                        }
                    ],
                }
            ],
        }

    def test_keep_existing_scalar_field(self):
        """
        Ensures that an existing scalar field isn't overwritten if the field
        from the API response is empty
        """

        existing_dataset = {
            "fides_key": "example",
            "name": "Example Dataset",
            "description": "An example dataset",
            "collections": [
                {
                    "name": "user",
                    "fields": [
                        {
                            "name": "a",
                            "data_categories": ["user"],
                            "fidesops_meta": {"data_type": "string"},
                        }
                    ],
                }
            ],
        }
        api_data = {"user": [{"a": None}]}

        assert generate_dataset(existing_dataset, api_data) == {
            "fides_key": "example",
            "name": "Example Dataset",
            "description": "An example dataset",
            "collections": [
                {
                    "name": "user",
                    "fields": [
                        {
                            "name": "a",
                            "data_categories": ["user"],
                            "fidesops_meta": {"data_type": "string"},
                        }
                    ],
                }
            ],
        }

    def test_missing_collection(self):
        """
        Ensures that an existing collection is preserved if the API data is empty for a collection
        """

        existing_dataset = {
            "fides_key": "example",
            "name": "Example Dataset",
            "description": "An example dataset",
            "collections": [
                {
                    "name": "user",
                    "fields": [
                        {
                            "name": "a",
                            "data_categories": ["user"],
                            "fidesops_meta": {"data_type": "string"},
                        }
                    ],
                }
            ],
        }
        api_data = {}

        assert generate_dataset(existing_dataset, api_data) == {
            "fides_key": "example",
            "name": "Example Dataset",
            "description": "An example dataset",
            "collections": [
                {
                    "name": "user",
                    "fields": [
                        {
                            "name": "a",
                            "data_categories": ["user"],
                            "fidesops_meta": {"data_type": "string"},
                        }
                    ],
                }
            ],
        }

    def test_collection_order(self):
        """
        Ensures that the collection matches the collection order in the existing dataset
        """

        existing_dataset = {
            "fides_key": "example",
            "name": "Example Dataset",
            "description": "An example dataset",
            "collections": [
                {
                    "name": "user",
                    "fields": [
                        {
                            "name": "a",
                            "data_categories": ["user"],
                            "fidesops_meta": {"data_type": "string"},
                        }
                    ],
                },
                {
                    "name": "posts",
                    "fields": [
                        {
                            "name": "b",
                            "data_categories": ["user"],
                            "fidesops_meta": {"data_type": "string"},
                        }
                    ],
                },
            ],
        }
        api_data = {}

        assert generate_dataset(existing_dataset, api_data) == {
            "fides_key": "example",
            "name": "Example Dataset",
            "description": "An example dataset",
            "collections": [
                {
                    "name": "user",
                    "fields": [
                        {
                            "name": "a",
                            "data_categories": ["user"],
                            "fidesops_meta": {"data_type": "string"},
                        }
                    ],
                },
                {
                    "name": "posts",
                    "fields": [
                        {
                            "name": "b",
                            "data_categories": ["user"],
                            "fidesops_meta": {"data_type": "string"},
                        }
                    ],
                },
            ],
        }

    def test_collection_order_override(self):
        """
        Ensures that the collection order matches the provided order
        """

        existing_dataset = {
            "fides_key": "example",
            "name": "Example Dataset",
            "description": "An example dataset",
            "collections": [
                {
                    "name": "user",
                    "fields": [
                        {
                            "name": "a",
                            "data_categories": ["user"],
                            "fidesops_meta": {"data_type": "string"},
                        }
                    ],
                },
                {
                    "name": "posts",
                    "fields": [
                        {
                            "name": "b",
                            "data_categories": ["user"],
                            "fidesops_meta": {"data_type": "string"},
                        }
                    ],
                },
            ],
        }
        api_data = {}

        assert generate_dataset(existing_dataset, api_data, ["posts", "user"]) == {
            "fides_key": "example",
            "name": "Example Dataset",
            "description": "An example dataset",
            "collections": [
                {
                    "name": "posts",
                    "fields": [
                        {
                            "name": "b",
                            "data_categories": ["user"],
                            "fidesops_meta": {"data_type": "string"},
                        }
                    ],
                },
                {
                    "name": "user",
                    "fields": [
                        {
                            "name": "a",
                            "data_categories": ["user"],
                            "fidesops_meta": {"data_type": "string"},
                        }
                    ],
                },
            ],
        }
