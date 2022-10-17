"""
This script is used to seed the application database with example
data for DSR processing.

This script is only designed to be run from the Nox session 'nox -s test_env'.
"""

from setup import constants, get_secret
from setup.authentication import get_auth_header
from setup.email import create_email_integration
from setup.healthcheck import check_health
from setup.mailchimp_connector import create_mailchimp_connector
from setup.mongodb_connector import create_mongodb_connector
from setup.dsr_policy import create_dsr_policy, create_rule, create_rule_target
from setup.postgres_connector import create_postgres_connector
from setup.privacy_request import create_privacy_request
from setup.s3_storage import create_s3_storage
from setup.stripe_connector import create_stripe_connector
from setup.user import create_user

print("Generating example data for local Fides test environment...")

try:
    check_health()
except RuntimeError:
    print(
        f"Connection error. Please ensure Fides is healthy and running at {constants.FIDES_URL}."
    )
    raise

# Start by creating an OAuth client and user for testing
auth_header = get_auth_header()
create_user(
    auth_header=auth_header,
)

# Create an S3 storage config to store DSR results
storage_key = constants.LOCAL_STORAGE_KEY
if (get_secret("AWS_SECRETS")["access_key_id"]):
    print("AWS secrets provided, attempting to configure S3 storage...")
    create_s3_storage(auth_header=auth_header, key=constants.S3_STORAGE_KEY)
    storage_key = constants.S3_STORAGE_KEY

# Create new DSR policies to use for testing privacy requests
# TODO: change this to edit the default policies instead, so the default privacy center can be used
create_dsr_policy(auth_header=auth_header, key=constants.ACCESS_POLICY_KEY)
create_dsr_policy(auth_header=auth_header, key=constants.ERASURE_POLICY_KEY)
create_rule(auth_header=auth_header, storage_key=storage_key)
create_rule(
    auth_header=auth_header,
    policy_key=constants.ERASURE_POLICY_KEY,
    rule_key=constants.ERASURE_RULE_KEY,
    storage_key=storage_key,
    action_type="erasure",
)
create_rule_target(auth_header=auth_header, target_key="access_user_data")
create_rule_target(
    auth_header=auth_header,
    policy_key=constants.ERASURE_POLICY_KEY,
    rule_key=constants.ERASURE_RULE_KEY,
    target_key="erasure_user_data",
)

# Configure the email integration to use for identity verification and notifications
if (get_secret("MAILGUN_SECRETS")["api_key"]):
    print("Mailgun secrets provided, attempting to configure email...")
    create_email_integration(
        auth_header=auth_header,
    )

# Configure a connector to the example Postgres database
create_postgres_connector(
    auth_header=auth_header,
)

# Configure a connector to the example Mongo database
create_mongodb_connector(auth_header=auth_header)

# Configure a connector to Mailchimp
if (get_secret("MAILCHIMP_SECRETS")["api_key"]):
    print("Mailchimp secrets provided, attempting to configure Mailchimp connector...")
    create_mailchimp_connector(
        auth_header=auth_header,
    )

# Configure a connector to Stripe
if (get_secret("STRIPE_SECRETS")["api_key"]):
    print("Stripe secrets provided, attempting to configure Mailchimp connector...")
    create_stripe_connector(
        auth_header=auth_header,
    )

# Run an example privacy request
create_privacy_request(user_email="jane@example.com")

print("Examples loaded successfully!")
