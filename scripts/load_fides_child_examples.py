"""
This script is used to seed the application database with example
Fides connector configurations to integration test Fides parent-child interactions.

This script is only designed to be run along with the `child` Nox flag.
"""

from setup import constants
from setup.authentication import get_auth_header
from setup.fides_connector import create_fides_connector
from setup.healthcheck import check_health
from setup.user import create_user

print("Generating example data for local Fides - child test environment...")

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


# Configure a connector to the example Postgres database
create_fides_connector(
    auth_header=auth_header,
)


print("Examples loaded successfully!")
