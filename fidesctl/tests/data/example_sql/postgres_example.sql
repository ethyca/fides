DROP TABLE IF EXISTS public.login;
DROP TABLE IF EXISTS public.visit;


CREATE TABLE public.visit (
    email CHARACTER VARYING(100),
    last_visit TIMESTAMP
);

CREATE TABLE public.login (
    id INT PRIMARY KEY,
    customer_id INT,
    time TIMESTAMP
);


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
