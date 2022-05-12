import logging
from typing import Dict

from fidesops.models.privacy_request import PrivacyRequestStatus
from fidesops.schemas.drp_privacy_request import DrpIdentity
from fidesops.schemas.privacy_request import PrivacyRequestDRPStatus
from fidesops.schemas.redis_cache import PrivacyRequestIdentity

logger = logging.getLogger(__name__)


class DrpFidesopsMapper:
    """
    Map DRP objects/enums to Fidesops
    """

    @staticmethod
    def map_identity(drp_identity: DrpIdentity) -> PrivacyRequestIdentity:
        """
        Currently, both email and phone_number identity props map 1:1 to the corresponding
        Fidesops identity props in PrivacyRequestIdentity. This may not always be the case.
        This class also allows us to implement custom logic to handle "verified" id props.
        """
        fidesops_identity_kwargs: Dict[str, str] = {}
        DRP_TO_FIDESOPS_SUPPORTED_IDENTITY_PROPS_MAP: Dict[str, str] = {
            "email": "email",
            "phone_number": "phone_number",
        }
        for attr, val in drp_identity.__dict__.items():
            if attr not in DRP_TO_FIDESOPS_SUPPORTED_IDENTITY_PROPS_MAP.keys():
                logger.warning(
                    f"Identity attribute of {attr} is not supported by Fidesops at this time. Continuing to use other identity props, if provided."
                )
            else:
                fidesops_prop: str = DRP_TO_FIDESOPS_SUPPORTED_IDENTITY_PROPS_MAP[attr]
                fidesops_identity_kwargs[fidesops_prop] = val
        return PrivacyRequestIdentity(**fidesops_identity_kwargs)

    @staticmethod
    def map_status(
        status: PrivacyRequestStatus,
    ) -> PrivacyRequestDRPStatus:
        PRIVACY_REQUEST_STATUS_TO_DRP_MAPPING: Dict[
            PrivacyRequestStatus, PrivacyRequestDRPStatus
        ] = {
            PrivacyRequestStatus.pending: PrivacyRequestDRPStatus.open,
            PrivacyRequestStatus.approved: PrivacyRequestDRPStatus.in_progress,
            PrivacyRequestStatus.denied: PrivacyRequestDRPStatus.denied,
            PrivacyRequestStatus.in_processing: PrivacyRequestDRPStatus.in_progress,
            PrivacyRequestStatus.complete: PrivacyRequestDRPStatus.fulfilled,
            PrivacyRequestStatus.paused: PrivacyRequestDRPStatus.in_progress,
            PrivacyRequestStatus.error: PrivacyRequestDRPStatus.expired,
        }
        try:
            return PRIVACY_REQUEST_STATUS_TO_DRP_MAPPING[status]
        except KeyError:
            raise ValueError(f"Request has invalid DRP request status: {status.value}")
