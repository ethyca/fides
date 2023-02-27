CREATE TABLE public.yotpo_customer (
    email CHARACTER VARYING(100) PRIMARY KEY,
    external_id CHARACTER VARYING(100)
);

INSERT INTO public.yotpo_customer VALUES
('test@example.com', 'ak123798684365sdfkj')