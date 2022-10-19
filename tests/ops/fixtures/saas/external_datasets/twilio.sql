CREATE TABLE public.twilio_users (
    email CHARACTER VARYING(100) PRIMARY KEY,
    user_id CHARACTER VARYING(100)
);

INSERT INTO public.twilio_users VALUES
('test@example.com', 'USa71692845d04414f84ace6687c39e507')