from __future__ import annotations

from uuid import uuid4

from sqlalchemy import Column, ForeignKey, String

from fides.api.db.base_class import Base


class ExperienceNotices(Base):
    """
    A many-to-many table that links Privacy Notices to shared Privacy Experience Configs.
    """

    def generate_uuid(self) -> str:
        """
        Generates a uuid with a prefix based on the tablename to be used as the
        record's ID value
        """
        try:
            prefix = f"{self.current_column.table.name[:3]}_"  # type: ignore
        except AttributeError:
            prefix = ""
        uuid = str(uuid4())
        return f"{prefix}{uuid}"

    # Overrides Base.id so this is not a primary key.
    # Instead, we have a composite PK of notice_id and experience_config_id
    id = Column(String(255), default=generate_uuid)

    notice_id = Column(
        String,
        ForeignKey("privacynotice.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        primary_key=True,
    )
    experience_config_id = Column(
        String,
        ForeignKey("privacyexperienceconfig.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        primary_key=True,
    )
