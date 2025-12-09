from enum import Enum


from enum import StrEnum

class GoogleCloudSQLIPType(StrEnum):
    """Enum for Google Cloud SQL IP types"""

    public = "public"
    private = "private"
    private_service_connect = "psc"
