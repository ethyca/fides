CREATE TABLE public.fullstory_users (
    email CHARACTER VARYING(100) PRIMARY KEY,
    fullstory_user_id CHARACTER VARYING(100)
);

INSERT INTO public.fullstory_users VALUES
('test@test.com', '1234')
