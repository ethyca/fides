CREATE KEYSPACE IF NOT EXISTS app_keyspace WITH REPLICATION = {'class': 'SimpleStrategy', 'replication_factor': 3};
USE app_keyspace;

CREATE TABLE if not exists users (
    user_id INT PRIMARY KEY,
    name TEXT,
    age INT,
    email TEXT
);

INSERT INTO users (user_id, name, age, email) VALUES (1, 'John', 41, 'customer-1@example.com') IF NOT EXISTS;
INSERT INTO users (user_id, name, age, email) VALUES (2, 'Jane', 38, 'jane@example.com') IF NOT EXISTS;
INSERT INTO users (user_id, name, age, email) VALUES (3, 'Marguerite', 27, 'customer-2@example.com') IF NOT EXISTS;
INSERT INTO users (user_id, name, age, email) VALUES (4, 'Lafayette', 55, 'customer-3@example.com') IF NOT EXISTS;
INSERT INTO users (user_id, name, age, email) VALUES (5, 'Manuel', 23, 'customer-4@example.com') IF NOT EXISTS;


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
