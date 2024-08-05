CREATE KEYSPACE IF NOT EXISTS app_keyspace WITH REPLICATION = {'class': 'SimpleStrategy', 'replication_factor': 3};
USE app_keyspace;

CREATE TABLE if not exists users (
    user_id INT PRIMARY KEY,
    name TEXT,
    age INT,
    email TEXT,
    alternative_contacts  MAP<TEXT, TEXT>,
    do_not_contact BOOLEAN,
    last_contacted DATE,
    states_lived SET <TEXT>,
    logins LIST <TIME>,
    ascii_data ASCII,
    big_int_data BIGINT,
    float_data FLOAT,
    double_data DOUBLE,
    timestamp TIMESTAMP,
    uuid UUID,
    duration DURATION
);

INSERT INTO users (user_id, name, age, email, alternative_contacts, do_not_contact, last_contacted, states_lived, logins, ascii_data, big_int_data, float_data, double_data, timestamp, uuid, duration) VALUES (1, 'John', 41, 'customer-1@example.com', { 'phone': '+1 (531) 988-5905', 'work_email': 'customer-1@example.com' }, true, null, {'VA', 'NC', 'TN'}, ['12:34:26'], '!"#$%&\()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~', 1844674407370955161, 1.1234568, 1.1234567890123446, '2011-02-03T04:05+0000', 7bac016c-3eec-4d76-ae39-605cb8ce2693, 12h30m) IF NOT EXISTS;
INSERT INTO users (user_id, name, age, email, alternative_contacts, do_not_contact, last_contacted, states_lived, logins) VALUES (2, 'Jane', 38, 'jane@example.com', {'phone': '+1 (393) 214-4128', 'work_email': 'jane@example.com' }, true, null, {'FL', 'MA', 'CA'}, ['11:23:15']) IF NOT EXISTS;
INSERT INTO users (user_id, name, age, email, alternative_contacts, do_not_contact, last_contacted, states_lived, logins) VALUES (3, 'Marguerite', 27, 'customer-2@example.com', { 'phone': '(472) 162-6435',  'work_email': 'customer-2-work@example.com' }, true, null, {'CA'}, ['08:12:54.123456789']) IF NOT EXISTS;
INSERT INTO users (user_id, name, age, email, alternative_contacts, do_not_contact, last_contacted, states_lived, logins) VALUES (4, 'Lafayette', 55, 'customer-3@example.com', { 'phone': '+1 (074) 534-0949',  'work_email': 'customer-3-work@example.com' }, false, '2011-02-03', {'NY', 'TX'}, ['08:12:54.123']) IF NOT EXISTS;
INSERT INTO users (user_id, name, age, email, alternative_contacts, do_not_contact, last_contacted, states_lived, logins) VALUES (5, 'Manuel', 23, 'customer-4@example.com', { 'phone': '+1 (831) 870-12348',  'work_email': 'customer-4@example.com' }, false, '2024-03-05', {'MO', 'KS'}, ['08:12:54.123456', '08:12:54.123456']) IF NOT EXISTS;
INSERT INTO users (user_id, name, age, email, alternative_contacts, do_not_contact, last_contacted, states_lived, logins) VALUES (6, NULL, 23, 'customer-6@example.com', { 'phone': '+1 (831) 870-12349',  'work_email': 'customer-6@example.com' }, false, '2024-04-05', {'MO', 'NY'}, ['08:12:54.123456', '08:12:54.123456']) IF NOT EXISTS;
INSERT INTO users (user_id, name, age, email, alternative_contacts, do_not_contact, last_contacted, states_lived, logins) VALUES (7, NULL, 26, 'customer-7@example.com', { 'phone': '+1 (831) 870-12359',  'work_email': 'customer-7@example.com' }, false, '2023-02-05', {'MO', 'TX'}, ['08:12:54.123456', '08:12:54.123456']) IF NOT EXISTS;
INSERT INTO users (user_id, name, age, email, alternative_contacts, do_not_contact, last_contacted, states_lived, logins) VALUES (8, 'Jasmine', 34, 'customer-8@example.com', { 'phone': '+1 (831) 214-12359',  'work_email': 'customer-8@example.com' }, false, '2024-01-23', {'CA', 'NY'}, ['08:12:54.123456', '08:12:54.123456']) IF NOT EXISTS;


CREATE TABLE if not exists user_activity (
    user_id INT,
    timestamp TIMESTAMP,
    user_agent TEXT,
    activity_type TEXT,
    PRIMARY KEY (user_id, timestamp)
);

