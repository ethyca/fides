from enum import Enum

from citext import CIText
from sqlalchemy import ARRAY, Column
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship

from fides.api.db.base_class import Base
from fides.api.models.fides_user import FidesUser
from fides.api.models.sql_models import System  # type: ignore[attr-defined]


class CustomTaxonomyColor(str, Enum):
    WHITE = "taxonomy_white"
    RED = "taxonomy_red"
    ORANGE = "taxonomy_orange"
    YELLOW = "taxonomy_yellow"
    GREEN = "taxonomy_green"
    BLUE = "taxonomy_blue"
    PURPLE = "taxonomy_purple"
    SANDSTONE = "sandstone"
    MINOS = "minos"


class SystemGroup(Base):
    @declared_attr
    def __tablename__(self) -> str:
        return "system_group"

    fides_key = Column(
        String,
        ForeignKey("taxonomy_element.fides_key", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    label_color = Column(
        EnumColumn(CustomTaxonomyColor, values_callable=lambda x: [i.value for i in x]),
        nullable=True,
    )
    data_steward_username = Column(
        CIText,
        ForeignKey(FidesUser.username, ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    data_uses = Column(
        ARRAY(String),
        nullable=False,
        server_default="{}",
        default=list,
    )  # a list of `fides_key`s of `DataUse` records
    data_steward = relationship(
        "FidesUser", foreign_keys=[data_steward_username], lazy="selectin"
    )

    systems = relationship(
        System,
        secondary="system_group_member",
        back_populates="system_groups",
        viewonly=True,
    )


class SystemGroupMember(Base):
    @declared_attr
    def __tablename__(self) -> str:
        return "system_group_member"

    system_group_id = Column(
        String(255), ForeignKey("system_group.id", ondelete="CASCADE"), index=True
    )
    system_id = Column(
        String(255), ForeignKey("ctl_systems.id", ondelete="CASCADE"), index=True
    )

    __table_args__ = (
        UniqueConstraint(
            "system_group_id",
            "system_id",
            name="uq_system_group_member_group_system",
        ),
    )
