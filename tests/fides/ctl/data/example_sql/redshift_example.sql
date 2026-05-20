DROP TABLE IF EXISTS public.visit;
DROP TABLE IF EXISTS public.login;

CREATE TABLE public.visit ( email varchar(100), last_visit DATETIME);
CREATE TABLE public.login ( id INT, customer_id INT, time DATETIME);


INSERT INTO public.visit VALUES ('customer-1@example.com', '2021-01-06 01:00:00'), ('customer-2@example.com', '2021-01-06 01:00:00');
INSERT INTO public.login VALUES (1, 1, '2021-01-01 01:00:00'), (2, 1, '2021-01-02 01:00:00'), (3, 1, '2021-01-03 01:00:00');
