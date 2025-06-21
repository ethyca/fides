from typing import List

from loguru import logger
from sqlalchemy_bigquery import BigQueryDialect

from fides.api.schemas.partitioning.time_based_partitioning import TimeBasedPartitioning


class BigQueryTimeBasedPartitioning(TimeBasedPartitioning):
    """Generates BigQuery-specific WHERE clauses for time-based partitioning."""

    def generate_where_clauses(self) -> List[str]:
        """Generate BigQuery-specific WHERE clauses."""
        conditions = self.generate_expressions()
        bigquery_dialect = BigQueryDialect()

        partition_clauses = []
        for condition in conditions:
            try:
                clause_str = str(
                    condition.compile(
                        dialect=bigquery_dialect,
                        compile_kwargs={"literal_binds": True},
                    )
                )
                partition_clauses.append(clause_str)
            except Exception as exc:
                logger.error("Could not generate where clause", exc_info=True)
                raise exc

        return partition_clauses
