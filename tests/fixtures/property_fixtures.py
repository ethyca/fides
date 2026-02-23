from typing import Generator

import pytest
from sqlalchemy.orm import Session

from fides.api.models.property import Property
from fides.api.schemas.property import Property as PropertySchema
from fides.api.schemas.property import PropertyType


@pytest.fixture(scope="function")
def property_a(db) -> Generator:
    prop_a = Property.create(
        db=db,
        data=PropertySchema(
            name="New Property",
            type=PropertyType.website,
            experiences=[],
            messaging_templates=[],
            paths=["test"],
        ).model_dump(),
    )
    yield prop_a
    prop_a.delete(db=db)


@pytest.fixture(scope="function")
def property_b(db: Session) -> Generator:
    prop_b = Property.create(
        db=db,
        data=PropertySchema(
            name="New Property b",
            type=PropertyType.website,
            experiences=[],
            messaging_templates=[],
            paths=[],
        ).model_dump(),
    )
    yield prop_b
    prop_b.delete(db=db)
