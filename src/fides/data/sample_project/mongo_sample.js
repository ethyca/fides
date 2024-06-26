db.createUser(
        {
            user: "mongo_user",
            pwd: "mongo_pass",
            roles: [
                {
                    role: "readWrite",
                    db: "mongo_test"
                }
            ]
        }
);

db.customer_details.insert([
    {
        "customer_id": 1,
        "customer_uuid": new UUID('3b241101-e2bb-4255-8caf-4136c566a962'),
        "gender": "male",
        "birthday": new ISODate("1988-01-10"),
        "workplace_info": {  // Discovered object field
            "employer": "Mountain Baking Company",
            "position": "Chief Strategist",
            "direct_reports": ["Robbie Margo", "Sully Hunter"]  // Discovered nested array of scalars
        },
        "emergency_contacts": [  // Discovered array of objects
            {"name": "June Customer", "relationship": "mother", "phone": "444-444-4444"},
            {"name": "Josh Customer", "relationship": "brother", "phone": "111-111-111"},
        ],
        "children": ["Christopher Customer", "Courtney Customer"],  // Discovered array of scalars
        "travel_identifiers": ["A111-11111", "B111-11111"], // References a nested array field, flights.passenger_information.passenger_ids
        "comments": [{"comment_id": "com_0001"}, {"comment_id": "com_0003"}, {"comment_id": "com_0005"}] // Array of objects references a nested object field, mongo_test.conversations.thread.comment
    },
     {
        "customer_id": 2,
        "gender": "female",
        "birthday": new ISODate("1985-03-05"),
        "workplace_info": {
            "employer": "Incline Software Company",
            "position": "Software Engineer",
            "direct_reports": ["Langdon Jeanne", "Dorothy Faron"]
        },
        "emergency_contacts": [
            {"name": "Jesse Customer", "relationship": "spouse", "phone": "111-111-1111"},
            {"name": "Jonathan Customer", "relationship": "brother", "phone": "222-222-2222"}
        ],
         "children": ["Connie Customer"],
        "travel_identifiers": ["C222-222222"]
    },
    {
        "customer_id": 3,
        "gender": "female",
        "birthday": new ISODate("1990-02-28"),
        "travel_identifiers": ["D111-11111"],
        "children": ["Erica Example"],
        "comments": [{"comment_id": "com_0002"}, {"comment_id": "com_0004"}, {"comment_id": "com_0006"}]
    }
]);

db.customer_feedback.insert([
    {
        "customer_information": {
            "email": "customer-1@example.com",  // Nested identity
            "phone": "333-333-3333",
            "internal_customer_id": "cust_001"  // References nested field internal_customer_profile.customer_identifiers.internal_id
        },
        "rating": 3,
        "date": new ISODate("2022-01-05"),
        "message": "Customer service wait times have increased to over an hour."
    },
    {
        "customer_information": {
            "email": "customer-2@example.com",
            "phone": "111-111-1111",
            "internal_customer_id": "cust_002"
        },
        "rating": 5,
        "date": new ISODate("2022-01-10"),
        "message": "Customer service rep was very helpful and answered all my questions."
    }
]);

db.internal_customer_profile.insert([
    {
        "customer_identifiers": {
            "internal_id": "cust_001"  // Nested field referenced by another nested field (customer_information.internal_customer_id)
        },
        "derived_interests": ["marketing", "food"]  // Discovered simple array
    },
    {
         "customer_identifiers": {
            "internal_id": "cust_002",
            "derived_phone": ["757-499-5508"]
        },
        "derived_interests": ["programming", "hiking", "skateboarding"]
    },
    {
        "customer_identifiers": {
            "internal_id": "cust_003",
            "derived_emails": ["jane1@example.com", "jane@example.com"],  // Identity within an array field
            "derived_phone": ["530-486-6983", "254-344-9868"]
        },
        "derived_interests": ["interior design", "travel", "photography"]
    }
]);

