USE master;

DROP DATABASE IF EXISTS mssql_example;
CREATE DATABASE mssql_example;
USE mssql_example;

DROP TABLE IF EXISTS dbo.report;
DROP TABLE IF EXISTS dbo.service_request;
DROP TABLE IF EXISTS dbo.login;
DROP TABLE IF EXISTS dbo.visit;
DROP TABLE IF EXISTS dbo.order_item;
DROP TABLE IF EXISTS dbo.orders;
DROP TABLE IF EXISTS dbo.payment_card;
DROP TABLE IF EXISTS dbo.employee;
DROP TABLE IF EXISTS dbo.customer;
DROP TABLE IF EXISTS dbo.address;
DROP TABLE IF EXISTS dbo.product;
DROP TABLE IF EXISTS dbo.composite_pk_test;
DROP TABLE IF EXISTS dbo.type_link_test;


CREATE TABLE dbo.product ( id INT PRIMARY KEY, name CHARACTER VARYING(100), price MONEY);

CREATE TABLE dbo.address ( id BIGINT PRIMARY KEY, house INT, street CHARACTER VARYING(100), city CHARACTER VARYING(100), state CHARACTER VARYING(100), zip CHARACTER VARYING(100));

CREATE TABLE dbo.customer ( id INT PRIMARY KEY, email CHARACTER VARYING(100), name CHARACTER VARYING(100), created DATETIME, address_id BIGINT);

CREATE TABLE dbo.employee ( id INT PRIMARY KEY, email CHARACTER VARYING(100), name CHARACTER VARYING(100), address_id BIGINT);

CREATE TABLE dbo.payment_card ( id CHARACTER VARYING(100) PRIMARY KEY, name CHARACTER VARYING(100), ccn BIGINT, code SMALLINT, preferred BIT, customer_id INT, billing_address_id BIGINT);

CREATE TABLE dbo.orders ( id CHARACTER VARYING(100) PRIMARY KEY, customer_id INT, shipping_address_id BIGINT, payment_card_id CHARACTER VARYING(100));

CREATE TABLE dbo.order_item ( order_id CHARACTER VARYING(100), item_no SMALLINT, product_id INT, quantity SMALLINT, CONSTRAINT order_item_pk PRIMARY KEY (order_id, item_no));

CREATE TABLE dbo.visit ( email CHARACTER VARYING(100), last_visit DATETIME, CONSTRAINT visit_pk PRIMARY KEY (email, last_visit));

CREATE TABLE dbo.login ( id INT PRIMARY KEY, customer_id INT, time DATETIME);

CREATE TABLE dbo.service_request ( id CHARACTER VARYING(100) PRIMARY KEY, email CHARACTER VARYING(100), alt_email CHARACTER VARYING(100), opened DATE, closed DATE, employee_id INT);

CREATE TABLE dbo.report ( id INT PRIMARY KEY, email CHARACTER VARYING(100), name CHARACTER VARYING(100), year INT, month INT, total_visits INT);

CREATE TABLE dbo.composite_pk_test ( id_a INT NOT NULL, id_b INT NOT NULL, description VARCHAR(100), customer_id INT, PRIMARY KEY(id_a, id_b));

INSERT INTO dbo.composite_pk_test VALUES (1,10,'linked to customer 1',1), (1,11,'linked to customer 2',2), (2,10,'linked to customer 3',3);

CREATE TABLE dbo.type_link_test ( id CHARACTER VARYING(100) PRIMARY KEY, name CHARACTER VARYING(100));

-- Populate tables with some public data
INSERT INTO dbo.product VALUES (1, 'Example Product 1', '$10.00'), (2, 'Example Product 2', '$20.00'), (3, 'Example Product 3', '$50.00');

INSERT INTO dbo.address VALUES (1, '123', 'Example Street', 'Exampletown', 'NY', '12345'), (2, '4', 'Example Lane', 'Exampletown', 'NY', '12321'), (3, '555', 'Example Ave', 'Example City', 'NY', '12000'), (4, '1111', 'Example Place', 'Example Mountain', 'TX', '54321');


INSERT INTO dbo.customer VALUES (1, 'customer-1@example.com', 'John Customer', '2020-04-01 11:47:42', 1), (2, 'customer-2@example.com', 'Jill Customer', '2020-04-01 11:47:42', 2), (3, 'jane@example.com', 'Jane Customer', '2020-04-01 11:47:42', 4);


INSERT INTO dbo.employee VALUES (1, 'employee-1@example.com', 'Jack Employee', 3), (2, 'employee-2@example.com', 'Jane Employee', 3);

INSERT INTO dbo.payment_card VALUES ('pay_aaa-aaa', 'Example Card 1', 123456789, 321, 1, 1, 1), ('pay_bbb-bbb', 'Example Card 2', 987654321, 123, 0, 2, 1), ('pay_ccc-ccc', 'Example Card 3', 373719391, 222, 0, 3, 4);


INSERT INTO dbo.orders VALUES ('ord_aaa-aaa', 1, 2, 'pay_aaa-aaa'), ('ord_bbb-bbb', 2, 1, 'pay_bbb-bbb'), ('ord_ccc-ccc', 1, 1, 'pay_aaa-aaa'), ('ord_ddd-ddd', 1, 1, 'pay_bbb-bbb'), ('ord_ddd-eee', 3, 4, 'pay-ccc-ccc');


INSERT INTO dbo.order_item VALUES ('ord_aaa-aaa', 1, 1, 1), ('ord_bbb-bbb', 1, 1, 1), ('ord_ccc-ccc', 1, 1, 1), ('ord_ccc-ccc', 2, 2, 1), ('ord_ddd-ddd', 1, 1, 1), ('ord_eee-eee', 3, 4, 3);


INSERT INTO dbo.visit VALUES ('customer-1@example.com', '2021-01-06 01:00:00'), ('customer-2@example.com', '2021-01-06 01:00:00');

INSERT INTO dbo.login VALUES (1, 1, '2021-01-01 01:00:00'), (2, 1, '2021-01-02 01:00:00'), (3, 1, '2021-01-03 01:00:00'), (4, 1, '2021-01-04 01:00:00'), (5, 1, '2021-01-05 01:00:00'), (6, 1, '2021-01-06 01:00:00'), (7, 2, '2021-01-06 01:00:00'), (8, 3, '2021-01-06 01:00:00');


INSERT INTO dbo.service_request VALUES ('ser_aaa-aaa', 'customer-1@example.com', 'customer-1-alt@example.com', '2021-01-01', '2021-01-03', 1), ('ser_bbb-bbb', 'customer-2@example.com', null, '2021-01-04', null, 1), ('ser_ccc-ccc', 'customer-3@example.com', null, '2021-01-05', '2020-01-07', 1), ('ser_ddd-ddd', 'customer-3@example.com', null, '2021-05-05', '2020-05-08', 2);

INSERT INTO dbo.report VALUES (1, 'admin-account@example.com', 'Monthly Report', 2021, 8, 100), (2, 'admin-account@example.com', 'Monthly Report', 2021, 9, 100), (3, 'admin-account@example.com', 'Monthly Report', 2021, 10, 100), (4, 'admin-account@example.com', 'Monthly Report', 2021, 11, 100);

INSERT INTO dbo.type_link_test VALUES ('1', 'name1'), ('2', 'name2');