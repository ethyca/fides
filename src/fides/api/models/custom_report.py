from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship

from fides.api.db.base_class import Base  # type: ignore[attr-defined]
from fides.api.models.fides_user import FidesUser
from fides.api.models.sql_models import (  # type: ignore[attr-defined]
    CustomFieldDefinition,
)

# Association between system-managed CustomReports (regulatory reporting
# templates) and the CustomFieldDefinitions they reference. Populated by
# the reporting-templates reconciler; not used for user-created reports.
reporting_template_custom_field = Table(
    "plus_reporting_template_custom_field",
    Base.metadata,
    Column(
        "custom_report_id",
        String,
        ForeignKey("plus_custom_report.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "custom_field_definition_id",
        String,
        ForeignKey(CustomFieldDefinition.id, ondelete="CASCADE"),
        primary_key=True,
    ),
)


class CustomReport(Base):
    @declared_attr
    def __tablename__(self) -> str:
        return "plus_custom_report"

    name = Column(String, unique=True)
    type = Column(String, nullable=False)
    created_by = Column(
        String,
        ForeignKey(FidesUser.id_field_path, ondelete="SET NULL"),
        nullable=True,
    )
    config = Column(MutableDict.as_mutable(JSONB))
    # Populated only for system-managed reporting templates.
    # ``system_template_key`` is the stable template identifier (e.g. "ico",
    # "dpc", "cnil"); ``location_code`` is the fides location that gates the
    # template's visibility (e.g. "gb", "ie", "fr"). Both are NULL for
    # user-created reports.
    system_template_key = Column(String, nullable=True, index=True)
    location_code = Column(String, nullable=True, index=True)

    custom_field_definitions = relationship(
        CustomFieldDefinition,
        secondary=reporting_template_custom_field,
    )
