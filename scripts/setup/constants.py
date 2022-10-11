from fides.api.ops.api.v1 import urn_registry as urls

FIDESOPS_URL = "http://localhost:8080"
BASE_URL = FIDESOPS_URL + urls.V1_URL_PREFIX

# These are external datastores so don't read them from the config
POSTGRES_SERVER = "host.docker.internal"
# POSTGRES_SERVER = "postgres_example"
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "postgres"
POSTGRES_PORT = 6432
POSTGRES_DB_NAME = "postgres_example"


ROOT_CLIENT_ID = "fidesopsadmin"
ROOT_CLIENT_SECRET = "fidesopsadminsecret"
