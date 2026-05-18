-- Each query needs to be on a single line for this implementation
DROP TABLE IF EXISTS login;
DROP TABLE IF EXISTS visit;

CREATE TABLE visit ( email CHARACTER VARYING(100), last_visit TIMESTAMP);
CREATE TABLE login (id INT PRIMARY KEY, customer_id INT, time TIMESTAMP);

INSERT INTO visit VALUES ('customer-1@example.com', '2021-01-06 01:00:00'), ('customer-2@example.com', '2021-01-06 01:00:00');
INSERT INTO login VALUES (1, 1, '2021-01-01 01:00:00'), (2, 1, '2021-01-02 01:00:00'), (3, 1, '2021-01-03 01:00:00');
