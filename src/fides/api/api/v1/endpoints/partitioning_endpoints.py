from typing import List

from fastapi import HTTPException, Security, status
from loguru import logger
from sqlalchemy_bigquery import BigQueryDialect

from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas.partitioning.time_based_partitioning import (
    TimeBasedPartitioning,
    combine_partitions,
)
from fides.api.util.api_router import APIRouter
from fides.common.api.scope_registry import CTL_DATASET_READ
from fides.common.api.v1.urn_registry import V1_URL_PREFIX

router = APIRouter(tags=["Partitions"], prefix=V1_URL_PREFIX)


@router.post(
    "/dataset/partitions/verify",
    dependencies=[Security(verify_oauth_client, scopes=[CTL_DATASET_READ])],
    response_model=List[str],
    status_code=status.HTTP_200_OK,
    name="Verify dataset partitioning schemas",
    summary="Verify dataset partitioning schemas",
    description="Validate the provided partitioning specs and return the rendered SQL WHERE clauses in the BigQuery dialect.",
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/TimeBasedPartitioning"},
                    },
                    "examples": {
                        "recent_data_weekly": {
                            "summary": "Recent data partitioned weekly",
                            "description": "Partition the last 30 days of data into weekly chunks",
                            "value": [
                                {
                                    "field": "created_at",
                                    "start": "NOW() - 30 DAYS",
                                    "end": "NOW()",
                                    "interval": "7 DAYS",
                                }
                            ],
                        },
                        "historical_data_monthly": {
                            "summary": "Historical data partitioned monthly",
                            "description": "Partition a specific year of data into monthly chunks",
                            "value": [
                                {
                                    "field": "order_date",
                                    "start": "2024-01-01",
                                    "end": "2024-12-31",
                                    "interval": "1 MONTH",
                                }
                            ],
                        },
                        "multiple_partitions": {
                            "summary": "Multiple time ranges",
                            "description": "Combine historical monthly data with recent daily data",
                            "value": [
                                {
                                    "field": "event_timestamp",
                                    "start": "2023-01-01",
                                    "end": "2023-12-31",
                                    "interval": "1 MONTH",
                                },
                                {
                                    "field": "event_timestamp",
                                    "start": "NOW() - 14 DAYS",
                                    "end": "NOW()",
                                    "interval": "1 DAY",
                                },
                            ],
                        },
                        "open_ended_partition": {
                            "summary": "Open-ended partition",
                            "description": "Partition all data from a specific date onwards",
                            "value": [
                                {"field": "user_created_at", "start": "2024-01-01"}
                            ],
                        },
                    },
                }
            }
        }
    },
)
async def verify_dataset_partitioning(
    partitions: List[TimeBasedPartitioning],
) -> List[str]:
    """Validate the provided partitioning specs and return the rendered SQL WHERE clauses in the BigQuery dialect."""
    try:
        expressions = combine_partitions(partitions)
        dialect = BigQueryDialect()
        compiled_clauses: List[str] = [
            str(expr.compile(dialect=dialect, compile_kwargs={"literal_binds": True}))
            for expr in expressions
        ]
        return compiled_clauses
    except Exception as exc:
        logger.error("Partitioning verification failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
