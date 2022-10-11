from setup.authentication import get_auth_header
import setup.constants as constants
from setup.email import create_email_integration
from setup.healthcheck import check_health
from setup.mailchimp_connector import create_mailchimp_connector
from setup.postgres_connector import create_postgres_connector
from setup.user import create_user


print("Running an example Fides configuration script...")

try:
    check_health()
except RuntimeError:
    print(
        f"Connection error. Please ensure Fides is healthy and running at {constants.FIDESOPS_URL}."
    )

auth_header = get_auth_header()
create_user(
    auth_header=auth_header,
    username="an_example_user",
    password="Atestpassword1!",
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

print("Example end.")
