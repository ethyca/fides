CREATE USER  IF NOT EXISTS 'mysql_user'@'mysql_example' IDENTIFIED BY 'mysql_pw';
GRANT ALL PRIVILEGES ON *.* TO 'mysql_user'@'mysql_example' ;
GRANT ALL PRIVILEGES ON *.* TO 'mysql_user'@'%' ;
FLUSH PRIVILEGES;
CREATE DATABASE IF NOT EXISTS mysql_example;
USE mysql_example;

DROP TABLE IF EXISTS login;
DROP TABLE IF EXISTS visit;

CREATE TABLE visit (
    email CHARACTER VARYING(100),
    last_visit TIMESTAMP
);

CREATE TABLE login (
    id INT PRIMARY KEY,
    customer_id INT,
    time TIMESTAMP
);


INSERT INTO visit VALUES
('customer-1@example.com', '2021-01-06 01:00:00'),
('customer-2@example.com', '2021-01-06 01:00:00');

INSERT INTO login VALUES
(1, 1, '2021-01-01 01:00:00'),
(2, 1, '2021-01-02 01:00:00'),
(3, 1, '2021-01-03 01:00:00'),
(4, 1, '2021-01-04 01:00:00'),
(5, 1, '2021-01-05 01:00:00'),
(6, 1, '2021-01-06 01:00:00'),
(7, 2, '2021-01-06 01:00:00');
