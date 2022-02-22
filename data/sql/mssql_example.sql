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

CREATE TABLE dbo.type_link_test ( id CHARACTER VARYING(100) PRIMARY KEY, name CHARACTER VARYING(100));