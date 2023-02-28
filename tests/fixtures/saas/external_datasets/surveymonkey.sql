CREATE TABLE public.surveymonkey_surveys (
    email CHARACTER VARYING(100) PRIMARY KEY,
    surveymonkey_survey_id CHARACTER VARYING(100)
);

INSERT INTO public.surveymonkey_surveys VALUES
('connectors+surveymonkey+sar@ethyca.com', '509267447')