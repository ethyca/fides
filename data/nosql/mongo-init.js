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
        "gender": "male",
        "birthday": new ISODate("1988-01-10")
    },
     {
        "customer_id": 2,
        "gender": "female",
        "birthday": new ISODate("1985-03-05")
    },
    {
        "customer_id": 3,
        "gender": "female",
        "birthday": new ISODate("1990-02-28")
    }
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
])

db.customer.insert([
    {
        "id": "1",
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
        "id": "2",
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
        "id": "3",
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
])



db.payment_card.insert([
    {
        "id": "pay_aaa-aaa",
        "name": "Example Card 1",
        "ccn": "123456789",
        "code": "321",
        "preferred": true,
        "customer_id": "1",
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
        "customer_id": "2",
        "billing_address": {
            "house": 123,
            "street": "Example Street",
            "city": "Exampletown",
            "state": "NY",
            "zip": "12345"
        }
    }
])

db.product.insert([
    {"id": "1", "name": "Example Product 1", "price": 10},
    {"id": "2", "name": "Example Product 2", "price": 20},
    {"id": "3", "name": "Example Product 2", "price": 50}

])

db.orders.insert([
    {
        "id": "ord_aaa-aaa",
        "customer_id": "1",
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
        "customer_id": "2",
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
        "customer_id": "1",
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
        "customer_id": "1",
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
])

db.reports.insert([
    {"email": "admin-account@example.com", "name": "Monthly Report", "year": 2021, "month": 8, "total_visits": 100},
    {"email": "admin-account@example.com", "name": "Monthly Report", "year": 2021, "month": 9, "total_visits": 100},
    {"email": "admin-account@example.com", "name": "Monthly Report", "year": 2021, "month": 10, "total_visits": 100},
    {"email": "admin-account@example.com", "name": "Monthly Report", "year": 2021, "month": 11, "total_visits": 100}
])

//values to support test by specific objectId search

db.type_link_test.insert([
    {"_id":ObjectId("000000000000000000000001"), "name":"v1", "key":1, "email":"test1@example.com"},
    {"_id":ObjectId("000000000000000000000002"), "name":"v2", "key":2, "email":"test1@example.com"},
    {"_id":ObjectId("000000000000000000000003"), "name":"v3", "key":3, "email":"test1@example.com"}
])
