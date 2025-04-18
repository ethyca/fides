from enum import Enum


class GoogleCloudSQLIPType(str, Enum):
    """Enum for Google Cloud SQL IP types"""

    public = "public"
    private = "private"
    private_service_connect = "psc"