db.conversations.insert([
    {
        "thread": [
            {"comment": "com_0001", "message": "hello, testing in-flight chat feature", "chat_name": "John C", "ccn": "123456789"}, // ccn points to mongo_test:payment_card
            {"comment": "com_0002", "message": "yep, got your message, looks like it works", "chat_name": "Jane C", "ccn": "987654321"}
        ]
    },
    {
        "thread": [
            {"comment": "com_0003", "message": "can I borrow your headphones?", "chat_name": "John C", "ccn": "123456789"},
            {"comment": "com_0004", "message": "no, sorry I'm using them.", "chat_name": "Jane C", "ccn": "987654321"},
            {"comment": "com_0005", "message": "did you bring anything to read?", "chat_name": "John C", "ccn": "123456789"},
            {"comment": "com_0006", "message": "try reading the informational brochure in the seat pouch.", "chat_name": "Jane C"}
        ]
    },
    {
       "thread": [
            {"comment": "com_0007", "message": "Flight attendants, prepare for take-off please.", "chat_name": "Pilot 1"},
            {"comment": "com_0008", "message": "Airliner A, runway 12 cleared for takeoff", "chat_name": "ATC 2"},
        ]
    }
]);

db.flights.insert([
    {
        "passenger_information": {
            "passenger_ids": ["old_travel_number", "A111-11111"],  // Array field referenced by another array field (customer_details.travel_identifiers)
            "full_name": "John Customer"
        },
        "flight_no": "AA230",
        "date": "2021-01-01",
        "pilots": ["1", "2"],  // Array field referencing a scalar field mongo_test.employee.id
        "plane": NumberInt(10002) // Scalar field referenced *by* an array field mongo_test.aircraft.planes
    },
    {
        "passenger_information": {
            "passenger_ids": ["E111-11111", "D111-11111"],
            "full_name": "Jane Customer"
        },
        "flight_no": "AA240",
        "date": "2021-02-01",
        "pilots": ["2"],
        "plane": NumberInt(30005)
    }
]);


db.aircraft.insert([
    {"model": "Airbus A350", "planes": ["10001", "10002", "10003", "10004", "10005"]},
    {"model": "Boeing 747-8", "planes": ["30005", "30006", "30007"]}
]);


db.employee.insert([
    {
        "email": "employee-1@example.com",
        "name": "Jack Employee",
        "id": "1",
        "address": {
            "house": 555,
            "street": "Example Ave",
            "city": "Example City",
            "state": "NY",
            "zip": "12000"
        },
	"foreign_id": "000000000000000000000001"
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
            "zip": "12000"
        },
	"foreign_id": "000000000000000000000002"
    }
]);

db.customer.insert([
    {
        "id": NumberInt(1),
        "email": "customer-1@example.com",
        "name": "John Customer",
        "created": Date("2020-04-01 11:47:42"),
        "address": {
            "house": 123,
            "street": "Example Street",
            "city": "Exampletown",
            "state": "NY",
            "zip": "12345"
        },
        "login": [
            {"time": Date("2021-01-01 01:00:00")},
            {"time": Date("2021-01-02 01:00:00")},
            {"time": Date("2021-01-03 01:00:00")},
            {"time": Date("2021-01-04 01:00:00")},
            {"time": Date("2021-01-05 01:00:00")},
            {"time": Date("2021-01-06 01:00:00")},
        ],
        "last_visit": Date("2021-01-06 01:00:00"),
        "alt_email": "customer-1-alt@example.com",
        "service_request": [
            {"id": "ser_aaa-aaa", "opened": Date("2021-01-01"), "closed": Date("2021-01-03"), "employee_id": "1"}
        ]
    },
    {
        "id": NumberInt(2),
        "email": "customer-2@example.com",
        "name": "Jill Customer",
        "created": Date("2020-04-01 11:47:42"),
        "address": {
            "house": 4,
            "street": "Example Lane",
            "city": "Exampletown",
            "state": "NY",
            "zip": "12321"
        },
         "login": [
            {"time": Date("2021-01-06 01:00:00")},
        ],
        "last_visit": Date("2021-01-06 01:00:00"),
        "alt_email": null,
         "service_request": [
            {"id": "ser_bbb-bbb", "opened": Date("2021-01-04"), "closed": null, "employee_id": "1"}
        ]
    },
     {
        "id": NumberInt(3),
        "email": "customer-3@example.com",
        "name": null,
        "address": null,
        "login": null,
        "last_visit": null,
        "alt_email": null,
         "service_request": [
            {"id": "ser_ccc-ccc", "opened": Date("2021-01-05"), "closed": Date("2021-01-07"), "employee_id": "1"},
            {"id": "ser_ddd-ddd", "opened": Date("2021-05-05"), "closed": Date("2021-05-08"), "employee_id": "2"}

        ]
    }
]);

