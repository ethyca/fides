CREATE TABLE public.doordash_deliveries (
    email CHARACTER VARYING(100) PRIMARY KEY,
    delivery_id CHARACTER VARYING(100)
);

INSERT INTO public.doordash_deliveries VALUES
('test@example.com', 'D-12345')