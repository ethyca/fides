import logging
from typing import List

from fastapi import APIRouter, HTTPException
from starlette.status import HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST

from fidesops.api.v1.urn_registry import MASKING, MASKING_STRATEGY, V1_URL_PREFIX
from fidesops.common_exceptions import ValidationError
from fidesops.schemas.masking.masking_response import MaskingAPIResponse
from fidesops.schemas.masking.masking_strategy_description import (
    MaskingStrategyDescription,
)
from fidesops.schemas.policy import PolicyMaskingSpec
from fidesops.service.masking.strategy.masking_strategy_factory import (
    get_strategies,
    get_strategy,
    NoSuchStrategyException,
)

router = APIRouter(tags=["Masking"], prefix=V1_URL_PREFIX)

logger = logging.getLogger(__name__)


@router.put(MASKING, response_model=MaskingAPIResponse)
def mask_value(masking_strategy: PolicyMaskingSpec, value: str) -> MaskingAPIResponse:
    """Masks the value provided using the provided masking strategy"""
    try:
        strategy = get_strategy(
            masking_strategy.strategy, masking_strategy.configuration
        )
        logger.info(f"Starting masking with strategy {masking_strategy.strategy}")
        masked_value = strategy.mask(value)
        return MaskingAPIResponse(plain=value, masked_value=masked_value)
    except NoSuchStrategyException as e:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(MASKING_STRATEGY, response_model=List[MaskingStrategyDescription])
def list_masking_strategies() -> List[MaskingStrategyDescription]:
    """Lists available masking strategies with instructions on how to use them"""
    logger.info("Getting available masking strategies")
    return [strategy.get_description() for strategy in get_strategies()]
