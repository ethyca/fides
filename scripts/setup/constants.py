"""
Default constants to use when generating example data via load_examples.py
"""

from fides.api.ctl.database.seed import (
    DEFAULT_ACCESS_POLICY,
    DEFAULT_ACCESS_POLICY_RULE,
    DEFAULT_ERASURE_POLICY,
    DEFAULT_ERASURE_POLICY_RULE,
)
from fides.api.ops.api.v1 import urn_registry as urls

# Explicitly set these so they don't look like unused imports
DEFAULT_ACCESS_POLICY = DEFAULT_ACCESS_POLICY
DEFAULT_ACCESS_POLICY_RULE = DEFAULT_ACCESS_POLICY_RULE
DEFAULT_ERASURE_POLICY = DEFAULT_ERASURE_POLICY
DEFAULT_ERASURE_POLICY_RULE = DEFAULT_ERASURE_POLICY_RULE

FIDES_USERNAME = "root_user"
FIDES_PASSWORD = "Testpassword1!"

FIDES_URL = "http://fides:8080"
BASE_URL = FIDES_URL + urls.V1_URL_PREFIX

S3_STORAGE_KEY = "s3_storage"
S3_STORAGE_BUCKET = "fides-test-privacy-requests"

MONGO_SERVER = "mongodb-test"
MONGO_USER = "mongo_user"
MONGO_PASSWORD = "mongo_pass"
MONGO_PORT = 27017
MONGO_DB = "mongo_test"

POSTGRES_SERVER = "postgres-test"
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "postgres"
POSTGRES_PORT = 5432
POSTGRES_DB_NAME = "postgres_example"

ROOT_CLIENT_ID = "fidesadmin"
ROOT_CLIENT_SECRET = "fidesadminsecret"
