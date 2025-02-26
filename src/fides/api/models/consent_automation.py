from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import RelationshipProperty, Session, relationship

from fides.api.db.base_class import Base, FidesBase  # type: ignore[attr-defined]
from fides.api.models.privacy_notice import PrivacyNotice


class ConsentAutomation(Base):
    @declared_attr
    def __tablename__(self) -> str:
        return "plus_consent_automation"

    connection_config_id = Column(
        String,
        ForeignKey("connectionconfig.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    consentable_items: "RelationshipProperty[List[ConsentableItem]]" = relationship(
        "ConsentableItem",
        back_populates="consent_automation",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @classmethod
    def create(
        cls, db: Session, *, data: Dict[str, Any], check_name: bool = False
    ) -> "ConsentAutomation":
        consentable_items = data.pop("consentable_items", [])
        consent_automation = super().create(db=db, data=data, check_name=check_name)
        link_consentable_items_to_consent_automation(
            db, consentable_items, consent_automation
        )
        return consent_automation

    def update(self, db: Session, *, data: Dict[str, Any]) -> "ConsentAutomation":
        consentable_items = data.pop("consentable_items", [])
        super().update(db=db, data=data)
        link_consentable_items_to_consent_automation(db, consentable_items, self)
        return self

    @classmethod
    def create_or_update(cls, db: Session, *, data: Dict[str, Any]) -> "ConsentAutomation":  # type: ignore[override]
        consent_automation = ConsentAutomation.filter(
            db=db,
            conditions=(
                ConsentAutomation.connection_config_id == data["connection_config_id"]
            ),
        ).first()

        if consent_automation:
            consent_automation.update(db=db, data=data)
        else:
            consent_automation = cls.create(db=db, data=data)

        return consent_automation


def link_consentable_items_to_consent_automation(
    db: Session,
    consentable_items: List[Dict[str, Any]],
    consent_automation: ConsentAutomation,
) -> None:
    """
    Takes a hierarchical list of consentable items and maps them to database items.
    Attaches the database items to the consent automation.
    """

    existing_items = {
        (item.type, str(item.external_id)): item
        for item in consent_automation.consentable_items
    }

    def process_items(
        items_data: List[Dict[str, Any]], parent_id: Optional[str] = None
    ) -> List[ConsentableItem]:
        processed_items = []
        for item_data in items_data:
            external_id = str(item_data["external_id"])
            item_type = item_data["type"]

            key = (item_type, external_id)
            item = existing_items.get(key)

            if item:
                item.notice_id = item_data.get("notice_id")
            else:
                item = ConsentableItem(
                    external_id=external_id,
                    consent_automation_id=consent_automation.id,
                    parent_id=parent_id,
                    type=item_type,
                    name=item_data["name"],
                    notice_id=item_data.get("notice_id"),
                )
                db.add(item)
                # flush to the DB so we can get the auto-generated ID for this item
                db.flush()

            processed_items.append(item)

            if "children" in item_data:
                processed_items.extend(
                    process_items(item_data["children"], parent_id=item.id)
                )

        return processed_items

    try:
        consent_automation.consentable_items = process_items(consentable_items)
        db.commit()
    except IntegrityError as exc:
        logger.error("Error occurred while attempting to save consentable items", exc)

    db.refresh(consent_automation)


class ConsentableItem(Base):
    @declared_attr
    def __tablename__(self) -> str:
        return "plus_consentable_item"

    id = Column(
        String(255), primary_key=True, index=True, default=FidesBase.generate_uuid
    )

    consent_automation_id = Column(
        String,
        ForeignKey(ConsentAutomation.id_field_path, ondelete="CASCADE"),
        nullable=False,
    )
    external_id = Column(
        String,
        nullable=False,
    )
    parent_id = Column(
        String,
        ForeignKey("plus_consentable_item.id", ondelete="CASCADE"),
        nullable=True,
    )
    notice_id = Column(String, ForeignKey(PrivacyNotice.id_field_path), nullable=True)
    type = Column(
        String,
        nullable=False,
    )
    name = Column(String, nullable=False)
    consent_automation = relationship(
        "ConsentAutomation", back_populates="consentable_items"
    )
    children: "RelationshipProperty[List[ConsentableItem]]" = relationship(
        "ConsentableItem",
        back_populates="parent",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    parent: "RelationshipProperty[Optional[ConsentableItem]]" = relationship(
        "ConsentableItem",
        back_populates="children",
        remote_side=[id],
    )

    __table_args__ = (UniqueConstraint("consent_automation_id", "type", "external_id"),)
