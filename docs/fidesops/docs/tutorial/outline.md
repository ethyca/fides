# Outline


Let's sketch out a Python file in `fidesdemo/flaskr/fidesops.py` where we'll add functions that use Python's [requests](https://docs.python-requests.org/en/latest/)
library to call the `Fidesops` API to build our required configuration.

As we go through each step in the tutorial, you'll add a couple of helper methods that are wrappers to API calls, and
then add calls to these functions at the bottom to be executed when we run this script.

```python
import logging
import requests
import yaml
from datetime import datetime

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# For tutorial simplicity. In prod, this should go in an ENV file or similar.
FIDESOPS_URL = "http://localhost:8000"
ROOT_CLIENT_ID = "fidesopsadmin"
ROOT_CLIENT_SECRET = "fidesopsadminsecret"
POSTGRES_SERVER = "db"
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "postgres"
POSTGRES_PORT = "5432"

# We'll define some functions here:


if __name__ == "__main__":
    """We'll add calls to our functions here"""

    # TODO Create a new OAuth client to use for our app

    # TODO Connect to our PostgreSQL database

    # TODO Upload the dataset YAML for our PostgreSQL schema

    # TODO Configure a Storage Config to upload the results

    # TODO Create a Policy that returns all user data

    # TODO Execute a Privacy Request for user@example.com

```