-- Each query needs to be on a single line for this implementation
USE master;
DROP DATABASE sqlserver_example;
CREATE DATABASE sqlserver_example;
USE sqlserver_example;

DROP TABLE IF EXISTS visit;
DROP TABLE IF EXISTS login;

CREATE TABLE visit ( email CHARACTER VARYING(100), last_visit SMALLDATETIME);
CREATE TABLE login ( id INT, customer_id INT, time SMALLDATETIME);


INSERT INTO visit VALUES ('customer-1@example.com', '2021-01-06 01:00:00'), ('customer-2@example.com', '2021-01-06 01:00:00');
INSERT INTO login VALUES (1, 1, '2021-01-01 01:00:00'), (2, 1, '2021-01-02 01:00:00'), (3, 1, '2021-01-03 01:00:00');
