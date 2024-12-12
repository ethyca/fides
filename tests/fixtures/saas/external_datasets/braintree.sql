CREATE TABLE public.braintree_customers (
    email CHARACTER VARYING(100) PRIMARY KEY,
    braintree_customer_id CHARACTER VARYING(100)
);

INSERT INTO public.braintree_customers VALUES
('JaneDoe@ethycatest.com', 'Y3VzdG9tZXJfMjY4ODQxMzA4')