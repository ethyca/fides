print("Loading imports...")
from setup import constants
from setup.authentication import get_auth_header
from setup.email import create_email_integration
from setup.healthcheck import check_health
from setup.mailchimp_connector import create_mailchimp_connector
from setup.mongodb_connector import create_mongodb_connector
from setup.policy import create_policy
from setup.postgres_connector import create_postgres_connector
from setup.privacy_request import create_privacy_request
from setup.rule import create_rule
from setup.rule_target import create_rule_target
from setup.s3_storage import create_s3_storage
from setup.stripe_connector import create_stripe_connector
from setup.user import create_user

print("Running an example Fides configuration script...")

try:
    check_health()
except RuntimeError:
    print(
        f"Connection error. Please ensure Fides is healthy and running at {constants.FIDES_URL}."
    )
    raise

try:
    from setup import secrets
except ImportError:
    raise SystemExit(
        "ERROR! Secrets module not found, checks the docs at 'guides/utility_scripts' for help getting set up."
    )

auth_header = get_auth_header()
create_user(
    auth_header=auth_header,
    username="an_example_user",
    password="Atestpassword1!",
)
create_policy(auth_header=auth_header)
create_policy(auth_header=auth_header, key=constants.ERASURE_POLICY_KEY)
create_s3_storage(auth_header=auth_header)
create_rule(auth_header=auth_header)
create_rule(
    auth_header=auth_header,
    policy_key=constants.ERASURE_POLICY_KEY,
    rule_key=constants.ERASURE_RULE_KEY,
    storage_key=constants.STORAGE_KEY,
    action_type="erasure",
)
create_rule_target(auth_header=auth_header, target_key="access_user_data")
create_rule_target(
    auth_header=auth_header,
    policy_key=constants.ERASURE_POLICY_KEY,
    rule_key=constants.ERASURE_RULE_KEY,
    target_key="erasure_user_data",
)
create_email_integration(
    auth_header=auth_header,
)
create_postgres_connector(
    auth_header=auth_header,
)
create_mailchimp_connector(
    auth_header=auth_header,
)
create_stripe_connector(
    auth_header=auth_header,
)
create_mongodb_connector(auth_header=auth_header)
create_privacy_request(user_email="an_example_user")

print("Example end.")
