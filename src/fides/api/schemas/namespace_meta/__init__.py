# Import all subclasses so __init_subclass__ fires and registers each
# implementation in the NamespaceMeta._implementations registry.
from fides.api.schemas.namespace_meta.bigquery_namespace_meta import (
    BigQueryNamespaceMeta,  # noqa: F401
)
from fides.api.schemas.namespace_meta.postgres_namespace_meta import (
    PostgresNamespaceMeta,  # noqa: F401
)
from fides.api.schemas.namespace_meta.rds_postgres_namespace_meta import (
    RDSPostgresNamespaceMeta,  # noqa: F401
)
from fides.api.schemas.namespace_meta.snowflake_namespace_meta import (
    SnowflakeNamespaceMeta,  # noqa: F401
)
