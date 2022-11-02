CREATE TABLE public.twilio_users (
    email CHARACTER VARYING(100) PRIMARY KEY,
    twilio_user_id CHARACTER VARYING(100)
);

INSERT INTO public.twilio_users VALUES
('test@example.com', 'US6f651b2beabf49c88ff68b32b98958f1')