
CREATE USER  IF NOT EXISTS 'mysql_user'@'mysql_example' IDENTIFIED BY 'mysql_pw';
GRANT ALL PRIVILEGES ON *.* TO 'mysql_user'@'mysql_example' ;
GRANT ALL PRIVILEGES ON *.* TO 'mysql_user'@'%' ;
FLUSH PRIVILEGES;
CREATE DATABASE IF NOT EXISTS mysql_example;
USE mysql_example;

-- Example Mysql schema matching the dataset in public/data/dataset/mysql_example_dataset.yml
DROP TABLE IF EXISTS report;
DROP TABLE IF EXISTS service_request;
DROP TABLE IF EXISTS login;
DROP TABLE IF EXISTS visit;
DROP TABLE IF EXISTS order_item;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS payment_card;
DROP TABLE IF EXISTS employee;
DROP TABLE IF EXISTS customer;
DROP TABLE IF EXISTS address;
DROP TABLE IF EXISTS product;

CREATE TABLE product (
                                id INT PRIMARY KEY,
                                name CHARACTER VARYING(100),
                                price DECIMAL(10,2)
);

CREATE TABLE address (
                                id BIGINT PRIMARY KEY,
                                house INT,
                                street CHARACTER VARYING(100),
                                city CHARACTER VARYING(100),
                                state CHARACTER VARYING(100),
                                zip CHARACTER VARYING(100)
);

CREATE TABLE customer (
                                 id INT PRIMARY KEY,
                                 email CHARACTER VARYING(100),
                                 name  CHARACTER VARYING(100),
                                 created TIMESTAMP,
                                 address_id BIGINT
);

CREATE TABLE employee (
                                 id INT PRIMARY KEY,
                                 email CHARACTER VARYING(100),
                                 name CHARACTER VARYING(100),
                                 address_id BIGINT
);

CREATE TABLE payment_card (
                                     id CHARACTER VARYING(100) PRIMARY KEY,
                                     name CHARACTER VARYING(100),
                                     ccn BIGINT,
                                     code SMALLINT,
                                     preferred BOOLEAN,
                                     customer_id INT,
                                     billing_address_id BIGINT
);

CREATE TABLE orders (
                               id CHARACTER VARYING(100) PRIMARY KEY,
                               customer_id INT,
                               shipping_address_id BIGINT,
                               payment_card_id CHARACTER VARYING(100)
);

CREATE TABLE order_item (
                                   order_id CHARACTER VARYING(100),
                                   item_no SMALLINT,
                                   product_id INT,
                                   quantity SMALLINT
);

CREATE TABLE visit (
                              email CHARACTER VARYING(100),
                              last_visit TIMESTAMP
);

CREATE TABLE login (
                              id INT PRIMARY KEY,
                              customer_id INT,
                              time TIMESTAMP
);

CREATE TABLE service_request (
                                        id CHARACTER VARYING(100) PRIMARY KEY,
                                        email CHARACTER VARYING(100),
                                        alt_email CHARACTER VARYING(100),
                                        opened DATE,
                                        closed DATE,
                                        employee_id INT
);

CREATE TABLE report (
                               id INT PRIMARY KEY,
                               email CHARACTER VARYING(100),
                               name CHARACTER VARYING(100),
                               year INT,
                               month INT,
                               total_visits INT
);

CREATE TABLE `Lead` (
                              email CHARACTER VARYING(100),
                              updated_at TIMESTAMP
);
