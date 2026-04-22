"""Shared persistence of custom privacy request fields.

Both ``PrivacyRequest`` and ``ConsentRequest`` attach user-submitted custom
fields to a row in the ``custompeivacyrequestfield`` table via a foreign key
column that differs between the two (``privacy_request_id`` vs
``consent_request_id``)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Dict, Optional

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.schemas.redis_cache import (
    CustomPrivacyRequestField as CustomPrivacyRequestFieldSchema,
)
from fides.api.schemas.redis_cache import is_empty_multivalue
from fides.config import CONFIG

if TYPE_CHECKING:
    pass


class CustomPrivacyRequestFieldPersistenceMixin:
    """Mixin providing ``persist_custom_privacy_request_fields``.

    Subclasses must set ``_custom_field_fk_column`` — the FK column on
    ``CustomPrivacyRequestField`` pointing at this row (e.g.
    ``"privacy_request_id"`` / ``"consent_request_id"``) — and expose
    ``self.id``.
    """

    _custom_field_fk_column: ClassVar[str] = ""

    def persist_custom_privacy_request_fields(
        self,
        db: Session,
        custom_privacy_request_fields: Optional[
            Dict[str, CustomPrivacyRequestFieldSchema]
        ],
    ) -> None:
        if not custom_privacy_request_fields:
            return

        if not CONFIG.execution.allow_custom_privacy_request_field_collection:
            logger.info(
                "Custom fields provided in {} {}, but config setting 'CONFIG.execution.allow_custom_privacy_request_field_collection' prevents their storage.",
                type(self).__name__,
                self.id,
            )
            return

        from fides.api.models.privacy_request.privacy_request import (
            CustomPrivacyRequestField,
        )

        for key, item in custom_privacy_request_fields.items():
            if is_empty_multivalue(item.value):
                continue
            CustomPrivacyRequestField.create(
                db=db,
                data={
                    self._custom_field_fk_column: self.id,
                    "field_name": key,
                    "field_label": item.label,
                    "encrypted_value": {"value": item.value},
                    "hashed_value": CustomPrivacyRequestField.hash_value(item.value),
                },
            )
