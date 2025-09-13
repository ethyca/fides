from datetime import datetime
from uuid import UUID

from bson import ObjectId

# Static representation of the mongo_sample.js dataset.
# Each top-level key is a collection name and the value is a list of
# documents that should be inserted into that collection.
# This is meant to replicate the data seeding that happens when running
# `nox -s dev -- mongodb` for the base MongoDB integration tests.

mongo_sample_data = {
    "customer_details": [
        {
            "customer_id": 1,
            "customer_uuid": UUID("3b241101-e2bb-4255-8caf-4136c566a962"),
            "gender": "male",
            "birthday": datetime(1988, 1, 10),
            "workplace_info": {
                "employer": "Mountain Baking Company",
                "position": "Chief Strategist",
                "direct_reports": [
                    "Robbie Margo",
                    "Sully Hunter",
                ],
            },
            "emergency_contacts": [
                {
                    "name": "June Customer",
                    "relationship": "mother",
                    "phone": "444-444-4444",
                },
                {
                    "name": "Josh Customer",
                    "relationship": "brother",
                    "phone": "111-111-111",
                },
            ],
            "children": [
                "Christopher Customer",
                "Courtney Customer",
            ],
            "travel_identifiers": [
                "A111-11111",
                "B111-11111",
            ],
            "comments": [
                {"comment_id": "com_0001"},
                {"comment_id": "com_0003"},
                {"comment_id": "com_0005"},
            ],
        },
        {
            "customer_id": 2,
            "gender": "female",
            "birthday": datetime(1985, 3, 5),
            "workplace_info": {
                "employer": "Incline Software Company",
                "position": "Software Engineer",
                "direct_reports": [
                    "Langdon Jeanne",
                    "Dorothy Faron",
                ],
            },
            "emergency_contacts": [
                {
                    "name": "Jesse Customer",
                    "relationship": "spouse",
                    "phone": "111-111-1111",
                },
                {
                    "name": "Jonathan Customer",
                    "relationship": "brother",
                    "phone": "222-222-2222",
                },
            ],
            "children": ["Connie Customer"],
            "travel_identifiers": ["C222-222222"],
        },
        {
            "customer_id": 3,
            "gender": "female",
            "birthday": datetime(1990, 2, 28),
            "travel_identifiers": ["D111-11111"],
            "children": ["Erica Example"],
            "comments": [
                {"comment_id": "com_0002"},
                {"comment_id": "com_0004"},
                {"comment_id": "com_0006"},
            ],
        },
    ],
    # ------------------- customer_feedback -------------------
    "customer_feedback": [
        {
            "customer_information": {
                "email": "customer-1@example.com",
                "phone": "333-333-3333",
                "internal_customer_id": "cust_001",
            },
            "rating": 3,
            "date": datetime(2022, 1, 5),
            "message": "Customer service wait times have increased to over an hour.",
        },
        {
            "customer_information": {
                "email": "customer-2@example.com",
                "phone": "111-111-1111",
                "internal_customer_id": "cust_002",
            },
            "rating": 5,
            "date": datetime(2022, 1, 10),
            "message": "Customer service rep was very helpful and answered all my questions.",
        },
    ],
    # ---------------- internal_customer_profile --------------
    "internal_customer_profile": [
        {
            "customer_identifiers": {"internal_id": "cust_001"},
            "derived_interests": ["marketing", "food"],
        },
        {
            "customer_identifiers": {
                "internal_id": "cust_002",
                "derived_phone": ["757-499-5508"],
            },
            "derived_interests": ["programming", "hiking", "skateboarding"],
        },
        {
            "customer_identifiers": {
                "internal_id": "cust_003",
                "derived_emails": [
                    "jane1@example.com",
                    "jane@example.com",
                ],
                "derived_phone": [
                    "530-486-6983",
                    "254-344-9868",
                ],
            },
            "derived_interests": [
                "interior design",
                "travel",
                "photography",
            ],
        },
    ],
    # --------------------- conversations ---------------------
    "conversations": [
        {
            "thread": [
                {
                    "comment": "com_0001",
                    "message": "hello, testing in-flight chat feature",
                    "chat_name": "John C",
                    "ccn": "123456789",
                },
                {
                    "comment": "com_0002",
                    "message": "yep, got your message, looks like it works",
                    "chat_name": "Jane C",
                    "ccn": "987654321",
                },
            ]
        },
        {
            "thread": [
                {
                    "comment": "com_0003",
                    "message": "can I borrow your headphones?",
                    "chat_name": "John C",
                    "ccn": "123456789",
                },
                {
                    "comment": "com_0004",
                    "message": "no, sorry I'm using them.",
                    "chat_name": "Jane C",
                    "ccn": "987654321",
                },
                {
                    "comment": "com_0005",
                    "message": "did you bring anything to read?",
                    "chat_name": "John C",
                    "ccn": "123456789",
                },
                {
                    "comment": "com_0006",
                    "message": "try reading the informational brochure in the seat pouch.",
                    "chat_name": "Jane C",
                },
            ]
        },
        {
            "thread": [
                {
                    "comment": "com_0007",
                    "message": "Flight attendants, prepare for take-off please.",
                    "chat_name": "Pilot 1",
                },
                {
                    "comment": "com_0008",
                    "message": "Airliner A, runway 12 cleared for takeoff",
                    "chat_name": "ATC 2",
                },
            ]
        },
    ],
    # ----------------------- flights -------------------------
    "flights": [
        {
            "passenger_information": {
                "passenger_ids": [
                    "old_travel_number",
                    "A111-11111",
                ],
                "full_name": "John Customer",
            },
            "flight_no": "AA230",
            "date": "2021-01-01",
            "pilots": ["1", "2"],
            "plane": 10002,
        },
        {
            "passenger_information": {
                "passenger_ids": [
                    "E111-11111",
                    "D111-11111",
                ],
                "full_name": "Jane Customer",
            },
            "flight_no": "AA240",
            "date": "2021-02-01",
            "pilots": ["2"],
            "plane": 30005,
        },
    ],
    # ---------------------- aircraft -------------------------
    "aircraft": [
        {
            "model": "Airbus A350",
            "planes": [
                "10001",
                "10002",
                "10003",
                "10004",
                "10005",
            ],
        },
        {
            "model": "Boeing 747-8",
            "planes": [
                "30005",
                "30006",
                "30007",
            ],
        },
    ],
    # ---------------------- employee -------------------------
    "employee": [
        {
            "email": "employee-1@example.com",
            "name": "Jack Employee",
            "id": "1",
            "address": {
                "house": 555,
                "street": "Example Ave",
                "city": "Example City",
                "state": "NY",
                "zip": "12000",
            },
            "foreign_id": "000000000000000000000001",
        },
        {
            "email": "employee-2@example.com",
            "name": "Jane Employee",
            "id": "2",
            "address": {
                "house": 555,
                "street": "Example Ave",
                "city": "Example City",
                "state": "NY",
                "zip": "12000",
            },
            "foreign_id": "000000000000000000000002",
        },
    ],
    # ----------------------- customer -----------------------
    "customer": [
        {
            "id": 1,
            "email": "customer-1@example.com",
            "name": "John Customer",
            "created": datetime(2020, 4, 1, 11, 47, 42),
            "address": {
                "house": 123,
                "street": "Example Street",
                "city": "Exampletown",
                "state": "NY",
                "zip": "12345",
            },
            "login": [
                {"time": datetime(2021, 1, 1, 1, 0, 0)},
                {"time": datetime(2021, 1, 2, 1, 0, 0)},
                {"time": datetime(2021, 1, 3, 1, 0, 0)},
                {"time": datetime(2021, 1, 4, 1, 0, 0)},
                {"time": datetime(2021, 1, 5, 1, 0, 0)},
                {"time": datetime(2021, 1, 6, 1, 0, 0)},
            ],
            "last_visit": datetime(2021, 1, 6, 1, 0, 0),
            "alt_email": "customer-1-alt@example.com",
            "service_request": [
                {
                    "id": "ser_aaa-aaa",
                    "opened": datetime(2021, 1, 1),
                    "closed": datetime(2021, 1, 3),
                    "employee_id": "1",
                }
            ],
        },
        {
            "id": 2,
            "email": "customer-2@example.com",
            "name": "Jill Customer",
            "created": datetime(2020, 4, 1, 11, 47, 42),
            "address": {
                "house": 4,
                "street": "Example Lane",
                "city": "Exampletown",
                "state": "NY",
                "zip": "12321",
            },
            "login": [
                {"time": datetime(2021, 1, 6, 1, 0, 0)},
            ],
            "last_visit": datetime(2021, 1, 6, 1, 0, 0),
            "alt_email": None,
            "service_request": [
                {
                    "id": "ser_bbb-bbb",
                    "opened": datetime(2021, 1, 4),
                    "closed": None,
                    "employee_id": "1",
                }
            ],
        },
        {
            "id": 3,
            "email": "customer-3@example.com",
            "name": None,
            "address": None,
            "login": None,
            "last_visit": None,
            "alt_email": None,
            "service_request": [
                {
                    "id": "ser_ccc-ccc",
                    "opened": datetime(2021, 1, 5),
                    "closed": datetime(2021, 1, 7),
                    "employee_id": "1",
                },
                {
                    "id": "ser_ddd-ddd",
                    "opened": datetime(2021, 5, 5),
                    "closed": datetime(2021, 5, 8),
                    "employee_id": "2",
                },
            ],
        },
    ],
    # ----------------------- rewards ------------------------
    "rewards": [
        {
            "owner": [
                {"phone": "530-486-6983", "shopper_name": "janec"},
                {"phone": "818-695-1881", "shopper_name": "janec"},
            ],
            "points": 95,
            "expiration": datetime(2023, 1, 5),
        },
        {
            "owner": [
                {"phone": "254-344-9868", "shopper_name": "janec"},
            ],
            "points": 50,
            "expiration": datetime(2023, 2, 5),
        },
        {
            "owner": [
                {"phone": "304-969-7140", "shopper-name": "timc"},
            ],
            "points": 3,
            "expiration": datetime(2022, 2, 5),
        },
    ],
    # --------------------- payment_card ---------------------
    "payment_card": [
        {
            "id": "pay_aaa-aaa",
            "name": "Example Card 1",
            "ccn": "123456789",
            "code": "321",
            "preferred": True,
            "customer_id": 1,
            "billing_address": {
                "house": 123,
                "street": "Example Street",
                "city": "Exampletown",
                "state": "NY",
                "zip": "12345",
            },
        },
        {
            "id": "pay_bbb-bbb",
            "name": "Example Card 2",
            "ccn": "987654321",
            "code": "123",
            "preferred": False,
            "customer_id": 2,
            "billing_address": {
                "house": 123,
                "street": "Example Street",
                "city": "Exampletown",
                "state": "NY",
                "zip": "12345",
            },
        },
    ],
    # ------------------------ product -----------------------
    "product": [
        {"id": "1", "name": "Example Product 1", "price": 10},
        {"id": "2", "name": "Example Product 2", "price": 20},
        {"id": "3", "name": "Example Product 2", "price": 50},
    ],
    # ------------------------ orders ------------------------
    "orders": [
        {
            "id": "ord_aaa-aaa",
            "customer_id": 1,
            "shipping_address": {
                "house": 4,
                "street": "Example Lane",
                "city": "Exampletown",
                "state": "NY",
                "zip": "12321",
            },
            "payment_card_id": "pay_aaa-aaa",
            "order_item": [
                {"item_no": 1, "product_id": "1", "quantity": 1},
            ],
        },
        {
            "id": "ord_bbb-bbb",
            "customer_id": 2,
            "shipping_address": {
                "house": 123,
                "street": "Example Street",
                "city": "Exampletown",
                "state": "NY",
                "zip": "12345",
            },
            "payment_card_id": "pay_bbb-bbb",
            "order_item": [
                {"item_no": 1, "product_id": "1", "quantity": 1},
            ],
        },
        {
            "id": "ord_ccc-ccc",
            "customer_id": 1,
            "shipping_address": {
                "house": 123,
                "street": "Example Street",
                "city": "Exampletown",
                "state": "NY",
                "zip": "12345",
            },
            "payment_card_id": "pay_aaa-aaa",
            "order_item": [
                {"item_no": 1, "product_id": "1", "quantity": 1},
                {"item_no": 2, "product_id": "2", "quantity": 1},
            ],
        },
        {
            "id": "ord_ddd-ddd",
            "customer_id": 1,
            "shipping_address": {
                "house": 123,
                "street": "Example Street",
                "city": "Exampletown",
                "state": "NY",
                "zip": "12345",
            },
            "payment_card_id": "pay_bbb-bbb",
            "order_item": [
                {"item_no": 1, "product_id": "1", "quantity": 1},
            ],
        },
    ],
    # ----------------------- reports ------------------------
    "reports": [
        {
            "email": "admin-account@example.com",
            "name": "Monthly Report",
            "year": 2021,
            "month": 8,
            "total_visits": 100,
        },
        {
            "email": "admin-account@example.com",
            "name": "Monthly Report",
            "year": 2021,
            "month": 9,
            "total_visits": 100,
        },
        {
            "email": "admin-account@example.com",
            "name": "Monthly Report",
            "year": 2021,
            "month": 10,
            "total_visits": 100,
        },
        {
            "email": "admin-account@example.com",
            "name": "Monthly Report",
            "year": 2021,
            "month": 11,
            "total_visits": 100,
        },
    ],
    # ----------------- composite_pk_test --------------------
    "composite_pk_test": [
        {
            "id_a": 1,
            "id_b": 10,
            "description": "linked to customer 1",
            "customer_id": 1,
        },
        {
            "id_a": 1,
            "id_b": 11,
            "description": "linked to customer 2",
            "customer_id": 2,
        },
        {
            "id_a": 2,
            "id_b": 10,
            "description": "linked to customer 3",
            "customer_id": 3,
        },
    ],
    # -------------------- type_link_test --------------------
    "type_link_test": [
        {
            "_id": ObjectId("000000000000000000000001"),
            "name": "v1",
            "key": 1,
            "email": "test1@example.com",
        },
        {
            "_id": ObjectId("000000000000000000000002"),
            "name": "v2",
            "key": 2,
            "email": "test1@example.com",
        },
        {
            "_id": ObjectId("000000000000000000000003"),
            "name": "v3",
            "key": 3,
            "email": "test1@example.com",
        },
    ],
}
