from typing import Dict

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session

from fides.api.db.base_class import Base


class SaasTemplateDataset(Base):
    """
    Stores the latest template dataset for each SaaS connection type.

    This table maintains a record of the template datasets that come with
    Fides for each SaaS connector type. It's used as a baseline for
    detecting customer modifications to datasets.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "saas_template_dataset"

    connection_type = Column(String, nullable=False, unique=True, index=True)
    dataset_json = Column(JSONB, nullable=False)

    def __repr__(self) -> str:
        return f"<SaasTemplateDataset(connection_type='{self.connection_type}')>"

    @classmethod
    def get_or_create(  # type: ignore[override]
        cls,
        db: Session,
        connector_type: str,
        dataset_json: Dict,
    ) -> tuple[bool, "SaasTemplateDataset"]:
        """
        Get existing SaasTemplateDataset by connector_type or create if it doesn't exist.

        Args:
            db: Database session
            connector_type: The connection type identifier
            dataset_json: The dataset JSON to use if creating

        Returns:
            Existing or newly created SaasTemplateDataset instance
        """
        created = False
        template_dataset = cls.get_by(
            db=db, field="connection_type", value=connector_type
        )

        if not template_dataset:
            template_dataset = cls.create(
                db=db,
                data={
                    "connection_type": connector_type,
                    "dataset_json": dataset_json,
                },
            )
            created = True

        return created, template_dataset
