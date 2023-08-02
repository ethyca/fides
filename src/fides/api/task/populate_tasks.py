from typing import Dict, Tuple
from fides.api.graph.config import (
    ROOT_COLLECTION_ADDRESS,
    TERMINATOR_ADDRESS,
    CollectionAddress,
    Field,
    FieldAddress,
    FieldPath,
)
from loguru import logger


def create_tasks(dask_dict: Dict[CollectionAddress, Tuple]) -> None:
    """Parse the task dictionary and upload them to the database."""
    for key, value in dask_dict.items():
        logger.info(f"Key: {key}")
        logger.info(f"Value: {value}")
    pass