db.rewards.insert([
    {"owner": [{"phone": "530-486-6983", "shopper_name": "janec"}, {"phone": "818-695-1881", "shopper_name": "janec"}], "points": 95, "expiration": Date("2023-01-05")},
    {"owner": [{"phone": "254-344-9868", "shopper_name": "janec"}], "points": 50, "expiration": Date("2023-02-05")},
    {"owner": [{"phone": "304-969-7140", "shopper-name": "timc"}], "points": 3, "expiration": Date("2022-02-05")}
])


db.payment_card.insert([
    {
        "id": "pay_aaa-aaa",
        "name": "Example Card 1",
        "ccn": "123456789",
        "code": "321",
        "preferred": true,
        "customer_id": NumberInt(1),
        "billing_address": {
            "house": 123,
            "street": "Example Street",
            "city": "Exampletown",
            "state": "NY",
            "zip": "12345"
        }
    },
    {
        "id": "pay_bbb-bbb",
        "name": "Example Card 2",
        "ccn": "987654321",
        "code": "123",
        "preferred": false,
        "customer_id": NumberInt(2),
        "billing_address": {
            "house": 123,
            "street": "Example Street",
            "city": "Exampletown",
            "state": "NY",
            "zip": "12345"
        }
    }
]);

db.product.insert([
    {"id": "1", "name": "Example Product 1", "price": 10},
    {"id": "2", "name": "Example Product 2", "price": 20},
    {"id": "3", "name": "Example Product 2", "price": 50}

]);

db.orders.insert([
    {
        "id": "ord_aaa-aaa",
        "customer_id": NumberInt(1),
        "shipping_address": {
            "house": 4,
            "street": "Example Lane",
            "city": "Exampletown",
            "state": "NY",
            "zip": "12321"
        },
        "payment_card_id": "pay_aaa-aaa",
        "order_item": [
            {"item_no": 1, "product_id": "1", "quantity": 1},
        ]
    },
    {
        "id": "ord_bbb-bbb",
        "customer_id": NumberInt(2),
            "shipping_address":  {
            "house": 123,
            "street": "Example Street",
            "city": "Exampletown",
            "state": "NY",
            "zip": "12345",
        },
        "payment_card_id": "pay_bbb-bbb",
        "order_item": [
            {"item_no": 1, "product_id": "1", "quantity": 1},
        ]
    },
      {
        "id": "ord_ccc-ccc",
        "customer_id": NumberInt(1),
            "shipping_address":  {
            "house": 123,
            "street": "Example Street",
            "city": "Exampletown",
            "state": "NY",
            "zip": "12345"
        },
        "payment_card_id": "pay_aaa-aaa",
         "order_item": [
            {"item_no": 1, "product_id": "1", "quantity": 1},
            {"item_no": 2, "product_id": "2", "quantity": 1},

        ]

    },
      {
        "id": "ord_ddd-ddd",
        "customer_id": NumberInt(1),
            "shipping_address":  {
            "house": 123,
            "street": "Example Street",
            "city": "Exampletown",
            "state": "NY",
            "zip": "12345"
        },
        "payment_card_id": "pay_bbb-bbb",
        "order_item": [
            {"item_no": 1, "product_id": "1", "quantity": 1},
        ]

    },
]);

db.reports.insert([
    {"email": "admin-account@example.com", "name": "Monthly Report", "year": 2021, "month": 8, "total_visits": 100},
    {"email": "admin-account@example.com", "name": "Monthly Report", "year": 2021, "month": 9, "total_visits": 100},
    {"email": "admin-account@example.com", "name": "Monthly Report", "year": 2021, "month": 10, "total_visits": 100},
    {"email": "admin-account@example.com", "name": "Monthly Report", "year": 2021, "month": 11, "total_visits": 100}
]);

db.composite_pk_test.insert([
    {"id_a":1, "id_b":10, "description":"linked to customer 1", "customer_id": NumberInt(1)},
    {"id_a":1, "id_b":11, "description":"linked to customer 2", "customer_id": NumberInt(2)},
    {"id_a":2, "id_b":10, "description":"linked to customer 3", "customer_id": NumberInt(3)}
]);

//values to support test by specific objectId search

db.type_link_test.insert([
    {"_id":ObjectId("000000000000000000000001"), "name":"v1", "key":1, "email":"test1@example.com"},
    {"_id":ObjectId("000000000000000000000002"), "name":"v2", "key":2, "email":"test1@example.com"},
    {"_id":ObjectId("000000000000000000000003"), "name":"v3", "key":3, "email":"test1@example.com"}
]);
