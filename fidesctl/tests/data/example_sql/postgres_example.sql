DROP TABLE IF EXISTS public.report;
DROP TABLE IF EXISTS public.service_request;
DROP TABLE IF EXISTS public.login;
DROP TABLE IF EXISTS public.visit;
DROP TABLE IF EXISTS public.order_item;
DROP TABLE IF EXISTS public.orders;
DROP TABLE IF EXISTS public.payment_card;
DROP TABLE IF EXISTS public.employee;
DROP TABLE IF EXISTS public.customer;
DROP TABLE IF EXISTS public.address;
DROP TABLE IF EXISTS public.product;
DROP TABLE IF EXISTS public.composite_pk_test;
DROP TABLE IF EXISTS public.type_link_test;


CREATE TABLE public.product (
    id INT PRIMARY KEY,
    name CHARACTER VARYING(100),
    price MONEY
);

CREATE TABLE public.address (
    id BIGINT PRIMARY KEY,
    house INT,
    street CHARACTER VARYING(100),
    city CHARACTER VARYING(100),
    state CHARACTER VARYING(100),
    zip CHARACTER VARYING(100)
);

CREATE TABLE public.customer (
    id INT PRIMARY KEY,
    email CHARACTER VARYING(100),
    name  CHARACTER VARYING(100),
    created TIMESTAMP,
    address_id BIGINT
);

CREATE TABLE public.employee (
    id INT PRIMARY KEY,
    email CHARACTER VARYING(100),
    name CHARACTER VARYING(100),
    address_id BIGINT
);

CREATE TABLE public.payment_card (
    id CHARACTER VARYING(100) PRIMARY KEY,
    name CHARACTER VARYING(100),
    ccn BIGINT,
    code SMALLINT,
    preferred BOOLEAN,
    customer_id INT,
    billing_address_id BIGINT
);

CREATE TABLE public.orders (
    id CHARACTER VARYING(100) PRIMARY KEY,
    customer_id INT,
    shipping_address_id BIGINT,
    payment_card_id CHARACTER VARYING(100)
);

CREATE TABLE public.order_item (
    order_id CHARACTER VARYING(100),
    item_no SMALLINT,
    product_id INT,
    quantity SMALLINT,
    CONSTRAINT order_item_pk PRIMARY KEY (order_id, item_no)
);

CREATE TABLE public.visit (
    email CHARACTER VARYING(100),
    last_visit TIMESTAMP,
    CONSTRAINT visit_pk PRIMARY KEY (email, last_visit)
);

CREATE TABLE public.login (
    id INT PRIMARY KEY,
    customer_id INT,
    time TIMESTAMP
);

CREATE TABLE public.service_request (
    id CHARACTER VARYING(100) PRIMARY KEY,
    email CHARACTER VARYING(100),
    alt_email CHARACTER VARYING(100),
    opened DATE,
    closed DATE,
    employee_id INT
);

CREATE TABLE public.report (
    id INT PRIMARY KEY,
    email CHARACTER VARYING(100),
    name CHARACTER VARYING(100),
    year INT,
    month INT,
    total_visits INT
);

CREATE TABLE public.composite_pk_test (
    id_a INT NOT NULL,
    id_b INT NOT NULL,
    description VARCHAR(100),
    customer_id INT,
    PRIMARY KEY(id_a, id_b)
);

INSERT INTO public.composite_pk_test VALUES
    (1,10,'linked to customer 1',1),
    (1,11,'linked to customer 2',2),
    (2,10,'linked to customer 3',3);

CREATE TABLE public.type_link_test (
    id CHARACTER VARYING(100) PRIMARY KEY,
    name CHARACTER VARYING(100)
);

-- Populate tables with some public data
INSERT INTO public.product VALUES
(1, 'Example Product 1', '$10.00'),
(2, 'Example Product 2', '$20.00'),
(3, 'Example Product 3', '$50.00');

INSERT INTO public.address VALUES
(1, '123', 'Example Street', 'Exampletown', 'NY', '12345'),
(2, '4', 'Example Lane', 'Exampletown', 'NY', '12321'),
(3, '555', 'Example Ave', 'Example City', 'NY', '12000'),
(4, '1111', 'Example Place', 'Example Mountain', 'TX', '54321');


INSERT INTO public.customer VALUES
(1, 'customer-1@example.com', 'John Customer', '2020-04-01 11:47:42', 1),
(2, 'customer-2@example.com', 'Jill Customer', '2020-04-01 11:47:42', 2),
(3, 'jane@example.com', 'Jane Customer', '2020-04-01 11:47:42', 4);


INSERT INTO public.employee VALUES
(1, 'employee-1@example.com', 'Jack Employee', 3),
(2, 'employee-2@example.com', 'Jane Employee', 3);

INSERT INTO public.payment_card VALUES
('pay_aaa-aaa', 'Example Card 1', 123456789, 321, true, 1, 1),
('pay_bbb-bbb', 'Example Card 2', 987654321, 123, false, 2, 1),
('pay_ccc-ccc', 'Example Card 3', 373719391, 222, false, 3, 4);


INSERT INTO public.orders VALUES
('ord_aaa-aaa', 1, 2, 'pay_aaa-aaa'),
('ord_bbb-bbb', 2, 1, 'pay_bbb-bbb'),
('ord_ccc-ccc', 1, 1, 'pay_aaa-aaa'),
('ord_ddd-ddd', 1, 1, 'pay_bbb-bbb'),
('ord_ddd-eee', 3, 4, 'pay-ccc-ccc');


INSERT INTO public.order_item VALUES
('ord_aaa-aaa', 1, 1, 1),
('ord_bbb-bbb', 1, 1, 1),
('ord_ccc-ccc', 1, 1, 1),
('ord_ccc-ccc', 2, 2, 1),
('ord_ddd-ddd', 1, 1, 1),
('ord_eee-eee', 3, 4, 3);


INSERT INTO public.visit VALUES
('customer-1@example.com', '2021-01-06 01:00:00'),
('customer-2@example.com', '2021-01-06 01:00:00');

INSERT INTO public.login VALUES
(1, 1, '2021-01-01 01:00:00'),
(2, 1, '2021-01-02 01:00:00'),
(3, 1, '2021-01-03 01:00:00'),
(4, 1, '2021-01-04 01:00:00'),
(5, 1, '2021-01-05 01:00:00'),
(6, 1, '2021-01-06 01:00:00'),
(7, 2, '2021-01-06 01:00:00'),
(8, 3, '2021-01-06 01:00:00');


INSERT INTO public.service_request VALUES
('ser_aaa-aaa', 'customer-1@example.com', 'customer-1-alt@example.com', '2021-01-01', '2021-01-03', 1),
('ser_bbb-bbb', 'customer-2@example.com', null, '2021-01-04', null, 1),
('ser_ccc-ccc', 'customer-3@example.com', null, '2021-01-05', '2020-01-07', 1),
('ser_ddd-ddd', 'customer-3@example.com', null, '2021-05-05', '2020-05-08', 2);

INSERT INTO public.report VALUES
(1, 'admin-account@example.com', 'Monthly Report', 2021, 8, 100),
(2, 'admin-account@example.com', 'Monthly Report', 2021, 9, 100),
(3, 'admin-account@example.com', 'Monthly Report', 2021, 10, 100),
(4, 'admin-account@example.com', 'Monthly Report', 2021, 11, 100);

INSERT INTO public.type_link_test VALUES
('1', 'name1'),
('2', 'name2');
