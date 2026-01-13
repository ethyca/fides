from enum import Enum, StrEnum


class GoogleCloudSQLIPType(StrEnum):
    """Enum for Google Cloud SQL IP types"""

    public = "public"
    private = "private"
    private_service_connect = "psc"
