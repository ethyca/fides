import os

AWS_SECRETS = {
    "access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
    "secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
}

MAILCHIMP_SECRETS = {
    "domain": os.getenv("MAILCHIMP_DOMAIN"),
    "username": os.getenv("MAILCHIMP_USERNAME"),
    "api_key": os.getenv("MAILCHIMP_API_KEY"),
}

MAILGUN_SECRETS = {
    "domain": os.getenv("MAILGUN_DOMAIN"),
    "api_key": os.getenv("MAILGUN_API_KEY"),
}

STRIPE_SECRETS = {
    "domain": os.getenv("STRIPE_DOMAIN"),
    "api_key": os.getenv("STRIPE_API_KEY"),
    "payment_types": os.getenv("STRIPE_PAYMENT_TYPES", "card"),
    "page_size": os.getenv("STRIPE_PAGE_SIZE", "100"),
}