INSERT INTO user_activity (user_id, timestamp, user_agent, activity_type) VALUES (1, '2024-07-09T04:05+0000', 'Safari', 'login') IF NOT EXISTS;
INSERT INTO user_activity (user_id, timestamp, user_agent, activity_type) VALUES (3, '2024-07-09T04:12+0000', 'Chrome', 'login') IF NOT EXISTS;
INSERT INTO user_activity (user_id, timestamp, user_agent, activity_type) VALUES (1, '2024-07-09T04:19+0000', 'Safari', 'logout') IF NOT EXISTS;
INSERT INTO user_activity (user_id, timestamp, user_agent, activity_type) VALUES (5, '2024-07-12T16:53+0000', 'Firefox', 'login') IF NOT EXISTS;
INSERT INTO user_activity (user_id, timestamp, user_agent, activity_type) VALUES (1, '2024-07-13T17:02+0000', 'Safari iOS', 'login') IF NOT EXISTS;


CREATE TABLE if not exists payment_methods (
    payment_method_id INT PRIMARY KEY,
    user_id INT,
    card_number TEXT,
    expiration_date DATE
);

INSERT INTO payment_methods (payment_method_id, user_id, card_number, expiration_date) VALUES (1, 1, '123456', '2024-09-05') IF NOT EXISTS;
INSERT INTO payment_methods (payment_method_id, user_id, card_number, expiration_date) VALUES (2, 2, '234567', '2028-02-01') IF NOT EXISTS;
INSERT INTO payment_methods (payment_method_id, user_id, card_number, expiration_date) VALUES (3, 1, '345678', '2027-10-31') IF NOT EXISTS;

CREATE TABLE if not exists orders (
    order_id INT PRIMARY KEY,
    payment_method_id INT,
    order_amount INT,
    order_date DATE,
    order_description TEXT
);

INSERT INTO orders (order_id, payment_method_id, order_amount, order_date, order_description) VALUES (1, 1, 123, '2024-08-05', 'office supplies') IF NOT EXISTS;
INSERT INTO orders (order_id, payment_method_id, order_amount, order_date, order_description) VALUES (2, 2, 85, '2024-08-07', 'books') IF NOT EXISTS;
INSERT INTO orders (order_id, payment_method_id, order_amount, order_date, order_description) VALUES (3, 3, 1350, '2024-08-12', 'new computer') IF NOT EXISTS;


CREATE KEYSPACE IF NOT EXISTS vendors_keyspace WITH REPLICATION = {'class': 'SimpleStrategy', 'replication_factor': 3};
USE vendors_keyspace;

CREATE TABLE if not exists vendors (
    vendor_id INT PRIMARY KEY,
    vendor_name TEXT,
    vendor_address TEXT,
    primary_contact_name TEXT,
    primary_contact_email TEXT,
    supplier_type TEXT
);

INSERT INTO vendors (vendor_id, vendor_name, vendor_address, primary_contact_name, primary_contact_email, supplier_type) VALUES (1, 'A+ Tile Supplies', '1810 Test Town, TX', 'Elliot Trace', 'employee-1@example.com', 'building supplies') IF NOT EXISTS;
INSERT INTO vendors (vendor_id, vendor_name, vendor_address, primary_contact_name, primary_contact_email, supplier_type) VALUES (2, 'Carpeting and More', '3421 Test City, TX', 'Chris Osbourne', 'employee-2@example.com', 'building supplies') IF NOT EXISTS;
INSERT INTO vendors (vendor_id, vendor_name, vendor_address, primary_contact_name, primary_contact_email, supplier_type) VALUES (3, 'Sunshine Bakery', '2394 Gottlieb Station, Romeoton, MS', 'Fatima Sultani', 'employee-3@example.com', 'coffee and tea') IF NOT EXISTS;
INSERT INTO vendors (vendor_id, vendor_name, vendor_address, primary_contact_name, primary_contact_email, supplier_type) VALUES (4, 'Sweetbrew', '609 Shanahan Points, Guillermotown, NC', 'Xavier Gutierrez', 'employee-4@example.com', 'coffee and tea') IF NOT EXISTS;
INSERT INTO vendors (vendor_id, vendor_name, vendor_address, primary_contact_name, primary_contact_email, supplier_type) VALUES (5, 'Artevista', '595 Blick Drive, Demetricebury, MO', 'Lana Anderson', 'employee-5@example.com', 'art supplies') IF NOT EXISTS;
INSERT INTO vendors (vendor_id, vendor_name, vendor_address, primary_contact_name, primary_contact_email, supplier_type) VALUES (6, 'CanvasCrafter', '1410 Parkway Street, San Diego, CA', 'Madelyn Houston', 'employee-6@example.com', 'art supplies') IF NOT EXISTS;
