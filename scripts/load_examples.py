"""
This script is used to seed the application database with example
data for DSR processing.

This script is only designed to be run from the Nox session 'nox -s test_env'.
"""

from setup import constants, get_secret
from setup.authentication import get_auth_header
from setup.dsr_policy import create_dsr_policy, create_rule
from setup.email import create_email_integration
from setup.healthcheck import check_health
from setup.mailchimp_connector import create_mailchimp_connector
from setup.mongodb_connector import create_mongodb_connector
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
if get_secret("AWS_SECRETS")["access_key_id"]:
    print("AWS secrets provided, attempting to configure S3 storage...")
    create_s3_storage(auth_header=auth_header)

# Edit the default DSR policies to use for testing privacy requests
# NOTE: We use the default policies to test the default privacy center
# TODO: change this to edit the default policies instead, so the default privacy center can be used
create_dsr_policy(auth_header=auth_header, key=constants.DEFAULT_ACCESS_POLICY)
create_dsr_policy(auth_header=auth_header, key=constants.DEFAULT_ERASURE_POLICY)
create_rule(
    auth_header=auth_header,
    policy_key=constants.DEFAULT_ACCESS_POLICY,
    rule_key=constants.DEFAULT_ACCESS_POLICY_RULE,
    action_type="access",
)
create_rule(
    auth_header=auth_header,
    policy_key=constants.DEFAULT_ERASURE_POLICY,
    rule_key=constants.DEFAULT_ERASURE_POLICY_RULE,
    action_type="erasure",
)

# Configure the email integration to use for identity verification and notifications
if get_secret("MAILGUN_SECRETS")["api_key"]:
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
if get_secret("MAILCHIMP_SECRETS")["api_key"]:
    print("Mailchimp secrets provided, attempting to configure Mailchimp connector...")
    create_mailchimp_connector(
        auth_header=auth_header,
    )

# Configure a connector to Stripe
if get_secret("STRIPE_SECRETS")["api_key"]:
    print("Stripe secrets provided, attempting to configure Mailchimp connector...")
    create_stripe_connector(
        auth_header=auth_header,
    )

print("Examples loaded successfully!")
