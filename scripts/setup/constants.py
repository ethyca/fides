from fides.api.ops.api.v1 import urn_registry as urls

FIDES_USERNAME = "fidestest"
FIDES_PASSWORD = "Apassword1!"

FIDES_URL = "http://fides:8080"
BASE_URL = FIDES_URL + urls.V1_URL_PREFIX

ACCESS_POLICY_KEY = "access"
ERASURE_POLICY_KEY = "erasure"

STORAGE_KEY = "s3_storage"
ACCESS_RULE_KEY = "access_rule_key"
ERASURE_RULE_KEY = "erasure_rule_key"

MONGO_SERVER = "mongodb-test"
MONGO_USER = "mongo_user"
MONGO_PASSWORD = "mongo_pass"
MONGO_PORT = 27017
MONGO_DB = "mongo_test"

# I have no idea why this hostname doesn't work...
# POSTGRES_SERVER = "postgres-test"
POSTGRES_SERVER = "host.docker.internal"
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "postgres"
POSTGRES_PORT = 6432
POSTGRES_DB_NAME = "postgres_example"

ROOT_CLIENT_ID = "fidesadmin"
ROOT_CLIENT_SECRET = "fidesadminsecret"
