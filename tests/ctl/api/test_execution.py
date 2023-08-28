test_traversal_map = (
    {
        "__ROOT__:__ROOT__": {
            "from": {},
            "to": {
                "mongo_test:internal_customer_profile": {
                    "email -> customer_identifiers.derived_emails"
                },
                "postgres_example_test_dataset:employee": {"email -> email"},
                "postgres_example_test_dataset:service_request": {
                    "email -> alt_email",
                    "email -> email",
                },
                "postgres_example_test_dataset:visit": {"email -> email"},
                "mongo_test:customer_feedback": {"email -> customer_information.email"},
                "postgres_example_test_dataset:customer": {"email -> email"},
                "mongo_test:employee": {"email -> email"},
                "postgres_example_test_dataset:report": {"email -> email"},
            },
        },
        "mongo_test:internal_customer_profile": {
            "from": {
                "__ROOT__:__ROOT__": {"email -> customer_identifiers.derived_emails"},
                "mongo_test:customer_feedback": {
                    "customer_information.internal_customer_id -> customer_identifiers.internal_id"
                },
            },
            "to": {
                "mongo_test:rewards": {
                    "customer_identifiers.derived_phone -> owner.phone"
                }
            },
        },
        "postgres_example_test_dataset:employee": {
            "from": {"__ROOT__:__ROOT__": {"email -> email"}},
            "to": {
                "postgres_example_test_dataset:service_request": {"id -> employee_id"},
                "postgres_example_test_dataset:address": {"address_id -> id"},
            },
        },
        "postgres_example_test_dataset:service_request": {
            "from": {
                "postgres_example_test_dataset:employee": {"id -> employee_id"},
                "__ROOT__:__ROOT__": {"email -> alt_email", "email -> email"},
            },
            "to": {},
        },
        "postgres_example_test_dataset:visit": {
            "from": {"__ROOT__:__ROOT__": {"email -> email"}},
            "to": {},
        },
        "mongo_test:customer_feedback": {
            "from": {"__ROOT__:__ROOT__": {"email -> customer_information.email"}},
            "to": {
                "mongo_test:internal_customer_profile": {
                    "customer_information.internal_customer_id -> customer_identifiers.internal_id"
                }
            },
        },
        "postgres_example_test_dataset:customer": {
            "from": {"__ROOT__:__ROOT__": {"email -> email"}},
            "to": {
                "postgres_example_test_dataset:address": {"address_id -> id"},
                "postgres_example_test_dataset:orders": {"id -> customer_id"},
                "postgres_example_test_dataset:login": {"id -> customer_id"},
                "postgres_example_test_dataset:payment_card": {"id -> customer_id"},
                "mongo_test:customer_details": {"id -> customer_id"},
            },
        },
        "mongo_test:employee": {
            "from": {
                "mongo_test:flights": {"pilots -> id"},
                "__ROOT__:__ROOT__": {"email -> email"},
            },
            "to": {},
        },
        "postgres_example_test_dataset:report": {
            "from": {"__ROOT__:__ROOT__": {"email -> email"}},
            "to": {},
        },
        "mongo_test:rewards": {
            "from": {
                "mongo_test:internal_customer_profile": {
                    "customer_identifiers.derived_phone -> owner.phone"
                }
            },
            "to": {},
        },
        "postgres_example_test_dataset:address": {
            "from": {
                "postgres_example_test_dataset:orders": {"shipping_address_id -> id"},
                "postgres_example_test_dataset:customer": {"address_id -> id"},
                "postgres_example_test_dataset:employee": {"address_id -> id"},
                "postgres_example_test_dataset:payment_card": {
                    "billing_address_id -> id"
                },
            },
            "to": {},
        },
        "postgres_example_test_dataset:orders": {
            "from": {"postgres_example_test_dataset:customer": {"id -> customer_id"}},
            "to": {
                "postgres_example_test_dataset:address": {"shipping_address_id -> id"},
                "postgres_example_test_dataset:order_item": {"id -> order_id"},
            },
        },
        "postgres_example_test_dataset:login": {
            "from": {"postgres_example_test_dataset:customer": {"id -> customer_id"}},
            "to": {},
        },
        "postgres_example_test_dataset:payment_card": {
            "from": {"postgres_example_test_dataset:customer": {"id -> customer_id"}},
            "to": {
                "postgres_example_test_dataset:address": {"billing_address_id -> id"}
            },
        },
        "mongo_test:customer_details": {
            "from": {"postgres_example_test_dataset:customer": {"id -> customer_id"}},
            "to": {
                "mongo_test:conversations": {"comments.comment_id -> thread.comment"},
                "mongo_test:flights": {
                    "travel_identifiers -> passenger_information.passenger_ids"
                },
            },
        },
        "postgres_example_test_dataset:order_item": {
            "from": {"postgres_example_test_dataset:orders": {"id -> order_id"}},
            "to": {"postgres_example_test_dataset:product": {"product_id -> id"}},
        },
        "mongo_test:conversations": {
            "from": {
                "mongo_test:customer_details": {"comments.comment_id -> thread.comment"}
            },
            "to": {"mongo_test:payment_card": {"thread.ccn -> ccn"}},
        },
        "mongo_test:flights": {
            "from": {
                "mongo_test:customer_details": {
                    "travel_identifiers -> passenger_information.passenger_ids"
                }
            },
            "to": {
                "mongo_test:employee": {"pilots -> id"},
                "mongo_test:aircraft": {"plane -> planes"},
            },
        },
        "postgres_example_test_dataset:product": {
            "from": {"postgres_example_test_dataset:order_item": {"product_id -> id"}},
            "to": {},
        },
        "mongo_test:payment_card": {
            "from": {"mongo_test:conversations": {"thread.ccn -> ccn"}},
            "to": {},
        },
        "mongo_test:aircraft": {
            "from": {"mongo_test:flights": {"plane -> planes"}},
            "to": {},
        },
    },
    [
        "mongo_test:internal_customer_profile",
        "postgres_example_test_dataset:service_request",
        "postgres_example_test_dataset:visit",
        "mongo_test:employee",
        "postgres_example_test_dataset:report",
        "mongo_test:rewards",
        "postgres_example_test_dataset:address",
        "postgres_example_test_dataset:login",
        "postgres_example_test_dataset:product",
        "mongo_test:payment_card",
        "mongo_test:aircraft",
    ],
)
